import pytest

from oh_sched.match import *


def test_get_scale():
    oh_list = ['Mon 9AM', 'Tue 2PM', 'Wed 4PM', 'oh slot']
    scale_dict = {
        r'Mon': 2.0,  # mondays 2x as valuable
        r'Wed': 0.5,  # weds 1/2 as valuable
        r'e': 10  # any office hour with an e in it is 10x as valuable
    }
    scale = get_scale(oh_list, scale_dict)
    expected = np.array([2, 10, 5, 1])
    np.testing.assert_array_almost_equal(scale, expected)

    with pytest.warns(UserWarning, match=f'scale not applied, no'):
        get_scale(oh_list=['a', 'b', 'c'],
                  scale_dict={'no match': 10})


def test_get_perc_max():
    # case0 ------------- everybody gets just what they want
    # prefs: rows correspond to TA, columns correspond to OH
    prefs = np.array([
        [1.0, 0.5, np.nan],
        [0.2, 0.9, 0.9]
    ])
    oh_ta_match = [
        [0],  # OH 0 -> TA 0
        [1],  # OH 1 -> TA 1
        []  # OH 2 unassigned
    ]

    perc = get_perc_max(oh_ta_match, prefs)
    expected = np.array([1.0, 1.0])
    np.testing.assert_allclose(perc, expected)

    # case1 -------------
    # TA0: max = 0.9 + 0.8 = 1.7, achieved = 0.9 + 0.4 = 1.3
    # TA1: max = 0.6 + 0.5 = 1.1, achieved = 0.6 + 0.5 = 1.1
    # TA2: max = 1.0 + 0.7 = 1.7, achieved = 0.7 + 1.0 = 1.7
    prefs = np.array([
        [0.9, 0.8, 0.4, np.nan, np.nan, np.nan],
        [np.nan, np.nan, np.nan, 0.6, 0.5, np.nan],
        [np.nan, 0.7, np.nan, np.nan, np.nan, 1.0],
    ])
    oh_ta_match = [[0], [2], [0], [1], [1], [2]]

    perc = get_perc_max(oh_ta_match, prefs)

    expected = np.array([1.3 / 1.7, 1, 1])
    np.testing.assert_allclose(perc, expected, rtol=1e-4)


def test_match():
    # case 1: Bijection
    prefs = np.array([
        [5, 0],
        [0, 10],
    ])
    oh_ta_match = match(prefs, oh_per_ta=1, max_ta_per_oh=1, shuffle=False)
    assert oh_ta_match == [[0], [1]]

    # case 2: Preference tie with shuffle randomness
    prefs = np.array([
        [1, 1],
        [1, 1],
    ])
    outcomes = set()
    for seed in range(10):
        oh_ta_match = match(prefs, oh_per_ta=1, max_ta_per_oh=2, shuffle=True,
                            seed=seed)
        result_tuple = tuple(tuple(x) for x in oh_ta_match)
        outcomes.add(result_tuple)
    assert len(outcomes) > 1

    # case 3: with NaNs
    prefs = np.array([
        [5, np.nan, 3],
        [np.nan, 10, np.nan],
    ])
    oh_ta_match = match(prefs, oh_per_ta=1, max_ta_per_oh=1, shuffle=False)
    flat_result = sorted([ta for lst in oh_ta_match for ta in lst])
    assert flat_result == [0, 1]

    # case 4: No availability error
    prefs = np.array([
        [np.nan, np.nan],
        [10, 5],
    ])
    with pytest.raises(RuntimeError, match="no remaining availability: TA_0"):
        match(prefs, oh_per_ta=1, max_ta_per_oh=1, shuffle=False)

    # case 4 (part 2): No availability error (with name)
    prefs = np.array([
        [np.nan, np.nan],
        [10, 5],
    ])
    with pytest.raises(RuntimeError, match="no remaining availability: matt"):
        match(prefs, oh_per_ta=1, max_ta_per_oh=1, shuffle=False,
              ta_name_list=['matt', 'zeke'])

    # case 5: Compete for single slot (only one can get it)
    prefs = np.array([
        [10, 2],
        [9, 1],
    ])
    oh_ta_match = match(prefs, oh_per_ta=1, max_ta_per_oh=1, shuffle=False)
    assert oh_ta_match == [[0], [1]]

    # case 6: Two OH per TA, more capacity
    prefs = np.array([
        [8, 7, 6],
        [6, 7, 8],
    ])
    oh_ta_match_exp = [[0], [0, 1], [1]]
    oh_ta_match = match(prefs, oh_per_ta=2, max_ta_per_oh=2, shuffle=False)
    assert oh_ta_match == oh_ta_match_exp

    # case 7: Three OHs, one can take both TAs, both want it
    prefs = np.array([
        [9, 2, 1],
        [8, 3, 0],
    ])
    oh_ta_match_exp = [[0, 1], [], []]
    oh_ta_match = match(prefs, oh_per_ta=1, max_ta_per_oh=2, shuffle=False)
    assert oh_ta_match == oh_ta_match_exp

    # case 8: not enough OH to go around for the TAs
    prefs = np.array([
        [9, 1, 1],
        [9, 2, 2],
    ])
    s_warn = 'only 1 OH slots assigned: TA_0'
    with pytest.warns(UserWarning, match=s_warn):
        match(prefs, oh_per_ta=2, max_ta_per_oh=1, shuffle=False)

    # case 8 (part 2, breaks out of loop): not enough OH to go around for the TAs
    prefs = np.array([
        [9, 1, 1],
    ])
    s_warn = 'only 3 OH slots assigned: TA_0'
    with pytest.warns(UserWarning, match=s_warn):
        match(prefs, oh_per_ta=4, max_ta_per_oh=1, shuffle=False)

    # case 9: avoids intersections (assigning oh0 and oh1 has highest score,
    # but these two slots intersect each other)
    prefs = np.array([
        [9, 9, 1],
    ])
    oh_int_dict = {0: [0, 1], 1: [1, 0], 2: [2]}
    oh_ta_match = match(prefs, oh_int_dict=oh_int_dict, oh_per_ta=2,
                        max_ta_per_oh=1, shuffle=False)
    oh_ta_match_exp = [[0], [], [0]]
    assert oh_ta_match == oh_ta_match_exp
