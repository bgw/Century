"""This module contains various classes for organizing and managing courses and
course properties as objects. Things are done in an extensible fashion, so that
if you want to append additional information to course objects, you can do so
easily."""

from collections import UserList
from collections import UserString
from string import Template
import re

class CourseList(UserList):
    """Represents a list of :class:`Course` objects, extendable to incorporate
    pulling lists of courses from various sources, such as an ISIS schedule, or
    the UF registrar."""
    
    def __init__(self, data=None):
        """Construct a new list from a given list of :class:`Course`s. If no
        list is given, a new empty list is made."""
        UserList.__init__(self, data if data else [])
    
    def _init_subset(self, data):
        """Should give a new list that has the same properties as the current
        list, but with new data."""
        return self.__class__(data)
    
    def __add__(self, other):
        if isinstance(other, UserList):
            return self._init_subset(self.data + other.data)
        elif isinstance(other, type(self.data)):
            return self._init_subset(self.data + other)
        return self._init_subset(self.data + list(other))
    
    def __radd__(self, other):
        if isinstance(other, UserList):
            return self._init_subset(other.data + self.data)
        elif isinstance(other, type(self.data)):
            return self._init_subset(other + self.data)
        return self._init_subset(list(other) + self.data)
    
    def __getitem__(self, n):
        res = UserList.__getitem__(self, n)
        if isinstance(n, slice):
            return self._init_subset(res)
        return res
    
    def __mul__(self, n):
        return self._init_subset(self.data*n)
    __rmul__ = __mul__
    
    def __str__(self):
        return "\n".join([str(course) for course in self])
    
    def get_campus_map_url_arguments(self):
        """Gets the value of :attr:`campus_map_url_arguments`."""
        return ";".join(i.campus_map_url_arguments for i in self)
    
    campus_map_url_arguments = property(get_campus_map_url_arguments, doc="""
        Gives the HTTP GET argument for the :attr:`campus_map_url`, useful when
        putting of multiple courses on the same map.""")
    
    def get_campus_map_url(self):
        """Gets the value of :attr:`campus_map_url`."""
        return "http://campusmap.ufl.edu/?sched=%s;" % \
               self.campus_map_url_arguments
    
    campus_map_url = property(get_campus_map_url, doc="""
        A url to a map that will show the location of the course on the campus
        using `campusmap.ufl.edu <http://campusmap.ufl.edu/>`_""")
    
    def open_campus_map(self, *args, controller=None, **kwargs):
        """Uses the :mod:`webbrowser` module to automatically open a user's
        webbrowser to show them the location of the course. If no controller
        keyword argument is specified, the default controller is used.
        Additional positional and keyword arguments will be passed into
        :meth:`webbrowser.open` or :meth:`controller.open`."""
        if controller:
            return controller.open(self.campus_map_url, *args, **kwargs)
        import webbrowser
        webbrowser.open(self.campus_map_url, *args, **kwargs)

def periods_str_to_tuple(period):
    """Take an ISIS-formatted set of periods, and make it into a tuple. Some
    examples of ISIS' formatting and their converted tuple forms are::
    
        7    --> (7,)
        11   --> (11,)
        5-8  --> (5, 6, 7, 8)
        6-10 --> (6, 7, 8, 9, 10)
        1011 --> (10, 11)
        11E2 --> (11, 12, 13)
    
    Periods starting with the letter "E" are converted from their ``EN`` form to
    ``11 + N``. ``E1`` becomes ``12``, ``E2`` becomes ``13``, and ``E3`` becomes
    ``14``. If this function is given ``None`` for the period string, or if it
    is given some sort of string specifying "TBA" (to be announced), ``None`` is
    returned."""
    
    if period is None:
        return None
    
    # utility function
    period_to_int = lambda period: \
        11 + int(period[1:]) if period[0] == "e" else int(period)
    
    period = period.strip().lower()
    if "to be" in period or "tba" in period:
        return None
    elif len(period) > 2:
        if "-" in period:
            index = period.index("-")
            start, end = period[:index], period[index + 1:]
        else:
            start, end = period[:2], period[2:]
        return tuple(range(period_to_int(start), period_to_int(end) + 1))
    else:
        return (period_to_int(period), )

_campus_map_url_template = Template("$course_code,$times")
_campus_map_url_time_template = Template("$days,$periods,$building,$room")

class Course:
    """Represents an immutable course object with various properties
    representing known information about the course. At the least, one should
    give a course code and a section number, as these are used to differentiate
    between various courses.
    
    *Keyword Arguments:*
    
    ``course_code``
        An string or an instance of :class:`CourseCode`, representing what the
        course is about. (If passed a string, a new instance of
        :class:`CourseCode` will be constructed from it)
    ``section_number``
        A four-digit alphanumeric code representing which specific section of
        the course this is. Different sections may be taught by different
        teachers, or may occur at different times. Should be a string. Included
        letters are made uppercase.
    ``title``
        The title of the course as a string, often abbreviated. This is designed
        to be human readable. A simple heuristic is used to attempt to correct
        capitalization.
    ``credits``
        How many credits the class is worth. If the class' credits are variable,
        this value should be -1. Should be an int.
    ``meetings``
        A list of :class:`CourseMeeting` objects, telling when and where the
        course is held. An empty list represents that the class meeting is
        "TBA". (Typically the case with online classes)
    ``gen_ed_credit``
        A string specifying what gen-ed credit the course provides. This
        value is made uppercase.
    ``gordon_rule``
        A string specifying what gordon-rule credits the course provides. This
        value is made uppercase.
    ``instructors``
        A list of strings representing who teaches the class. The capitalization
        heuristic applied in the title processing is also done here to improve
        readability.
    
    .. note::
        Leading and trailing spaces are stripped of of any string arguments, so
        if your source has them, you can leave them on.
    
    .. note::
        While a ``course_code`` and ``section_number`` are required, all the
        other arguments are optional. A value of ``None`` represents that the
        piece of information is unknown.
    """
    def __init__(self, course_code, section_number, title=None, credits=None,
                 meetings=None, gen_ed_credit=None, gordon_rule=None,
                 instructors=None):
        if not isinstance(course_code, CourseCode):
            course_code = CourseCode(course_code)
        self.__course_code = course_code
        self.__section_number = section_number.strip().upper()
        if title is not None:
            title = title.strip()
            if title == title.upper() or title == title.lower():
                # we need to fix capitalization
                title = " ".join(t.capitalize() for t in title.split(" "))
        self.__title = title
        self.__credits = credits
        self.__meetings = meetings
        if gen_ed_credit is not None:
            gen_ed_credit = gen_ed_credit.strip().upper()
        self.__gen_ed_credit = gen_ed_credit 
        if gordon_rule is not None:
            gordon_rule = gordon_rule.strip().upper()
        self.__gordon_rule = gordon_rule
        if instructors is not None:
            instructors = [self._fix_capitalization(i) for i in instructors]
        self.__instructors = instructors
    
    def _fix_capitalization(self, string):
        """A cheap heuristic used in title and instructor name processing that
        attempts to fix capitalization in strings."""
        if string == string.upper() or string == string.lower():
            # we need to fix capitalization
            return " ".join(s.capitalize() for s in string.split(" "))
        return string
    
    def __str__(self):
        """Makes a pretty human-readable representation of this object."""
        output = ["Course %s (Section %s):" %
                  (self.course_code, self.section_number)]
        if self.title:
            output.append("Title (Name): %s" % self.title)
        if self.credits:
            output.append("Credits: %s" %
                          ("Variable" if self.credits == -1 else self.credits))
        if self.meetings:
            label = "Meeting%s: " % ("s" if len(self.meetings) > 1 else "")
            output.append(label + ("\n" + " " * (len(label) + 4))
                                   .join(str(m) for m in self.meetings))
        if self.gen_ed_credit:
            output.append("Gen-Ed Credit: %s" % self.gen_ed_credit)
        if self.gordon_rule:
            output.append("Gordon Rule: %s" % self.gordon_rule)
        if self.instructors:
            label = "Taught By: "
            output.append(label + ("\n" + " " * (len(label) + 4))
                                   .join(i for i in self.instructors))
        return "\n    ".join(output)
    
    def get_course_code(self):
        """Gets the value of :attr:`course_code`."""
        return self.__course_code
    
    course_code = property(get_course_code, doc="""
        A :class:`CourseCode` representing what this course is about.""")
    
    def get_section_number(self):
        """Gets the value of :attr:`section_number`."""
        return self.__section_number
    
    section_number = property(get_section_number, doc="""
        A four-digit alphanumeric code representing which specific section of
        the course this is. Different sections may be taught by different
        teachers, or may occur at different times. Is a string.""")
    
    def get_title(self):
        """Gets the value of :attr:`title`."""
        return self.__title
    
    title = property(get_title, doc="""
        The title of the course as a string, often abbreviated. This is designed
        to be human readable. ``None`` if the title is unknown.""")
    
    def get_credits(self):
        """Gets the value of :attr:`credits`."""
        return self.__credits
    
    credits = property(get_credits, doc="""
        How many credits the class is worth. If the class' credits are variable,
        this value will be -1. ``None`` if the number of credits is unknown.""")
    
    def get_meetings(self):
        """Gets the value of :attr:`meetings`."""
        return self.__meetings
    
    meetings = property(get_meetings, doc="""
        A list of :class:`CourseMeeting` objects, telling when and where the
        course is held.""")
    
    def get_gen_ed_credit(self):
        """Gets the value of :attr:`gen_ed_credit`."""
        return self.__gen_ed_credit
    
    gen_ed_credit = property(get_gen_ed_credit, doc="""
        A string representing what general education credit a class provides.
        """)
    
    def get_gordon_rule(self):
        """Gets the value of :attr:`gordon_rule`."""
        return self.__gordon_rule
    
    gordon_rule = property(get_gordon_rule, doc="""
        A string representing what Gordon-Rule related credits this course
        provides.""")
    
    def get_instructors(self):
        """Gets the value of :attr:`instructors`."""
        return self.__instructors
    
    instructors = property(get_instructors, doc="""
        A list of strings showing who is teaching the class.""")
    
    def get_campus_map_url_arguments(self):
        """Gets the value of :attr:`campus_map_url_arguments`."""
        time_strings = []
        for time in self.meetings:
            if len(time.periods) == 1:
                periods_str = time.periods[0]
            else:
                periods_str = "%d-%d" % (time.periods[0], time.periods[-1])
            time_strings.append(_campus_map_url_time_template.substitute(
                days="".join(time.days),
                periods=periods_str,
                building=time.building,
                room=time.room
            ))
        return _campus_map_url_template.substitute(course_code=self.course_code,
                                                   times=",".join(time_strings))
    
    campus_map_url_arguments = property(get_campus_map_url_arguments, doc="""
        Gives the HTTP GET argument for the :attr:`campus_map_url`, useful when
        putting of multiple courses on the same map.""")
    
    def get_campus_map_url(self):
        """Gets the value of :attr:`campus_map_url`."""
        return "http://campusmap.ufl.edu/?sched=%s;" % \
               self.campus_map_url_arguments
    
    campus_map_url = property(get_campus_map_url, doc="""
        A url to a map that will show the location of the course on the campus
        using `campusmap.ufl.edu <http://campusmap.ufl.edu/>`_""")
    
    def open_campus_map(self, *args, controller=None, **kwargs):
        """Uses the :mod:`webbrowser` module to automatically open a user's
        webbrowser to show them the location of the course. If no controller
        keyword argument is specified, the default controller is used.
        Additional positional and keyword arguments will be passed into
        :meth:`webbrowser.open` or :meth:`controller.open`."""
        if controller:
            return controller.open(self.campus_map_url, *args, **kwargs)
        import webbrowser
        webbrowser.open(self.campus_map_url, *args, **kwargs)
    
    def __eq__(self, other):
        """Tests equality based on the :attr:`course_code` and
        :attr:`section_number`."""
        if self is other:
            return True
        return self.course_code == other.course_code and \
               self.section == other.section
    
    def __hash__(self):
        """Computes a hash based on the :attr:`course_code` and
        :attr:`section_number`, allowing you to use :class:`Course` objects in a
        :class:`dict`."""
        return hash((self.course_code, self.section_number))

class CourseCode(UserString):
    """Represents a code, such as "MAC2311" which represents which class is
    being taken. The format for this is defined by the State of Florida and the
    `Florida Department of Education <http://scns.fldoe.org>`_. It is `described
    in more detail (than is included here) online
    <https://catalog.ufl.edu/ugrad/current/courses/Pages/scns.aspx>`_.
    
    This class extends :class:`collections.UserString`, so that one can treat it
    like a string, but it also provides a set of methods to make processing
    easier.
    
    .. note::
        You may construct this object, passing in a string like "mac 2311", and
        it will convert it to the consistent format "MAC2311".
    """
    
    def __init__(self, code_str):
        UserString.__init__(self, re.sub(r"(\s|[-_])", "", code_str).upper())
    
    def get_prefix(self):
        """Gets the value of :attr:`prefix`."""
        return str(self[0:3])
    
    prefix = property(get_prefix, doc="""
        The first three characters (typically capitalized) are the prefix,
        typically representing the `"major division of an academic discipline,
        subject matter area, or sub-category of knowledge"
        <https://catalog.ufl.edu/ugrad/current/courses/Pages/scns.aspx>`_. In
        the example "MAC2311", that would be "MAC".""")
    
    def get_number(self):
        """Gets the value of :attr:`number`."""
        return int(self[3:7])
    
    number = property(get_number, doc="""
        The four-digit number following the prefix (not counting a potential lab
        suffix) as an int.""")
    
    def get_level_code(self):
        """Gets the value of :attr:`level_code`."""
        return int(self[3])
    
    level_code = property(get_level_code, doc="""
        The first digit of the course :attr:`number` as an int. It represents
        the difficulty of the class, where 1 is "lower freshman" difficulty, and
        5 is "graduate" difficulty.""")
    
    def get_century_digit(self):
        """Gets the value of :attr:`century_digit`."""
        return int(self[4])
    
    century_digit = property(get_century_digit, doc="""
        The second digit of the course :attr:`number` as an int. This and the
        next 2 digits following it describe what this course is about.""")
    
    def get_decade_digit(self):
        """Gets the value of :attr:`decade_digit`."""
        return int(self[5])
    
    decade_digit = property(get_decade_digit, doc="""
        The third digit of the course :attr:`number` as an int.""")
    
    def get_unit_digit(self):
        """Gets the value of :attr:`unit_digit`."""
        return int(self[6])
    
    unit_digit = property(get_unit_digit, doc="""
        The last digit in the course :attr:`number` as an int. This often
        represents what course this is in a series. For example, MAC2311 is the
        first in a Calculus series, typically followed by MAC2312 and MAC2313
        (Calculus 2 and 3, respectively).""")
    
    def get_lab(self):
        """Gets the value of :attr:`lab`."""
        return None if len(self) != 8 else str(self[7])
    
    lab = property(get_lab, doc="""
        Some courses, such as CHM2045L (General Chemistry's Lab Component) have
        an additional character, an "L" or a "C", which specifies the class' lab
        component, where "L" represents that this course is the lab component
        for the class (often required), and "C" represents that the lab
        component is at the same place and time as the general class.""")

class CourseMeeting:
    """Represents a location and a set of times when a course will be held at
    that location.
    
    *Keyword Arguments:*
    
    ``days``
        Either a tuple or a string representing what days the course is being
        held at this location. A passed string can be in the ISIS/Registrar
        format, where a string like ``M WRF`` represents that class is being
        held on Monday, Wednesday, Thursday, and Friday. Spaces are stripped,
        text is capitalized (in case it isn't already) and a tuple is formed
        by turning each character in the string into an item in the tuple. A
        passed tuple may only contain values in the :class:`Days` enum.
    ``periods``
        Either a tuple or a string representing which periods the course is
        being held at this location. If passed a string, we run
        :data:`periods_str_to_tuple` on it, which means that you can pull
        strings straight from ISIS or the Registrar and have them converted. If
        given a tuple, the tuple should already be sorted, and there should be
        no gaps in the list. In other words::
            
            tuple(range(periods[0], periods[-1] + 1)) == periods
        
    ``building``
        The building code where the course is being held at as a string. This
        will be capitalized, and stripped of leading and trailing white-space.
    ``room``
        The room number in the building where the course is being held as a
        string. This will be capitalized, and stripped of leading and trailing
        whitespace.
    """
    
    def __init__(self, days, periods, building, room):
        if isinstance(days, str):
            days = tuple(days.upper().replace(" ", ""))
        if isinstance(periods, str):
            periods = periods_str_to_tuple(periods)
        self.__days = days
        self.__periods = periods
        if not building:
            self.__building = None
        else:
            self.__building = building.strip().upper()
        if not room:
            self.__room = None
        else:
            self.__room = room.strip().upper()
    
    def get_days(self):
        """Gets the value of :attr:`days`."""
        return self.__days
    
    days = property(get_days, doc="""
        A tuple of days, containing values defined in
        :class:`Days`. A nice feature of this, is that you can write code such
        as::
        
            Days.MONDAY in my_course_time.days
        """)
    
    def get_periods(self):
        """Gets the value of :attr:`periods`."""
        return self.__periods
    
    periods = property(get_periods, doc="""
        A tuple of periods as ints when this class is being held. A nice feature
        of this, is that you can write code such as
        ``10 in my_course_time.periods``.""")
    
    def get_periods_str(self):
        """Gets the value of :attr:`periods_str`."""
        if len(self.periods) == 1:
            return self.periods[0]
        else:
            return "%d-%d" % (self.periods[0], self.periods[-1])
    
    periods_str = property(get_periods_str, doc="""
        Gives :attr:`periods` in an easy to read string format, similar to the
        one ISIS gives (except we do not guarantee a length of 4 or less, and
        the hyphen isn't omitted when dealing with 2-character long periods,
        such as period 10). A hyphen is simply inserted between the starting and
        ending periods of the periods tuple, or if there is only one period,
        only that periods is given. Here's some example output::
        
            (5, 6, 7, 8, 9, 10) --> "5-10"
            (10, 11)            --> "10-11"
            (4)                 --> "4"
        """)
    
    def get_building(self):
        """Gets the value of :attr:`building`."""
        return self.__building
    
    building = property(get_building, doc="""
        A string, containing the building code, such as MAE or NPB. Building
        codes are typically 3 or 4 letters long, and are always capitalized.""")
    
    def get_room(self):
        """Gets the value of :attr:`room`."""
        return self.__room
    
    room = property(get_room, doc="""
        The room number in the building where the course takes place as a
        string. Any letters in the room number are capitalized.""")
    
    def __str__(self):
        return "Periods %s on %s at %s %s" % \
               (self.periods_str, " ".join(self.days), self.building, self.room)

class Days:
    """A set of valid values to use in a list/tuple of days, playing the role of
    an enum-like construct."""
    MONDAY = "M"
    TUESDAY = "T"
    WEDNESDAY = "W"
    THURSDAY = "R"
    FRIDAY = "F"
    SATURDAY = "S"
    EVERY_DAY = tuple("MTWRFS")

class Semesters:
    """A set of valid values to use in a list/tuple of semesters, playing the
    role of an enum-like construct."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
