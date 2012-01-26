=============================================================
``course_listings`` -- Pulling Course Data from the Registrar
=============================================================

.. automodule:: lib.tasks.registrar.course_listings

.. autoclass:: CourseReader
    
    .. autoattribute:: base_url
    .. autoattribute:: departments
    .. automethod:: lookup_prefix
    .. automethod:: lookup_course
    .. automethod:: auto_load
    .. automethod:: force_load

.. autoclass:: Department
    
    .. autoattribute:: name
    .. autoattribute:: alternate_names
    .. autoattribute:: all_names
    .. automethod:: rate_similarity
    .. automethod:: get_prefixes
    .. autoattribute:: prefixes
    .. autoattribute:: browser
    .. autoattribute:: course_list
    .. autoattribute:: loaded
    .. automethod:: auto_load
    .. automethod:: force_load
    .. automethod:: __str__
