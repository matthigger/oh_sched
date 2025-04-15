import re

import pandas as pd
import tzlocal
from icalendar import Calendar, Event
from pytz import timezone


def normalize_day_of_week(day_str):
    """ extracts a day of week, as index, from a string

    Args:
        day_str (str): string containing some day of the week

    Returns:
        day_idx (int): 0 for monday, 1 for tuesday, ...
    """
    date_regex = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    match_list = [bool(re.search(pattern, day_str, re.IGNORECASE))
                  for pattern in date_regex]

    assert sum(match_list) < 2, f'non-unique day of week found in: {day_str}'
    assert sum(match_list) == 1, f'no day of week found in: {day_str}'

    # return idx of first match in list
    for idx, b in enumerate(match_list):
        if b:
            return idx


def to_time(time_str):
    """ converts to timedelta, from beginning of day to time_str

    Args:
        time_str (str): comes in one of two formats: "6:30 PM" or "4 AM"

    Returns:
        delta (timedelta): from beginning of day
    """
    # Match patterns for 12-hour and 24-hour unambiguous formats
    patterns = [
        ('%I:%M%p', re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)', re.IGNORECASE)),
        ('%I%p', re.compile(r'\d{1,2}\s*(?:AM|PM)', re.IGNORECASE))
    ]

    for fmt, pattern in patterns:
        match_list = pattern.findall(time_str)
        match len(match_list):
            case 0:
                # no match found
                continue
            case 1:
                # unique match found
                s_match = match_list[0].replace(' ', '')
                return datetime.strptime(s_match, fmt).time()
            case _:
                raise ValueError(f'Multiple times found: {time_str}')

    raise ValueError(f"Ambiguous or invalid time string: '{time_str}'")


from datetime import datetime, timedelta


def get_event_kwargs(date_start, date_end, time_str, tz=None, **kwargs):
    """ gets weekly recurring event arguments, to be passed to Event

    Args:
        date_start (str): start date
        date_end (str): end date
        time_str (str): time of event, includes a start and stop seperated
            by a '-' character.  see get_time() function for parsing info on
            each side
        tz (str or timezone, optional): timezone. If not provided, the local
            timezone is used.
        **kwargs: Additional parameters to be included in the event

    Returns:
        kwargs: dictionary to be unapcked into Event object

    Raises:
        AttributeError: event exceeds the maximum weekly repeats (53 weeks)
    """
    # Convert date_start, date_end to date objects
    date_start = pd.to_datetime(date_start).date()
    date_end = pd.to_datetime(date_end).date()

    # Move start date up to the correct weekday
    weekday, time_str = time_str.split('@')
    weekday_idx = normalize_day_of_week(weekday)
    while date_start.weekday() != weekday_idx:
        date_start += timedelta(days=1)

    # Convert time_str to timedelta (time since start of day)
    time_start, time_end = time_str.split('-')
    time_start = to_time(time_start)
    time_end = to_time(time_end)

    # Handle timezone (default to local time if not provided)
    if tz is None:
        tz = tzlocal.get_localzone()
    tz = timezone(str(tz))

    kwargs['dtstart'] = tz.localize(datetime.combine(date_start, time_start))
    kwargs['dtend'] = tz.localize(datetime.combine(date_start, time_end))

    # Compute the number of weekly repeats before the end date
    date = date_start
    for repeats in range(53):  # Max 53 weekly repeats
        if date > date_end:
            break
        date = date + timedelta(weeks=1)
    else:
        raise AttributeError(
            f"Exceeded max weekly repeats (start: {date_start}, stop: {date_end})")

    kwargs['rrule'] = {'freq': 'weekly', 'count': repeats}

    return kwargs


def get_event(*args, **kwargs):
    """ differs only from _get_event() by returning an Event (easier testing)
    """
    kwargs = get_event_kwargs(*args, **kwargs)

    # build event with proper attributes of event, may include additional
    # ones not computed above (e.g. 'summary' or 'description')
    event = Event()
    for key, val in kwargs.items():
        event.add(key, val)

    return event


def build_calendar(oh_ta_dict, date_start, date_end):
    """  builds a calendar, a set of events, from oh_ta_dict

    Args:
        oh_ta_dict (dict): keys are office hours slots (see time_str in
            get_event_kwargs()), values are lists of str (TA names)
        date_start (str): starting date for office hours for course
            (inclusive), see  get_event_kwargs()
        date_end (str): ending date for office hours for course (inclusive),
            see get_event_kwargs()=

    Returns:
        cal (Calendar): ready to be exported to ics format
    """
    cal = Calendar()
    for time_str, ta_list in oh_ta_dict.items():
        if not ta_list:
            # skip oh slots without any TAs
            continue
        ta_list = [ta.capitalize() for ta in sorted(ta_list)]
        summary = ', '.join(sorted(ta_list))
        event = get_event(summary=summary,
                          date_start=date_start,
                          date_end=date_end,
                          time_str=time_str)
        cal.add_component(event)

    return cal
