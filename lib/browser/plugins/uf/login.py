"""A module for handling
`Shibboleth <https://www.youtube.com/watch?v=HlsnToZLD3k>`_ related GatorLink
logins."""

from ..redirect import BaseRedirectionPlugin
from ..decorators import *
from ... import parsers

import html.parser
import re
import logging

logger = logging.getLogger("browser.plugins.uf.login")
_html_unescape = lambda data: html.parser.HTMLParser.unescape(None, data)

class LoginBrowserPlugin(BaseRedirectionPlugin):
    """Can handle pages asking for your GatorLink login information using the
    standard Shibboleth-based form. It works in 99% of login cases, and can even
    be set up to enter one's password completely automatically, acting like a
    simple redirect."""
    
    def __init__(self):
        """Instantiates a plugin instance, without any login information. To
        enable automatic logins, call :meth:`uf_set_autologin`."""
        page_match = re.compile(r'.*\<title\>.*?GatorLink login.*?\</title\>.*?'
                                r'\<body\>.*?Enter your GatorLink username and '
                                r'password.*?\</body\>',
                                re.IGNORECASE | re.DOTALL)
        BaseRedirectionPlugin.__init__(self, page_match=page_match,
                                       parser=parsers.passthrough_str)
        self._uf_session_cookie = None
        self._login_url = "https://login.ufl.edu/idp/Authn/UserPassword"
        self._auto_login = False
        self.__username = None
        self.__password = None
    
    def _is_valid_url(self, url):
        return self._auto_login# and url == self._login_url
    
    @property_extension
    def uf_username(plugin, browser):
        """A :func:`lib.browser.plugins.decorators.property_extension`
        representing the plugin's autologin username. Note that simply setting
        this does not enable autologin, that must be done with
        :meth:`uf_set_autologin`."""
        def getter():
            return plugin.__username
        def setter(val):
            plugin.__username = val
        return property(getter, setter)
    
    @property_extension
    def uf_password(plugin, browser):
        """A :func:`lib.browser.plugins.decorators.property_extension`
        representing the plugin's autologin password. Note that simply setting
        this does not enable autologin, that must be done with
        :meth:`uf_set_autologin`. As is the case with any tool using your
        password, make sure you do not load any rouge, untrusted plugins, as one
        could potentially steal your plaintext password with it."""
        def getter():
            return plugin.__password
        def setter(val):
            plugin.__password = val
        return property(getter, setter)
    
    @extension
    def uf_set_autologin(plugin, browser, username=None, password=None,
                         enabled=True):
        """A :func:`lib.browser.plugins.decorators.extension` that can be used
        to enable or disable automatic login handling."""
        plugin._auto_login = enabled
        if username:
            plugin.__username = username
        if password:
            plugin.__password = password
    
    @property_extension
    def uf_session_cookie(plugin, browser):
        """A :func:`lib.browser.plugins.decorators.property_extension` that can
        get (but not set) a :class:`http.cookiejar.Cookie` object containing the
        login state. If we have not not logged in, or our session is expired,
        gives ``None``."""
        def getter():
            c = plugin._uf_session_cookie
            if c is not None and not c.is_expired():
                return c
            return None
        return property(getter)
    
    @extension
    def uf_login(plugin, browser, username, password, *args, **kwargs):
        """A :func:`lib.browser.plugins.decorators.extension` that will submit a
        HTTP POST Request to login. Please note that :mod:`urllib` (or
        :mod:`urllib2` in Python 2) does not perform SSL certificate
        authentication, so while the connection will be done over HTTPS, an
        active man-in-the-middle attack could potentially compromise your
        password, however the chance of that is quite rare. This function does
        not load the login page, nor does it need to, it simply submits the
        login form as though it had already loaded the login page."""
        # suspend automatic login, so we can catch a possible failed login
        al = plugin._auto_login
        plugin._auto_login = False
        
        new_kwargs = dict(kwargs)
        new_kwargs["parser"] = parsers.passthrough_args
        result = browser.submit("POST", plugin._login_url,
                                [("j_username", username),
                                 ("j_password", password),
                                 ("login", "Login")],
                                *args, **new_kwargs)
        source = parsers.passthrough_str(*result)
        
        # check to see if we had a bad username/password combo
        if "Your username or password is incorrect. Please try again." in \
           source:
            raise LoginError()
        
        if "An error occurred while processing your request." in source:
            raise LoginError()
        
        plugin._uf_session_cookie = plugin.__get_login_cookie(
            browser.cookie_jar
        )
        
        # restore automatic login
        plugin._auto_login = al
        
        return browser._parse_page(
            kwargs["parser"] if "parser" in kwargs else None, *result
        )
    
    def handle_redirect(plugin, browser, base_url, source, *args, **kwargs):
        """If ``plugin``'s :attr:`_auto_login` is ``True``, handles a login page
        automatically."""
        return browser.uf_login(browser.uf_username, browser.uf_password, *args,
               **kwargs)
    
    def __get_login_cookie(self, jar):
        last_expiration = 0
        last_cookie = None
        for cookie in jar:
            if not cookie.is_expired() and cookie.path == "/idp" and \
               cookie.name == "JSESSIONID":
                if not cookie.is_expired(last_expiration):
                    last_expiration = cookie.expires
                    last_cookie = cookie
            return cookie
    
    @extension
    def uf_logout(plugin, browser, refresh=False):
        """Disables the auto-login system, and logs you out (by simply deleting
        the session cookie). The ``refresh`` argument can be used to call
        :meth:`lib.browser.Browser.refresh`, returning the new result."""
        # disable auto-login
        browser.uf_set_autologin(enabled=False)
        
        # clear login cookies
        try:
            browser.cookie_jar.clear(path="/idp", name="JSESSIONID")
            browser.cookie_jar.clear(path="/", name="UF_GSM")
            plugin._uf_session_cookie = None
        except KeyError:
            pass
        
        if refresh:
            if browser.current_url.index("https://login.ufl.edu") == 0:
                return browser.refresh(data=None)
            else:
                return browser.refresh()

class LoginError(Exception):
    def __init__(self):
        Exception.__init__(self, "Bad username or password.")


class LoginContinueRedirect(BaseRedirectionPlugin):
    """Handles Shibboleth redirection pages that need a specially-formed POST
    message to continue through. This is normally handed via JavaScript, but
    we'll just handle this ourselves. This should be used with
    :class:`LoginBrowserPlugin`."""
    
    def __init__(self):
        url_match = re.compile(
            r"https://login.ufl.edu(:\d+)?/idp/"
            r"(profile/SAML2/Redirect/SSO|Authn/UserPassword)"
        )
        page_match_re = re.compile(
            r'.*?\<body onload="document\.forms\[0].submit\(\)"\>.*?'
            r'\<noscript\>.*?\<form action="(?P<post_url>.*?Shibboleth\.sso.*?'
            r'SAML2.*?POST)" method="post"\>',
            re.IGNORECASE | re.DOTALL
        )
        BaseRedirectionPlugin.__init__(self, url_match=url_match,
                                       page_match=page_match_re,
                                       parser=parsers.passthrough_str)
        
        self._page_match_re = page_match_re
        # compile the regex objects we'll need to parse the page
        self._form_element_re = re.compile(
            r'\<input( .*?)?? name="(?P<name>.+?)"( .*?)?? '
            r'value="(?P<value>.+?)".*?/>',
            re.IGNORECASE | re.DOTALL
        )
    
    def handle_redirect(plugin, browser, base_url, source, *args, **kwargs):
        """The function that does the magic of pulling the form data from the
        Shibboleth redirection page, and resubmits it."""
        logger.debug("Page matched")
        post_url = plugin._page_match_re.match(source).group("post_url")
        post_url = _html_unescape(post_url)
        form_re = re.compile(
            r'(\<form action=".*?Shibboleth\.sso.*?" method="post"\>)(.*?)'
            r'(\</form\>)',
            re.IGNORECASE | re.DOTALL
        )
        form = form_re.search(source).group(2)
        
        # build our POST values list
        post_data = [(i.group("name"), _html_unescape(i.group("value")))
                     for i in plugin._form_element_re.finditer(form)]
        
        # submit it
        return browser.submit("POST", post_url, post_data, *args,
                              **kwargs)
