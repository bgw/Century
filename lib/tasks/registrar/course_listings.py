"""The module is a work-in-progress, and doesn't actually do anything yet."""

SPRING = "spring"; SUMMER = "summer"; FALL = "fall"

_course_archive_url = "http://www.registrar.ufl.edu/socarchive/"

_course_schedule_urls = None

def get_course_reader(year, semester, full=True, browser=None):
    """A factory for CoursesReader objects, finding the url for a selected year
    and semester for you. If a matching url cannot be found, a ``KeyError`` will
    be raised.
    
    Keyword arguments:
    year -- Either a string or an int representing the year to look into, such
            as "2011". Please note that the registrar's records only date back
            to 2001.
    semester -- A string with a value :py:data:`SPRING`, :py:data:`SUMMER`, or
                :py:data:`FALL`.
    full -- A bool, ``True`` if you want all the course listings, ``False`` if
            you are an online student, and only want the web-based course
            listings.
    """
    if _course_schedule_urls is None:
        _course_schedule_urls = _get_course_schedule_urls()
    return _course_schedule_urls[(int(year), semester.lower(), full)]

def _get_course_schedule_urls():
    
