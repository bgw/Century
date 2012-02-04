from . import PhonebookBackend
from .person import *
from ...browser import parsers
from .ldap import utils as ldap_utils

import lxml
import re
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
    ``name``
        The person's name, as a string, typically: "Lastname, Firstname"
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
        self.__fields = ldap_utils.supported_fields | \
                        {"url", "url_ldap", "url_full", "url_vcard"}
    
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
            url_ldap = self.browser.expand_relative_url("full/", url)
            identifier = _person_url_re.match(url).group("ident")
            data_hint = HttpLdapDataHint(url_ldap)
            return [Person(identifier=identifier, backend=self, **dict(
                list({key:[data_hint] for key in self.fields}.items()) +
                list({
                    "url":url, "url_ldap":url_ldap, "url_full":url_ldap,
                    "url_vcard":self.browser.expand_relative_url("vcard/", url)
                }.items())
            ))]
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
            private = bool(url_match.group("priv"))
            
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
            results.append(Person(identifier=identifier, backend=self,
                                  **attributes))
        return results
    
    def process_datahint(self, hint):
        lxml_source = self.browser.load_page(hint.url, parser=parsers.lxml_html)
        
        element_list = lxml_source.xpath("//div[@id='ldap']/dl")[0]
        keys = [i.text.strip() for i in element_list.xpath("./dt")]
        values = [i.text.strip() for i in element_list.xpath("./dd")]
        
        return ldap_utils.process_data(zip(keys, values))
