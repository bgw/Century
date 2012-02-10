from string import Template
import datetime

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
        subline = self.description
        if self.data_type is not object:
            dataline = "**Type:** \"%s\" *(or compatible)*" % \
                       self.data_type.__name__
            if subline is None:
                subline = dataline
            else:
                subline += "\n\n" + dataline
        if subline is not None:
            return "``%s``\n    %s" % (self.name, self.description)
        else:
            return "``%s``" % self.name
    
    docstring = property(get_docstring)
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other.name

def process_docstring(docstring, field_info_list, label="Supported Fields"):
    out = "\n".join(field_info.docstring for field_info in field_info_list)
    if label:
        out = "*%s:*\n\n%s" % (label, out)
    return Template(docstring).safe_substitute(field_info=out)

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
              "Described `here <https://phonebook.ufl.edu/affiliations/>`_. As "
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
