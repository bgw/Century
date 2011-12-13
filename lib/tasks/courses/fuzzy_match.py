"""Contains a set of utilities for performing "fuzzy" matches on strings, lists,
or list-like objects. Utilities like these can often be useful with handling
stuff like course titles or department names, which may or may not always be
written the same way.

.. warning::
    If you plan to use strings, note that all of these functions are case-
    sensitive. You may wish to make strings the same case before beginning to
    avoid capitalization issues.

.. warning::
    These functions only give rough guesses as to equality, and you should
    expect them to not always work perfectly. Use them as nothing more than a
    heuristic if at all possible.
"""

import unittest
import timeit
import string
import random

def similar_zip(list_a, list_b, cache=True):
    """Makes a list of tuple representing the closest pairs between list items,
    using :func:`lev_ratio`, and a custom drafting algorithm. Takes ``O(mnab)``
    time, where m and n the average lengths of items in the first and second
    lists, respectively; and a and b are the lengths of the first and second
    lists, respectively. The returned list will be sorted by match strength,
    from closest matching to least-matching."""
    if len(list_b) < len(list_a):
        raise Exception("list_b cannot be shorter than list_a, because there "
                        "won't be guarenteed matches for each item in list_a.")
    # build lists of each item's scores
    scores = [[lev_ratio(a, b, cache=cache) for b in list_b] for a in list_a]
    score_map = []
    for ai, abscore_list in enumerate(scores):
        for bi, abscore in enumerate(abscore_list):
            score_map.append((abscore, ai, bi))
    score_map.sort(); score_map.reverse()
    similars = []
    similar_ai_taken, similar_bi_taken = set(), set()
    i = 0
    while len(similars) < len(list_a):
        score, ai, bi = score_map[i]
        if ai in similar_ai_taken or bi in similar_bi_taken:
            i += 1
            continue
        similars.append((list_a[ai], list_b[bi]))
        similar_ai_taken.add(ai)
        similar_bi_taken.add(bi)
        i += 1
    return similars

def lev_ratio(s1, s2, cache=True):
    """Gives a value between 0 and 1, based on the similarity of two list-like
    objects. A value of 1 means they are the same value, 0 means there is no
    similarity between the two. The Levenshtein Distance algorithm is used to
    compute the similarity."""
    maxlen = max(len(s1), len(s2))
    if not maxlen:
        # division by zero would be bad
        return 1.
    return (maxlen - lev_dist(s1, s2)) / maxlen

_previous_lev = {}
def lev_dist(s1, s2, cache=True):
    """Measure and return the Levenshtein Distance between two list-like
    objects. Stolen from `the wikibooks page on the algorithm
    <https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/
    Levenshtein_distance#Python>`_, and *slightly* tweaked. The greater the
    value, the less similar the two arguments. The maximum distance is::
    
        max(len(s1), len(s2))
    """
    
    # handle caching/memoization first
    if cache:
        # lists are reversable, so make sure they end up in some deterministic
        # order (sort 'em!)
        key = tuple(sorted([tuple(s1), tuple(s2)]))
        try:
            return _previous_lev[key]
        except KeyError:
            _previous_lev[key] = lev_dist(s1, s2, cache=False)
            return _previous_lev[key]
    
    if len(s1) < len(s2):
        return lev_dist(s2, s1)
    if not s1:
        return len(s2)
 
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since
                                                 # previous_row and current_row
                                                 # are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]

class TestLevDist(unittest.TestCase):
    """We compare values against some generated `via this webpage
    <http://igm.univ-mlv.fr/~lecroq/seqcomp/node2.html>`"""
    
    def setUp(self):
        self.test_values = [("YHCQPGK", "LAHYQQKPGKA", 6),
                            ("alphabet", "nom nom nom", 11),
                            ("abcd", "abcd", 0),
                            ("TOTALLY", "different", 9)]
    
    def test_cache_off(self):
        for a, b, result in self.test_values:
            assert lev_dist(a, b, cache=False) == result
            assert lev_dist(b, a, cache=False) == result
    
    def test_cache_on(self):
        """Tests not only for accuracy, but also performance. If the caching is
        working, the test should finish rather quickly."""
        number_of_runs = 1000
        def test(cache):
            for a, b, result in self.test_values:
                assert lev_dist(a, b, cache=cache) == result
                assert lev_dist(b, a, cache=cache) == result
        assert (timeit.timeit(lambda: test(True), number=number_of_runs) /
                timeit.timeit(lambda: test(False), number=number_of_runs)) < .2

def _get_random_string():
        return "".join([string.ascii_lowercase[random.randrange(4)]
                        for i in range(random.randrange(4))])

class TestLevRatio(unittest.TestCase):
    def test_limits(self):
        for i in range(1000):
            ratio = lev_ratio(_get_random_string(),
                              _get_random_string())
            assert ratio >= 0 and ratio <= 1
    
    def test_same(self):
        for i in range(50):
            val = _get_random_string()
            self.assertAlmostEqual(lev_ratio(val, val), 1)
    
    def test_unique(self):
        for i in range(50):
            val = None
            while not val: # ensure we don't get an empty string
                val = _get_random_string()
            self.assertAlmostEqual(lev_ratio(val.lower(), val.upper()), 0)

class TestSimilarZip(unittest.TestCase):
    def test_exact_pairs(self):
        for i in range(50):
            l = [_get_random_string() for k in range(25)]
            for a, b in similar_zip(l, l):
                assert a == b
            l_shuffled = list(l)
            random.shuffle(l_shuffled)
            for a, b in similar_zip(l, l_shuffled):
                assert a == b

if __name__ == "__main__":
    unittest.main()
