from string import Template
import datetime
import re

class FieldInfo:
    def __init__(self, name, description=None, data_type=object):
        object.__init__(self)
        self.__name = name
        self.description = description
        self.data_type = data_type
    
    def get_name(self):
        return self.__name
    
    name = property(get_name)
    
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
    
    docstring = property(get_docstring)
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other.name

def process_docstring(docstring, field_info_list, label="Supported Fields"):
    out = "\n".join(field_info.docstring for field_info in field_info_list)
    if label:
        out = "*%s:*\n\n%s" % (label, out)
    match = re.search("([ \t]*)(\$field_info)", docstring)
    out = out.replace("\n", "\n" + match.group(1))
    return docstring[:match.start(2)] + out + docstring[match.end(2):]

info_dict = {info.name:info for info in [
    FieldInfo("url",
              "The url of the person's html page.", str),
    FieldInfo("url_ldap",
              "The url of the person's html LDAP listing page.", str),
    FieldInfo("url_full",
              "An alias to ``url_ldap``.", str),
    FieldInfo("url_vcard",
              "The url to the person's vcard file.", str),
    FieldInfo("name",
              "The person's name, typically: \"Lastname, Firstname\"", str),
    FieldInfo("title",
              "Usually something like \"student\", or \"Resident, DN-ORAL "
              "SURGERY RESIDENT\"", str),
    FieldInfo("phone",
              "The preferred phone number (or at least the first one that "
              "shows up", str),
    FieldInfo("preferred_phone",
              "An alias to ``phone``.", str),
    FieldInfo("email",
              "The person's email address.", str),
    FieldInfo("gatorlink_email",
              "The person's gatorlink email address (if not explicitly "
              "provided, this is guessed to be the person's gatorlink, with "
              "\"@ufl.edu\" appended onto the end).", str),
    FieldInfo("gatorlink",
              "The person's gatorlink username.", str),
    FieldInfo("department_number",
              "A code representing what department this person belongs to.",
              str),
    FieldInfo("employee_number",
              "If this person is employed by the University of Florida, this "
              "is their employee number. This is the same as one's UFID "
              "Number.", str),
    FieldInfo("affiliation",
              "`Described here <https://phonebook.ufl.edu/affiliations/>`_. As "
              "of writing, possible values include \"faculty\", \"staff\", "
              "\"student\", and \"member\".", str),
    FieldInfo("address",
              "The person's home address (or if that's not available, their "
              "first available physical address).", str),
    FieldInfo("office_address",
              "The person's office address (if available).", str),
    FieldInfo("language",
              "The person's prefered language.", str),
    FieldInfo("birth_date",
              "An instance of :py:class:`datetime.date` representing the "
              "person's date of birth.", datetime.date),
    FieldInfo("raw_ldap",
              "The raw fields pulled from the person's LDAP entry.", dict)
]}
