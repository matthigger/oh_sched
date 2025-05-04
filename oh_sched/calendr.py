import re
from datetime import datetime, timedelta
from functools import total_ordering

import numpy as np
import pandas as pd
import tzlocal
from icalendar import Calendar, Event
from pytz import timezone


@total_ordering
class OfficeHour:
    def __init__(self, s):
        self.s_orig = s
        self.day_idx, s = parse_day(s)

        if s.count('-') != 1:
            raise ValueError(f'doesnt contain unique `-`: {s}')
        time_start, time_end = s.split('-')
        self.time_start, name0 = parse_time(time_start)
        self.time_end, name1 = parse_time(time_end)

        # build name (remove name0 or name1 if empty string)
        name_tup = [name0, name1]
        name_tup = [s for s in name_tup if s]
        self.name = ' '.join(name_tup)

    def to_tuple(self):
        return self.day_idx, self.time_start, self.time_end, self.name

    def __hash__(self):
        return hash(self.to_tuple())

    def __str__(self):
        return f'OfficeHour({self.s_orig})'

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


def parse_day(day_str):
    """ extracts a day of week, as index, from a string

    Args:
        day_str (str): string containing some day of the week

    Returns:
        day_idx (int): 0 for Monday, 1 for Tuesday, ...
        day_str_clean (str): String with the day and nearby time removed
    """
    day_regexes = [r'\bmon(day)?\b',
                   r'\btue(s(day)?)?\b',
                   r'\bwed(nesday)?\b',
                   r'\bthu(r(sday)?)?\b',
                   r'\bfri(day)?\b',
                   r'\bsat(urday)?\b',
                   r'\bsun(day)?\b']

    found = [(i, re.search(pat, day_str, re.IGNORECASE))
             for i, pat in enumerate(day_regexes)]
    matches = [(i, m) for i, m in found if m]

    assert len(matches) == 1, \
        f'Expected one day of week in "{day_str}", found {len(matches)}'

    day_idx, match = matches[0]

    # Remove the matched day and any nearby time
    idx0, idx1 = match.span()
    day_str_clean = day_str[:idx0] + day_str[idx1:]
    day_str_clean = day_str_clean.strip(" ,:-")

    return day_idx, day_str_clean


def parse_time(s):
    """ converts to timedelta, from beginning of day to time_str

    Args:
        s (str): comes in one of two formats: "6:30 PM" or "4 AM"

    Returns:
        time (time): time of day
        s_clean (re.Match): input s, having time removed
    """
    # Match patterns for 12-hour and 24-hour unambiguous formats
    patterns = [
        ('%I:%M%p', re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)', re.IGNORECASE)),
        ('%I%p', re.compile(r'\d{1,2}\s*(?:AM|PM)', re.IGNORECASE))
    ]

    for fmt, pattern in patterns:
        match_list = pattern.findall(s)
        match len(match_list):
            case 0:
                # no match found
                continue
            case 1:
                # unique match found
                match = pattern.search(s)
                s_match = match.group().replace(' ', '')
                time = datetime.strptime(s_match, fmt).time()

                # Remove the matched day and any nearby time
                idx0, idx1 = match.span()
                s_clean = s[:idx0] + s[idx1:]
                s_clean = s_clean.strip(" ,:-")

                return time, s_clean
            case _:
                raise ValueError(f'Multiple times found: {s}')

    raise ValueError(f'Ambiguous or invalid time string: "{s}"')


def build_calendar(oh_ta_dict, date_start, date_end, **kwargs):
    """  builds a calendar, a set of events, from oh_ta_dict

    Args:
        oh_ta_dict (dict): keys are OfficeHour, vals are lists of str (TA
            names)
        date_start (str): starting date for office hours for course
            (inclusive), see  get_event_kwargs()
        date_end (str): ending date for office hours for course (inclusive),
            see get_event_kwargs()=

    Returns:
        cal (Calendar): ready to be exported to ics format
    """
    cal = Calendar()
    for oh, ta_list in oh_ta_dict.items():
        if not ta_list:
            # skip oh slots without any TAs
            continue
        ta_list = [ta.capitalize() for ta in sorted(ta_list)]
        summary = oh.name + ': ' + ', '.join(sorted(ta_list))

        _kwargs = oh.get_event_kwargs(summary=summary,
                                      date_start=date_start,
                                      date_end=date_end,
                                      **kwargs)

        # build event with proper attributes of event,
        _kwargs = kwargs | _kwargs
        event = Event()
        for key, val in _kwargs.items():
            event.add(key, val)
        cal.add_component(event)

    return cal
