from . import BaseBrowserPlugin
from .decorators import *

firefox = {"iceweasel-linux-5.0":"Mozilla/5.0 (X11; Linux x86; rv:5.0) "
                                 "Gecko/20100101 Firefox/5.0 Iceweasel/5.0",
           "firefox-macintosh-5.0":"Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                   "10.7; rv:5.0) Gecko/20100101 Firefox/5.0",
           "firefox-windows-4.0":"Mozilla/5.0 (Windows; U; Windows NT 5.1; "
                                 "en-US; rv:2.0.1) Gecko/20110606"
                                 "Firefox/4.0.1"
          }

class UserAgentSpoofer(BaseBrowserPlugin):
    """Allows one to easily change the browser's HTTP ``user-agent`` header.
    This can be handy if you want to ensure that we are treated like a
    real-world browser."""
    
    def __init__(self, agent_string):
        """Creates a new instance of the plugin using the specified user-agent
        string. The string can be custom, or can be pulled from one of the
        class' example strings."""
        BaseBrowserPlugin.__init__(self)
        self.addheaders += [("user-agent", agent_string)]
