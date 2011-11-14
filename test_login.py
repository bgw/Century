import config
from lib import browser
from lib.browser import parsers
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

b = browser.get_new_uf_browser()
b.uf_set_autologin(config.username, config.password)
b.load_page("https://www.isis.ufl.edu/cgi-bin/nirvana?MDASTRAN=RSI-FSCHED")
