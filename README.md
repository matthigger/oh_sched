# Formatting office hours time

Office hours take place weekly during a timeslot on one day of the week.  Here are two valid examples:
    
    Mondays 3PM-4PM
    Tue 11:15am-1 Pm

Following either of these examples is sufficient, but for those interested here are the gory parsing detail:

- The day of the week is determined by checking for the case-insensitive three letter abbreviation of the day (e.g. "thu").  See `normalize_day_of_week()` in [calendr.py](oh_sched/calendr.py)
- Start and end times for office hours are separated by the unique appearance of '-' in the string.
- Each starting and ending time must follow one two formats below:


    12:15AM
    1 PM

which are both case / space insensitive.  See `to_time()` in [calendr.py](oh_sched/calendr.py)


Including extra text is fine so long as the weekday and start / end times are unique.  The following parses just fine: 

    Office Hours from Monday at 3 PM - 4:15 PM (preferred please)

Hopefully this flexibiliy allows you to communicate with TAs more gracefully in the google form
