from . import PhonebookBackend
from .person import *
from ...browser import parsers

import lxml
import datetime
import re
import collections
import logging
try: # py3k
    import urllib.parse as urlpar
except: # py2
    import urllib2 as urlpar

logger = logging.getLogger("tasks.phonebook.http")

_person_url_re = re.compile(
    r"https?://.*?\.ufl\.edu(\:\d+)?(?P<priv>/private)?/people/"
    r"(?P<ident>[A-Za-z0-9]*)/?"
)

class HttpLdapDataHint(DataHint):
    def __init__(self, url):
        DataHint.__init__(self)
        self.url = url
    
    def __hash__(self):
        return hash(self.url)
    
    def __eq__(self, other):
        return self.url

class HttpBackend(PhonebookBackend):
    """Provides the http backend for the UF phonebook. Data is pulled from the
    returned html pages. Depending on the initial search query, some pulled data
    could potentially change (because it could end up getting pulled in a
    different fashion). If the data cannot be found, ``None`` is given. All
    values are of either type ``str`` or ``NoneType``, unless otherwise
    specified.
    
    Some information on UF's LDAP fields `can be found here
    <http://www.webadmin.ufl.edu/projects/phonebook/ldap-field-spec.html>`_ and
    `here <http://open-systems.ufl.edu/content/uf-ldap-schema>`_.
    
    *Keyword arguments:*
    
    ``url``
        The url of the person's html page.
    ``url_ldap``
        The url of the person's html LDAP listing page.
    ``url_full``
        An alias to ``url_ldap``.
    ``title``
        A string, usually saying something like "student", or "Resident, DN-ORAL
        SURGERY RESIDENT".
    ``phone``
        The prefered phone number (or at least the first one that shows up)
    ``preferred_phone``
        An alias to ``phone``.
    ``email``
        The person's email address.
    ``gatorlink_email``
        The person's gatorlink email address (if not explicitly provided, this
        is guessed to be the person's gatorlink, with "@ufl.edu" appended onto
        the end).
    ``gatorlink``
        The person's gatorlink username.
    ``department_number``
        A code representing what department this person belongs to.
    ``employee_number``
        If this person is employed by the University of Florida, this is their
        employee number. This is the same as one's UFID Number.
    ``affiliation``
        Described `here <https://phonebook.ufl.edu/affiliations/>`_. As of
        writing, possible values include "faculty", "staff", "student", and
        "member".
    ``address``
        The person's home address (or if that's not available, their first
        available physical address).
    ``office_address``
        The person's office address (if available).
    ``language``
        The person's prefered language.
    ``birth_date``
        An instance of :py:class:`datetype.date` representing the person's date
        of birth.
    ``raw_ldap``
        A dictionary of the raw fields pulled from the person's LDAP entry.
    """
    
    def __init__(self, browser):
        PhonebookBackend.__init__(self, browser)
        self.__fields = {"url", "url_ldap", "url_full", "title", "phone",
                         "preferred_phone", "email", "gatorlink_email",
                         "gatorlink", "department_number", "employee_number",
                         "affiliation", "address", "office_address", "language",
                         "birth_date"}
    
    def get_fields(self):
        return self.__fields
    
    fields = property(get_fields)
    
    def get_search_results(self, query, username, password):
        if username is not None and password is not None:
            search_url = "https://phonebook.ufl.edu/private/people/search"
        else:
            search_url = "https://phonebook.ufl.edu/people/search"
        
        lxml_source = self.browser.submit("GET", search_url, {"query":query},
                                          parser=parsers.lxml_html)
        
        info = lxml_source.xpath("//div[@id='results_info']/p")[0] \
                                .text_content().lower().strip()
        
        if "returned only one" in info:
            attributes = {}
            url = self.browser.current_url
            identifier = _person_url_re.match(url)
            data_hint = \
                HttpLdapDataHint(self.browser.expand_relative_url("full/", url))
            return [Person(**{key:[data_hint] for key in self.fields},
                           identifier=identifier)]
        elif "did not match any members" in info:
            return []
        else:
            if "returned the following" in info:
                pass
            elif "returned too many people" in info:
                logger.warning("Too many people returned by query, some "
                               "results were skipped.")
            else:
                logger.error("Unable to determine status of query; trying to "
                             "parse as though multiple results were returned.")
            return self.get_search_results_from_list(lxml_source)
    
    
    def get_search_results_from_list(self, lxml_source):
        table = lxml_source.xpath("//div[@id='content']//table")[0]
        headers = [i.text.lower().strip() for i in table.xpath("./thead//th")]
        body = table.xpath("./tbody//tr")
        # build Person objects
        results = []
        for row in body:
            d = dict(zip(headers, row.xpath("./td")))
            
            # process the url
            url = d["name"][0].get("href")
            url_ldap = self.browser.expand_relative_url("full/", url)
            url_match = _person_url_re.match(url)
            identifier = url_match.group("ident")
            private = url_match.group("priv") > 0
            
            data_hint = HttpLdapDataHint(url_ldap)
            # initially fill in all fields with DataHints, marking them unknown
            attributes = {key:[data_hint] for key in self.fields}
            
            # fill in the attributes related to the url
            attributes.update(
                url=url, url_ldap=url_ldap, url_full=url_ldap,
                url_vcard=self.browser.expand_relative_url("vcard/", url)
            )
            
            name = d["name"].text_content().strip()
            title = d["title"].text_content().strip()
            phone = d["phone"].text_content().strip()
            if not phone:
                phone = None
            email = d["email"].text_content().strip()
            if not email:
                email = None
            elif "@ufl.edu" in email:
                gatorlink = email[:-len("@ufl.edu")]
                gatorlink_email = attributes["email"]
                attributes.update(gatorlink=gatorlink,
                                  gatorlink_email=gatorlink_email)
            attributes.update(name=name, title=title, phone=phone,
                              preferred_phone=phone, email=email)
            results.append(Person(**attributes, identifier=identifier))
        return results
    
    def process_datahint(self, hint):
        lxml_source = self.browser.load_page(hint.url, parser=parsers.lxml_html)
        
        element_list = lxml_source.xpath("//div[@id='ldap']/dl")[0]
        keys = [i.text.strip() for i in element_list.xpath("./dt")]
        values = [i.text.strip() for i in element_list.xpath("./dd")]
        data = collections.defaultdict(lambda: None)
        base_data = dict(zip(keys, values))
        data.update(base_data)
        
        # Utility Functions:
        def fix_address(s): # Replace the $s in addresses with newlines
            return s.replace("$", "\n") if s is not None else None
        def select(data, *keys): # given keys, select the first one with a value
            for i in keys:
                if data[i]:
                    return data[i]
            return None
        
        # process some more complicated fields first:
        base_title = select("title", "eduPersonPrimaryAffiliation")
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
            gatorlink_email = attributes["email"]
        else:
            gatorlink = data["uid"] if data["uid"] \
                                    else data["homeDirectory"][3:] \
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
                    select(data, "postalAddress",
                           "homePostalAddress", "registeredAddress",
                           "uflEduOfficeLocation", "street"
                    )
                ),
            "office_address":
                fix_address(
                    select(data, "officeAddress", "uflEduOfficeLocation")
                ),
            "language":data["language"],
            "birth_date":birth_date
        }.items() if v is not None}
