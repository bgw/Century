from . import BaseBrowserPlugin
from .decorators import *

from urllib.request import HTTPCookieProcessor
from http.cookiejar import CookieJar

class CookieBrowserPlugin(BaseBrowserPlugin):
    """Adds a handler to a :class:`lib.browser.Browser` for cookies. Recieving
    and sending cookies then happens in a automatic fashion."""
    def __init__(self):
        """Creates a new plugin with an empty jar."""
        BaseBrowserPlugin.__init__(self)
        self._jar = CookieJar()
        self.handlers.append(HTTPCookieProcessor(self._jar))
    
    @property_extension
    def cookie_jar(plugin, browser):
        """Adds the property ``cookie_jar`` to the browser, allowing you to get
        the handler's :class:`http.cookiejar.CookieJar` instance."""
        def getter():
            return plugin._jar
        return property(getter)
