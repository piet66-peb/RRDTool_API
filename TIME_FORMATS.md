<!-- use sgmlproc for generating a html file -->

# Time Formats

The RRdtool software offers a wide range of time formats. See the excerpt
 of the RRDtool documentation below.
RRDTool_API supports these formats as well, with some differences:

<br>

### Differences between RRDtool and RRDTool_API

* **m** = abbreviation, will be changed to minute
* **M** = abbreviation, will be changed to Month
* **0** (single character) is equal to 00 is equal to 00:00 today.
* **YYYY-MM-DD** is the same as DD.MM.YYYY is the same as MM/DD/YYYY
* Additionally: **last** = timestamp of the last stored entry.
* Additionally: **first** = timestamp of the first stored entry in top archive rra[0].

In case of a graph the very **last** respectively very **first** timestamp of all included databases is taken.

Specifications in the browser command line:
* **e** = \<end time>, default: now
* **l** = \<length of the time interval>, default: 1day
* **s** = \<start time>, default: \<end time> - \<length>
* **r** = \<resolution>, *rrdfetch+select*: parameter --resolution, *rrdgraph*: parameter --step, default: highest resolution

Parameter hierarchy:
1. input value
2. value from graph definition file
3. default value

<br>

### Treating midnight (start of the day) in the times

Start and end times:
* **midnight** = **midnight today** = midnight of the current day
* **midnight -1day** = midnight of the previous day
* **midnight Monday** = if Monday is the current day: midnight of the current day, 
  otherwise midnight of the next Monday
* **midnight Monday -1week** = if Monday is the current day: midnight of Monday previous week, 
  otherwise midnight of Monday in current week
* **midnight Feb1** = midnight of February 1 in current year
* **midnight Feb1 -1year** = midnight of February 1 in previous year
* **midnight Feb1 2022** = midnight of February 1 in year 2022

Time intervals:
* **s=midnight -1day** and **e=midnight** = complete previous day
* **s=midnight Mon -1week** and **e=midnight Mon** = complete week, maybe previous
   week or this week
* **s=midnight Feb1** and **e=midnight Mar1** = complete February this year
* **s=midnight Jan1 -1year** and **e=midnight Jan1** = complete previous year

<br>

### Enhancement for defining midnight (start of the day) in the times

The function **midnight()** provides a comfortable method to define the start 
point of a day/ week/ month/ year depending on any timestamp. 

Definition:
<br>**midnight(&lt;kind of interval&gt;, &lt;timestamp&gt;)**
<br>with:
- **&lt;kind of interval&gt;**: **D**=day|**W**=week|**M**=month|**Y**=year
- **&lt;timestamp&gt;**: **now**|**last**|any timestamp
<br>First day of the week is day #1 = Monday, according to ISO 8601.

Examples:
<br>**midnight(D, now)**: midnight of current day (= 0 = midnight = midnight today)
<br>**midnight(D, now)-1day**: midnight of previous day (= midnight today -1day)
<br>**midnight(D, last)**: midnight of the day with last value stored
<br>**midnight(W, now)**: first day of current week midnight
<br>**midnight(W, now)-1week**: first day of previous week midnight
<br>**midnight(W, last)**: midnight of the first day of the week with last value stored
<br>**midnight(M, now)**:  first day of current month midnight
<br>**midnight(M, now)-1Month**: first day of previous month midnight
<br>**midnight(M, last)**: midnight of the first day of the month with last value stored
<br>**midnight(Y, now)**:  first day of current year midnight
<br>**midnight(Y, now)-1year**: first day of previous year midnight
<br>**midnight(Y, last)**: midnight of the first day of the year with last value stored

<br>

## Time Specification of the RRDtool Software
Source: https://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html


### TIME SPECIFICATION

* **-\-start|-s start** (default **end-1day**)

start of the time series. A time in seconds since epoch (1970-01-01) is 
required. Negative numbers are relative to the current time. By default, 
one day worth of data will be fetched. See also **AT-STYLE TIME SPECIFICATION** 
for a detailed explanation on ways to specify the start time.

* **-\-end|-e end** (default **now**)

the end of the time series in seconds since epoch. See also **AT-STYLE TIME 
SPECIFICATION** for a detailed explanation of how to specify the end time.

<br>

### AT-STYLE TIME SPECIFICATION

Apart from the traditional Seconds since epoch, RRDtool does also understand 
at-style time specification. The specification is called "at-style" after the 
Unix command at(1) that has moderately complex ways to specify time to run your 
job at a certain date and time. The at-style specification consists of two 
parts: the **TIME REFERENCE SPECIFICATION** and the **TIME OFFSET SPECIFICATION**.

### TIME REFERENCE SPECIFICATION

The time reference specification is used, well, to establish a reference moment 
in time (to which the time offset is then applied to). When present, it should 
come first, when omitted, it defaults to **now**. On its own part, time reference 
consists of a time-of-day reference (which should come first, if present) and 
a day reference.

The time-of-day can be specified as **HH:MM**, **HH**.**MM**, or just **HH**. 
You can suffix 
it with **am** or **pm** or use 24-hours clock. Some special times of day are 
understood as well, including **midnight** (00:00), **noon** (12:00) and British 
**teatime** (16:00).

The day can be specified as month-name day-of-the-month and optional a 2- or 
4-digit year number (e.g. March 8 1999). Alternatively, you can use 
day-of-week-name (e.g. Monday), or one of the words: **yesterday**, **today**, 
**tomorrow**. You can also specify the day as a full date in several numerical 
formats, including **MM/DD/[YY]YY**, **DD**.**MM.[YY]YY**, or **YYYYMMDD**.

NOTE1: <br>this is different from the original at(1) behavior, where a single-number 
date is interpreted as MMDD[YY]YY.

NOTE2: <br>if you specify the day in this way, the time-of-day is REQUIRED as well.

Finally, you can use the words **now**, **start**, **end** or **epoch** as 
your time reference. 
**Now** refers to the current moment (and is also the default time reference). 
**Start** (**end**) can be used to specify a time relative to the start (end) time 
for those tools that use these categories (rrdfetch, rrdgraph) and **epoch** 
indicates the *IX epoch (*IX timestamp 0 = 1970-01-01 00:00:00 UTC). **epoch** 
is useful to disambiguate between a timestamp value and some forms of 
abbreviated date/time specifications, because it allows one to use time 
offset specifications using units, eg. **epoch**+19711205s unambiguously denotes 
timestamp 19711205 and not 1971-12-05 00:00:00 UTC.

Month and day of the week names can be used in their naturally abbreviated 
form (e.g., Dec for December, Sun for Sunday, etc.). The words **now**, **start**, 
end can be abbreviated as **n**, **s**, **e**.

### TIME OFFSET SPECIFICATION

The time offset specification is used to add/subtract certain time intervals 
to/from the time reference moment. It consists of a sign (+ or -) and an amount. 
The following time units can be used to specify the amount: **years**, **months**, 
**weeks**, **days**, **hours**, **minutes**, or **seconds**. These units 
can be used in singular 
or plural form, and abbreviated naturally or to a single letter (e.g. +3days, 
-1wk, -3y). Several time units can be combined (e.g., -5mon1w2d) or 
concatenated (e.g., -5h45min = -5h-45min = -6h+15min = -7h+1h30m-15min, etc.)

NOTE3: <br>If you specify time offset in days, weeks, months, or years, you will 
end with the time offset that may vary depending on your time reference, 
because all those time units have no single well defined time interval value 
(1 year contains either 365 or 366 days, 1 month is 28 to 31 days long, and 
even 1 day may be not equal to 24 hours twice a year, when DST-related clock 
adjustments take place). To cope with this, when you use days, weeks, months, 
or years as your time offset units your time reference date is adjusted 
accordingly without too much further effort to ensure anything about it 
(in the hope that mktime(3) will take care of this later). This may lead to 
some surprising (or even invalid!) results, e.g. 'May 31 -1month' = 'Apr 31' 
(meaningless) = 'May 1' (after mktime(3) normalization); in the EET timezone 
'3:30am Mar 29 1999 -1 day' yields '3:30am Mar 28 1999' (Sunday) which is an 
invalid time/date combination (because of 3am -> 4am DST forward clock 
adjustment, see the below example).

In contrast, hours, minutes, and seconds are well defined time intervals, and 
these are guaranteed to always produce time offsets exactly as specified (e.g. 
for EET timezone, '8:00 Mar 27 1999 +2 days' = '8:00 Mar 29 1999', but since 
there is 1-hour DST forward clock adjustment that occurs around 3:00 Mar 28 
1999, the actual time interval between 8:00 Mar 27 1999 and 8:00 Mar 29 1999 
equals 47 hours; on the other hand, '8:00 Mar 27 1999 +48 hours' = '9:00 Mar 
29 1999', as expected)

~~NOTE4:~~ <br>
~~The single-letter abbreviation for both **months** and **minutes** is **m**. 
To disambiguate them, the parser tries to read your mind :) by applying the 
following two heuristics:~~

* ~~If **m** is used in context of (i.e. right after the) years, months, weeks, or 
days it is assumed to mean **months**, while in the context of hours, minutes, and 
seconds it means **minutes**. (e.g., in -1y6m or +3w1m m is interpreted as months, 
while in -3h20m or +5s2m m the parser decides for minutes).~~

* ~~Out of context (i.e. right after the + or - sign) the meaning of **m** is 
guessed from the number it directly follows. Currently, if the number's 
absolute value is below 6 it is assumed that m means **months**, otherwise it is 
treated as **minutes**. (e.g., -6m == -6m minutes, while +5m == +5 months)~~

Final NOTES:<br>
* Time specification is case-insensitive.
* Whitespace can be inserted freely or omitted altogether. There are, however, cases 
when whitespace is required (e.g., 'midnight Thu'). ~~In this case you should either 
quote the whole phrase to prevent it from being taken apart by your shell or use 
'_' (underscore) or ',' (comma) which also count as whitespace (e.g., midnight_Thu 
or midnight,Thu).~~

### TIME SPECIFICATION EXAMPLES

* **Oct 12** -- October 12 this year
* **-1month** or ~~**-1m**~~ **-1M** -- current time of day, only a month before (may yield surprises, see NOTE3 above).
* **noon yesterday-3hours** -- yesterday morning; can also be specified as 9am-1day.
* **23:59 31.12.1999** -- 1 minute to the year 2000.
* **12/31/99 11:59pm** -- 1 minute to the year 2000 for imperialists.
* **12am 01/01/01** -- start of the new millennium
* **end-3weeks** or **e-3w** -- 3 weeks before end time (may be used as start time specification).
* **start+6hours** or **s+6h** -- 6 hours after start time (may be used as end time specification).
* **931200300** -- 18:45 (UTC), July 5th, 1999 (yes, seconds since 1970 are valid as well).
* **19970703 12:45** -- 12:45 July 3th, 1997 (my favorite, and it has even got an ISO number (8601)).

