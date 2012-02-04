from lib.tasks import phonebook
from lib.tasks.phonebook.http import HttpBackend
import logging
import config

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

phonebook = phonebook.Phonebook(HttpBackend)
phonebook.browser.uf_set_autologin(config.username, config.password)
print(phonebook.search("q"))
