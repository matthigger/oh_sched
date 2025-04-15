from oh_sched.__main__ import *
from oh_sched.config import *


def test_main():
    folder = pathlib.Path(oh_sched.__file__).parents[1] / 'test'

    # default config, but swap in test folder
    config = Config(f_csv='oh_prefs.csv', f_out='oh.ics')
    config.f_csv = folder / config.f_csv
    config.f_out = folder / config.f_out

    if config.f_out.exists() and config.f_out.is_file():
        # clean up output
        config.f_out.unlink()

    main(config)

    assert config.f_out.exists()

    if config.f_out.exists() and config.f_out.is_file():
        # clean up output
        config.f_out.unlink()
