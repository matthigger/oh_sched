import tempfile

from oh_sched.config import *


def get_tmp(**kwargs):
    return pathlib.Path(tempfile.NamedTemporaryFile(**kwargs).name)


def test_to_from_yaml():
    config_empty = Config()
    config_full = Config(oh_per_ta=1,
                         max_ta_per_oh=2,
                         scale_dict={'a': 1.1, 'b': .9},
                         date_start='May 1 2025',
                         date_end='May 2 2025',
                         tz='America/New_York',
                         f_out='office_hours.ics',
                         verbose=False)

    for config in [config_empty, config_full]:
        f_yaml = get_tmp(suffix='.yaml')
        config.to_yaml(f_yaml)
        _config = Config.from_yaml(f_yaml)
        assert config == _config

        f_yaml.unlink()
