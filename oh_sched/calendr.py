import re
from datetime import datetime, timedelta

import ics
import pandas as pd


def normalize_day_of_week(date_str):
    date_regex = ['mon', 'tues', 'wed', 'thurs', 'fri', 'sat', 'sun']
    match_list = [bool(re.search(pattern, date_str, re.IGNORECASE))
                  for pattern in (date_regex)]

    assert sum(match_list) < 2, f'non-unique day of week found in: {date_str}'
    assert sum(match_list) == 1, f'no day of week found in: {date_str}'

    # return idx of first match in list
    for idx, b in enumerate(match_list):
        if b:
            return idx


def to_timedelta(time_str):
    """ converts to timedelta, from beggining of day to time_str

    Args:
        time_str (str): comes in one of two formats: "6:30 PM" or "4 AM"

    Returns:
        delta (timedelta): from beginning of day
    """
    if ':' in time_str:
        s_fmt = '%I:%M%p'
    else:
        s_fmt = '%I%p'

    return datetime.strptime(time_str.strip(), s_fmt).time()


def start_stop_iter(date_start, date_end, time_str):
    # convert to date objects
    date = pd.to_datetime(date_start).date()
    date_end = pd.to_datetime(date_end).date()

    # move start date up to proper day of the week
    weekday, time_str = time_str.split('@')
    weekday_idx = normalize_day_of_week(weekday)
    while date.weekday() != weekday_idx:
        date += timedelta(days=1)

    # convert to timedelta (time since start of day)
    time_start, time_end = time_str.split('-')
    time_start = to_timedelta(time_start)
    time_end = to_timedelta(time_end)

    while date <= date_end:
        yield (datetime.combine(date, time_start),
               datetime.combine(date, time_end))

        date += timedelta(days=7)


def start_stop_iter_event(*args, name, **kwargs):
    for start, stop in start_stop_iter(*args, **kwargs):
        yield ics.Event(name=name,
                        begin=start,
                        end=stop)


def build_calendar(oh_ta_dict, date_start, date_end):
    cal = ics.Calendar()
    for oh, ta_list in oh_ta_dict.items():
        ta_list = [ta.capitalize() for ta in sorted(ta_list)]
        name = 'Online OH- ' + ', '.join(sorted(ta_list))
        for event in start_stop_iter_event(name=name,
                                           date_start=date_start,
                                           date_end=date_end,
                                           time_str=oh):
            cal.events.add(event)

    return cal


if __name__ == '__main__':
    x = list(start_stop_iter_event(name='OH test',
                                   date_start='today',
                                   date_end='dec 4 2024',
                                   time_str='Monday @ 6 PM - 7 PM'))

    print('hi')
