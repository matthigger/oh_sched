import pathlib

from oh_sched.main import *


def test_main():
    folder_test = pathlib.Path(oh_sched.__file__).parents[1] / 'test'

    # simple end-to-end testing that CLI works and output is generated
    f_csv = folder_test / 'oh_prefs.csv'
    oh_per_ta = 3
    max_ta_per_oh = 4
    scale_dict = {r'(Friday|Thursday).*[45678] ?PM': 1.1}
    date_start = 'sept 13 2024'
    date_end = 'dec 4 2024'
    f_out = folder_test / 'oh.ics'

    if f_out.exists() and f_out.is_file():
        f_out.unlink()

    args = ['--f_csv', str(f_csv),
            '--oh_per_ta', str(oh_per_ta),
            '--max_ta_per_oh', str(max_ta_per_oh),
            '--scale_dict', str(scale_dict),
            '--date_start', date_start,
            '--date_end', date_end,
            '--f_out', str(f_out)]

    config = parse_args(args)
    main(config)

    assert f_out.exists()

    if f_out.exists() and f_out.is_file():
        # clean up output
        f_out.unlink()
