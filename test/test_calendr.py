from datetime import time

import pytest

from oh_sched.calendr import *


def test_get_intersection_dict():
    oh_list = [
        'Tue 09:00AM-10:00AM',  # 0 — different day, no overlap
        'Mon 09:30AM-10:30AM',  # 1 — overlaps with 3
        'Mon 12:00PM-01:00PM virtual',  # 2 — overlaps with 5
        'Mon 09:00AM-10:00AM',  # 3 — overlaps with 1
        'Mon 10:30AM-11:30AM',  # 4 — no overlap (adjacent to 1)
        'Mon 12:00PM-1:00PM in person'  # 5 — overlaps with 2
    ]

    oh_int_dict = get_intersection_dict(oh_list)

    oh_int_dict_exp = {
        0: [0],
        1: [1, 3],
        2: [2, 5],
        3: [3, 1],
        4: [4],
        5: [5, 2]
    }

    # convert list values to sets to avoid order issues in comparisons
    oh_int_dict = {k: set(v) for k, v in oh_int_dict.items()}
    oh_int_dict_exp = {k: set(v) for k, v in oh_int_dict_exp.items()}
    assert oh_int_dict == oh_int_dict_exp


def test_parse_day():
    # Valid cases (notice, we avoid mid-word matches in first two)
    assert parse_day('Mon leMON meeting') == (0, 'leMON meeting')
    assert parse_day('tue THUmp call') == (1, 'THUmp call')
    assert parse_day('WED deadline') == (2, 'deadline')
    assert parse_day('Check on thursday') == (3, 'Check on')
    assert parse_day('Friday night') == (4, 'night')
    assert parse_day('Sat work') == (5, 'work')
    assert parse_day('Sun brunch') == (6, 'brunch')

    # Case insensitivity
    assert parse_day('MONDAY') == (0, '')
    assert parse_day('friDAY') == (4, '')

    # No match (should raise)
    with pytest.raises(AssertionError, match='Expected one day of week in'):
        parse_day('holiday')

    # Multiple matches (should raise)
    with pytest.raises(AssertionError, match='Expected one day of week in'):
        parse_day('mon tue meeting')


def test_parse_time():
    # Standard time formats
    assert parse_time('6:30 PM') == (time(18, 30), '')
    assert parse_time('4 aM') == (time(4, 0), '')
    assert parse_time('12:00 am') == (time(0, 0), '')
    assert parse_time('12 Pm') == (time(12, 0), '')

    # With extra spaces or additional text
    assert parse_time('at 9 PM OH starts') == \
           (time(21, 0), 'at  OH starts')
    assert parse_time('!  7:15AM  !') == (time(7, 15), '!    !')
    assert parse_time('9 PM extra') == (time(21, 0), 'extra')

    for time_str in ['6.30 PM',
                     'noon',
                     '6:30PM to 7:00PM']:
        with pytest.raises(ValueError):
            parse_time(time_str)


# Helper function to check equality of datetimes (ignoring tzinfo if needed)
def check_datetime_equal(dt1, dt2):
    return dt1.replace(tzinfo=None) == dt2.replace(tzinfo=None)


class TestOfficeHour:
    def test_init(self):
        # parse_day & parse_time tested elsewhere
        test_cases = [('Monday 9 AM - 10 AM Meeting', 'Meeting'),
                      ('Tue 8:00 AM - 9:30 AM Breakfast', 'Breakfast'),
                      ('Wed Call 7 AM - 8 AM Standup', 'Call Standup'),
                      ('Thursday 6 PM - 7 PM Review', 'Review'),
                      ('Fri Briefing 10 AM - 11 AM', 'Briefing'),
                      ('Sat 1 PM - 2 PM', ''),
                      ('Sun 12:00 AM - 1:00 AM Midnight', 'Midnight'),
                      ('Monday 9 AM - 9 AM', ''),
                      ('Tuesday 11:15 AM - 12:45 PM Session', 'Session'),
                      ]
        for idx, (s, name_exp) in enumerate(test_cases):
            oh = OfficeHour(s)
            assert oh.name == name_exp, f'fail case: {idx}'

        with pytest.raises(ValueError, match='doesnt contain unique `-`'):
            OfficeHour('Mon Check-in 3 PM - 4 PM')

    def test_to_tuple(self):
        oh = OfficeHour('Mon 09:00AM-10:00AM')
        assert oh.to_tuple() == (0, time(9, 0), time(10, 0))

    def test_lt(self):
        oh1 = OfficeHour('Mon 09:00AM-10:00AM')
        oh2 = OfficeHour('Mon 10:00AM-11:00AM')
        assert oh1 < oh2
        assert not (oh2 < oh1)

    def test_eq(self):
        oh1 = OfficeHour('Mon 09:00AM-10:00AM')
        oh2 = OfficeHour('Mon 9AM-10AM')
        oh3 = OfficeHour('Mon 10:00AM-11:00AM')
        assert oh1 == oh2
        assert oh1 != oh3

    def test_intersects(self):
        # Same day, overlapping
        oh1 = OfficeHour('Mon 09:00AM-10:30AM')
        oh2 = OfficeHour('Mon 10:00AM-11:00AM')
        assert oh1.intersects(oh2)
        assert oh2.intersects(oh1)

        # Same day, no overlap
        oh3 = OfficeHour('Mon 11:00AM-12:00PM')
        assert not oh1.intersects(oh3)
        assert not oh3.intersects(oh1)

        # Different days
        oh4 = OfficeHour('Tue 09:00AM-10:00AM')
        assert not oh1.intersects(oh4)

    def test_get_event_kwargs(self):
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
