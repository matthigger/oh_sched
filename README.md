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

# Percentage Max

To quantify the quality of the matching, we compute a percentage maximum score for every TA.  Consider the following toy example:

|     | OH0 | OH1 | OH2 | OH3 |
|-----|-----|-----|-----|-----|
| TA0 | 4   | 3   |     |     |
| TA1 |     | 3   | 4   | 1   |

Let us assume that we're assigning two office hours slots per TA (i.e. `oh_per_ta=2`).  In this case, the maximum preference score for TA1's two OH slots is 7 (assigning them OH1 and OH2).  If TA1 was assigned OH2 and OH3 then the schedule achieved a score of only 5.  In this case TA1's percentage max is $5/7\approx.71$.  

The TA with the smallest percentage max score has the least favorable schedule, as compared to their own preferences.  Examining the minimum and mean percentage max score (printed to the command line when run) gives a sense of how favorable the matching is for TAs.

# Email Comparison

The software will take the latest TA preference, allowing TAs to update their preferences as desired.  One challenge here is that a typo on entering their email a second (or first) time would have the software treat each entry as belonging to a unique TA.  To mitigate this, we throw a warning when two emails are sufficiently similar (Levenshtein distance of 2 or less).  Other than warning, no adjustment is made by the software.  Should you receive this warning, please check the input CSV for this kind of error and manually edit and re-run as needed.