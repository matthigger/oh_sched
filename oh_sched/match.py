import re
from collections import Counter
from collections import defaultdict
from copy import copy
from itertools import chain

import numpy as np
from scipy.optimize import linear_sum_assignment

INVALID = -1


def match(prefs, ta_list, oh_list, oh_per_ta=3, max_ta_per_oh=4, decay=1):
    # match operation is destructive
    prefs = copy(prefs)
    ta_list = copy(ta_list)

    # set invalid entries with low score
    prefs[np.isnan(prefs)] = INVALID

    # init
    oh_ta_dict = {oh: list() for oh in oh_list}
    _oh_per_ta = defaultdict(lambda: 0)

    while ta_list:
        # match
        ta_idx, oh_idx = linear_sum_assignment(cost_matrix=prefs,
                                               maximize=True)

        for _ta_idx, _oh_idx in zip(ta_idx, oh_idx):
            oh = oh_list[_oh_idx]
            email = ta_list[_ta_idx]

            if prefs[_ta_idx, _oh_idx] == INVALID:
                raise RuntimeError(f'no valid slots for TA found: {email}')

            # record match
            oh_ta_dict[oh].append(email)
            _oh_per_ta[email] += 1

            # invalidate this match in future iterations
            prefs[_ta_idx, _oh_idx] = INVALID

            # decay this office hours slot (discourages future selection ->
            # uniform spread)
            prefs[:, _oh_idx] *= decay

        # remove any office hours slots which are full
        for oh, _ta_list in oh_ta_dict.items():
            if len(_ta_list) >= max_ta_per_oh:
                _oh_idx = oh_list.index(oh)
                oh_list.pop(_oh_idx)
                prefs = np.delete(prefs, _oh_idx, axis=1)

        # remove any emails which have enough oh
        for email, num_oh in _oh_per_ta.items():
            if num_oh >= oh_per_ta:
                _ta_idx = ta_list.index(email)
                ta_list.pop(_ta_idx)
                prefs = np.delete(prefs, _ta_idx, axis=0)

    return oh_ta_dict


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
