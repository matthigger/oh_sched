import tempfile

import oh_sched
from oh_sched.config import *


def get_tmp(**kwargs):
    return pathlib.Path(tempfile.NamedTemporaryFile(**kwargs).name)


def test_init():
    config = Config(date_start='May 01 2025', tz='US/Eastern')


    test_folder = pathlib.Path(oh_sched.__file__).parents[1] / 'test'
    config.to_yaml(test_folder / 'config.yaml')
    _config_exp = Config.from_yaml(test_folder / 'config.yaml')
    assert config == _config_exp


def test_to_from_yaml():
    config_empty = Config()
    config_full = Config(oh_per_ta=1,
                         max_ta_per_oh=2,
                         scale_dict={'a': 1.1, 'b': .9},
                         date_start='May 1 2025',
                         date_end='May 2 2025',
                         tz='US/Eastern',
                         f_out='office_hours.ics',
                         verbose=False)

    for config in [config_empty, config_full]:
        f_yaml = get_tmp(suffix='.yaml')
        config.to_yaml(f_yaml)
        _config = Config.from_yaml(f_yaml)
        assert config == _config

        f_yaml.unlink()
