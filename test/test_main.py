from oh_sched.__main__ import *
from oh_sched.config import *
import tempfile


def test_main():
    test_folder = pathlib.Path(oh_sched.__file__).parents[1] / 'test'

    # run main, read in output ics file
    config = Config(f_out=tempfile.NamedTemporaryFile(suffix='.ics').name)
    main(f_csv=test_folder / 'oh_prefs.csv', config=config)

    # read in / delete output file
    s_ics = open(config.f_out, 'r').read()
    config.f_out.unlink()

    # read in expected output
    s_ics_expected = open(test_folder / 'office_hours.ics', 'r').read()

    # ensure it matches expected ics file
    assert s_ics == s_ics_expected

