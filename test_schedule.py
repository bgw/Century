from lib.tasks.isis import schedule_reader
import logging
import config

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

reader = schedule_reader.ScheduleReader("spring")
reader.browser.uf_set_autologin(config.username, config.password)
print(str(reader.course_list))
# reader.course_list.open_campus_map()
