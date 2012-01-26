"""Contains the utility functions and scoring algorithms used by the
:mod:`lib.tasks.registrar.course_listings` module to match department names that
are written differently with each other."""

from ..courses import fuzzy_match

# make a list of common abbreviations used in department names, to improve
# accuracy when comparing department names (this helps a lot)
_abbreviations = (
    ("&", "and"),
    ("  ", " "),
    ("languages, literatures and cultures", "languages lit/culture"),
    ("sociology, criminology and law", "sociology/criminology/law"),
    ("tourism, recreation and sport", "tourism recreation sp"),
    ("pharmacy", "pha"),
    ("special education, school psychology and early childhood studies",
        "sp ed/sch psyc/early ch"),
    ("management", "mgt"),
    ("center for ", ""),
    ("manage", "mgt"),
    ("pharmacy", "pha"),
    ("veterinary medicine", "medicine"),
    ("human", "hum"),
    ("pathol,immunol and lab med", "pathobiology"),
    ("biological", "bio"),
    ("biology", "bio"),
    ("biolog", "bio"),
    ("developmental", "dev"),
    ("development", "dev"),
    ("information", "info"),
    ("engineering", "engineer"),
    ("science", "sci"),
    (" and ", "/"),
    (" - ", "-"),
    ("-", " "),
    (",", ""),
)

def replace_abbreviations(s):
    for k, v in _abbreviations:
        s = s.replace(k, v)
    return s

def scoring_algorithm(s1, s2):
    # this can't be part of a class, because then multiprocessing wouldn't be
    # able to pickle it.
    scores = (fuzzy_match.frequency_ratio(s1, s2),
              fuzzy_match.hamming_ratio(s1, s2, False))
    return (max(scores) + sum(scores)) / 2
