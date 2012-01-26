from lib.tasks.registrar.course_listings import *
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

course_reader = CourseReader(2011, courses.Semesters.FALL)

print("Departments Offering CDA classes:")
print("\n".join(str(dep) for dep in course_reader.lookup_prefix("EGN", False)))
print()

print("MAC2311 Course Instances:")
print("\n".join(str(course) for course in \
      course_reader.lookup_course("MAC2311", False)))
print()

print("MAC2313 Instructors:")
instructors = set()
for course in course_reader.lookup_course("MAC2313"):
    instructors.update(course.instructors)
print("\n".join(instructors))
