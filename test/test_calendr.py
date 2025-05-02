from datetime import time

import pytest

from oh_sched.calendr import *


def test_normalize_day_of_week():
    # Valid cases
    assert normalize_day_of_week('Mon meeting') == 0
    assert normalize_day_of_week('tue call') == 1
    assert normalize_day_of_week('WED deadline') == 2
    assert normalize_day_of_week('Check on thursday') == 3
    assert normalize_day_of_week('Friday night') == 4
    assert normalize_day_of_week('Sat work') == 5
    assert normalize_day_of_week('Sun brunch') == 6

    # Case insensitivity
    assert normalize_day_of_week('MONDAY') == 0
    assert normalize_day_of_week('friDAY') == 4

    # No match (should raise)
    with pytest.raises(AssertionError, match='no day of week found'):
        normalize_day_of_week('holiday')

    # Multiple matches (should raise)
    with pytest.raises(AssertionError, match='non-unique day of week found'):
        normalize_day_of_week('mon tue meeting')


def test_to_time():
    # Standard time formats
    assert to_time('6:30 PM') == time(18, 30)
    assert to_time('4 aM') == time(4, 0)
    assert to_time('12:00 am') == time(0, 0)
    assert to_time('12 Pm') == time(12, 0)

    # With extra spaces or additional text
    assert to_time('at 9 PM OH starts') == time(21, 0)
    assert to_time('  7:15AM  ') == time(7, 15)
    assert to_time('9 PM ') == time(21, 0)

    for time_str in ['6.30 PM',
                     'noon',
                     '6:30PM to 7:00PM']:
        with pytest.raises(ValueError):
            to_time(time_str)


# Helper function to check equality of datetimes (ignoring tzinfo if needed)
def check_datetime_equal(dt1, dt2):
    return dt1.replace(tzinfo=None) == dt2.replace(tzinfo=None)


def test_get_event_kwargs():
    # Case 1: Normal weekly event in UTC
    tz = timezone('UTC')
    oh = OfficeHour('Tue@9:00 AM-10:00 AM')
    kwargs = oh.get_event_kwargs(
        date_start='2025-04-01',  # Tuesday
        date_end='2025-05-01',
        tz=tz,
        summary='Test Event'
    )

    expected_dtstart = tz.localize(datetime(2025, 4, 1, 9, 0))
    expected_dtend = tz.localize(datetime(2025, 4, 1, 10, 0))

    assert kwargs['dtstart'] == expected_dtstart
    assert kwargs['dtend'] == expected_dtend
    assert kwargs['rrule'] == {'freq': 'weekly', 'count': 5}
    assert kwargs['summary'] == 'Test Event'

    # Case 2: Start date not on target weekday (Wed -> next Mon)
    oh = OfficeHour('Mon@6:00 PM-7:00 PM')
    kwargs = oh.get_event_kwargs(
        date_start='2025-04-02',  # Wednesday
        date_end='2025-04-20',
        tz=tz,
    )
    assert kwargs['dtstart'] == tz.localize(datetime(2025, 4, 7, 18, 0))
    assert kwargs['dtend'] == tz.localize(datetime(2025, 4, 7, 19, 0))
    assert kwargs['rrule'] == {'freq': 'weekly', 'count': 2}

    # Case 3: Uses local timezone if not provided
    oh = OfficeHour('Tue@12:00 PM-1:00 PM')
    kwargs = oh.get_event_kwargs(
        date_start='2025-04-01',
        date_end='2025-04-30'
    )
    assert kwargs['dtstart'].tzinfo is not None
    assert kwargs['dtend'].tzinfo is not None
    assert kwargs['rrule']['count'] == 5

    # Case 4: Raises error on exceeding repeat limit
    oh = OfficeHour('Sun@1:00 AM-2:00 AM')
    with pytest.raises(AttributeError):
        oh.get_event_kwargs(
            date_start='2023-01-01',
            date_end='2025-01-01',
            tz=tz
        )
