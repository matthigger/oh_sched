import argparse

import numpy as np

import oh_sched


def main(config):
    prefs, email_list, name_list, oh_list = oh_sched.extract_csv(config.f_csv)

    if config.verbose:
        # print message about availability given by TAs
        num_available = prefs.shape[1] - np.isnan(prefs).sum(axis=1)
        print(f'TAs with lowest 20% of availability given:')
        for ta_idx in np.argsort(num_available)[:len(email_list) // 5]:
            n = num_available[ta_idx]
            print(f'  {n} OH slots possible: {email_list[ta_idx]}')

    # scale per day
    prefs_adjust = prefs * oh_sched.get_scale(oh_list,
                                              scale_dict=config.scale_dict)

    # match
    oh_ta_match = oh_sched.match(prefs_adjust,
                                 oh_per_ta=config.oh_per_ta,
                                 max_ta_per_oh=config.max_ta_per_oh)

    perc_max = oh_sched.get_perc_max(oh_ta_match, prefs=prefs)
    assert not np.isnan(perc_max).any(), 'TA assigned outside availability'

    # export to ics
    oh_ta_dict = {oh_list[oh]: [name_list[ta] for ta in ta_list]
                  for oh, ta_list in enumerate(oh_ta_match)}
    cal = oh_sched.build_calendar(oh_ta_dict,
                                  date_start=config.date_start,
                                  date_end=config.date_end)

    if config.verbose:
        # print TAs per slot
        print('Schedule:')
        for oh, ta_list in oh_ta_dict.items():
            print(f'{oh}: {len(ta_list)} TAs')

        print('Percentage Max Score :')
        print(
            'https://github.com/matthigger/oh_sched?tab=readme-ov-file#percentage-max')
        print(f'min percentage max score: {perc_max.min():.4f}')
        print(f'mean percentage max score: {perc_max.mean():.4f}')

    if config.f_out is not None:
        if config.verbose:
            print(f'\noutput ics file, maybe be imported to calendar apps: '
                  f'{config.f_out}')
        else:
            print('\npass f_out to create ics file, importable to calendar '
                  'apps')

        with open(config.f_out, 'wb') as f:
            f.write(cal.to_ical())


def parse_args(args=None):
    if args is None:
        args = []

    parser = argparse.ArgumentParser(
        description='https://github.com/matthigger/oh_sched')
    # Add arguments to the parser
    parser.add_argument('--f_csv', type=str, default='oh_prefs.csv',
                        help='CSV file of TA preferences for each OH slot')
    parser.add_argument('--oh_per_ta', type=int, default=1,
                        help='Number of OH assigned per TA')
    parser.add_argument('--max_ta_per_oh', type=int, default=None,
                        help='Maximum TAs per OH')
    parser.add_argument('--scale_dict', type=str, default=None,
                        help='Dictionary for scaling, represented as a string. If not provided, no scaling will be applied.')
    parser.add_argument('--date_start', type=str, default='Sept 3 2025',
                        help='Start date of office hours (inclusive)')
    parser.add_argument('--date_end', type=str, default='Dec 7 2025',
                        help='End date for office hourse (inclusive)')
    parser.add_argument('--f_out', type=str, default='oh.ics',
                        help='Output ICS calendar file')
    parser.add_argument('--quiet', action='store_true', dest='verbose',
                        help='Suppress command line output')

    config = parser.parse_args(args)

    # Convert scale_dict string to actual dictionary if provided
    if config.scale_dict is not None:
        config.scale_dict = eval(config.scale_dict)

    return config


if __name__ == '__main__':
    config = parse_args()
    main(config)
