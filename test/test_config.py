import tempfile

import pytest

from oh_sched.config import *


def get_tmp(**kwargs):
    return pathlib.Path(tempfile.NamedTemporaryFile(**kwargs).name)


def test_to_ics():
    oh_set = {'a0', 'a1', 'b0', 'b1'}
    oh_ta_dict = {oh: list() for oh in oh_set}

    class Case:
        def __init__(self, regex_oh_set_tup):
            self.f_out_dict = dict()
            self.f_dict_exp = dict()
            for s_regex, oh_set_exp in regex_oh_set_tup:
                file = get_tmp(suffix='.ics')
                self.f_out_dict[file] = s_regex
                self.f_dict_exp[file] = {oh: list() for oh in oh_set_exp}

    case0 = Case([('a', {'a0', 'a1'}),
                  (OH_ALL, oh_set)])
    case1 = Case([('a', {'a0', 'a1'}),
                  ('a0', {'a0'}),
                  (OH_LEFTOVER, {'b0', 'b1'})])

    # test
    for case_idx, case in enumerate([case0, case1]):
        config = Config(f_out_dict=case.f_out_dict)
        f_dict = config.to_ics(oh_ta_dict, verbose=False)
        assert f_dict == case.f_dict_exp, f'fail case{case_idx}'

        # cleanup (delete ics files created)
        for file in case.f_out_dict.keys():
            assert file.exists(), f'file not written: {file}'
            file.unlink()

    # ensure that warning is thrown if any oh slots are not exported
    case_missing = Case([('a', {'a0', 'a1'})])
    config = Config(f_out_dict=case_missing.f_out_dict)
    s_warn_exp = re.escape("OH not written to any ics outputs: ['b0', 'b1']")
    with pytest.warns(UserWarning, match=s_warn_exp):
        config.to_ics(oh_ta_dict, verbose=False)
