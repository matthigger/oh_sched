import re
from datetime import datetime, timedelta

import pandas as pd
import tzlocal
from icalendar import Calendar, Event
from pytz import timezone


def normalize_day_of_week(date_str):
    date_regex = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
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


def get_event(date_start, date_end, time_str, tz=None, **kwargs):
    """ returns 1st start stop datetimes after (or on) a given date """
    # convert date_start, date_end to date objects
    date_start = pd.to_datetime(date_start).date()
    date_end = pd.to_datetime(date_end).date()

    # move start date up to proper day of the week
    weekday, time_str = time_str.split('@')
    weekday_idx = normalize_day_of_week(weekday)
    while date_start.weekday() != weekday_idx:
        date_start += timedelta(days=1)

    # convert time_str to timedelta (time since start of day)
    time_start, time_end = time_str.split('-')
    time_start = to_timedelta(time_start)
    time_end = to_timedelta(time_end)

    # specify start and end time
    if tz is None:
        tz = tzlocal.get_localzone()
    tz = timezone(str(tz))
    kwargs['dtstart'] = tz.localize(datetime.combine(date_start, time_start))
    kwargs['dtend'] = tz.localize(datetime.combine(date_start, time_end))

    # compute number of repeats before end date
    date = date_start
    for repeats in range(53):
        if date > date_end:
            break
        date = date + timedelta(weeks=1)
    else:
        raise AttributeError(f'exceeded max weekly repeats (start: '
                             f'{date_start} stop: {date_end})')
    kwargs['rrule'] = {'freq': 'weekly', 'count': repeats}

    # build event with proper attributes of event, may include additional
    # ones not computed above (e.g. 'summary' or 'description')
    event = Event()
    for key, val in kwargs.items():
        event.add(key, val)

    return event


def build_calendar(oh_ta_dict, date_start, date_end):
    cal = Calendar()
    for oh, ta_list in oh_ta_dict.items():
        if not ta_list:
            # skip oh slots without any TAs
            continue
        ta_list = [ta.capitalize() for ta in sorted(ta_list)]
        summary = ', '.join(sorted(ta_list))
        event = get_event(summary=summary,
                          date_start=date_start,
                          date_end=date_end,
                          time_str=oh)
        cal.add_component(event)

    return cal


if __name__ == '__main__':
    oh_ta_dict = {'Monday @ 6PM - 7PM': ['ta-test0', 'ta-test1']}
    cal = build_calendar(oh_ta_dict,
                         date_start='today',
                         date_end='dec 4 2024')
    with open('oh_test.ics', 'wb') as f:
        f.write(cal.to_ical())

