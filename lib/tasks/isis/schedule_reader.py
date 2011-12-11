from ...browser import parsers
from .. import *
from ..isis import table_to_list
from .. import courses

import lxml.html
import lxml.etree

import re
import logging
import webbrowser

logger = logging.getLogger("task.schedule.reader")

# a lookup table for isis' page codes
_semester_codes = {courses.Semesters.SPRING:"RSI-SSCHED",
                   courses.Semesters.SUMMER:"RSI-USCHED",
                   courses.Semesters.FALL:"RSI-FSCHED"}

_table_inner_re = re.compile(
    r'\<div id="reg_sched"\>.*?\<table\>(.+?)\</table\>',
    re.IGNORECASE | re.DOTALL
)

class ScheduleReader(BaseUFTaskManager, BaseTaskManager):
    """Attempts to provide information from the ISIS schedule page in as
    transparent of a format as possible.
    
    *Keyword Arguments:*
    
    ``semester``
        A string, "spring", "summer", or "fall", representing what semester
        schedule we should pull up.
    ``browser``
        A custom browser object to use. (If None is passed, a new uf-browser
        instance is created.)
    
    .. warning::
        Getting properties from this page may cause a page-load to happen, in
        order to pull the required data, however caching is done when possible.
        It is suggested that you call :func:`lib.browser.plugins.uf.login.
        LoginBrowserPlugin.uf_set_autologin` on the browser object ahead of
        time.
    """
    
    def __init__(self, semester, browser=None):
        BaseUFTaskManager.__init__(self)
        BaseTaskManager.__init__(self, browser)
        self.__semester = semester
        self.__loaded = False
        self._page_src = None # as the result of parser.passthrough_args
    
    def get_semester(self):
        """Gets the value of :attr:`semester`."""
        return self.__semester
    
    semester = property(get_semester, doc="""
        A string, "spring", "summer", or "fall", representing what semester
        schedule we are working with.""")
    
    def get_semester_code(self):
        """Gets the value of :attr:`semester_code`."""
        return _semester_codes[self.semester.lower()]
    
    semester_code = property(get_semester_code, doc="""
        Gets a value like "RSI-SSCHED", which can be used as an HTTP GET or POST
        parameter in the request for the page with the schedule.""")
    
    def _get_page_byte_source(self):
        self.auto_load()
        return self.__page_byte_source
    
    _page_byte_source = property(_get_page_byte_source)
    
    def get_user_info(self):
        """Returns a list of tuple-pairs containing the user's info in all
        lowercase. The first item in every tuple is the datatype, such as
        "major" or "college". The second item is the related information. An
        example of this could be ``("college", "engineering")``. The pairs
        defined match with those on the top of the ISIS schedule page."""
        self.auto_load()
        return self.__user_info
    
    user_info = property(get_user_info)
    
    def get_user_info_dict(self):
        """Returns a dictionary containing the information in ``user_info``. If
        there are multiple pieces of information for the same key, at least one
        of the values will be included in the dictionary, however which one is
        undefined."""
        self.auto_load()
        return self.__user_info_dict
    
    user_info_dict = property(get_user_info_dict)
    
    def get_course_list(self):
        """Gets the value of :attr:`course_list`."""
        self.auto_load()
        return self.__course_list
    
    course_list = property(get_course_list, doc="""
        A :class:`lib.tasks.courses.CourseList` object filled with
        :class:`lib.tasks.courses.Course` objects. The ``course_code``,
        ``section_number``, ``credits``, and ``meetings`` fields are populated
        in each :class:`lib.tasks.isis.Course` object.
        
        .. note::
            Formerly, this class had a function for getting a url to a campus
            map. That functionality is now in :attr:`lib.tasks.courses.
            CourseList.campus_map_url`.
        """)
    
    def auto_load(self):
        """Checks to see if the page has been loaded before. If not, it loads
        it."""
        if not self.__loaded:
            self.force_load()
    
    def force_load(self):
        """Loads the page, regardless of if it has already been loaded or
        not."""
        byte_source = self.browser.load_isis_page(
            self.semester_code, parser=parsers.passthrough_args
        )
        str_source = parsers.passthrough_str(*byte_source)
        self.__page_byte_source = byte_source
        lxml_source = parsers.lxml_html(*byte_source)
        
        
        # pull user info
        working_block = lxml_source.get_element_by_id("phead")
        label_data_pairs = working_block.xpath("./tr/td")
        label_data_pairs = [i.text.lower().strip() for i in label_data_pairs]
        # make a list of tuples and a dictionary containing all the user info
        self.__user_info = [
            (label_data_pairs[i * 2][:-1], label_data_pairs[i * 2 + 1]) \
            for i in range(len(label_data_pairs) // 2)
        ]
        self.__user_info_dict = dict(self.__user_info)
        
        
        
        # pull from the schedule block
        working_block = lxml_source.get_element_by_id("reg_sched")
        
        # Put it into a list of dicts
        # We need to grab it before lxml has a chance to try to parse it
        rows = table_to_list(_table_inner_re.search(str_source).group(1))
        total_credits = int(rows[-1]["credits"]) # we'll use this for validation
        rows = rows[:-1] # get rid of footer
        
        # parse columns
        for r in rows:
            r["credits"] = int(r["credits"]) if r["credits"] is not None \
                                             else None
        
        # validate that the table was processed correctly
        if not total_credits == sum(i["credits"] for i in rows if i["credits"]):
            logger.error("Table reading likely failed: ISIS' reported credit"
                         "total fails to match the sum of all credits.")
        
        course_list = courses.CourseList()
        for r in rows:
            # get the meeting defined in the row
            if "to be" not in r["days"] and "tba" not in r["days"]:
                meet = courses.CourseMeeting(r["days"], r["periods"], r["bldg"],
                                             r["room"])
            else:
                meet = None
            if r["section"] is not None: # no orphans here!
                course_list.append(
                    courses.Course(r["course"], r["section"],
                                  credits=r["credits"],
                                  meetings=[meet] if meet else [])
                )
            else: # we have an orphaned row
                # an orphaned row is one where only a meeting is defined, the
                # class declaration is implicitly defined by last non-orphaned
                # row
                course_list[-1].meetings.append(meet)
        
        self.__course_list = course_list
