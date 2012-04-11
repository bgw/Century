"""Provides a useful introspection-capable way of documenting supported fields
in a backend.

$field_info"""

from string import Template
import datetime
import re
import logging

logger = logging.getLogger("tasks.phonebook.fields")

class FieldInfo:
    """Gives details about what the information in a field by a specific name
    should include.
    
    *Keyword Arguments:*
    
    ``name``
        The name of the field. This should be unique, and be the same as the
        corresponding key in :data:`info_dict`. It should give some brief idea
        of what to expect in the field.
    ``description``
        Human-readable text about the significance of the field. This is used in
        forming docstrings about the field.
    ``data_type``
        If unspecified, :class:`object`, otherwise, a type, such as a
        :class:`str` or an :class:`int`
    ``auto_store``
        When ``True``, ``self`` is automatically saved to :data:`info_dict`.
    """
    def __init__(self, name, description=None, data_type=object,
                 auto_store=True):
        object.__init__(self)
        if name in info_dict:
            logger.warning("A field by the name of '%s' is being redefined. "
                           "Field names should be universally unique." % name)
        self.__name = name
        self.description = description
        self.data_type = data_type
        if auto_store:
            info_dict[name] = self
    
    def get_name(self):
        return self.__name
    
    name = property(get_name, doc="""
        The name of the field. This should be unique, and be the same as the
        corresponding key in :data:`info_dict`. It should give some brief idea
        of what to expect in the field.
    """)
    
    def get_docstring(self):
        topline = None
        if self.data_type is not object:
            if self.data_type.__module__ == "builtins":
                data_type_str = self.data_type.__name__
            else:
                data_type_str = "%s.%s" % (self.data_type.__module__,
                                           self.data_type.__name__)
            topline = "``%s`` (:class:`%s`)" % (self.name, data_type_str)
        else:
            topline = "``%s``" % self.name
        
        subline = self.description
        
        if subline is not None:
            return "%s\n    %s" % (topline, subline.replace("\n", "\n    "))
        else:
            return "``%s``" % topline
    
    docstring = property(get_docstring, doc="""
        A ReST-formatted string that displays information about the field that
        could easily be put into a list (like is done with
        :func:`process_docstring`.
        
        *For example:*
        
        ``name`` (:class:`str`)
            The person's name, typically: "Lastname, Firstname"
    """)
    
    def __hash__(self):
        """Returns a hash based on the field name (as it is assumed to be
        unique)."""
        return hash(self.name)
    
    def __eq__(self, other):
        """Checks equality based on the field name (as it is assumed to be
        unique)."""
        return self.name == other.name

def process_docstring(docstring, field_info_list, label="Supported Fields"):
    """
    Takes a docstring formed like::
        
        Some information about my *great* class.
        
        $field_info
        
        .. warning::
            Some sort of text after our field information.
    
    And turns inserts a ReST block with detailed field information in place of
    ``field_info``.
    
    *Keyword Arguments:*
    
    ``docstring``
        The docstring to transform. The transformed version of this is returned.
    ``field_info_list``
        A list of :class:`FieldInfo` objects to list in place of
        ``$field_info``. If one doesn't have the :class:`FieldInfo` objects, but
        rather the field names, they can be pulled by name from
        :data:`info_dict`.
    ``label``
        The label written above the field list. If ``None`` it is left off.
        Double-emphasized (typically bold) and appended with a colon.
    """
    linestart_str = " " * 4 if label else ""
    out = linestart_str + ("\n" + linestart_str).join(
        field_info.docstring.replace("\n", "\n" + linestart_str)
        for field_info in field_info_list
    )
    if label:
        out = "**%s:**\n\n%s" % (label, out)
    match = re.search("([ \t]*)(\$field_info)", docstring)
    out = out.replace("\n", "\n" + match.group(1))
    return docstring[:match.start(2)] + out + docstring[match.end(2):]

# create and populate info_dict
info_dict = {}
FieldInfo("url",
          "The url of the person's html page.", str)
FieldInfo("url_ldap",
          "The url of the person's html LDAP listing page.", str)
FieldInfo("url_full",
          "An alias to ``url_ldap``.", str)
FieldInfo("url_vcard",
          "The url to the person's vcard file.", str)
FieldInfo("name",
          "The person's name, typically: \"Lastname, Firstname\"", str)
FieldInfo("title",
          "Usually something like \"student\", or \"Resident, DN-ORAL SURGERY "
          "RESIDENT\"", str)
FieldInfo("phone",
          "The preferred phone number (or at least the first one that shows up",
          str)
FieldInfo("preferred_phone",
          "An alias to ``phone``.", str)
FieldInfo("email",
          "The person's email address.", str)
FieldInfo("gatorlink_email",
          "The person's gatorlink email address (if not explicitly provided, "
          "this is guessed to be the person's gatorlink, with \"@ufl.edu\" "
          "appended onto the end).", str)
FieldInfo("gatorlink",
          "The person's gatorlink username.", str)
FieldInfo("department_number",
          "A code representing what department this person belongs to.", str)
FieldInfo("employee_number",
          "If this person is employed by the University of Florida, this is "
          "their employee number. This is the same as one's UFID Number.", str)
FieldInfo("affiliation",
          "`Described here <https://phonebook.ufl.edu/affiliations/>`_. As "
          "of writing, possible values include \"faculty\", \"staff\", "
          "\"student\", and \"member\".", str)
FieldInfo("address",
          "The person's home address (or if that's not available, their first "
          "available physical address).", str)
FieldInfo("office_address",
          "The person's office address (if available).", str),
FieldInfo("language",
          "The person's prefered language.", str)
FieldInfo("birth_date",
          "An instance of :py:class:`datetime.date` representing the person's "
          "date of birth.", datetime.date)
FieldInfo("raw_ldap",
          "The raw fields pulled from the person's LDAP entry.", dict)

__doc__ = process_docstring(__doc__, info_dict.values(),
                            label="Built-in Fields")
