import re
from datetime import datetime, timedelta
from functools import total_ordering

import pandas as pd
import tzlocal
from icalendar import Calendar, Event
from pytz import timezone
import numpy as np

@total_ordering
class OfficeHour:
    def __init__(self, name):
        self.day_idx = normalize_day_of_week(name)
        time_start, time_end = name.split('-')
        self.time_start = to_time(time_start)
        self.time_end = to_time(time_end)
        self.name = name

    def to_tuple(self):
        return self.day_idx, self.time_start, self.time_end

    def __str__(self):
        return f'OfficeHour({self.name})'

    def __lt__(self, other):
        return self.to_tuple() < other.to_tuple()

    def __eq__(self, other):
        return self.to_tuple() == other.to_tuple()

    def intersects(self, other):
        if self.day_idx != other.day_idx:
            # different days, can't intersect
            return False

        if self < other:
            # self begins first (or at same time)
            return self.time_end > other.time_start
        else:
            # other begins first (or at same time)
            return other.time_end > self.time_start

    def get_event_kwargs(self, date_start, date_end, tz=None, **kwargs):
        """ gets weekly recurring event arguments, to be passed to Event

        Args:
            date_start (str): start date
            date_end (str): end date
            tz (str or timezone, optional): timezone. If not given, the local
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
        while date_start.weekday() != self.day_idx:
            date_start += timedelta(days=1)

        # Handle timezone (default to local time if not provided)
        if tz is None:
            tz = tzlocal.get_localzone()
        tz = timezone(str(tz))

        # build output starts / ends
        dtstart = datetime.combine(date_start, self.time_start)
        kwargs['dtstart'] = tz.localize(dtstart)
        dtend = datetime.combine(date_start, self.time_end)
        kwargs['dtend'] = tz.localize(dtend)

        # Compute the number of weekly repeats before the end date
        date = date_start
        for repeats in range(52):
            if date > date_end:
                break
            date = date + timedelta(weeks=1)
        else:
            raise AttributeError(f'> 1 yr event: {date_start} to {date_end}')

        kwargs['rrule'] = {'freq': 'weekly', 'count': repeats}

        return kwargs


def get_intersection_dict(oh_list):
    # order office hours (from earliest to latest in the day)
    _oh_list = [OfficeHour(oh) for oh in oh_list]
    idx_map = np.argsort(_oh_list)
    _oh_list.sort()

    # find intersections (initialize with reflexivity)
    oh_int_dict = {idx: [idx] for idx in range(len(oh_list))}
    for idx0, oh0 in enumerate(_oh_list):
        for _idx1, oh1 in enumerate(_oh_list[idx0 + 1:]):
            # idx1 is consistent with ordering of _oh_list
            idx1 = _idx1 + idx0 + 1
            if oh0.intersects(oh1):
                oh_int_dict[idx0].append(idx1)
                oh_int_dict[idx1].append(idx0)
            else:
                # oh0 is before oh1, if oh0 doesn't intersect oh1 it can't
                # intersect any which come after it in _oh_list, its sorted
                break

    # map from indexing of _oh_list back to given oh_list indexing
    oh_int_dict = {idx_map[k]: [idx_map[_v] for _v in v]
                   for k, v in oh_int_dict.items()}

    return oh_int_dict


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
    return None


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

    raise ValueError(f'Ambiguous or invalid time string: "{time_str}"')


def build_calendar(oh_ta_dict, date_start, date_end, **kwargs):
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
    for oh_name, ta_list in oh_ta_dict.items():
        if not ta_list:
            # skip oh slots without any TAs
            continue
        ta_list = [ta.capitalize() for ta in sorted(ta_list)]
        summary = ', '.join(sorted(ta_list))

        oh = OfficeHour(name=oh_name)
        _kwargs = oh.get_event_kwargs(summary=summary,
                                     date_start=date_start,
                                     date_end=date_end,
                                     **kwargs)

        # build event with proper attributes of event,
        _kwargs = kwargs | _kwargs
        cal.add_component(Event(**_kwargs))

    return cal
