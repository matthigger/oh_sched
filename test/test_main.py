import tempfile

from oh_sched.__main__ import *
from oh_sched.config import *


def test_main():
    # paths
    folder = pathlib.Path(oh_sched.__file__).parents[1] / 'test'
    f_csv = folder / 'oh_prefs.csv'
    f_out = tempfile.NamedTemporaryFile(suffix='.ics')
    f_out = pathlib.Path(f_out.name)

    config = Config(f_out=f_out)
    main(f_csv=f_csv, config=config)

    assert f_out.exists()

    if f_out.exists() and f_out.is_file():
        # clean up output
        f_out.unlink()
