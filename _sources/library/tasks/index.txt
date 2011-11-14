======================
Task-Oriented Services
======================

While the browser-oriented features of Century in the :mod:`browser` module and
its sub-modules provides generic services for dealing with UF's site (and
potentially even other websites), the :mod:`tasks` module serves to accomplish
specific goals, such as pulling a student's home address from the UF phonebook
(after proper authentication, of course), or looking up a student's schedule
(via ISIS, with that student's GatorLink).

The point here is to build up a pool of ready-to-go components that can be used
in larger applications without much fuss. Furthermore, tasks are not restricted
to the :class:`browser.Browser` namespace, and so rules governing their
development are not as strict. For example, there are no limitations on
dependencies here (within reason), while everything in :mod:`browser` is
intended to be usable with nothing but the standard Python library. The point is
that you can selectively choose which parts of Century you want to use, and pay
the cost of extra dependencies *as you go*.

.. automodule:: lib.tasks

.. autoclass:: BaseTaskManager
    
    .. automethod:: __init__
    .. automethod:: get_browser
    .. autoattribute:: browser
    .. automethod:: _get_new_browser

.. autoclass:: BaseRepeatedTaskManager
    
    .. automethod:: __init__
    .. automethod:: get_delay
    .. autoattribute:: delay
    .. automethod:: start
    .. automethod:: stop
    .. automethod:: _run

.. autoclass:: BaseUFTaskManager
    
    .. automethod:: __init__
    .. automethod:: _get_new_browser
