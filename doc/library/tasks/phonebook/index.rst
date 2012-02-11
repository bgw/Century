=================================================================
``phonebook`` -- Handling of the UF Student and Faculty Directory
=================================================================

.. automodule:: lib.tasks.phonebook

.. autoclass:: Phonebook
    
    .. automethod:: search

.. autoclass:: PhonebookBackend
    
    .. autoattribute:: browser
    .. autoattribute:: fields
    .. automethod:: get_search_results
    .. automethod:: process_datahint

Supporting Modules
------------------

.. toctree::
    person
    fields
    http
    ldap/utils
