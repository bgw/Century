==============================================================
``courses`` -- Object Representations of UF Course Information
==============================================================

.. automodule:: lib.tasks.courses

.. autoclass:: Course
    
    .. automethod:: get_course_code
    .. autoattribute:: course_code
    .. automethod:: get_section_number
    .. autoattribute:: section_number
    .. automethod:: get_title
    .. autoattribute:: title
    .. automethod:: get_credits
    .. autoattribute:: credits
    .. automethod:: get_meetings
    .. autoattribute:: meetings
    .. automethod:: get_gen_ed_credit
    .. autoattribute:: gen_ed_credit
    .. automethod:: get_gordon_rule
    .. autoattribute:: gordon_rule
    .. automethod:: get_instructors
    .. autoattribute:: instructors
    .. automethod:: get_campus_map_url_arguments
    .. autoattribute:: campus_map_url_arguments
    .. automethod:: get_campus_map_url
    .. autoattribute:: campus_map_url
    .. automethod:: open_campus_map
    .. automethod:: __eq__
    .. automethod:: __hash__
    .. automethod:: __str__

.. autofunction:: periods_str_to_tuple

.. autoclass:: CourseCode
    
    .. automethod:: get_prefix
    .. autoattribute:: prefix
    .. automethod:: get_number
    .. autoattribute:: number
    .. automethod:: get_level_code
    .. autoattribute:: level_code
    .. automethod:: get_century_digit
    .. autoattribute:: century_digit
    .. automethod:: get_decade_digit
    .. autoattribute:: decade_digit
    .. automethod:: get_unit_digit
    .. autoattribute:: unit_digit
    .. automethod:: get_lab
    .. autoattribute:: lab

.. autoclass:: CourseMeeting

    .. automethod:: get_days
    .. autoattribute:: days
    .. automethod:: get_periods
    .. autoattribute:: periods
    .. automethod:: get_periods_str
    .. autoattribute:: periods_str
    .. automethod:: get_building
    .. autoattribute:: building
    .. automethod:: get_room
    .. autoattribute:: room
    .. automethod:: __str__

.. autoclass:: CourseList
    
    .. automethod:: _init_subset
    .. automethod:: get_campus_map_url_arguments
    .. autoattribute:: campus_map_url_arguments
    .. automethod:: get_campus_map_url
    .. autoattribute:: campus_map_url
    .. automethod:: open_campus_map

.. autoclass:: Days
    :members:

.. autoclass:: Semesters
    :members:

``courses.fuzzy_match`` -- Fuzzy Matching with List and String-like Objects
---------------------------------------------------------------------------

.. automodule:: lib.tasks.courses.fuzzy_match

.. autofunction:: similar_zip

Algorithms
~~~~~~~~~~

All algorithms share one property; that they must be callable in the form::

    algorithm(s1, s2)

Where ``s1`` and ``s2`` are the two objects to compare.

.. autofunction:: lev_dist
.. autofunction:: lev_ratio
.. autofunction:: hamming_dist
.. autofunction:: hamming_ratio
.. autofunction:: frequency_dist
.. autofunction:: frequency_ratio

Meta-Algorithms
~~~~~~~~~~~~~~~

Meta-Algorithms are functions that use other algorithms in various ways.

.. autofunction:: offset_minimum
.. autofunction:: offset_maximum
