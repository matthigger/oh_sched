import numpy as np

import oh_sched
from oh_sched.config import Config
from oh_sched.email import find_similar_str


def main(f_csv, config):
    prefs, email_list, name_list, oh_list = oh_sched.extract_csv(f_csv)

    if config.verbose:
        # print message about availability given by TAs
        num_available = prefs.shape[1] - np.isnan(prefs).sum(axis=1)
        print(f'TAs with lowest 20% of availability given:')
        for ta_idx in np.argsort(num_available)[:len(email_list) // 5]:
            n = num_available[ta_idx]
            print(f'  {n} OH slots possible: {email_list[ta_idx]}')

    # scale per day
    if config.scale_dict is not None:
        prefs = prefs * oh_sched.get_scale(oh_list,
                                           scale_dict=config.scale_dict,
                                           verbose=config.verbose)

    # match
    oh_ta_match = oh_sched.match(prefs,
                                 oh_per_ta=config.oh_per_ta,
                                 max_ta_per_oh=config.max_ta_per_oh)

    perc_max = oh_sched.get_perc_max(oh_ta_match, prefs=prefs)
    assert not np.isnan(perc_max).any(), 'TA assigned outside availability'

    # export to ics
    oh_ta_dict = {oh_list[oh]: [name_list[ta] for ta in ta_list]
                  for oh, ta_list in enumerate(oh_ta_match)}
    config.to_ics(oh_ta_dict)

    if config.verbose:
        # print TAs per slot
        print('\nSchedule:')
        for oh, ta_list in oh_ta_dict.items():
            if not len(ta_list):
                continue

            ta_csv = ', '.join(ta_list)
            print(f'{oh} has {len(ta_list)} TAs: {ta_csv}')

        print('\nPercentage Max Score :')
        print(
            'https://github.com/matthigger/oh_sched?tab=readme-ov-file#percentage-max')
        print(f'min percentage max score: {perc_max.min():.4f}')
        print(f'mean percentage max score: {perc_max.mean():.4f}\n')

    # warn on similar emails
    email_tup_list = list(find_similar_str(email_list, max_distance=2))
    if email_tup_list:
        print('WARNING: similar emails treated as unique')
        print('https://github.com/matthigger/oh_sched?tab=readme-ov-file#email-comparison')
        for email0, email1 in email_tup_list:
            print(f'{email0} vs \n{email1}\n')
        print('')


if __name__ == '__main__':
    import argparse
    import pathlib

    parser = argparse.ArgumentParser(
        description='https://github.com/matthigger/oh_sched')
    parser.add_argument('f_csv', type=str,
                        help='Path to the TA OH preference CSV')
    parser.add_argument('-c', '--config', type=str, default=None,
                        help='path to yaml file with configuration.  you may use (and create) a default configuration yaml by not passing this parameter')
    param = parser.parse_args()

    if param.config is None:
        f_config = pathlib.Path('config.yaml')

        if f_config.exists():
            print(f'Using config file {f_config}, pass with -c {f_config} to '
                  f'avoid this message')
            config = Config.from_yaml(f_config)
        else:
            # build default config, dump to file for user
            print(f'Using default config {f_config} please revise as needed '
                  f'(https://github.com/matthigger/oh_sched)')
            config = Config()
            config.to_yaml(f_config)
    else:
        config = Config.from_yaml(param.config)

    main(param.f_csv, config)
