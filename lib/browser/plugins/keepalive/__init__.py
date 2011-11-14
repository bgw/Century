from .. import BaseBrowserPlugin
from ..decorators import *
from . import handler

class KeepAlivePlugin(BaseBrowserPlugin):
    """Adds a :mod:`urllib` handler to make :mod:`urllib` and
    :class:`lib.browser.Browser` utilize HTTP's ``Keep-Alive`` header, making
    muliple page loads from the same server *significantly* faster."""
    
    def __init__(self):
        BaseBrowserPlugin.__init__(self)
        self.handlers.append(handler.HTTPHandler())
