=================================================================
``fields`` -- Constructs to Aid Handling of Phonebook Field Types
=================================================================

.. automodule:: lib.tasks.phonebook.fields

.. autoclass:: FieldInfo
    
    .. autoattribute:: name
    .. attribute:: description
        
        Human-readable text about the significance of the field. This is used in
        forming docstrings about the field.
    
    .. autoattribute:: docstring
    .. automethod:: __hash__
    .. automethod:: __eq__

.. autofunction:: process_docstring
.. data:: info_dict
    
    Contains the global list of defined fields. Given a name, one should be able
    to pull instrospection information from here.
