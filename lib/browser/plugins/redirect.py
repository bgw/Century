from . import BaseBrowserPlugin
from .decorators import *
from .. import parsers

import re
import abc
import logging

logger = logging.getLogger("browser.plugins.redirect")

class BaseRedirectionPlugin(BaseBrowserPlugin, metaclass=abc.ABCMeta):
    """Provides a simple framework for handling pages that require a redirection
    with a hope to reduce the necessity for so much boilerplate code. You don't
    have to extend this class to handle redirections, but it might make things
    easier."""
    
    def __init__(self, url_match=None, page_match=None,
                 parser=parsers.passthrough_str):
        """Keyword arguments:
        
        ``url_match``
            A string, regex object (using ``match``), or callable used to check
            if a page url can potentially be a page that needs redirection.
        ``page_match``
            A string, regex object (using ``match``), or callable used to check
            if a page source (decoded by parser) can potentially be a page that
            needs redirection.
        ``parser``
            A parser function that should be applied to the page data before
            sending it to :meth:`handle_redirect`."""
        BaseBrowserPlugin.__init__(self)
        self.__url_match = url_match
        self.__page_match = page_match
        self.__parser = parser
    
    def __match(self, key, value):
        if key is None: return True # True if we have no key to check against
        if isinstance(key, str): return key == value # direct match
        if hasattr(key, "match"): return key.match(value) # regex
        return self.__url_match(url) # callable: lambda or function
    
    def _is_valid_url(self, url):
        """One can override this function as an alternative to providing a
        ``url_match`` value via the constructor. If neither is specified, this
        just returns ``True``."""
        return self.__match(self.__url_match, url)
    
    def _is_valid_page(self, source):
        """One can override this function as an alternative to providing a
        ``page_match`` value via the constructor. If neither is specified, this
        just returns ``True``."""
        return self.__match(self.__page_match, source)
    
    @override
    def load_page(plugin, browser, base_function, url, *args, **kwargs):
        """Calls :meth:`handle_redirect` if there is both a url and page match,
        otherwise, it simply passes through."""
        url = browser._simplify_url(url)
        if not plugin._is_valid_url(url):
            return base_function(url, *args, **kwargs)
        
        # mix around our arguments
        new_kwargs = dict(kwargs)
        new_kwargs["parser"] = parsers.passthrough_args
        
        # load the page
        parser_args = base_function(url, *args, **new_kwargs)
        if url != parser_args[2]:
            url = browser._simplify_url(parser_args[2]) # update the url
            if not plugin._is_valid_url(url):
                return base_function(url, *args, **kwargs)
        
        # check that it's the right page before we waste time trying to
        # parse it
        def fallback():
            return browser._parse_page(
                kwargs["parser"] if "parser" in kwargs else None, *parser_args
            )
        parsed_page_src = plugin.__parser(*parser_args)
        if not plugin._is_valid_page(parsed_page_src):
            return fallback()
        
        result = plugin.handle_redirect(browser, url, parsed_page_src,
                                        *args, **kwargs)
        if result is None:
            return fallback()
        
        return result
    
    @abc.abstractmethod
    def handle_redirect(plugin, browser, url, source, *args,
                        **kwargs):
        """Should return the value given by ``browser.load_page`` with the
        additional arguments, ``*args`` and ``**kwargs`` (modified if desired).
        If it returns ``None`` or raises a :class:`PageRedirectionError`, the
        redirect is canceled. Here's an example handle_redirect method::
        
            def handle_redirect(plugin, browser, url, parsed, *args, **kwargs):
                "For this example, we'll say the plugin's parser is lxml"
                return browser.load_page(parsed.xpath("//a")[0].attrib["href"],
                                         *args, **kwargs)
        
        ..
        """
        pass

class PageRedirectionError(Exception):
    def __init__(self):
        Exception.__init__(self)



class BrowserMetaRefreshHander(BaseRedirectionPlugin):
    """Handles pages using the deprecated html `meta refresh`_ feature.
    
    ..  _meta refresh: http://www.w3.org/TR/WCAG10-HTML-TECHS/#meta-element"""
    def __init__(self, max_seconds=None):
        BaseRedirectionPlugin.__init__(self, parser=parsers.passthrough_str)
        self._max_seconds = max_seconds
        
        # compile all the regex patterns we use in handle_redirect
        self._meta_re = re.compile(
            r"""\<meta( [^>]*)? http-equiv=["']refresh["']( [^>]*)?\>""",
            re.IGNORECASE | re.DOTALL
        )
        self._content_re = re.compile(r"""(?<=content=["']).+?(?=["'])""",
                                      re.IGNORECASE | re.DOTALL)
        self._timeout_re = re.compile(r"""\A\d+""")
        self._url_re = re.compile(r"""(?<=url=).+""")
    
    
    def handle_redirect(plugin, browser, base_url, source, *args, **kwargs):
        # look for a <meta> tag with the refresh property
        meta_tag = plugin._meta_re.search(source)
        if not meta_tag: return None # not a match
        meta_tag = meta_tag.group()
        
        # pull the content property from the tag if it's there
        content = plugin._content_re.search(meta_tag)
        content = content.group() if content else ""
        
        # parse the data in the content property
        
        # solve for the load delay (specified in seconds)
        timeout = plugin._timeout_re.search(content)
        if timeout:
            timeout = int(timeout.group())
        else:
            timeout = 0
        if plugin._max_seconds is not None and timeout > plugin._max_seconds:
            return None # we shouldn't follow this redirect
        
        # solve for the new url to go to (if none is specified, just refresh)
        new_url = plugin._url_re.search(content)
        if new_url:
            new_url = new_url.group()
        else:
            new_url = base_url
        
        return browser.load_page(new_url, *args, **kwargs)
