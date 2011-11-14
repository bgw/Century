"""Defines a set of useful parser functions, and generators for parser
functions. A parser function must take three arguments:

``source``
    The non-decoded raw byte result from the page load. This should be the
    result from a call to ``read()`` from the urllib file hander resulting from
    calling urllib.
``headers``
    The result of a call to ``info()`` on the file handler.
``url``
    The url of the current page (after redirects).
"""

import logging
import re

logger = logging.getLogger("browser.parser")

def passthrough(source, headers, url):
    """Returns the byte data given my the ``read()`` method on the result from
    ``urlopen``. This just returns the source argument that it's passed."""
    return source

def passthrough_args(source, headers, url):
    """Returns a tuple of the arguments it's given. You can then use these
    arguments to call multiple other parsers. Here's an example::
        
        args = lib.browser.load_page(url, parser=passthrough_args)
        lxml_data = lxml_html(*args)
        str_data = passthrough_str(*args)
    
    ..
    """
    return (source, headers, url)


def _get_header_charset(headers):
    try: # python 3
        return headers.get_param("charset")
    except AttributeError: # python 2
        try:
            return headers.getparam("charset")
        except AttributeError: # happens with file:// protocol
            return None

_meta_content_type_re = re.compile(
    r"""\<meta( [^>]*)? http-equiv=["']content-type["']( [^>]*)?\>""",
    re.IGNORECASE | re.DOTALL
)

_meta_inner_content_re = re.compile(r"""(?<=content=["']).+?(?=["'])""",
                                    re.IGNORECASE | re.DOTALL)

_meta_charset_re = re.compile(r"(?<=charset=)[a-z0-9-_]+",
                              re.IGNORECASE | re.DOTALL)

def _find_charset(str_source):
    # attempt to pull it from the html source
    start_search_at = 0
    while True:
        tag = _meta_content_type_re.search(str_source, start_search_at)
        if not tag:
            break
        start_search_at = tag.endpos
        
        tag = _meta_inner_content_re.search(tag.group(0))
        if not tag: continue
        
        tag = _meta_charset_re.search(tag.group(0))
        if not tag: continue
        
        return tag.group(0)
    return None

def _decode_with_charset(byte_source, charset):
    """Attempts to decode a byte string with a charset, falling back to UTF-8 if
    the codec can't be found, and ignoring bad characters if certain characters
    can't be found within a charset. If the passed charset is ``None``, we fall
    back to UTF-8."""
    if charset is None:
        charset = "UTF-8"
    try:
        return byte_source.decode(charset, errors="ignore")
    except LookupError: # we don't have the right codec! Fall back!
        logger.warning("Codec matching name '%s' could not be found. "
                       "Falling back to UTF-8.")
        try:
            return byte_source.decode("UTF-8", errors="ignore")
        except LookupError:
            logger.warning("WTF, bro? Y U NO Unicode? Falling back to Python's "
                           "default encoding")
            return byte_source.decode(errors="ignore")

def passthrough_str(byte_source, headers, url):
    """Like :func:`passthrough`, but returns a unicod ``str`` object rather than
    a sequence of bytes.
    
    Encoding is automatically determined via http headers or (if that fails)
    from the html source if it has a meta http-equiv tag to handle it (assuming
    that tag can be decoded via a best-attempt UTF-8 decoding). If encoding
    cannot be determined, we just try to decode it in UTF-8, ignoring unknown
    characters.
    
    Unfortunately, this function does not yet have a system like
    :py:class:`BeautifulSoup.UnicodeDammit`, or :py:mod:`chardet`, which can
    actually build a statistical model of the page's possible encoding."""
    charset = _get_header_charset(headers)
    
    str_source = None
    if charset is not None: # if in headers
        logger.debug("Found page encoding in http headers: %s" % charset)
        str_source = _decode_with_charset(byte_source, charset)
    else: # find it in the html page
        str_source = _decode_with_charset(byte_source, None)
        charset = _find_charset(str_source)
        if charset is not None:
            logger.debug("Found page encoding in page: %s" % charset)
            str_source = _decode_with_charset(byte_source, charset)
        else:
            logger.warning("Page encoding could not be determined for %s. "
                           "Falling back to UTF-8." % url)
    return str_source


def passthrough_str_with_encoding(encoding):
    """Creates and returns a custom version of :func:`passthrough_str`,
    utilizing a specified string encoding format, rather than attempting to
    automatically detect things."""
    def f(source, headers, url):
        source.read().decode(encoding)
    return f

# Built-in Python Libraries
def htmlparser(subclass, *args, **kwargs):
    """Taking a subclass of :py:class:`html.parser.HTMLParser` (in py3k) or
    :py:class:`HTMLParser.HTMLParser` (in py2), or alternatively a factory
    returning a subclass of one of those, builds a parser. When given data, the
    returned parser will construct a new instance of the subclass"""
    def f(source, headers, url):
        parser = subclass(*args, **kwargs)
        parser.feed(source)
        parser.close()
        return parser
    return f

# 3rd-Party (Yet Popular) Python Libraries
def lxml_html(source, headers, url):
    """Returns an :py:func:`lxml.etree.ElementTree` generated with
    `lxml's html module <http://lxml.de/lxmlhtml.html>`_."""
    import lxml.html
    return lxml.html.document_fromstring(source, base_url=url)#,
                                         #encoding=_get_header_charset(headers))

def lxml_xml(source, headers, url):
    """Returns an :py:func:`lxml.etree.ElementTree` generated with
    `lxml's etree module <http://lxml.de/tutorial.html>`_."""
    import lxml.etree
    return etree.parse(StringIO(source))

def beautiful_soup_html(source, headers, url):
    """Returns a :py:class:`BeautifulSoup.BeautifulSoup` object using the
    `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/>`_ library.
    BeautifulSoup is very error resistant, and may be useful for some rather
    broken html. Additionally, it's written in pure python, unlike lxml which
    has native dependencies. Unfortunately, it is rather slow compared to lxml,
    and it has poor Python 3 support at the moment."""
    from BeautifulSoup import BeautifulSoup
    return BeautifulSoup(source, fromEncoding=_get_header_charset(headers))

def beautiful_soup_xml(source, headers, url):
    """Returns a :py:class:`BeautifulSoup.BeautifulStoneSoup` object using the
    `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/>`_ library.
    BeautifulSoup is very error resistant, and may be useful for some rather
    broken xml. Additionally, it's written in pure python, unlike lxml which has
    native dependencies. Unfortunately, it is rather slow compared to lxml, and
    it has poor Python 3 support at the moment."""
    from BeautifulSoup import BeautifulStoneSoup
    return BeautifulStoneSoup(source, fromEncoding=_get_header_charset(headers))
