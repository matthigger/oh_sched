import Levenshtein


def find_similar_str(s_list, max_distance=2, case_insensitive=True):
    """ returns iterator of strings with edit distance of 3 (or less) apart

    used here to find email typos

    Args:
        s_list (list): list of strings to compare
        max_distance (int): maximum levenshtein distance at which two
            strings are still declared "similar"

    Yields:
        s_tup (tuple): (2) strings which are deemed "similar"
    """
    if case_insensitive:
        s_list = [s.lower() for s in s_list]

    for idx, s0 in enumerate(s_list):
        for s1 in s_list[idx + 1:]:
            if Levenshtein.distance(s0, s1) <= max_distance:
                yield s0, s1
