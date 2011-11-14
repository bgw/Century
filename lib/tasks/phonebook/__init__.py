from ...browser import parsers
from .. import *

import abc

class Phonebook(BaseUFTaskManager, BaseTaskManager):
    """Pulls information from the database available at
    https://phonebook.ufl.edu/. While a best attempt is made, take the
    information pulled with a grain of salt: not all the info in the database is
    correct or up to date. Additionally, in an attempt to simplify data access,
    some data (unfortunately) may be missed, especially as UF adds new keys to
    their LDAP system."""
    
    def __init__(self, backend, browser=None, caching=True):
        BaseUFTaskManager.__init__(self)
        BaseTaskManager.__init__(self, browser)
        self.__caching = caching
        self.__backend = backend(self.browser)
        if self.__caching:
            self.__person_pool = {}
    
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
                person_id = results[i]._identifier
                if person_id in self.__person_pool:
                    results[i] = self.__person_pool[person_id]
                else:
                    self.__person_pool[person_id] = results[i]
        return results


class PhonebookBackend(metaclass=abc.ABCMeta):
    def __init__(self, browser):
        self.__browser = browser
    
    def get_browser(self):
        return self.__browser
    
    browser = property(get_browser)
    
    @abc.abstractmethod
    def get_search_results(self, query, username, password):
        pass


class Person(object):
    def __init__(self, identifier, attributes):
        self.__identifier = identifier
        self.__attributes = attributes
    
    def _get_identifier(self):
        return self.__identifier
    
    _identifier = property(_get_identifier)
    
    def __eq__(self, other):
        return self._identifier == other._Person_identifier
    
    def __getitem__(self, key):
        if hasattr(self.__attributes[key], "__call__"):
            self.__attributes[key] = self.__attributes[key]()
        return self.__attributes[key]
    
    def __str__(self):
        return str({i:str(self[i]) for i in self.__attributes})
    
    def __repr__(self):
        return "Person(%s, %s)" % (repr(self._identifier), str(self))
