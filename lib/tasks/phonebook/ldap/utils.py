"""A set of shared utilities useful for dealing with LDAP or LDAP-like data
sources. Contains a list of LDAP-entry defined fields and a partial processor
for LDAP data."""

import collections
import datetime
from .. import fields

supported_fields = frozenset([
    "name",
    "title",
    "phone",
    "preferred_phone",
    "email",
    "gatorlink_email",
    "gatorlink",
    "department_number",
    "employee_number",
    "affiliation",
    "address",
    "office_address",
    "language",
    "birth_date",
    "raw_ldap"
])

# we can't set the docstring for supported_fields, as it is read-only, but we
# can add some documentation to the module, so that 
__doc__ += fields.process_docstring("""
    
    .. data:: supported_fields
        
        A set of fields supported by the :func:`process_data` function.
        
        $field_info
    """.replace("\n    ", "\n"),
    [fields.info_dict[i] for i in sorted(supported_fields)],
    label = None
)

def process_data(data):
    """Takes a dict or list of tuples with "raw" LDAP data in string format, and
    processes it into more pythonic objects with keys matching those listed in
    :data:`supported_fields`. The processed dict is returned."""
    base_data = dict(data)
    data = collections.defaultdict(lambda: None)
    data.update(base_data)
    
    # Utility Functions:
    def fix_address(s): # Replace the $s in addresses with newlines
        if s is None:
            return None
        return "\n".join(i.strip() for i in s.split("$"))
    def select(data, *keys): # given keys, select the first one with a value
        for i in keys:
            if data[i]:
                return data[i]
        return None
    
    # process some more complicated fields first:
    base_title = select(data, "title", "eduPersonPrimaryAffiliation")
    if "o" in data:
        if base_title is not None:
            title = "%s, %s" % (base_title, data["o"])
        else:
            title = data["o"]
    else:
        title = base_title
    phone = select(data, "telephoneNumber", "homePhone")
    email = data["mail"]
    if email and "@ufl.edu" in email:
        gatorlink = email[:-len("@ufl.edu")]
        gatorlink_email = email
    else:
        gatorlink = data["uid"] if data["uid"] else data["homeDirectory"][3:] \
                                              if data["homeDirectory"] else None
        gatorlink_email = ("%s@ufl.edu" % gatorlink) if gatorlink else None
    birth_date = \
        datetime.date(*[
            int(i) for i in data["uflEduBirthDate"].split("-")
        ]) if data["uflEduBirthDate"] else None
    
    # plug in and return ALL THE THINGS
    return {k:v for k, v in {
        "raw_ldap":base_data,
        "affiliation":data["eduPersonPrimaryAffiliation"],
        "name":select(data, "displayName", "cn", "gecos"),
        "phone":phone,
            "preferred_phone":phone,
            "email":email,
            "gatorlink":gatorlink,
            "gatorlink_email":gatorlink_email,
            "department_number":
                select(data, "departmentNumber", "uflEduPsDeptId"),
            "employee_number":data["employeeNumber"],
            "address":
                fix_address(
                    select(data, "postalAddress", "homePostalAddress",
                           "registeredAddress", "uflEduOfficeLocation", "street"
                    )
                ),
            "office_address":
                fix_address(
                    select(data, "officeAddress", "uflEduOfficeLocation")
                ),
            "language":data["language"],
            "birth_date":birth_date
        }.items() if v is not None}
