from .. import BaseBrowserPlugin
from ..decorators import *

"""This module is designed to help with various sections of the ISIS site.

**Please Note:** "The use of any automated program to attempt to add courses or
to search sections on the ISIS registration system is strictly prohibited," so
be careful not to do anything against the rules with this module."""

class IsisBrowserTools(BaseBrowserPlugin):
    """Contains various simple ISIS utilities."""
    
    def __init__(self):
        BaseBrowserPlugin.__init__(self)
        self._base_url = "https://www.isis.ufl.edu/cgi-bin/nirvana"
        self._page_key = "MDASTRAN"
    
    @extension
    def load_isis_page(plugin, browser, page_code, *args, **kwargs):
        """Given a page code (given by the links on the isis sidebar), loads a
        page. Examples of this are ``TRQ-SPEND``, ``RSI-GRADES`` or
        ``RSI-RGHOLD``. Codes appear to be in all caps, composed of 3 letters,
        followed by a hyphen, and then another small group of letters, however
        this could change. Page codes can be submitted as either HTTP GET or
        POST requests, however this method simply uses GET requests, making
        requests apparent when looking at the loaded URL."""
        return browser.submit("GET", plugin._base_url,
                              {plugin._page_key:page_code}, *args, **kwargs)
