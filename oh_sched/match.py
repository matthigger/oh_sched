import re
from collections import Counter
from collections import defaultdict
from copy import copy
from itertools import chain

import numpy as np
from scipy.optimize import linear_sum_assignment

INVALID = -1

# scale of preferences to random noise added (to shuffle match order)
STD_SCALE_NOISE = .001


def match(prefs, oh_per_ta=3, max_ta_per_oh=4, shuffle=True, seed=0):
    """ matches ta to oh slot to maximize sum of prefs achieved

    Args:
        prefs (np.array): (num_ta, num_oh) preference scores for every
            combination of ta and oh.  nan where unavailable
        oh_per_ta (int): office hours assigned per ta
        max_ta_per_oh (int): maximum ta assigned to any particular oh
        shuffle (bool): toggles shuffling of tie breaking (seems to prefer
            earlier ta_idx)
        seed: given to shuffling

    Returns:
        oh_ta_match (list of lists): oh_ta_match[oh_idx] is a list of the
            index of all tas assigned particular oh_idx
    """
    # set invalid entries with low score
    prefs = copy(prefs)
    prefs[np.isnan(prefs)] = INVALID

    # init
    num_ta, num_oh = prefs.shape
    oh_ta_match = [list() for _ in range(num_oh)]

    # init random number generator
    rng = np.random.default_rng(seed=seed)
    std_pref = np.nanstd(prefs.flatten())

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

        if shuffle:
            # add some noise to shuffle assignment order (don't add noise to
            # invalid positions)
            c = STD_SCALE_NOISE / std_pref
            bool_invalid = _prefs == INVALID
            _prefs += rng.standard_normal(_prefs.shape) * c
            _prefs[bool_invalid] = INVALID

        # match
        ta_idx, oh_idx = linear_sum_assignment(cost_matrix=_prefs,
                                               maximize=True)

        # record & validate matches
        for _ta_idx, _oh_idx in zip(ta_idx, oh_idx):
            if _prefs[_ta_idx, _oh_idx] == INVALID:
                raise RuntimeError(f'no availability for TA index: {_ta_idx}')
            _oh_ta_match[_oh_idx].append(_ta_idx)

            # mark this spot as invalid for this TA
            oh_idx = oh_ta_match.index(_oh_ta_match[_oh_idx])
            prefs[_ta_idx, oh_idx] = INVALID

    return oh_ta_match


def get_scale(oh_list, scale_dict):
    scale = np.ones(len(oh_list))
    for regex, mult in scale_dict.items():
        for oh_idx, oh in enumerate(oh_list):
            if re.search(regex, oh):
                scale[oh_idx] *= mult
    return scale


def get_perc_max(oh_ta_match, prefs):
    """ computes percent of maximum score achieved per ta"""
    num_ta, num_oh = prefs.shape

    # count oh per ta in dict
    num_oh = np.zeros(num_ta, dtype=int)
    for ta_list in oh_ta_match:
        for ta in ta_list:
            num_oh[ta] += 1

    # compute max score possible
    ta_max = np.empty(num_ta)
    for ta, _pref in enumerate(prefs):
        _pref = _pref[~np.isnan(_pref)]
        _pref.sort()
        ta_max[ta] = sum(_pref[-num_oh[ta]:])

    # compute score achieved
    ta_achieve = np.zeros(num_ta)
    for oh, ta_list in enumerate(oh_ta_match):
        for ta in ta_list:
            ta_achieve[ta] += prefs[ta, oh]

    # divide
    perc_max = ta_achieve / ta_max

    return perc_max, num_oh
