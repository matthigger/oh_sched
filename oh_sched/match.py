import re
import warnings
from copy import copy
from itertools import chain

import numpy as np
from scipy.optimize import linear_sum_assignment

INVALID = -1

# scale of preferences to random noise added (to shuffle match order)
STD_SCALE_NOISE = .00001


def match(prefs, oh_per_ta, max_ta_per_oh=None, oh_int_dict=None, shuffle=True,
          seed=0):
    """ matches TA to OH slot to maximize sum of prefs achieved

    Args:
        prefs (np.array): (num_ta, num_oh) preference scores for every
            combination of ta and oh.  nan where unavailable
        oh_per_ta (int): office hours assigned per ta
        max_ta_per_oh (int): maximum ta assigned to any particular oh
        oh_int_dict (dict): keys are oh index, values are a list of all oh
            indexes (including itself) which intersect (overlap).  See
            get_intersection_dict().  if None passed, each oh only overlaps
            itself
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

    if max_ta_per_oh is None:
        max_ta_per_oh = num_ta

    if oh_int_dict is None:
        # each office hour only intersects itself
        oh_int_dict = {idx: [idx] for idx in range(num_oh)}

    # init random number generator
    rng = np.random.default_rng(seed=seed)
    std_pref = np.nanstd(prefs.flatten())
    if std_pref == 0:
        std_pref = 1

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
            bool_invalid = _prefs == INVALID
            c = STD_SCALE_NOISE / std_pref
            _prefs = _prefs + rng.standard_normal(_prefs.shape) * c
            _prefs[bool_invalid] = INVALID

        # match
        ta_idx, oh_idx = linear_sum_assignment(cost_matrix=_prefs,
                                               maximize=True)

        # record & validate matches
        for _ta_idx, _oh_idx in zip(ta_idx, oh_idx):
            if _prefs[_ta_idx, _oh_idx] == INVALID:
                raise RuntimeError(f'no availability for TA index: {_ta_idx}')
            _oh_ta_match[_oh_idx].append(_ta_idx)

            # get oh_idx (in original indexing, recall that _oh_ta_match may
            # have multiple references to the same office hours section)
            oh_idx = oh_ta_match.index(_oh_ta_match[_oh_idx])

            # mark this spot as invalid for this TA
            for idx in oh_int_dict[oh_idx]:
                prefs[_ta_idx, idx] = INVALID

    # count oh per ta
    _oh_per_ta, _ = np.histogram(list(chain.from_iterable(oh_ta_match)),
                                 bins=np.arange(-.5, num_ta + .5))
    if (_oh_per_ta != oh_per_ta).any():
        warnings.warn(f'not enough OH slots & preferences given to'
                      f' assign all TAs {oh_per_ta} OH slots')

    return oh_ta_match


def get_scale(oh_list, scale_dict, verbose=True):
    """ associates each scaling factor to all matching office hours in oh_list

    Args:
        oh_list (list): list of strings, each is an office hours slot
        scale_dict (dict): keys are regex which match any relevant office
            hours, values are multiplicative factors to adjust preferences
            in these hours by
        verbose (bool): toggles command line output

    Returns:
        scale (np.array): scaling factor for every office hours slot
    """
    if verbose:
        print('\nScaling office hours preferences:')
    scale = np.ones(len(oh_list))
    for regex, mult in scale_dict.items():
        for oh_idx, oh in enumerate(oh_list):
            if re.search(regex, oh):
                # multiplier is applicable to this office hours slot
                scale[oh_idx] *= mult
                print(
                    f'{oh} multiplied by {mult} (cumulative scale={scale[oh_idx]})')
    return scale


def get_perc_max(oh_ta_match, prefs):
    """ computes percent of maximum score achieved per TA

    a perc_max value of .9 for a TA means that the matching achieved 90% of
    the maximum preferences score for a TA if we matched to optimize only
    this TAs preferences.

    Args:
        oh_ta_match (list of lists): oh_ta_match[oh_idx] is a list of the index
            of all tas assigned particular oh_idx
        prefs (np.array): (num_ta, num_oh) preference scores for every
            combination of ta and oh.  nan where unavailable

    Returns:
        perc_max (np.array): (num_ta) perc_max score for each TA
    """
    num_ta, num_oh = prefs.shape

    # count oh per ta in dict
    num_oh = np.zeros(num_ta, dtype=int)
    for ta_list in oh_ta_match:
        for ta in ta_list:
            num_oh[ta] += 1

    # compute max score possible (giving this TA their num_oh slots which
    # maximize preference)
    ta_max = np.empty(num_ta)
    for ta_idx, _pref in enumerate(prefs):
        _pref = _pref[~np.isnan(_pref)]
        _pref.sort()
        ta_max[ta_idx] = sum(_pref[-num_oh[ta_idx]:])

    # compute score achieved for each TA
    ta_achieve = np.zeros(num_ta)
    for oh, ta_list in enumerate(oh_ta_match):
        for ta in ta_list:
            ta_achieve[ta] += prefs[ta, oh]

    return ta_achieve / ta_max
