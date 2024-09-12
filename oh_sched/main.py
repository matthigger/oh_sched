if __name__ == '__main__':
    import oh_sched
    import numpy as np

    f_csv = 'oh_response_clean.csv'
    oh_per_ta = 3
    max_ta_per_oh = 4
    decay = .99
    scale_dict = {r'(Friday|Thursday).*[45678] ?PM': 1.1}

    # extract
    prefs, email_list, name_list, oh_list = oh_sched.extract_csv(f_csv)

    # scale per day (push fridays, & thursdays, later in the day)
    prefs *= oh_sched.get_scale(oh_list, scale_dict=scale_dict)

    # match
    oh_ta_match = oh_sched.match(prefs,
                                 oh_per_ta=oh_per_ta,
                                 max_ta_per_oh=max_ta_per_oh)

    # # export to ics
    # cal = oh_sched.build_calendar(oh_ta_dict,
    #                               date_start='sept 13 2024',
    #                               date_end='dec 4 2024')
    # perc_max, ta_num_oh_dict = oh_sched.get_perc_max(oh_ta_dict,
    #                                                  oh_list=oh_list,
    #                                                  ta_list=name_list,
    #                                                  prefs=prefs)
    #
    # for ta, p in perc_max.items():
    #     assert not np.isnan(p), f'TA assigned outside available: {ta}'
    #
    # with open('oh.ics', 'wb') as f:
    #     f.write(cal.to_ical())
    #
    # # print TAs per slot
    # for oh, ta_list in oh_ta_dict.items():
    #     print(f'{oh}: {len(ta_list)} TAs')
