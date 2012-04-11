from ...browser import parsers
from .. import *
from .person import *

import abc

class Phonebook(BaseUFTaskManager, BaseTaskManager):
    """Pulls information from the database available at
    https://phonebook.ufl.edu/.
    
    .. warning::
        While a best attempt is made, take the information pulled with a grain
        of salt: not all the info in the database is correct or up to date.
        Additionally, in an attempt to simplify data access, some data
        (unfortunately) may be missed, especially as UF adds new keys to their
        LDAP system.
    
    *Keyword Arguments:*
    
    ``backend``
        A :class:`PhonebookBackend` class (not instance). The backend is used to
        pull information on a person.
    ``browser``
        A browser to use. If passed ``None``, a new one is automatically
        created.
    ``caching``
        When ``True``, saves information on people, such that all the detailed
        data on the people is immediately available. 
    """
    
    def __init__(self, backend, browser=None, caching=True):
        BaseUFTaskManager.__init__(self)
        BaseTaskManager.__init__(self, browser)
        self.__caching = caching
        self.__backend = backend(self.browser)
        if self.__caching:
            self.__person_pool = {}
    
    def get_fields(self):
        return self.__backend.fields
    
    fields = property(get_fields, """
        Returns the :class:`frozenset` instance provided by
        :attr:`PhonebookBackend.fields`. Further information about these fields
        can be looked up in :data:`lib.tasks.phonebook.fields.info_dict`.
    """)
    
    def search(self, query):
        """Passes the plain-text query off to a backend. This will always return
        a list, as should the related function on the backend. If the backend
        returns a result that it has already returned, and if caching is
        enabled, this function will replace the new results with their cached
        results from a pool."""
        results = self.__backend.get_search_results(query,
                                                    self.browser.uf_username,
                                                    self.browser.uf_password)
        if self.__caching:
            for i in range(len(results)):
                person_id = results[i].identifier
                if person_id in self.__person_pool:
                    results[i] = self.__person_pool[person_id]
                else:
                    self.__person_pool[person_id] = results[i]
        return results


class PhonebookBackend(metaclass=abc.ABCMeta):
    """A subclass can be used by the :class:`Phonebook` class to lookup person
    information."""
    def __init__(self, browser):
        self.__browser = browser
    
    def get_browser(self):
        return self.__browser
    
    browser = property(get_browser, doc="""
        The state-machine browser to use to pull information and submit queries
        with.
    """)
    
    fields = abc.abstractproperty()
    
    @abc.abstractmethod
    def get_search_results(self, query, username, password):
        """A method that should be overridden to provide search results, given
        a query and login credentials. Results should be a list of
        :class:`lib.tasks.phonebook.person.Person` objects."""
        pass
    
    @abc.abstractmethod
    def process_datahint(self, data_hint):
        """Given a :class:`lib.tasks.phonebook.person.DataHint`, this method
        should find as much information about the person as possible, and then
        it should return it as a dict. Duplicate information is discarded, extra
        information is saved."""
        pass

PhonebookBackend.fields.__doc__ = """
    A list of all possible keys in resulting
    :class:`lib.tasks.phonebook.person.Person` objects. Any values listed in
    here without value in the :class:`lib.tasks.phonebook.person.Person` object
    should be None.
"""
