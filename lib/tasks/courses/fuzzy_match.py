"""Contains a set of utilities for performing "fuzzy" matches on strings, lists,
or list-like objects. Utilities like these can often be useful with handling
stuff like course titles or department names, which may or may not always be
written the same way.

.. warning::
    If you plan to use strings, note that all of these functions are case-
    sensitive. You may wish to make strings the same case before beginning to
    avoid capitalization issues.

.. warning::
    These functions only give rough guesses as to equality, and you shouldn't
    expect them to always work perfectly. Use them as nothing more than a
    heuristic whenever possible.
"""

import collections
import multiprocessing

# testing modules
import unittest
import timeit
import string
import random

def similar_zip(list_a, list_b, scoring_algorithm=None, high_is_similar=True,
                single_match=True, key=None, direct_first=False,
                max_processes=1):
    """Makes a list of tuple representing the closest pairs between list items,
    using :func:`lev_ratio`, and a custom (greedy) drafting algorithm. The
    returned list will be sorted by match strength, from closest matching to
    least-matching.
    
    .. note::
        This is similar to the Python Standard Library :func:`zip` function
        (hence the name), but with a few exceptions, notably, we only support
        two lists, and ``list_a`` must be longer than ``list_b``.
    
    .. warning::
        This function must check every item in ``list_a`` against every other
        item in ``list_b``, taking O(mn) time. This means that when paired with
        a slow ``scoring_algorithm``, such as :func:`lev_ratio`, performance can
        be horrid on large lists.
    
    *Keyword Arguments:*
    
    ``scoring_algorithm``
        The function to use to rate the closeness of the match between two items
        in the lists. It should be callable like::
        
            scoring_algorithm(s1, s2)
        
        This function will be called a lot, so if you are going to be working
        with large lists, make sure it is a fast function. *Scores are treated
        as relative*, so you might want to use a function with output normalized
        to string length, like :func:`hamming_ratio`. By default, we use
        :func:`offset_maximum`, with its default base algorithm.
    ``high_is_similar``
        Some scoring algorithms, like :func:`lev_dist` will give low scores for
        similar items, while other scoring algorithms, like :func:`lev_ratio`
        will give high scores for similar items. This value should be set based
        on the value of the ``scoring_algorithm`` argument.
    ``single_match``
        If this is True, we look for one-on-one matches between each item. If it
        isn't, items in ``list_b`` may be used more than once to match with
        items in ``list_a``.
    ``key``
        A function, given a value, gives the value to plug into
        ``scoring_algorithm``. For example, if you simply wanted to compare the
        first 3 letters of each list's items, you could pass in::
        
            lambda val: val[3:]
        
    ``direct_first``
        If ``True``, will enable an optimization, pulling direct matches out
        first. This only works assuming the best scores are given to direct
        matches by the algorithm (typically the case).
    ``max_processes``
        The maximum number of processes to use in the :mod:`multiprocessing`
        pool when computing match scores. If this value is 1, the
        multiprocessing module won't be used, everything will act within a
        single thread, and no new child processes will be spawned. Because the
        behavior of this feature can be unpredictable at times, this is disabled
        (set to 1) by default. In certain cases, this feature can slow down
        processing (this happens often with really small lists). Also, the
        ``scoring_algorithm`` must be picklable for this to work. (must be
        defined statically as a top-level function.
    """
    # sorry if the internals of this function are ugly, 95% of that is because
    # of some of the optimizations which need lots of special casing (mainly
    # direct_first and multiprocessing stuff). Frankly, this function just has
    # one metric shit-ton of options to deal with.
    
    if single_match and len(list_b) < len(list_a):
        raise Exception("list_b cannot be shorter than list_a, because there "
                        "won't be guarenteed matches for each item in list_a.")
    list_a = list(list_a); list_b = list(list_b)
    if key:
        list_a_vals = [key(a) for a in list_a]
        list_b_vals = [key(b) for b in list_b]
    else:
        list_a_vals = list(list_a)
        list_b_vals = list(list_b)
    direct_matches = [] # direct matches will go here to be returned later
    if direct_first:
        # list_b_dict is used for looking up list_b indexes by their value
        list_b_dict = dict(zip(list_b_vals, range(len(list_b_vals))))
        if single_match:
            # we'll build a list of indexes to remove after processing direct
            # matches (we can't do this while processing the direct matches,
            # because managing the index offsets then would be too difficult)
            del_list = []
        ai = 0
        while ai < len(list_a):
            a_val = list_a_vals[ai]
            if a_val in list_b_dict:
                bi = list_b_dict[a_val]
                a, b = list_a[ai], list_b[bi]
                del list_a[ai]
                del list_a_vals[ai]
                if single_match:
                    # mark values for deletion later
                    del_list.append(bi)
                    del list_b_dict[a_val]
                direct_matches.append((a, b))
                ai -= 1 # we need to shift the index down to compensate for the
                        # removed value in list_a/list_a_vals
            ai += 1
        if single_match:
            # go ahead and remove the values from list_b/list_b_vals now
            offset = 0
            for bi in sorted(del_list):
                del list_b[bi - offset]
                del list_b_vals[bi - offset]
                offset += 1
    
    if scoring_algorithm is None:
        scoring_algorithm = offset_maximum
    
    # compute all the scores for every list_a/list_b combination
    score_map = []
    if max_processes == 1:
        for ai, a_val in enumerate(list_a_vals):
            for bi, b_val in enumerate(list_b_vals):
                score_map.append((scoring_algorithm(a_val, b_val), ai, bi))
    else:
        if max_processes is None:
            max_processes = float("inf")
        def error_callback(er):
            raise er
        process_count = min(max_processes, 9, len(list_a) * len(list_b))
        pool = multiprocessing.Pool(processes=process_count)
        # queue up processes
        queue = []
        for ai, a_val in enumerate(list_a_vals):
            for bi, b_val in enumerate(list_b_vals):
                queue.append((scoring_algorithm, a_val, b_val))
        scores = list(pool.map(_alg, queue,
            chunksize=int(
                len(list_a) * len(list_b) / process_count + 0.5
            )
        ))
        for ai in range(len(list_a)):
            for bi in range(len(list_b)):
                score_map.append((scores[ai * len(list_b) + bi], ai, bi))
    
    # Use a greedy-picking algorithm to pull out the winning pairs
    # Note: a better choice here would be something like the min-max algorithm,
    #       but that would be much more difficult to implement, and would be a
    #       lot slower
    if high_is_similar:
        score_map.sort(reverse=True)
    else:
        score_map.sort()
    similars = []
    similar_ai_taken, similar_bi_taken = set(), set()
    i = 0
    while len(similars) < len(list_a):
        score, ai, bi = score_map[i]
        if ai in similar_ai_taken or (single_match and bi in similar_bi_taken):
            i += 1
            continue
        similars.append((list_a[ai], list_b[bi]))
        similar_ai_taken.add(ai)
        similar_bi_taken.add(bi)
        i += 1
    return direct_matches + similars

def _alg(args):
    return args[0](*args[1:])

def lev_ratio(s1, s2, cache=True):
    """Gives a value between 0 and 1, based on the similarity of two list-like
    objects. A value of 1 means they are the same value, 0 means there is no
    similarity between the two. The :func:`lev_dist` function is used to compute
    the similarity.
    
    .. note::
        Unlike :func:`lev_dist`, a larger value means values are more similar.
    
    *Keyword Arguments:*
    
    ``cache``
        If True, look values up before trying to recompute their distance (and
        therefore, ratio) scores. If we have already calculated the scores for
        ``s1`` and ``s2``, we will simply reuse those values.
    """
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
    
    .. note::
        The Levenshtein Distance algorithm is horridly slow, *especially for
        long lists or strings*. For this reason, be careful with how you use
        this function and its derivatives.
    
    *Keyword Arguments:*
    
    ``cache``
        If True, look values up before trying to recompute their distances. If
        we have already calculated the distances for ``s1`` and ``s2``, we will
        simply reuse those values.
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

def hamming_ratio(s1, s2, count_ends=False):
    """Gives a value between 0 and 1, based on the similarity of two list-like
    objects. A value of 1 means they are the same value, 0 means there is no
    similarity between the two. The :func:`hamming_dist` function is used to
    compute the similarity.
    
    .. note::
        Unlike :func:`hamming_dist`, a larger value means values are more
        similar.
    
    *Keyword Arguments:*
    
    ``count_ends``
        If this is True, and s1 and s2 have different lengths, the difference
        between their lengths will be added to the distance score.
    """
    maxscore = (max(len(s1), len(s2)) if count_ends else min(len(s1), len(s2)))
    if not maxscore:
        return 1.
    return (maxscore - hamming_dist(s1, s2, count_ends)) / maxscore
           

def hamming_dist(s1, s2, count_ends=False):
    """Measures the Hamming distance between two strings or list-like objects,
    ``s1`` and ``s2``. The Hamming distance is simply the number of
    substitutions required to make the first list equal to the second. The
    maximum possible returned value is::
    
        max(s1, s2) if count_ends else min(s1, s2)
    
    .. note::
        This function is *very* fast, but accuracy compared to many other
        algorithms, such as :func:`lev_dist` is often horrible. It may make
        sense to pair this algorithm with another one.
    
    .. note::
        Unlike in the :func:`lev_dist` and :func:`lev_ratio` algorithms, caching
        isn't provided here, because it wouldn't provide a real performance
        boost, as hashing a string would take almost as long as running the
        algorithm on it.
    
    *Keyword Arguments:*
    
    ``count_ends``
        If this is True, and s1 and s2 have different lengths, the difference
        between their lengths will be added to the distance score.
    """
    score = max(len(s1), len(s2)) - min(len(s1), len(s2)) if count_ends else 0
    for a, b in zip(s1, s2):
        score += (a != b)
    return score

def frequency_ratio(s1, s2):
    """Gives a value between 0 and 1, based on the similarity of two list-like
    objects. A value of 1 means they are the same value, 0 means there is no
    similarity between the two. The :func:`frequency_dist` function is used to
    compute the similarity.
    
    .. note::
        Unlike :func:`frequency_dist`, a larger value means values are more
        similar.
    """
    maxscore = len(s1) + len(s2)
    if not maxscore:
        return 1
    return (maxscore - frequency_dist(s1, s2)) / maxscore

def frequency_dist(s1, s2):
    """Compares the frequency of each element in s1 with each element in s2. For
    example, given the strings, "abc", "abbc", we would expect a distance of 1,
    because there is 1 more b in the second string than the first. Here are some
    more examples and their outputs:
    
    ======  ======  ======
    s1      s2      dist
    ======  ======  ======
    "abc"   "bc"    1
    "abc"   "bbc"   2
    "bbc"   "abc"   2
    "cab"   "bac"   0
    "dog"   "cat"   6
    ======  ======  ======
    
    The maximum distance is::
    
        len(s1) + len(s2)
    
    While the minimum distance is naturally zero.
    
    .. note::
        This function is *very* fast, but accuracy compared to many other
        algorithms, such as :func:`lev_dist` is often horrible. It may make
        sense to pair this algorithm with another one.
    """
    s1_freq = collections.Counter(s1); s2_freq = collections.Counter(s2)
    diff = 0
    for i in s1_freq.keys() | s2_freq.keys():
        diff += abs(s1_freq.get(i, 0) - s2_freq.get(i, 0))
    return diff

def offset_minimum(s1, s2, algorithm=hamming_dist, placeholder=None):
    """Tries shifting each string around to find the minimum score between them.
    This uses a naive algorithm where ``s1`` is moved forward ``len(s2)``
    spaces, with gaps in the front filled in by ``placeholder``, and ``s2`` is
    moved forward ``len(s1)`` spaces. The best score derived by running
    ``algorithm`` on each of the resulting list-like objects will be returned.
    
    *Keyword Arguments:*
    
    ``algorithm``
        This should be a function that can be called like::
        
            algorithm(s1_offset, s2_offset)
        
        where ``s1_offset`` and ``s2_offset`` are tuples. The default is
        :func:`hamming_dist`.
    ``placeholder``
        The value to insert in front of ``s1`` and ``s2`` to offset their
        positions.
    """
    return _offset_general(s1, s2, algorithm, placeholder, min)

def offset_maximum(s1, s2, algorithm=hamming_ratio, placeholder=None):
    """Tries shifting each string around to find the maximum score between them.
    This uses a naive algorithm where ``s1`` is moved forward ``len(s2)``
    spaces, with gaps in the front filled in by ``placeholder``, and ``s2`` is
    moved forward ``len(s1)`` spaces. The best score derived by running
    ``algorithm`` on each of the resulting list-like objects will be returned.
    
    *Keyword Arguments:*
    
    ``algorithm``
        This should be a function that can be called like::
        
            algorithm(s1_offset, s2_offset)
        
        where ``s1_offset`` and ``s2_offset`` are tuples. The default is
        :func:`hamming_ratio`.
    ``placeholder``
        The value to insert in front of ``s1`` and ``s2`` to offset their
        positions.
    """
    return _offset_general(s1, s2, algorithm, placeholder, max)

def _offset_general(s1, s2, algorithm, placeholder, comparison_func):
    """A general solution for :func:`offset_minimum` and
    :func:`offset_maximum`."""
    s1, s2 = tuple(s1), tuple(s2)
    def set_best_score(score):
        if set_best_score.best_score is None:
            set_best_score.best_score = score
        else:
            set_best_score.best_score = comparison_func(
                set_best_score.best_score, score)
    set_best_score.best_score = None
    for i in range(len(s1)):
        set_best_score(algorithm(s1, (placeholder,) * i + s2))
    for i in range(len(s2)):
        set_best_score(algorithm((placeholder,) * i + s1, s2))
    return set_best_score.best_score

#####################
# Tests Begin Here! #
#####################

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
    """A utility function for some tests, likely to create collisions."""
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
        # DO NOT use multiprocessing with this test.
        # Since _test_exact_pairs_scoring_algorithm is in the same module as the
        # main module when testing, this will create a forkbomb (not that I
        # tried that or anything...)
        scoring_algorithm = _test_exact_pairs_scoring_algorithm
        for i in range(50):
            l = [_get_random_string() for k in range(25)]
            for a, b in similar_zip(l, l,
                                    scoring_algorithm=scoring_algorithm,
                                    direct_first=False,
                                    max_processes=1):
                assert a == b
            for a, b in similar_zip(l, l,
                                    scoring_algorithm=scoring_algorithm,
                                    direct_first=True,
                                    max_processes=1):
                assert a == b
            l_shuffled = list(l)
            random.shuffle(l_shuffled)
            for a, b in similar_zip(l, l_shuffled,
                                    scoring_algorithm=scoring_algorithm,
                                    direct_first=False,
                                    max_processes=1):
                assert a == b
            for a, b in similar_zip(l, l_shuffled,
                                    scoring_algorithm=scoring_algorithm,
                                    direct_first=True,
                                    max_processes=1):
                assert a == b

def _test_exact_pairs_scoring_algorithm(s1, s2):
    """A toplevel function used by TestSimilarZip (must be toplevel to be
    pickleable)."""
    # we must enforce that we count the ends, otherwise perfect matches aren't
    # guaranteed by similar_zip, in the case that you have an empty string.
    return hamming_ratio(s1, s2, count_ends=True)

class TestHammingDist(unittest.TestCase):
    def test_single_change(self):
        for a, b in [("hello", "bello"), ("nom", "pom"), ("wow", "cow"),
                     ("abc", "abd"), ("a", "b")]:
            assert hamming_dist(a, b, count_ends=True) == 1
            assert hamming_dist(a, b, count_ends=False) == 1
    
    def test_no_change(self):
        for i in range(1000):
            s = _get_random_string()
            assert hamming_dist(s, s, count_ends=True) == 0
            assert hamming_dist(s, s, count_ends=False) == 0

class TestFrequencyDist(unittest.TestCase):
    def test_example_table(self):
        # Tests the examples given in the documentation
        vals = [("abc", "abbc", 1),
                ("abc", "bc",   1),
                ("bbc", "abc",  2),
                ("abc", "bbc",  2),
                ("cab", "bac",  0),
                ("dog", "cat",  6)]
        for s1, s2, result in vals:
            assert frequency_dist(s1, s2) == result
            assert frequency_dist(s2, s1) == result

if __name__ == "__main__":
    unittest.main()
