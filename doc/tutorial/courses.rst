=========================================
Representing and Handling Course Sections
=========================================

The :mod:`lib.tasks.courses` module contains various constructs for representing
courses at the University of Florida.

.. note::
    The appropriate classes from the :mod:`lib.tasks.courses` module should be
    imported before the code is executed.

.. testsetup:: *
    
    from lib.tasks.courses import *

The ``CourseCode`` Class
------------------------

:class:`lib.tasks.courses.CourseCode` is a subclass of
:class:`collections.UserString`, meaning it can be used like a ``str`` object,
but also like a traditional object with various properties. When constructing a
:class:`lib.tasks.courses.CourseCode`, a code string is forced into a consistant
format.

.. doctest::
    
    >>> CourseCode("mac 2311")
    'MAC2311'
    >>> CourseCode("phy2048 L")
    'PHY2048L'
    >>> CourseCode("phy 2048 l") == CourseCode("PHY2048L")
    True

Getting the prefix of the course code is trivial, and can be done in a readable
fashion:

.. doctest::
    
    >>> CourseCode("MAC2311").prefix
    'MAC'
    >>> CourseCode("MAC2311")[0:3] # alternatively
    'MAC'

Various other properties and documentation can be found on the
:class:`lib.tasks.courses.CourseCode` page.

The ``CourseMeeting`` Class
---------------------------

Representing course meeting times is a step more complex from course codes.
Often, one will see course meeting times represented on ISIS or the Registrar
with sets of day and period identifiers, such as ``MWF 2-3``. One
:class:`lib.tasks.courses.CourseMeeting` object represents one day/period pair.
Each :class:`lib.tasks.courses.Course` object can contain multiple
:class:`lib.tasks.courses.CourseMeeting` objects. Constructing one of these
objects can be done a few ways:

.. doctest::
    
    >>> str(CourseMeeting("MWF", "2-3", building="MAEB", room="123C"))
    'Periods 2-3 on M W F at MAEB 123C'
    >>> str(CourseMeeting((Days.MONDAY, "W", "F"), (2, 3), "MAEB", "123C"))
    'Periods 2-3 on M W F at MAEB 123C'

Once you have a :class:`lib.tasks.courses.CourseMeeting` object, you can do some
moderately interesting things with it (although it is mainly just intended as a
container):

.. doctest::
    
    >>> mae_meeting = CourseMeeting("MWF", "2-3", building="MAEB", room="123C")
    >>> Days.WEDNESDAY in mae_meeting.days and 3 in mae_meeting.periods
    True
    >>> mae_meeting.periods_str
    '2-3'

Again, more documentation is available on the
:class:`lib.tasks.courses.CourseMeeting` page.

The ``Course`` Class
--------------------

Now that we've covered the dependent classes, we can begin building and using
:class:`lib.tasks.courses.Course` objects.

While it might be a bit of a misnomer, a single
:class:`lib.tasks.courses.Course` object represents a single section of a class,
rather than a class itself. This may seem a bit odd, but it is this way as an
attempt to map things a bit closer to how ISIS and the Registrar represent their
information.

The minimum requirements for a :class:`lib.tasks.courses.Course` object are a
course code, and section number (represented as a string). For convenience, a
course code can be passed in as a string, and it will automatically be turned
into a :class:`lib.tasks.courses.CourseCode` object. Typically when we have a
function, method, or constructor in Century that needs a course code, you can
pass either a string or a :class:`lib.tasks.courses.CourseCode` object, and
conversions will happen automatically.

Let's make a simple course, for our Calc 1 (``MAC2311``) class:

.. doctest::
    
    >>> calc1 = Course("mac 2311", "145D")
    >>> str(calc1)
    'Course MAC2311 (Section 145D):'

Okay, that works, but it does feel kinda empty... From the documentation
reference page for :class:`lib.tasks.courses.Course`, we can see that the
constructor will accept:

- A course title (as a ``str``)
- A number of credits (as an ``int``)
- A list (or any other kind of iterable) of meetings
- A one-character ``str`` representing the Gen-Ed credit the course gives
- A ``str`` specifying information about what Gordon-Rule requirements the
  course fulfills
- A list of instructors as strings

.. note::
    Some processing is applied to certain attributes to fix capitalization. The
    processing applied to attributes is described more in depth on the class
    reference page.

Wow, that's a mouthful, and some of that may be a bit overkill for our needs,
but fortunately we don't have to put more information in there than we want.
Let's put some more information in there though:

.. doctest::
    
    >>> calc1 = Course("mac 2311", "145D", title="ANALYT GEOM & CALC 1",
    ...                credits=4, meetings=[mae_meeting],
    ...                instructors=["john doe", "ann frank", "big lequisha"])
    >>> print(str(calc1))
    Course MAC2311 (Section 145D):
        Title (Name): Analyt Geom & Calc 1
        Credits: 4
        Meeting: Periods 2-3 on M W F at MAEB 123C
        Taught By: John Doe
                   Ann Frank
                   Big Lequisha

Nice! We now have an object to work with, and even some "pretty" output to show
for it. As is with most things in the :mod:`lib.tasks.courses` module, the
:class:`lib.tasks.courses.Course` class mainly exists as a mechanism for
information storage, but there are a couple interesting things that we can do
with our formed ``calc1`` object.

From an ISIS schedule page, one can pull up a campus map, visually showing where
courses are on campus. We can generate a similar URL for one course, by fetching
the :attr:`lib.tasks.courses.Course.campus_map_url` attribute:

.. doctest::
    
    >>> calc1.campus_map_url
    'http://campusmap.ufl.edu/?sched=MAC2311,MWF,2-3,MAEB,123C;'

One can even pull up the webpage in the user's default browser using the simple
:meth:`lib.tasks.courses.Course.open_campus_map` method.

The ``CourseList`` Class
------------------------

As a minor additional feature, you can group course objects together with
:class:`lib.tasks.courses.CourseList` objects. The class is a subclass of
:class:`collections.UserList`, so it looks, acts, behaves, and feels like a
list, with a few extra features, for example, we can construct a
:class:`lib.tasks.courses.CourseList`

.. doctest::
    
    >>> calc_list = CourseList([calc1, calc1, calc1])

and then do:

.. doctest::
    
    >>> print(str(calc_list))
    Course MAC2311 (Section 145D):
        Title (Name): Analyt Geom & Calc 1
        Credits: 4
        Meeting: Periods 2-3 on M W F at MAEB 123C
        Taught By: John Doe
                   Ann Frank
                   Big Lequisha
    Course MAC2311 (Section 145D):
        Title (Name): Analyt Geom & Calc 1
        Credits: 4
        Meeting: Periods 2-3 on M W F at MAEB 123C
        Taught By: John Doe
                   Ann Frank
                   Big Lequisha
    Course MAC2311 (Section 145D):
        Title (Name): Analyt Geom & Calc 1
        Credits: 4
        Meeting: Periods 2-3 on M W F at MAEB 123C
        Taught By: John Doe
                   Ann Frank
                   Big Lequisha

Notice how all the courses get pretty-printed. What if we wanted to pull up a
campus map with all three of those courses? (not too interesting in our case, as
all our courses are the same)

.. doctest::
    
    >>> calc_list.campus_map_url
    'http://campusmap.ufl.edu/?sched=MAC2311,MWF,2-3,MAEB,123C;MAC2311,MWF,2-3,MAEB,123C;MAC2311,MWF,2-3,MAEB,123C;'

Of course, if we can subdivide the list using slices, but what makes this
slightly more interesting is that the result we get out is another
:class:`lib.tasks.courses.CourseList` object:

.. doctest::
    
    >>> len(calc_list)
    3
    >>> type(calc_list)
    <class 'lib.tasks.courses.CourseList'>
    >>> len(calc_list[0:2])
    2
    >>> type(calc_list[0:2])
    <class 'lib.tasks.courses.CourseList'>
