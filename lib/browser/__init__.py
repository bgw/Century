from . import parsers
from .plugins.decorators import plugin_attribute
from .plugins import Pluggable

import urllib.request as urlreq
import urllib.parse as urlpar
import logging

logger = logging.getLogger("browser")

class Browser(Pluggable):
    """An extensible system for using urllib like a state-machine. Functions act
    much like they would on a browser, with stuff like a :meth:`back` method and
    caching. A plugin system is used to allow a prototypical multiple-
    inheritance-like system at runtime. It's like a highly structured form of
    monkey-patching."""
    
    def __init__(self, *plugins, default_parser=parsers.passthrough_str):
        """Creates a new :py:class:`Browser` object, loaded with the specified
        set of plugins, and using the specified default parser. Both these
        values can be changed after instantiation (however you cannot remove
        plugins, only add them)."""
        Pluggable.__init__(self)
        self.default_parser = default_parser
        self.__history = [] # (url, data)
        self.__history_offset = 0
        self.__opener = urlreq.build_opener()
        self.load_plugins(*plugins)
    
    @plugin_attribute
    def handlers(self, handler):
        """Defines how :py:class:`Pluggable` will work with urllib handlers. For
        example, if you wanted to add cookie handling support via a plugin, you
        could run::
            
            self.handlers.append(HTTPCookieProcessor(CookieJar))
        
        within the ``__init__`` function.
        """
        self.__opener.add_handler(handler)
    
    @plugin_attribute
    def addheaders(self, header):
        """Used by :py:class:`Pluggable` to handle additional headers for the
        urllib opener. Here's an example of how it can be used within a plugin::
            
            self.addheaders.append(("user-agent", agent_string))
        
        ..
        """
        self.__opener.addheaders.append(header)
    
    # public attributes
    
    history = property(lambda self: self.get_history(),
        doc="""A list containing information on previously visited web pages, in
        the form of tuples, ``(url, post_data)``. While HTTP POST data is
        included explicitly, HTTP GET data is included within the URL.""")
    
    def get_history(self):
        if not self.__history:
            return ()
        return tuple(self.__url_history[:-1])
    
    
    current_url = property(lambda self: self.get_current_url())
    
    def get_current_url(self):
        return self.__history[-1][0]
    
    current_data = property(lambda self: self.get_current_data())
    
    def get_current_data(self):
        return self.__history[-1][1]
    
    # actual networking functions
    def submit(self, method, url, values, *args, **kwargs):
        """Takes values and encodes them to send back to the server, eventually
        loading a new page as a result. It satisfies the
        :func:`lxml.html.submit_form` ``open_http`` argument. Many of the
        keyword arguments map directly to :meth:`load_page`.
        
        *Keyword arguments:*
        
        ``method``
            A string consisting of ``"GET"`` or ``"POST"``.
        ``url``
            The ``http://`` or ``https://`` page to load.
        ``values``
            Either a dictionary or list of two-item tuples containing the data
            to encode
        ``parser``
            If ``None``, maps to the default parser, specified upon
            construction. (If one was not specified, then
            :func:`.parsers.passthrough` is used, which does nothing to the page
            data, and just returns the page source. A parser should follow the
            format::
                
                parser(source, url)
                
        ``record_history``
            If ``False``, the page will not be entered into the internal list of
            pages loaded, and so the only reminder of this page load will be the
            cache (and possibly stuff like cookies for instance if you have
            :class:`cookies.CookieBrowserPlugin` enabled). This is used
            internally for the :meth:`back`, :meth:`forward` and :meth:`refresh`
            functions.
        """
        
        if method == 'GET':
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += urlpar.urlencode(values)
            data = None
        else:
            data = urlpar.urlencode(values).encode()
       	
        kwargs["data"] = data
        
        return self.load_page(url, *args, **kwargs)
    
    
    def load_page(self, url, parser=None, data=None, record_history=True):
        """Requests, loads, and parses a webpage using the internal
        :mod:`urllib` based opener It is recommended, but not required, that
        beyond the first url argument, you use keyword arguments, as some poorly
        written plugins overriding this function may not behave nicely with the
        large number of positional arguments. Additionally, their order is
        subject to change.
        
        *Keyword arguments:*
        
        ``url``
            The ``http://`` or ``https://`` page to load. Can alternatively
            be a relative address (which is then treated as relative to the
            current page)
        ``parser``
            If ``None``, maps to the default parser, specified upon
            construction. (If one was not specified, then
            :func:`.parsers.passthrough` is used, which does nothing to the page
            data, and just returns the page source. A parser should follow the
            format::
                
                parser(source, url)
            
        ``data``
            Maps to the ``data`` parameter of :func:`urllib.request.urlopen`.
            This should contain pre-encoded ``HTTP`` ``POST`` data. ``GET`` data
            should be encoded into the page url.
        ``record_history``
            If ``False``, the page will not be entered into the internal list of
            pages loaded, and so the only reminder of this page load will be the
            cache (and possibly stuff like cookies for instance if you have
            :class:`cookies.CookieBrowserPlugin` enabled). This is used
            internally for the :meth:`back`, :meth:`forward` and :meth:`refresh`
            functions.
        """
        logger.info("Loading url: '%s'" % (url if url is not None else "None"))
        
        # preprocess arguments
        if not url:
            raise ValueError("cannot submit, no URL provided")
        
        if "://" not in url: # solve relative urls
            url = urlpar.urljoin(self.current_url, url)
            logger.debug("Relative URL expanded to %s" % url)
        # remove ending slashes from urls to make them easier to compare
        url = self._simplify_url(url)
        
        try:
            raw_source = self.__opener.open(url, data)
        except Exception as err:
            raw_source = err
        source = raw_source.read()
        url = self._simplify_url(raw_source.geturl()) # updates the url in case
                                                      # we got header-redirected
        
        if record_history:
            self.__history.append((url, data))
            if self.__history_offset < 0:
               self.__history = self.__history[:self.__history_offset]
            self.__history_offset = 0
        
        # log the loaded page source to screen
        logger.info("Page url %s is done loading." % url)
        if logger.isEnabledFor(logging.DEBUG): # save some cpu, do conditionally
            logger.debug("Page source (fast UTF-8 decode): %s" %
                         source.decode("UTF-8", errors="ignore"))
        
        return self._parse_page(parser, source, raw_source.info(), url)
    
    def expand_relative_url(self, url, relative_to=None):
        """If passed a relative url, finds it's absolute url in relation to the
        current page's url."""
        relative_to = self.current_url if relative_to is None else relative_to
        if "://" not in url: # solve relative urls
            url = urlpar.urljoin(relative_to, url)
        return url
    
    # Browsing history functions
    def _load_relative(self, relative_index, *args, **kwargs):
        """Loads a page relative in history to the current page. For example,
        going back one page could be done with::
            
            self._load_relative(-1, *args, **kwargs)
        
        This method is not to be confused with the similarly named
        :py:meth:`expand_relative_url`, which instead works to turn relative
        urls into absolute ones."""
        if "record_history" not in kwargs and len(args) < 4:
            kwargs["record_history"] = False
        self.__history_offset += relative_index
        index = len(self.__history) - 1 + self.__history_offset
        assert index > 0 and index < len(self.__history)
        if "data" not in kwargs and len(args) < 3:
            kwargs["data"] = self.__history[index][1]
        return load_page(self.__history[index][0], *args, **kwargs)
    
    def back(self, *args, **kwargs):
        """Reloads the previous page (if there is one) and returns it.
        Additional arguments (positional and keyword) will be passed through to
        :py:meth:`load_page`."""
        self._load_relative(-1, *args, **kwargs)
    
    def forward(self, *args, **kwargs):
        """Reloads the next page (if there is one) and returns it."""
        self._load_relative(1, *args, **kwargs)
    
    def refresh(self, *args, **kwargs):
        """Reloads the current web page, and returns it."""
        self._load_relative(0, *args, **kwargs)
    
    # utility function
    def _parse_page(self, parser, *args, **kwargs):
        """Takes a page and parses it with a given parser, or with the default
        parser if the given parser is ``None``. There are two ways to call this
        method:
        
         - ``self._parse_page(parser, source, headers, url)``
         - ``self._parse_page(parser, response)``
        
        Where ``source`` is the byte-string gotten from ``response.read()``,
        ``headers`` is the result of calling ``response.info()``, and response
        is the result given by calling :py:func:`urllib.response.urlopen`.
        """
        # pass ourselves off to the proper helper method
        if len(args) + len(kwargs) == 3:
            return self.__parse_page_base(parser, *args, **kwargs)
        return self.__parse_page_resp(self, parser, *args, **kwargs)
    
    def __parse_page_base(self, parser, source, headers, url):
        if parser is None:
            return self.default_parser(source, headers, url)
        return parser(source, headers, url)
    
    def __parse_page_resp(self, parser, response):
        return self.__parse_page_base(parser, response.read(), response.headers,
                                      response.geturl())
    
    def _simplify_url(self, url):
        """Removes ``#fragments`` from urls, removes a ``trailing/`` from the
        path, if there is one (without destroying ``?parameters``), and gets rid
        of any unnecessary elements, like an unused ``?``. This is useful,
        because it makes it easier to compare urls, for caching, and for other
        reasons."""
        #split_url = list(urlpar.urlparse(url))
        ## if split_url[2] and split_url[2][-1] == "/": # simplify the path attr
        ##     split_url[2] = split_url[2][:-1]
        #split_url[5] = "" # get rid of page#fragments
        #return urlpar.urlunparse(split_url) # stitch it all back together
        return url

def get_new_uf_browser():
    """Returns a new Browser object with the set of recommended plugins."""
    from . import parsers
    from .plugins import cookies
    from .plugins import useragent
    from .plugins import redirect
    from .plugins import keepalive
    from .plugins.uf import isis
    from .plugins.uf import login
    return Browser(cookies.CookieBrowserPlugin(), useragent.UserAgentSpoofer(
                   useragent.firefox["iceweasel-linux-5.0"]),
                   redirect.BrowserMetaRefreshHander(),
                   keepalive.KeepAlivePlugin(),
                   isis.IsisBrowserTools(), login.LoginBrowserPlugin(),
                   login.LoginContinueRedirect(),
                   default_parser=parsers.lxml_html)
