import re
from collections import Counter
from collections import defaultdict
from copy import copy
from itertools import chain

import numpy as np
from scipy.optimize import linear_sum_assignment

INVALID = -1


def match(prefs, oh_per_ta=3, max_ta_per_oh=4):
    """ matches ta to oh slot to maximize sum of prefs achieved

    Args:
        prefs (np.array): (num_ta, num_oh) preference scores for every
            combination of ta and oh.  nan where unavailable
        oh_per_ta (int): office hours assigned per ta
        max_ta_per_oh (int): maximum ta assigned to any particular oh

    Returns:
        oh_ta_match (list of lists): oh_ta_match[oh_idx] is a list of the
            index of all tas assigned particular oh_idx
    """
    # set invalid entries with low score
    prefs = copy(prefs)
    prefs[np.isnan(prefs)] = INVALID

    # init
    num_ta, num_oh = prefs.shape
    oh_ta_match = [list() for _ in range(num_ta)]

    for match_idx in range(oh_per_ta):
        # build new _prefs and _oh_ta_match per availability remaining.
        # (i.e. if each oh spot has 2 open spots then each column repeated
        # twice and _oh_ta_match has two refs to each list in oh_ta_match)
        pref_list = list()
        _oh_ta_match = list()
        for oh_idx, ta_list in enumerate(oh_ta_match):
            num_ta_spots_left = max_ta_per_oh - len(ta_list)

            for _ in range(num_ta_spots_left):
                pref_list.append(prefs[:, oh_idx])
                _oh_ta_match.append(ta_list)
        _prefs = np.stack(pref_list, axis=1)

        # match
        ta_idx, oh_idx = linear_sum_assignment(cost_matrix=_prefs,
                                               maximize=True)

        # record & validate matches
        for _ta_idx, _oh_idx in zip(ta_idx, oh_idx):
            if _prefs[_ta_idx, _oh_idx] == INVALID:
                raise RuntimeError(f'no availability for TA index: {_ta_idx}')
            _oh_ta_match[_oh_idx].append(_ta_idx)

    return oh_ta_match


def get_scale(oh_list, scale_dict):
    scale = np.ones(len(oh_list))
    for regex, mult in scale_dict.items():
        for oh_idx, oh in enumerate(oh_list):
            if re.search(regex, oh):
                scale[oh_idx] *= mult
    return scale


def get_perc_max(oh_ta_dict, oh_list, ta_list, prefs):
    """ computes percent of maximum score achieved per ta"""
    # count oh per ta in dict
    ta_num_oh_dict = Counter(chain(*oh_ta_dict.values()))

    # compute max score possible
    ta_max_dict = dict()
    for ta, num_oh in ta_num_oh_dict.items():
        ta_idx = ta_list.index(ta)
        pref_decrease = sorted(prefs[ta_idx, :], reverse=True)
        ta_max_dict[ta] = sum(pref_decrease[:num_oh])

    # compute score achieved
    ta_achieve_dict = defaultdict(lambda: 0)
    for oh, ta_list in oh_ta_dict.items():
        oh_idx = oh_list.index(oh)
        for ta in ta_list:
            ta_idx = ta_list.index(ta)
            ta_achieve_dict[ta] += prefs[ta_idx, oh_idx]

    # divide
    perc_max = {ta: ach / ta_max_dict[ta]
                for ta, ach in ta_achieve_dict.items()}

    return perc_max, ta_num_oh_dict
