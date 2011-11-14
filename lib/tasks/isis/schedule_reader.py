from ...browser import parsers
from .. import *

import lxml.html
import lxml.etree

import re
import logging
import webbrowser

logger = logging.getLogger("task.schedule.reader")

_semester_codes = {"spring":"RSI-SSCHED", "summer":"RSI-USCHED",
                   "fall":"RSI-FSCHED"}

_table_inner_re = re.compile(
    r'\<div id="reg_sched"\>.*?\<table\>(.+?)\</table\>',
    re.IGNORECASE | re.DOTALL
)
_table_tr_re = re.compile(r"\</?tr/?\>", re.IGNORECASE)

# define weekday characters used in the schedule table
MONDAY = "M"; TUESDAY = "T"; WEDNESDAY = "W"; THURSDAY = "R"; FRIDAY = "F"

class ScheduleReader(BaseUFTaskManager, BaseTaskManager):
    """Attempts to provide information from the ISIS schedule page in as
    transparent of a format as possible.
    
    *Please Note:* Getting properties from this page may cause a page-load to
    happen, in order to pull the required data, however caching is done when
    possible. It is suggested that you call
    :py:func:`...browser.plugins.uf.login.LoginBrowserPlugin.uf_set_autologin`
    on the browser object ahead of time."""
    
    def __init__(self, semester, browser=None):
        BaseUFTaskManager.__init__(self)
        BaseTaskManager.__init__(self, browser)
        self.__semester = semester
        self.__loaded = False
        self._page_src = None # as the result of parser.passthrough_args
    
    def get_semester(self):
        return self.__semester
    
    semester = property(get_semester)
    
    def get_semester_code(self):
        return _semester_codes[self.semester.lower()]
    
    semester_code = property(get_semester_code)
    
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
    
    def get_classes(self):
        """Returns a list of dictionaries, one for each class, containing
        information pulled from the table.
        
        Data:
        section -- An string representing the section code (usually written as
                   an integer, _but not always_).
        type -- A string representing the "Type" column in the table. I have no
                clue what this is supposed to represent. If someone could shed
                some light on it, that would be appreciated.
        course -- A string representing the course number, in the format
                  "COL1234", where "COL" is the college name, and "1234" is the
                  4-digit code for that course within the college
        credits -- An integer representing the number of credits that class
                   gives.
        times -- A list of dictionaries, representing subcolumns, "days",
                 "periods", "building", and "room". Each dictionary represents a
                 set of grouped times and locations. "days" is a tuple of
                 single-character strings, "M", "T", "W", "R", and "F", which
                 match with :py:data:`MONDAY`, :py:data:`TUESDAY`,
                 :py:data:`WEDNESDAY`, :py:data:`THURSDAY`, and
                 :py:data:`FRIDAY`, respectively. "periods" is a tuple of ints,
                 representing each period that class if being held at. For
                 example, "7-9" would turn into ``(7, 8, 9)``. Finally,
                 "building" and "room" both contain strings with their matching
                 information.
        """
        self.auto_load()
        return self.__classes
    
    classes = property(get_classes)
    
    def get_campus_map_url(self):
        self.auto_load()
        return self.__campus_map_url
    
    campus_map_url = property(get_campus_map_url)
    
    def open_campus_map(self, new=1, autoraise=True):
        """Uses the webbrowser module to open the campus map webpage. No
        authentication is needed on the side of the browser."""
        webbrowser.open(self.campus_map_url, new=new, autoraise=autoraise)
    
    
    
    def auto_load(self):
        """Checks to see if the page has been loaded before. If not, it loads
        it."""
        if not self.__loaded:
            self.force_reload()
    
    def force_reload(self):
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
        # look in the table
        rows = working_block.xpath("./table")[0]
        # fix isis' crappy html code
        # Also, we need to grab it before lxml has a chance to try to parse it
        rows = lxml.html.fragment_fromstring(
            "<table>%s</table>" % self._fix_table_html(
                _table_inner_re.search(str_source).group(1)
            )
        )
        # start ripping things from the schedule and putting them into a dict
        headers = [i.text.strip().lower() for i in rows[0]]
        row_dicts = []
        for r in rows[1:]:
            d = {}; i = 0; k = 0
            while i < len(r):
                tag = r[i]
                text = tag.text.strip() if tag.text else None
                if not text: text = None
                if "colspan" in tag.attrib:
                    span = int(tag.get("colspan").strip())
                    for m in range(span):
                        if k + m >= len(headers):
                            break # fucking broken isis html
                        d[headers[k + m]] = text
                    k += span
                else:
                    d[headers[k]] = text
                    k += 1
                i += 1
            row_dicts.append(d)
        rows = row_dicts[:-1] # get rid of footer
        total_credits = int(row_dicts[-1]["credits"]) # we'll use this for
                                                      # validation later on
        
        # utility function
        period_to_int = lambda period: \
            11 + int(period[1:]) if period[0].upper() == "E" else int(period)
        # parse credits, days, and periods columns, and make their formats more
        # user-friendly
        for r in rows:
            r["credits"] = int(r["credits"]) if r["credits"] is not None \
                                             else None
            r["days"] = tuple(r["days"].upper().split())
            # make periods into a tuple of ints
            period = r["periods"]
            if period is None:
                pass
            elif "to be" in period or "tba" in period.lower():
                r["periods"] = None
                r["days"] = None
            elif "-" in period:
                index = period.index("-")
                start = period[:index]; end = period[index + 1:]
                r["periods"] = tuple(range(period_to_int(start),
                                           period_to_int(end) + 1))
            else:
                r["periods"] = (period_to_int(period), )
        
        if not total_credits == sum([0 if not i["credits"] else i["credits"] \
                                     for i in rows]):
            logger.error("Table reading likely failed: ISIS' reported credit"
                         "total fails to match the sum of all credits.")
        
        classes = []
        
        build_time_dict = lambda i: {"days": rows[i]["days"],
                                     "periods": rows[i]["periods"],
                                     "building": rows[i]["bldg"],
                                     "room": rows[i]["room"]}
        # fix orphans and populate classes list with dicts
        for i in range(len(rows)):
            if rows[i]["section"] is not None: # no orphans here!
                class_dict = {}
                classes.append(class_dict)
                class_dict["section"] = rows[i]["section"]
                class_dict["type"] = rows[i]["type"]
                class_dict["course"] = rows[i]["course"]
                class_dict["credits"] = rows[i]["credits"]
                if rows[i]["periods"] is None:
                    class_dict["times"] = None
                else:
                    class_dict["times"] = [build_time_dict(i), ]
            else: # we have an orphaned row
                parent = classes[-1]
                parent["times"].append(build_time_dict(i))
        
        self.__classes = classes
        
        # find the url for the campus map
        try:
            self.__campus_map_url = \
                working_block.xpath("./a[@target='map']")[0].attrib["href"]
        except IndexError:
            logger.warning("Map could not be found. Do you not have any "
                           "classes with locations? Reverting map url to "
                           "'http://campusmap.ufl.edu'.")
            self.__campus_map_url = "http://campusmap.ufl.edu"
        
        self._page_src = byte_source
        self.__loaded = True
    
    def _fix_table_html(self, source):
        """Source should be a string with the contents of the table, excluding
        the <table> tags"""
        rows = \
            [i for i in [k.strip() for k in _table_tr_re.split(source)] if i]
        return "<tr>%s</tr>" % "</tr><tr>".join(rows)
    
    def get_formatted_classes_string(self):
        """Takes the data from the schedule table and re-formats it into a
        pretty string, useful for printing out on a shell."""
        classes = self.classes
        
        # utility function
        table_str = lambda x: \
            "" if x is None else \
            " ".join([str(i) for i in x]) if isinstance(x, tuple) or \
                                             isinstance(x, list) else \
            str(x)
        
        section_col = ["section"]
        type_col = ["type"]
        course_col = ["course"]
        credits_col = ["credits"]
        days_col = ["days"] # part of times
        periods_col = ["periods"] # part of times
        building_col = ["building"] # part of times
        room_col = ["room"] # part of times
        
        # build the columns
        for c in classes:
            section_col.append(table_str(c["section"]))
            type_col.append(table_str(c["type"]))
            course_col.append(table_str(c["course"]))
            credits_col.append(table_str(c["credits"]))
            if c["times"] is None:
                days_col.append("TBA")
                periods_col.append("TBA")
                building_col.append("TBA")
                room_col.append("TBA")
            else:
                first_round = True
                for t in c["times"]:
                    days_col.append(table_str(t["days"]))
                    periods_col.append(table_str(t["periods"]))
                    building_col.append(table_str(t["building"]))
                    room_col.append(table_str(t["room"]))
                    if first_round:
                        first_round = False
                        continue
                    section_col.append("")
                    type_col.append("")
                    course_col.append("")
                    credits_col.append("")
        
        # turn it into a string
        result = ""
        columns = [section_col, type_col, course_col, credits_col, days_col,
                   periods_col, building_col, room_col]
        widths = [max([len(elem) for elem in col]) for col in columns]
        for r in range(len(section_col)):
            for c in range(len(columns)):
                result += columns[c][r].ljust(widths[c] + 2)
            result += "\n"
        return result[:-1] # trim off the last '\n'
    
    formatted_classes_string = property(get_formatted_classes_string)
