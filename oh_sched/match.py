import re
from collections import defaultdict
from copy import copy

import numpy as np
from scipy.optimize import linear_sum_assignment

INVALID = -1


def match(prefs, ta_list, oh_list, oh_per_ta=3, max_ta_per_oh=4, decay=1):
    # set invalid entries with low score
    prefs = copy(prefs)
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
