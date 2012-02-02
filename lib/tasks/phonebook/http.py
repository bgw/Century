from . import PhonebookBackend
from . import Person
from ...browser import parsers

import lxml
import datetime
import re
import logging
try: # py3k
    import urllib.parse as urlpar
except: # py2
    import urllib2 as urlpar

logger = logging.getLogger("tasks.phonebook.http")

_person_url_re = re.compile(
    r"https?://.*?\.ufl\.edu(\:\d+)?(/private)?/people/"
    r"(?P<ident>[A-Za-z0-9]*)/?"
)

class HttpBackend(PhonebookBackend):
    """Provides the http backend for the UF phonebook. Data is pulled from the
    returned html pages. Depending on the initial search query, some pulled data
    could potentially change (because it could end up getting pulled in a
    different fashion). If the data cannot be found, ``None`` is given. All
    values are of either type ``str`` or ``NoneType``, unless otherwise
    specified.
    
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
        employee number.
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
    """
    
    def __init__(self, browser):
        PhonebookBackend.__init__(self, browser)
    
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
            identifier = self._add_url_attributes(
                attributes, self.browser.current_url
            )
            self._add_ldap_attributes(attributes)
            return [Person(identifier, attributes), ]
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
            attributes = {}
            
            identifier = self._add_url_attributes(attributes,
                                                  d["name"][0].get("href"))
            
            attributes["name"] = d["name"].text_content().strip()
            attributes["title"] = d["title"].text_content().strip()
            attributes["phone"] = d["phone"].text.strip()
            attributes["preferred_phone"] = attributes["phone"]
            attributes["email"] = d["email"].text_content().strip()
            if "@ufl.edu" in attributes["email"]:
                attributes["gatorlink"] = attributes["email"][:-len("@ufl.edu")]
                attributes["gatorlink_email"] = attributes["email"]
            for i in attributes:
                if attributes[i] == "":
                    attributes[i] = None
            self._add_ldap_attributes(attributes)
            results.append(Person(identifier, attributes))
        return results
    
    
    def _add_url_attributes(self, attributes, url):
        """Adds attributes based on the "url" attribute, and then returns the
        identifier."""
        print(url)
        attributes["url"] = url
        attributes["url_ldap"] = self.browser.expand_relative_url("full/", url)
        attributes["url_full"] = attributes["url_ldap"]
        attributes["url_vcard"] = self.browser.expand_relative_url("vcard/",
                                                                   url)
        return _person_url_re.match(url).group("ident")
    
    
    def _add_ldap_attributes(self, attributes):
        def load_ldap():
            lxml_source = self.browser.load_page(attributes["url_ldap"],
                                                 parser=parsers.lxml_html)
            element_list = lxml_source.xpath("//div[@id='ldap']/dl")[0]
            keys = [i.text.strip() for i in element_list.xpath("./dt")]
            values = [i.text.strip() for i in element_list.xpath("./dd")]
            data = dict(zip(keys, values))
            
            # utility function
            def auto_fill(attr_key, *ldap_keys, apply_func=lambda x: x):
                """You can specify multiple ``ldap_keys``, because the ldap
                database contains tons of extra fields with (often) redundant
                information that are sometimes used, sometimes not."""
                if attributes[attr_key] is None or \
                   hasattr(attributes[attr_key], "__call__"):
                    for i in ldap_keys:
                        if i not in data:
                            continue
                        attributes[attr_key] = apply_func(data[i])
                        return
                    attributes[attr_key] = None
            
            def fix_address(string):
                return "\n".join([i.strip() for i in string.split("$")])
            
            auto_fill("name", "displayName", "cn")
            
            auto_fill("affiliation", "eduPersonPrimaryAffiliation")
            if hasattr(attributes["title"], "__call__"):
                base_title = data["title"] if "title" in data else \
                             attributes["affiliation"]
                if "o" in data:
                    attributes["title"] = "%s, %s" % (base_title, data["o"])
                else:
                    attributes["title"] = base_title
            
            auto_fill("email", "mail")
            auto_fill("phone", "telephoneNumber", "homePhone")
            attributes["preferred_phone"] = attributes["phone"]
            
            auto_fill("gatorlink", "uid")
            auto_fill("gatorlink", "homeDirectory", lambda s: s[3:])
            if hasattr(attributes["gatorlink_email"], "__call__"):
                attributes["gatorlink_email"] = "%s@ufl.edu" % \
                                                attributes["gatorlink"]
            auto_fill("department_number", "departmentNumber", "uflEduPsDeptId")
            auto_fill("employee_number", "employeeNumber")
            auto_fill("address", "postalAddress", "homePostalAddress",
                      "registeredAddress", "uflEduOfficeLocation", "street",
                      apply_func=fix_address)
            auto_fill("office_address", "officeAddress", apply_func=fix_address)
            auto_fill("language", "preferredLanguage")
            auto_fill(
                "birth_date", "uflEduBirthDate",
                apply_func=lambda s:
                    datetime.date(*[int(i) for i in s.split("-")])
            )
        
        def function_writer(value):
            def get_value():
                load_ldap()
                return attributes[value]
            return get_value
        
        provided_attributes = (
            "name", "title", "phone", "preferred_phone", "email",
            "gatorlink_email", "gatorlink", "department_number",
            "employee_number", "affiliation", "address", "office_address",
            "language", "birth_date"
        )
        
        # write and add all the callbacks
        for i in provided_attributes:
            if i not in attributes or attributes[i] is None:
                attributes[i] = function_writer(i)
