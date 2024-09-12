if __name__ == '__main__':
    import oh_sched
    import numpy as np

    f_csv = 'oh_response_clean.csv'
    oh_per_ta = 3
    max_ta_per_oh = 4
    scale_dict = {r'(Friday|Thursday).*[45678] ?PM': 1.1}

    # extract
    prefs, email_list, name_list, oh_list = oh_sched.extract_csv(f_csv)

    # print message about
    num_available = prefs.shape[1] - np.isnan(prefs).sum(axis=1)
    print(f'lowest 10% of availability:')
    for ta_idx in np.argsort(num_available)[:len(name_list) // 10]:
        n = num_available[ta_idx]
        print(f'  {n} OH slots possible: {email_list[ta_idx]}')

    # scale per day (push fridays, & thursdays, later in the day)
    prefs_adjust = prefs * oh_sched.get_scale(oh_list, scale_dict=scale_dict)

    # match
    oh_ta_match = oh_sched.match(prefs_adjust,
                                 oh_per_ta=oh_per_ta,
                                 max_ta_per_oh=max_ta_per_oh)

    perc_max, num_oh = oh_sched.get_perc_max(oh_ta_match,
                                             prefs=prefs)
    assert (num_oh == oh_per_ta).all(), 'TAs not given proper number of OH'
    assert not np.isnan(perc_max).any(), 'TA assigned outside availability'

    # export to ics
    oh_ta_dict = {oh_list[oh]: [name_list[ta] for ta in ta_list]
                  for oh, ta_list in enumerate(oh_ta_match)}
    cal = oh_sched.build_calendar(oh_ta_dict,
                                  date_start='sept 13 2024',
                                  date_end='dec 4 2024')
    with open('oh.ics', 'wb') as f:
        f.write(cal.to_ical())

    # print TAs per slot
    for oh, ta_list in oh_ta_dict.items():
        print(f'{oh}: {len(ta_list)} TAs')

    print(f'min percentage max score: {perc_max.min():.4f}')
    print(f'mean percentage max score: {perc_max.mean():.4f}')
