from lib.tasks.registrar.course_listings import *
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

course_reader = CourseReader(2012, courses.Semesters.SPRING)

print("\n".join(str(dep) for dep in course_reader.lookup_prefix("CDA", True)))
print("\n".join(str(course) for course in \
      course_reader.lookup_course("MAC2311", True)))
