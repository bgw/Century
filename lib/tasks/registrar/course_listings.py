"""The module is a work-in-progress, and doesn't actually do anything yet."""

from .. import *
from ...browser import parsers
from .. import courses
from ..courses import fuzzy_match
import time
import logging

_course_archive_url = "http://www.registrar.ufl.edu/socarchive/"

_course_schedule_urls = None

logger = logging.getLogger("lib.tasks.registrar.course_listings")

class CourseReader(BaseUFTaskManager, BaseTaskManager):
    """Generates the url for, and uses the Registrar list of courses. If a
    matching url cannot be found or generated, a ``KeyError`` will be raised.
    
    *Keyword arguments:*
    
    year -- Either a string or an int representing the year to look into, such
            as "2011". Please note that the registrar's records only date back
            to 2001.
    semester -- A string with a value :py:data:`SPRING`, :py:data:`SUMMER`, or
                :py:data:`FALL`.
    full -- A boolean, ``True`` if you want all the course listings, ``False``
            if you are an online student, and only want the web-based course
            listings.
    browser -- A browser to use. If passed ``None``, a new one is automatically
               created.
    """
    def __init__(self, year, semester, full=True, browser=None):
        BaseUFTaskManager.__init__(self)
        BaseTaskManager.__init__(self, browser)
        
        year = int(year)
        # check argument validity
        if year < 2001:
            raise KeyError(
                "Course listings are unavailable for the year %d." % year
            )
        if not full and year < 2005:
            raise KeyError(
                "Web-Course listings are unavailable for the year %d." % year
            )
        
        if semester == courses.Semesters.SPRING:
            month = "01"
        elif semester == courses.Semesters.SUMMER:
            month = "06"
        elif semester == courses.Semesters.FALL:
            month = "08"
        self.__base_url = "http://www.registrar.ufl.edu/soc/%d%s/%s/" % \
                          (year, month, "all" if full else "web")
        self.__departments = None
        self.__loaded = False
    
    def get_base_url(self):
        return self.__base_url
    
    base_url = property(get_base_url)
    
    def get_departments(self):
        self.auto_load()
        return self.__departments
    
    departments = property(get_departments)
    
    def lookup_prefix(self, prefix, fast=True):
        for dep in self.departments:
            if prefix.upper() in dep.get_prefixes(fast):
                yield dep
    
    def lookup_course(self, course_code, fast=True):
        if not hasattr(course_code, "prefix"):
            course_code = courses.CourseCode(course_code)
        for dep in self.lookup_prefix(course_code.prefix):
            found = False
            for course in dep.course_list:
                if course.course_code == course_code:
                    yield course
            if found:
                break
    
    def auto_load(self):
        if not self.__loaded:
            self.force_load()
    
    def force_load(self):
        """
        .. note::
            Calling this function, in addition to loading the webpage, performs
            some moderately CPU intensive tasks to attempt to determine what
            department name matches to what department name (with fuzzy string
            matching). This shouldn't be much of a concern though, as the
            processing shouldn't take more than about a tenth of a second. The
            largest bottleneck is still probably the page load time.
        """
        # process the raw html data into an intermediate form
        lxml_source = self.browser.load_page(self.base_url,
                                             parser=parsers.lxml_html)
        # get department names and thir html page names from the dropdown menu
        department_menu = self.__parse_department_menu(lxml_source.cssselect(
            ".soc_menu select"
        )[0])
        # get prefixes and matching department names from the central table
        # Note: There can be multiple prefixes for each department, and multiple
        #       departments for each prefix
        prefix_table = self.__parse_course_prefix_table(lxml_source.cssselect(
            "#soc_content table.filterable"
        )[0])
        
        start_time = time.time()
        
        # We need to build Department objects from all the data we have.
        # Unfortunately, UF calls departments by different names, depending on
        # where they're listed! This means that we need to bring in
        # lib.tasks.courses.fuzzy_match to align things!
        
        # build a list of department names according to department_menu
        department_menu_department_names = next(zip(*department_menu)) # unzip
        
        # build a list of department names according to prefix_table
        prefix_table_department_names = list(zip(*prefix_table))[1] # unzip
        
        # Build a list of department names, and their similars
        # I cannot begin to tell you how much work it was to get this working,
        # and to get it working relatively fast
        matched_depts = fuzzy_match.similar_zip(
            department_menu_department_names,
            set(prefix_table_department_names),
            scoring_algorithm=_scoring_algorithm,
            key=lambda v: _replace_abbreviations(v.lower()),
            single_match=True,
            high_is_similar=True,
            direct_first=True, # optimization
            max_processes=5    # optimization
        )
        
        assert len(matched_depts) == len(department_menu_department_names)
        
        logger.debug("Matched department names:\n    %s" %
                     "\n    ".join(" -> ".join(i) for i in matched_depts))
        logger.info("Pairing %d department names took %.2f seconds." %
                    (len(matched_depts), time.time() - start_time))
        
        url_lookup = dict(department_menu)
        prefix_lookup = self.__parallel_lists_to_tuple_dict(
                                            *reversed(list(zip(*prefix_table))))
        departments = []
        for department_menu_name, prefix_table_name in matched_depts:
            # use the department names from prefix_table for the primary name,
            # because they are typically written out in a cleaner format
            alternate_names = [department_menu_name] if \
                              department_menu_name != prefix_table_name else []
            departments.append(Department(prefix_table_name, alternate_names,
                                          prefix_lookup[prefix_table_name],
                                          self.browser, self.base_url,
                                          url_lookup[department_menu_name]))
        self.__departments = departments
        self.__loaded = True
    
    def __parse_course_prefix_table(self, table):
        result_list = []
        for row in table.cssselect("tr")[1:]:
            result_list.append(tuple(
                cell.text_content().strip() for cell in row.cssselect("td")
            ))
        return result_list
    
    def __parse_department_menu(self, menu):
        options = menu.cssselect("option")[1:] # drop the first, garbage value
        result_list = []
        for o in options:
            name = o.text_content().strip()
            html_page = o.get("value").strip()
            result_list.append((name, html_page))
        return result_list
    
    def __parallel_lists_to_tuple_dict(self, list_a, list_b):
        tuple_dict = {}
        for a, b in zip(list_a, list_b):
            b_list = tuple_dict.get(a, [])
            b_list.append(b)
            tuple_dict[a] = b_list
        # convert dictionary values to tuples
        for key in tuple_dict:
            tuple_dict[key] = tuple(tuple_dict[key])
        return tuple_dict

class Department:
    def __init__(self, name, alternate_names=[], prefixes=[],
                 browser=None, base_url=None, relative_url=None):
        self.__name = name
        self.__alternate_names = alternate_names
        self._abbreviated_names = \
            [_replace_abbreviations(i) for i in [name] + alternate_names]
        self.__prefixes = prefixes
        self.__browser = browser
        self.__base_url = base_url
        self.__relative_url = relative_url
        self.__course_list = None
        self.__loaded = False
    
    def get_name(self):
        return self.__name
    
    name = property(get_name)
    
    def get_alternate_names(self):
        return self.__alternate_names
    
    alternate_names = property(get_alternate_names)
    
    def get_all_names(self):
        return [self.name] + self.alternate_names
    
    all_names = property(get_all_names)
    
    def get_prefixes(self, fast=True):
        if not fast:
            self.auto_load()
        return self.__prefixes
    
    prefixes = property(get_prefixes, doc="""
        Gives a heuristic guess at all the possible prefixes mapping to this
        department name. This is nothing more than an educated guess, and while
        the results here should be valid most of the time, they are not always.
        """)
    
    def get_browser(self):
        return self.__browser
    
    browser = property(get_browser)
    
    def _get_base_url(self):
        return self.__base_url
    
    _base_url = property(_get_base_url)
    
    def _get_relative_url(self):
        return self.__relative_url
    
    _relative_url = property(_get_relative_url)
    
    def _get_url(self):
        return self.browser.expand_relative_url(self._relative_url,
                                                relative_to=self._base_url)
    
    _url = property(_get_url)
    
    def get_course_list(self):
        self.auto_load()
        return self.__course_list
    
    course_list = property(get_course_list)
    
    def auto_load(self):
        if not self.__loaded:
            self.force_load()
    
    def force_load(self):
        # Load the department page's html and feed it to lxml:
        lxml_source = self.browser.load_page(self._url,
                                             parser=parsers.lxml_html)
        # We're only concerned about the table of courses: pull that out
        department_table = lxml_source.cssselect("#soc_content table")[1]
        department_table_rows = department_table.cssselect("tr")
        # The first few rows are are information about the department (0-2).
        #     We're not doing anything with them, so we'll just ignore them
        # Then we have the headers for the course table, we'll use these values
        #     as keys in a bunch of little dictionaries.
        header_row = department_table_rows[2]
        # The rest of the table contains the data about the courses
        course_rows = department_table_rows[3:]
        # Some data rows may contain junk comment data, discard it
        course_rows = [r for r in course_rows \
                       if not r.cssselect("th.soc_comment")]
        # process each header cell, converting lxml tags to strings
        headers = [i.text.strip().lower() for i in
                   header_row.cssselect(".colhelp a")]
        def stripped_or_none(tag): # utility function: gives stripped version of
                                   # a tag, or None if it's empty
            stripped = tag.text_content().strip()
            return stripped if stripped else None
        # turn each row in the table into little dicts, where we can look up
        #     data by the column (specified by the header)
        course_dicts = [
            dict(zip(headers, [stripped_or_none(i) for i in row]))
            for row in course_rows
        ]
        
        # We're done with our first stage of processing. Now we'll convert each
        # little dict into a Course object, and shove them all into a CourseList
        
        base_course_list = [] # the list we'll later build our CourseList from
        def build_meeting(d): # utility funciton: builds a meeting given a dict
            if not d["day(s)"] or "tba" in d["day(s)"].lower():
                return None
            return courses.CourseMeeting(days=d["day(s)"], periods=d["period"],
                                         building=d["bldg"], room=d["room"])
        for d in course_dicts:
            if d["course"]:
                credits = int(d["cred"]) if "var" not in d["cred"].lower() \
                                         else -1
                meeting = build_meeting(d)
                c = courses.Course(d["course"], d["sect"],
                                   title=d["course title & textbook(s)"],
                                   credits=credits,
                                   meetings=[meeting] if meeting else [],
                                   gen_ed_credit=d["ge"], gordon_rule=d["wm"],
                                   instructors=[i.strip() for i in
                                                d["instructor(s)"].split("\n")])
                base_course_list.append(c)
            else:
                meeting = build_meeting(d)
                if meeting:
                    base_course_list[-1].meetings.append(meeting)
        
        self.__course_list = courses.CourseList(base_course_list)
        
        # Using the course list, find the prefixes for this department
        self.__prefixes = []
        for c in self.__course_list:
            if c.course_code.prefix not in self.__prefixes:
                self.__prefixes.append(c.course_code.prefix)
        
        self.__loaded = True
    
    def rate_similarity(self, department_name, fast=False):
        if fast:
            algorithm = _scoring_algorithm
        else:
            algorithm = fuzzy_match.lev_ratio
        department_name = _replace_abbreviations(department_name)
        return max(algorithm(department_name, i)
                   for i in self._abbreviated_names)
    
    def __hash__(self):
        return hash(self._abbreviated_names[0])
    
    def __str__(self):
        return "Department: %s; Prefixes: %s%s" % (
            self.name,
            " ".join(self.prefixes) if self.prefixes else "???",
            "" if self.__loaded else " (best guess)"
        )

# make a list of common abbreviations used in department names, to improve
# accuracy when comparing department names (this helps a lot)
_abbreviations = (
    ("&", "and"),
    ("  ", " "),
    ("languages, literatures and cultures", "languages lit/culture"),
    ("sociology, criminology and law", "sociology/criminology/law"),
    ("tourism, recreation and sport", "tourism recreation sp"),
    ("pharmacy", "pha"),
    ("special education, school psychology and early childhood studies",
        "sp ed/sch psyc/early ch"),
    ("management", "mgt"),
    ("center for ", ""),
    ("manage", "mgt"),
    ("pharmacy", "pha"),
    ("veterinary medicine", "medicine"),
    ("human", "hum"),
    ("pathol,immunol and lab med", "pathobiology"),
    ("biological", "bio"),
    ("biology", "bio"),
    ("biolog", "bio"),
    ("developmental", "dev"),
    ("development", "dev"),
    ("information", "info"),
    ("engineering", "engineer"),
    ("science", "sci"),
    (" and ", "/"),
    (" - ", "-"),
    ("-", " "),
    (",", ""),
)

def _replace_abbreviations(s):
    for k, v in _abbreviations:
        s = s.replace(k, v)
    return s

def _scoring_algorithm(s1, s2):
    # this can't be part of a class, because then muliprocessing wouldn't be
    # able to pickle it.
    scores = (fuzzy_match.frequency_ratio(s1, s2),
              fuzzy_match.hamming_ratio(s1, s2, False))
    return (max(scores) + sum(scores)) / 2
