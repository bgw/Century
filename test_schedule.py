from lib.tasks.isis import schedule_reader
import logging
import config

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

reader = schedule_reader.ScheduleReader("fall")
reader.browser.uf_set_autologin(config.username, config.password)
print(reader.formatted_classes_string)
