"""The edgetz corpus: curated real-world pathological datetimes.

Every case below is real. Time-zone cases were transcribed from the IANA time
zone database (transition instants, offsets to the second) and re-verified
against a host tzdata build (2025b) before shipping; calendar and epoch cases
are checkable with pure arithmetic. Nothing here is synthetic: each entry
names an event that actually bit production systems or is scheduled to.

Curation policy (also in ``docs/corpus-format.md``):

- ``why`` must name the bug class the case triggers, not restate the data.
- ``source`` records provenance (tzdata region file, IERS bulletin, spec).
- ``verify`` declares how ``edgetz verify`` can re-check the ground truth.
- Recurring traps (DST 2026) sit next to one-off history (Samoa 2011),
  because backfills and historical queries hit the old ones forever.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .model import Case

#: Category registry: slug -> one-line description of what bites you.
CATEGORIES: Dict[str, str] = {
    "dst-gap": "Wall-clock times that do not exist (spring-forward gaps).",
    "dst-fold": "Wall-clock times that exist twice (fall-back folds).",
    "missing-midnight": "Calendar dates that have no 00:00 because DST starts at midnight.",
    "skipped-date": "Entire calendar dates that never happened in a zone.",
    "offset-shift": "Permanent UTC-offset changes and odd offsets (:30, :45, seconds).",
    "weird-dst": "DST that is not one hour forward: 30-minute, 2-hour, negative, doubled.",
    "leap-day": "February 29 realities and the century years that lack one.",
    "week-53": "ISO week-date traps: 53-week years and week-year vs calendar-year drift.",
    "leap-second": "The 23:59:60 seconds that POSIX time cannot represent.",
    "epoch-boundary": "Integer-width and epoch-convention cliffs (2038, GPS, NTP, sentinels).",
}

#: Every leap second ever inserted (all positive so far), as
#: ``(UTC date carrying the 23:59:60 second, TAI-UTC after insertion)``.
#: Source: IERS Bulletin C. TAI-UTC has been 37 s since 2017-01-01.
LEAP_SECONDS: Tuple[Tuple[str, int], ...] = (
    ("1972-06-30", 11),
    ("1972-12-31", 12),
    ("1973-12-31", 13),
    ("1974-12-31", 14),
    ("1975-12-31", 15),
    ("1976-12-31", 16),
    ("1977-12-31", 17),
    ("1978-12-31", 18),
    ("1979-12-31", 19),
    ("1981-06-30", 20),
    ("1982-06-30", 21),
    ("1983-06-30", 22),
    ("1985-06-30", 23),
    ("1987-12-31", 24),
    ("1989-12-31", 25),
    ("1990-12-31", 26),
    ("1992-06-30", 27),
    ("1993-06-30", 28),
    ("1994-06-30", 29),
    ("1995-12-31", 30),
    ("1997-06-30", 31),
    ("1998-12-31", 32),
    ("2005-12-31", 33),
    ("2008-12-31", 34),
    ("2012-06-30", 35),
    ("2015-06-30", 36),
    ("2016-12-31", 37),
)

_CASES: Tuple[Case, ...] = (
    # ------------------------------------------------------------------
    # dst-gap: wall-clock times that do not exist
    # ------------------------------------------------------------------
    Case(
        id="gap-new-york-2026",
        category="dst-gap",
        zone="America/New_York",
        local="2026-03-08T02:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-05:00",
            "offset_after": "-04:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-03-08T07:00:00Z",
        },
        why=(
            "02:00-02:59:59 does not exist on this date; schedulers that add "
            "'same wall clock tomorrow' or parse a 02:30 log line land inside "
            "the hole and either crash or silently shift."
        ),
        source="IANA tzdata, northamerica (US rules, second Sunday in March)",
        tags=("recurring", "spring-forward", "usa"),
        verify="tzdata",
    ),
    Case(
        id="gap-london-2026",
        category="dst-gap",
        zone="Europe/London",
        local="2026-03-29T01:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+00:00",
            "offset_after": "+01:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-03-29T01:00:00Z",
        },
        why=(
            "London springs forward at 01:00 GMT, so 01:xx local is the hour "
            "that vanishes -- one hour earlier on the clock face than the US "
            "pattern, which breaks 'the gap is always 02:00' assumptions."
        ),
        source="IANA tzdata, europe (EU rules, last Sunday in March)",
        tags=("recurring", "spring-forward", "europe"),
        verify="tzdata",
    ),
    Case(
        id="gap-berlin-2026",
        category="dst-gap",
        zone="Europe/Berlin",
        local="2026-03-29T02:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+01:00",
            "offset_after": "+02:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-03-29T01:00:00Z",
        },
        why=(
            "All EU zones jump at the same UTC instant but at different "
            "wall-clock hours; a meeting recurring at 02:30 Berlin time has "
            "no valid start while 02:30 Lisbon time is fine."
        ),
        source="IANA tzdata, europe (EU rules, last Sunday in March)",
        tags=("recurring", "spring-forward", "europe"),
        verify="tzdata",
    ),
    Case(
        id="gap-sydney-2026",
        category="dst-gap",
        zone="Australia/Sydney",
        local="2026-10-04T02:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+10:00",
            "offset_after": "+11:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-10-03T16:00:00Z",
        },
        why=(
            "The southern hemisphere springs forward in October; any code or "
            "runbook that hard-codes 'DST changes happen in March and "
            "November' misses this transition entirely."
        ),
        source="IANA tzdata, australasia (AN rules, first Sunday in October)",
        tags=("recurring", "spring-forward", "southern-hemisphere"),
        verify="tzdata",
    ),
    Case(
        id="gap-casablanca-2026",
        category="dst-gap",
        zone="Africa/Casablanca",
        local="2026-03-22T02:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+00:00",
            "offset_after": "+01:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-03-22T02:00:00Z",
        },
        why=(
            "Morocco is permanently on +01 but drops to +00 for Ramadan, so "
            "the spring-forward date follows the lunar calendar and moves "
            "about 11 days earlier each year -- no fixed rule predicts it."
        ),
        source="IANA tzdata, africa (Morocco rules, Ramadan-driven)",
        tags=("recurring", "spring-forward", "ramadan"),
        verify="tzdata",
    ),
    Case(
        id="gap-new-york-war-time-1942",
        category="dst-gap",
        zone="America/New_York",
        local="1942-02-09T02:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-05:00",
            "offset_after": "-04:00",
            "gap_seconds": 3600,
            "transition_utc": "1942-02-09T07:00:00Z",
        },
        why=(
            "US 'War Time' started in February 1942 and stayed on year-round "
            "until 1945; historical data pipelines that assume pre-1966 "
            "timestamps are DST-free mislabel three years of records."
        ),
        source="IANA tzdata, northamerica (War Time, Act of Jan 20, 1942)",
        tags=("historical", "spring-forward", "war-time"),
        verify="tzdata",
    ),
    # ------------------------------------------------------------------
    # dst-fold: wall-clock times that exist twice
    # ------------------------------------------------------------------
    Case(
        id="fold-new-york-2026",
        category="dst-fold",
        zone="America/New_York",
        local="2026-11-01T01:30:00",
        utc=("2026-11-01T05:30:00Z", "2026-11-01T06:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "-04:00",
            "offset_after": "-05:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-11-01T06:00:00Z",
        },
        why=(
            "01:30 happens twice, one hour apart; naive-datetime "
            "deduplication keys collide, and 'parse local, convert to UTC' "
            "silently picks one of two instants without telling you."
        ),
        source="IANA tzdata, northamerica (US rules, first Sunday in November)",
        tags=("recurring", "fall-back", "usa"),
        verify="tzdata",
    ),
    Case(
        id="fold-london-2026",
        category="dst-fold",
        zone="Europe/London",
        local="2026-10-25T01:30:00",
        utc=("2026-10-25T00:30:00Z", "2026-10-25T01:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+01:00",
            "offset_after": "+00:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-10-25T01:00:00Z",
        },
        why=(
            "The second occurrence of 01:30 London time equals 01:30 UTC, so "
            "spot-checking 'local == UTC, must be winter' passes for a "
            "timestamp recorded during the ambiguous hour on the DST side."
        ),
        source="IANA tzdata, europe (EU rules, last Sunday in October)",
        tags=("recurring", "fall-back", "europe"),
        verify="tzdata",
    ),
    Case(
        id="fold-berlin-2026",
        category="dst-fold",
        zone="Europe/Berlin",
        local="2026-10-25T02:30:00",
        utc=("2026-10-25T00:30:00Z", "2026-10-25T01:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+02:00",
            "offset_after": "+01:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-10-25T01:00:00Z",
        },
        why=(
            "A cron job scheduled at 02:30 local fires twice on this date "
            "unless the scheduler resolves folds; invoice and report "
            "generators are the classic double-run victims."
        ),
        source="IANA tzdata, europe (EU rules, last Sunday in October)",
        tags=("recurring", "fall-back", "europe"),
        verify="tzdata",
    ),
    Case(
        id="fold-sydney-2026",
        category="dst-fold",
        zone="Australia/Sydney",
        local="2026-04-05T02:30:00",
        utc=("2026-04-04T15:30:00Z", "2026-04-04T16:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+11:00",
            "offset_after": "+10:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-04-04T16:00:00Z",
        },
        why=(
            "Both occurrences of this local time fall on the previous UTC "
            "date, so day-bucketed aggregations disagree with local reports "
            "and the fold doubles a bucket that is already off by one day."
        ),
        source="IANA tzdata, australasia (AN rules, first Sunday in April)",
        tags=("recurring", "fall-back", "southern-hemisphere", "date-boundary"),
        verify="tzdata",
    ),
    Case(
        id="fold-havana-double-midnight-2026",
        category="dst-fold",
        zone="America/Havana",
        local="2026-11-01T00:00:00",
        utc=("2026-11-01T04:00:00Z", "2026-11-01T05:00:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "-04:00",
            "offset_after": "-05:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-11-01T05:00:00Z",
        },
        why=(
            "Cuba falls back at 01:00, so midnight itself occurs twice: the "
            "date boundary fires two times, and 'run once at 00:00' jobs "
            "double-execute on a 25-hour day that starts twice."
        ),
        source="IANA tzdata, northamerica (Cuba rules)",
        tags=("recurring", "fall-back", "double-midnight", "date-boundary"),
        verify="tzdata",
    ),
    Case(
        id="fold-santiago-day-ends-twice-2026",
        category="dst-fold",
        zone="America/Santiago",
        local="2026-04-04T23:30:00",
        utc=("2026-04-05T02:30:00Z", "2026-04-05T03:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "-03:00",
            "offset_after": "-04:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-04-05T03:00:00Z",
        },
        why=(
            "Chile falls back at 24:00, so 23:00-23:59 repeats and April 4 "
            "ends twice; end-of-day batch jobs double-fire and 'last event "
            "of the day' queries return two different answers."
        ),
        source="IANA tzdata, southamerica (Chile rules)",
        tags=("recurring", "fall-back", "date-boundary"),
        verify="tzdata",
    ),
    Case(
        id="fold-casablanca-ramadan-2026",
        category="dst-fold",
        zone="Africa/Casablanca",
        local="2026-02-15T02:30:00",
        utc=("2026-02-15T01:30:00Z", "2026-02-15T02:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+01:00",
            "offset_after": "+00:00",
            "fold_seconds": 3600,
            "transition_utc": "2026-02-15T02:00:00Z",
        },
        why=(
            "A fall-back in February: Morocco leaves its permanent +01 for "
            "Ramadan, inverting every 'clocks only change in spring and "
            "autumn' calendar assumption baked into ops tooling."
        ),
        source="IANA tzdata, africa (Morocco rules, Ramadan-driven)",
        tags=("recurring", "fall-back", "ramadan"),
        verify="tzdata",
    ),
    # ------------------------------------------------------------------
    # missing-midnight: dates that have no 00:00
    # ------------------------------------------------------------------
    Case(
        id="no-midnight-santiago-2026",
        category="missing-midnight",
        zone="America/Santiago",
        local="2026-09-06T00:00:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-04:00",
            "offset_after": "-03:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-09-06T04:00:00Z",
            "first_valid_local": "2026-09-06T01:00:00",
        },
        why=(
            "Chile springs forward at 24:00, so this date starts at 01:00; "
            "datetime.combine(date, time()) and 'midnight cron' both "
            "construct a time that does not exist."
        ),
        source="IANA tzdata, southamerica (Chile rules)",
        tags=("recurring", "spring-forward", "midnight"),
        verify="tzdata",
    ),
    Case(
        id="no-midnight-sao-paulo-2018",
        category="missing-midnight",
        zone="America/Sao_Paulo",
        local="2018-11-04T00:00:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-03:00",
            "offset_after": "-02:00",
            "gap_seconds": 3600,
            "transition_utc": "2018-11-04T03:00:00Z",
            "first_valid_local": "2018-11-04T01:00:00",
        },
        why=(
            "Brazil abolished DST in 2019, but every backfill, replay, or "
            "historical query touching November 2018 still has to survive a "
            "date whose midnight never existed."
        ),
        source="IANA tzdata, southamerica (Brazil rules, abolished 2019)",
        tags=("historical", "spring-forward", "midnight"),
        verify="tzdata",
    ),
    Case(
        id="no-midnight-havana-2026",
        category="missing-midnight",
        zone="America/Havana",
        local="2026-03-08T00:00:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-05:00",
            "offset_after": "-04:00",
            "gap_seconds": 3600,
            "transition_utc": "2026-03-08T05:00:00Z",
            "first_valid_local": "2026-03-08T01:00:00",
        },
        why=(
            "Cuba springs forward at 00:00, so the calendar day both begins "
            "at 01:00 in March and gains a second midnight in November -- "
            "one zone that breaks both halves of a date-boundary scheduler."
        ),
        source="IANA tzdata, northamerica (Cuba rules)",
        tags=("recurring", "spring-forward", "midnight"),
        verify="tzdata",
    ),
    Case(
        id="no-midnight-tehran-2022",
        category="missing-midnight",
        zone="Asia/Tehran",
        local="2022-03-22T00:00:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+03:30",
            "offset_after": "+04:30",
            "gap_seconds": 3600,
            "transition_utc": "2022-03-21T20:30:00Z",
            "first_valid_local": "2022-03-22T01:00:00",
        },
        why=(
            "Iran's last-ever spring forward (DST abolished later in 2022) "
            "jumped from a :30 base offset at midnight: half-hour offsets "
            "and a missing midnight in one timestamp."
        ),
        source="IANA tzdata, asia (Iran rules, DST abolished 2022)",
        tags=("historical", "spring-forward", "midnight", "half-hour-offset"),
        verify="tzdata",
    ),
    # ------------------------------------------------------------------
    # skipped-date: whole calendar dates that never happened
    # ------------------------------------------------------------------
    Case(
        id="skip-samoa-2011-12-30",
        category="skipped-date",
        zone="Pacific/Apia",
        local="2011-12-30T12:00:00",
        utc=(),
        expect={
            "kind": "skipped-date",
            "date": "2011-12-30",
            "offset_before": "-10:00",
            "offset_after": "+14:00",
            "gap_seconds": 86400,
            "transition_utc": "2011-12-30T10:00:00Z",
        },
        why=(
            "Samoa crossed the date line westward: Thursday Dec 29 was "
            "followed by Saturday Dec 31. Age, billing-period, and "
            "days-between code that assumes every local date exists is off "
            "by one forever. Both offsets shown include DST (-10 = DST of "
            "-11; +14 = DST of +13)."
        ),
        source="IANA tzdata, australasia (Samoa date-line change, 2011)",
        tags=("historical", "date-line", "one-off"),
        verify="tzdata",
    ),
    Case(
        id="skip-kwajalein-1993-08-21",
        category="skipped-date",
        zone="Pacific/Kwajalein",
        local="1993-08-21T12:00:00",
        utc=(),
        expect={
            "kind": "skipped-date",
            "date": "1993-08-21",
            "offset_before": "-12:00",
            "offset_after": "+12:00",
            "gap_seconds": 86400,
            "transition_utc": "1993-08-21T12:00:00Z",
        },
        why=(
            "Kwajalein hopped from the extreme east (-12:00) to the extreme "
            "west (+12:00) of the date line, deleting a Saturday; the same "
            "UTC instant maps to local dates a full day apart across the "
            "transition."
        ),
        source="IANA tzdata, australasia (Marshall Islands realignment, 1993)",
        tags=("historical", "date-line", "one-off", "extreme-offset"),
        verify="tzdata",
    ),
    Case(
        id="skip-kiritimati-1994-12-31",
        category="skipped-date",
        zone="Pacific/Kiritimati",
        local="1994-12-31T12:00:00",
        utc=(),
        expect={
            "kind": "skipped-date",
            "date": "1994-12-31",
            "offset_before": "-10:00",
            "offset_after": "+14:00",
            "gap_seconds": 86400,
            "transition_utc": "1994-12-31T10:00:00Z",
        },
        why=(
            "Kiribati skipped New Year's Eve 1994 and invented UTC+14, the "
            "largest offset in use; offset validators capped at +12 or +13 "
            "reject real present-day timestamps from this zone."
        ),
        source="IANA tzdata, australasia (Kiribati realignment, 1994/1995)",
        tags=("historical", "date-line", "one-off", "extreme-offset"),
        verify="tzdata",
    ),
    # ------------------------------------------------------------------
    # offset-shift: permanent changes and odd offsets
    # ------------------------------------------------------------------
    Case(
        id="shift-monrovia-1972",
        category="offset-shift",
        zone="Africa/Monrovia",
        local="1972-01-07T00:20:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-00:44:30",
            "offset_after": "+00:00",
            "gap_seconds": 2670,
            "transition_utc": "1972-01-07T00:44:30Z",
            "first_valid_local": "1972-01-07T00:44:30",
        },
        why=(
            "Liberia ran at -00:44:30 (seconds precision!) until 1972, then "
            "jumped to GMT: a 44.5-minute gap, a date with no midnight, and "
            "an offset that HH:MM-only parsers cannot even represent."
        ),
        source="IANA tzdata, africa (Liberia standardization, 1972)",
        tags=("historical", "seconds-offset", "midnight", "one-off"),
        verify="tzdata",
    ),
    Case(
        id="shift-kathmandu-1986",
        category="offset-shift",
        zone="Asia/Kathmandu",
        local="1986-01-01T00:10:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+05:30",
            "offset_after": "+05:45",
            "gap_seconds": 900,
            "transition_utc": "1985-12-31T18:30:00Z",
            "first_valid_local": "1986-01-01T00:15:00",
        },
        why=(
            "Nepal moved to +05:45 at midnight into 1986: New Year's Day "
            "began at 00:15, and the world's strangest active offset was "
            "born -- :45 offsets still break quarter-hour-naive code today."
        ),
        source="IANA tzdata, asia (Nepal offset change, 1986)",
        tags=("historical", "45-minute-offset", "midnight", "new-year"),
        verify="tzdata",
    ),
    Case(
        id="shift-caracas-2007",
        category="offset-shift",
        zone="America/Caracas",
        local="2007-12-09T02:45:00",
        utc=("2007-12-09T06:45:00Z", "2007-12-09T07:15:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "-04:00",
            "offset_after": "-04:30",
            "fold_seconds": 1800,
            "transition_utc": "2007-12-09T07:00:00Z",
        },
        why=(
            "Venezuela moved to -04:30 by decree with weeks of notice: a "
            "30-minute fold in December, outside any DST calendar, in a "
            "zone most systems had cached as whole-hour."
        ),
        source="IANA tzdata, southamerica (Venezuela decree, 2007)",
        tags=("historical", "half-hour-offset", "political", "one-off"),
        verify="tzdata",
    ),
    Case(
        id="shift-caracas-2016",
        category="offset-shift",
        zone="America/Caracas",
        local="2016-05-01T02:45:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "-04:30",
            "offset_after": "-04:00",
            "gap_seconds": 1800,
            "transition_utc": "2016-05-01T07:00:00Z",
        },
        why=(
            "The 2007 change was reversed in 2016, creating a 30-minute gap "
            "on a Sunday in May; timestamps recorded between the two "
            "decrees replay wrongly on systems with stale tzdata."
        ),
        source="IANA tzdata, southamerica (Venezuela decree, 2016)",
        tags=("historical", "half-hour-offset", "political", "one-off"),
        verify="tzdata",
    ),
    Case(
        id="shift-pyongyang-2015",
        category="offset-shift",
        zone="Asia/Pyongyang",
        local="2015-08-14T23:45:00",
        utc=("2015-08-14T14:45:00Z", "2015-08-14T15:15:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+09:00",
            "offset_after": "+08:30",
            "fold_seconds": 1800,
            "transition_utc": "2015-08-14T15:00:00Z",
        },
        why=(
            "North Korea created +08:30 with about a week of public notice: "
            "August 14 ends twice, and devices that had not shipped a "
            "tzdata update in that week wrote wrong offsets."
        ),
        source="IANA tzdata, asia (Pyongyang Time introduced, 2015)",
        tags=("historical", "half-hour-offset", "political", "date-boundary"),
        verify="tzdata",
    ),
    Case(
        id="shift-pyongyang-2018",
        category="offset-shift",
        zone="Asia/Pyongyang",
        local="2018-05-04T23:45:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+08:30",
            "offset_after": "+09:00",
            "gap_seconds": 1800,
            "transition_utc": "2018-05-04T15:00:00Z",
        },
        why=(
            "The reversal in 2018 deleted the last 30 minutes of May 4: the "
            "day ends at 23:29:59, so 'append a 23:59:59 end-of-day "
            "timestamp' produces a time that never existed."
        ),
        source="IANA tzdata, asia (Pyongyang Time reverted, 2018)",
        tags=("historical", "half-hour-offset", "political", "date-boundary"),
        verify="tzdata",
    ),
    Case(
        id="extreme-kiritimati-plus14",
        category="offset-shift",
        zone="Pacific/Kiritimati",
        local="2026-01-01T00:00:00",
        utc=("2025-12-31T10:00:00Z",),
        expect={
            "kind": "extreme-offset",
            "offset": "+14:00",
            "aoe_equivalent": "2025-12-30T22:00:00-12:00",
        },
        why=(
            "New Year arrives at UTC+14 while it is still Dec 30 in "
            "Anywhere-on-Earth (-12): the same instant spans three calendar "
            "dates of wall clock, and any given date is 'today' somewhere "
            "for 50 straight hours."
        ),
        source="IANA tzdata, australasia (Line Islands, UTC+14 since 1995)",
        tags=("recurring", "extreme-offset", "date-line", "new-year"),
        verify="tzdata",
    ),
    # ------------------------------------------------------------------
    # weird-dst: DST that is not one hour forward
    # ------------------------------------------------------------------
    Case(
        id="weird-lord-howe-gap-2026",
        category="weird-dst",
        zone="Australia/Lord_Howe",
        local="2026-10-04T02:15:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+10:30",
            "offset_after": "+11:00",
            "gap_seconds": 1800,
            "transition_utc": "2026-10-03T15:30:00Z",
        },
        why=(
            "Lord Howe Island observes 30-minute DST from a +10:30 base; "
            "code that models DST as 'plus one hour' computes offsets that "
            "are wrong by 30 minutes for half the year."
        ),
        source="IANA tzdata, australasia (Lord Howe Island rules)",
        tags=("recurring", "half-hour-dst", "spring-forward"),
        verify="tzdata",
    ),
    Case(
        id="weird-lord-howe-fold-2026",
        category="weird-dst",
        zone="Australia/Lord_Howe",
        local="2026-04-05T01:45:00",
        utc=("2026-04-04T14:45:00Z", "2026-04-04T15:15:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+11:00",
            "offset_after": "+10:30",
            "fold_seconds": 1800,
            "transition_utc": "2026-04-04T15:00:00Z",
        },
        why=(
            "The matching 30-minute fold: the two occurrences of 01:45 are "
            "only half an hour apart, tight enough to slip inside clock-skew "
            "tolerances and pass sanity checks that would catch a full hour."
        ),
        source="IANA tzdata, australasia (Lord Howe Island rules)",
        tags=("recurring", "half-hour-dst", "fall-back"),
        verify="tzdata",
    ),
    Case(
        id="weird-troll-gap-2026",
        category="weird-dst",
        zone="Antarctica/Troll",
        local="2026-03-29T02:00:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+00:00",
            "offset_after": "+02:00",
            "gap_seconds": 7200,
            "transition_utc": "2026-03-29T01:00:00Z",
        },
        why=(
            "Norway's Troll research station jumps two full hours (+00 to "
            "+02) each spring -- the only 2-hour DST in tzdata; 'the gap is "
            "exactly one hour' fallback logic lands inside the hole it was "
            "supposed to escape."
        ),
        source="IANA tzdata, antarctica (Troll station rules)",
        tags=("recurring", "two-hour-dst", "spring-forward", "antarctica"),
        verify="tzdata",
    ),
    Case(
        id="weird-troll-fold-2026",
        category="weird-dst",
        zone="Antarctica/Troll",
        local="2026-10-25T02:00:00",
        utc=("2026-10-25T00:00:00Z", "2026-10-25T02:00:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+02:00",
            "offset_after": "+00:00",
            "fold_seconds": 7200,
            "transition_utc": "2026-10-25T01:00:00Z",
        },
        why=(
            "The matching 2-hour fold: 01:00-02:59 repeats, and the same "
            "wall clock maps to instants two hours apart -- far outside the "
            "one-hour ambiguity window most fold-resolution code assumes."
        ),
        source="IANA tzdata, antarctica (Troll station rules)",
        tags=("recurring", "two-hour-dst", "fall-back", "antarctica"),
        verify="tzdata",
    ),
    Case(
        id="weird-chatham-fold-2026",
        category="weird-dst",
        zone="Pacific/Chatham",
        local="2026-04-05T03:15:00",
        utc=("2026-04-04T13:30:00Z", "2026-04-04T14:30:00Z"),
        expect={
            "kind": "fold",
            "offset_before": "+13:45",
            "offset_after": "+12:45",
            "fold_seconds": 3600,
            "transition_utc": "2026-04-04T14:00:00Z",
        },
        why=(
            "The Chatham Islands run at +12:45/+13:45 -- the only :45 zone "
            "with DST; every stage of a pipeline (parse, store, display) "
            "must carry quarter-hour offsets through a fold correctly."
        ),
        source="IANA tzdata, australasia (Chatham Islands rules)",
        tags=("recurring", "45-minute-offset", "fall-back"),
        verify="tzdata",
    ),
    Case(
        id="weird-dublin-negative-dst",
        category="weird-dst",
        zone="Europe/Dublin",
        local="2026-01-15T12:00:00",
        utc=("2026-01-15T12:00:00Z",),
        expect={
            "kind": "negative-dst",
            "probe_winter": "2026-01-15T12:00:00",
            "offset_winter": "+00:00",
            "tzname_winter": "GMT",
            "probe_summer": "2026-07-15T12:00:00",
            "offset_summer": "+01:00",
            "tzname_summer": "IST",
        },
        why=(
            "tzdata models Irish Standard Time (+01) as the standard and "
            "winter as DST with SAVE -1:00, so libraries reading vanguard "
            "data report a negative dst() in January; assertions like "
            "dst() >= 0 or is_dst == (offset > standard) both break."
        ),
        source="IANA tzdata, europe (Ireland, negative SAVE since 2018a)",
        tags=("recurring", "negative-dst", "modeling-trap"),
        verify="tzdata",
    ),
    Case(
        id="weird-london-double-summer-1941",
        category="weird-dst",
        zone="Europe/London",
        local="1941-05-04T02:30:00",
        utc=(),
        expect={
            "kind": "gap",
            "offset_before": "+01:00",
            "offset_after": "+02:00",
            "gap_seconds": 3600,
            "transition_utc": "1941-05-04T01:00:00Z",
        },
        why=(
            "British Double Summer Time put London on +02 -- two hours ahead "
            "of its 'standard' GMT -- and the UK never returned to GMT that "
            "winter; wartime records need two stacked DST offsets to decode."
        ),
        source="IANA tzdata, europe (British Double Summer Time, 1941-1945)",
        tags=("historical", "double-dst", "war-time", "spring-forward"),
        verify="tzdata",
    ),
    # ------------------------------------------------------------------
    # leap-day: February 29 and its impostors
    # ------------------------------------------------------------------
    Case(
        id="leap-day-2024",
        category="leap-day",
        local="2024-02-29T00:00:00",
        utc=(),
        expect={"kind": "leap-day", "valid": True, "reason": "divisible-by-4"},
        why=(
            "The ordinary leap day that still ships outages every four "
            "years: hardcoded 'YYYY-02-28 is the last day of February' "
            "logic, 365-day year math, and certificate-expiry arithmetic "
            "all resurface on this date."
        ),
        source="Gregorian calendar rules (Inter gravissimas, 1582)",
        tags=("recurring", "february-29"),
        verify="calendar",
    ),
    Case(
        id="leap-day-2000",
        category="leap-day",
        local="2000-02-29T00:00:00",
        utc=(),
        expect={"kind": "leap-day", "valid": True, "reason": "divisible-by-400"},
        why=(
            "2000 was a leap year only because of the divisible-by-400 "
            "exception-to-the-exception; implementations that stopped at "
            "'centuries are not leap years' skipped a day that exists."
        ),
        source="Gregorian calendar rules (Inter gravissimas, 1582)",
        tags=("historical", "february-29", "century-rule"),
        verify="calendar",
    ),
    Case(
        id="leap-day-1900-invalid",
        category="leap-day",
        literal="1900-02-29",
        expect={"kind": "leap-day", "valid": False, "reason": "divisible-by-100-not-400"},
        why=(
            "1900-02-29 never happened, yet spreadsheet serial-date systems "
            "treat it as day 60 for Lotus 1-2-3 compatibility; every "
            "spreadsheet import/export layer must decide whether to "
            "reproduce or reject the phantom day."
        ),
        source="Gregorian calendar rules; spreadsheet serial-date lore",
        tags=("historical", "february-29", "century-rule", "spreadsheet"),
        verify="calendar",
    ),
    Case(
        id="leap-day-2100-invalid",
        category="leap-day",
        literal="2100-02-29",
        expect={"kind": "leap-day", "valid": False, "reason": "divisible-by-100-not-400"},
        why=(
            "The next phantom leap day: 2100 is not a leap year, and "
            "long-dated instruments (mortgages, bonds, 99-year leases) "
            "already compute schedules across it with 'every 4 years' "
            "shortcuts that will be wrong."
        ),
        source="Gregorian calendar rules (Inter gravissimas, 1582)",
        tags=("future", "february-29", "century-rule"),
        verify="calendar",
    ),
    Case(
        id="leap-day-plus-one-year",
        category="leap-day",
        local="2024-02-29T00:00:00",
        utc=(),
        expect={
            "kind": "leap-day",
            "valid": True,
            "reason": "divisible-by-4",
            "anniversary_candidates": ["2025-02-28", "2025-03-01"],
        },
        why=(
            "Feb 29 plus 'one year' has no single answer: libraries clamp "
            "to Feb 28, roll to Mar 1, or raise -- so birthdays, contract "
            "anniversaries, and subscription renewals silently diverge "
            "between systems."
        ),
        source="Gregorian calendar rules; divergent library conventions",
        tags=("recurring", "february-29", "arithmetic"),
        verify="calendar",
    ),
    Case(
        id="leap-day-sweden-1712",
        category="leap-day",
        literal="1712-02-30",
        expect={"kind": "leap-day", "valid": False, "reason": "swedish-calendar-only"},
        why=(
            "Sweden's botched Julian-to-Gregorian migration produced a real "
            "February 30 in 1712 -- proof that 'Feb 30 is always invalid' "
            "is a Gregorian-only truth; it also makes a handy "
            "guaranteed-unparseable probe string."
        ),
        source="Swedish calendar, 1700-1712 (outside tzdata's model)",
        tags=("historical", "february-30", "calendar-reform"),
        verify="none",
    ),
    # ------------------------------------------------------------------
    # week-53: ISO week-date traps
    # ------------------------------------------------------------------
    Case(
        id="week53-2020",
        category="week-53",
        local="2020-12-31T00:00:00",
        utc=(),
        expect={"kind": "iso-week", "iso_year": 2020, "iso_week": 53, "iso_weekday": 4},
        why=(
            "2020 had 53 ISO weeks; fixed-size 'weeks[52]' buffers, "
            "week-indexed partitions, and yearly KPI comparisons that "
            "assume 52 columns all overflow or misalign."
        ),
        source="ISO 8601 week-date rules",
        tags=("historical", "53-week-year"),
        verify="calendar",
    ),
    Case(
        id="week53-2026",
        category="week-53",
        local="2026-12-31T00:00:00",
        utc=(),
        expect={"kind": "iso-week", "iso_year": 2026, "iso_week": 53, "iso_weekday": 4},
        why=(
            "The current 53-week year: any dashboard, payroll calendar, or "
            "forecast comparing 'week N this year vs last year' needs an "
            "answer for week 53 of 2026 that 2025 does not have."
        ),
        source="ISO 8601 week-date rules",
        tags=("recurring", "53-week-year"),
        verify="calendar",
    ),
    Case(
        id="week-mismatch-jan-2021",
        category="week-53",
        local="2021-01-01T00:00:00",
        utc=(),
        expect={"kind": "iso-week", "iso_year": 2020, "iso_week": 53, "iso_weekday": 5},
        why=(
            "January 1, 2021 belongs to ISO year 2020: formatting it with a "
            "week-year pattern (YYYY in Java/Swift, %G in strftime) instead "
            "of the calendar year prints '2020' -- the classic new-year "
            "display bug."
        ),
        source="ISO 8601 week-date rules",
        tags=("historical", "week-year-mismatch", "new-year"),
        verify="calendar",
    ),
    Case(
        id="week-mismatch-dec-2024",
        category="week-53",
        local="2024-12-31T00:00:00",
        utc=(),
        expect={"kind": "iso-week", "iso_year": 2025, "iso_week": 1, "iso_weekday": 2},
        why=(
            "December 31, 2024 is already ISO week 1 of 2025 -- the "
            "mirror-image trap: week-year formatting jumps ahead before New "
            "Year's Eve, the exact shape of the historical "
            "week-year-in-December outages."
        ),
        source="ISO 8601 week-date rules",
        tags=("historical", "week-year-mismatch", "new-year"),
        verify="calendar",
    ),
    Case(
        id="week1-starts-in-december-2025",
        category="week-53",
        local="2025-12-29T00:00:00",
        utc=(),
        expect={"kind": "iso-week", "iso_year": 2026, "iso_week": 1, "iso_weekday": 1},
        why=(
            "ISO week 1 of 2026 starts on Monday, December 29, 2025: "
            "week-partitioned storage puts late-December rows in next "
            "year's partition, and 'this year's weeks' queries silently "
            "drop them."
        ),
        source="ISO 8601 week-date rules",
        tags=("recurring", "week-year-mismatch", "partitioning"),
        verify="calendar",
    ),
    # ------------------------------------------------------------------
    # leap-second: the 61st second
    # ------------------------------------------------------------------
    Case(
        id="leap-second-2016",
        category="leap-second",
        literal="2016-12-31T23:59:60Z",
        expect={
            "kind": "leap-second",
            "utc_date": "2016-12-31",
            "tai_utc_after": 37,
            "next_utc": "2017-01-01T00:00:00Z",
        },
        why=(
            "The most recent leap second: a real, broadcast timestamp that "
            "ISO parsers in most languages reject outright; POSIX clocks "
            "replayed 23:59:59 twice instead, so identical epoch seconds "
            "cover two real seconds."
        ),
        source="IERS Bulletin C 52",
        tags=("historical", "second-60", "new-year"),
        verify="calendar",
    ),
    Case(
        id="leap-second-2015",
        category="leap-second",
        literal="2015-06-30T23:59:60Z",
        expect={
            "kind": "leap-second",
            "utc_date": "2015-06-30",
            "tai_utc_after": 36,
            "next_utc": "2015-07-01T00:00:00Z",
        },
        why=(
            "A mid-year leap second: it lands at the end of June, so 'leap "
            "seconds only happen on New Year's Eve' filters miss it, and it "
            "arrived during market hours in Asia-Pacific."
        ),
        source="IERS Bulletin C 49",
        tags=("historical", "second-60", "mid-year"),
        verify="calendar",
    ),
    Case(
        id="leap-second-2012",
        category="leap-second",
        literal="2012-06-30T23:59:60Z",
        expect={
            "kind": "leap-second",
            "utc_date": "2012-06-30",
            "tai_utc_after": 35,
            "next_utc": "2012-07-01T00:00:00Z",
        },
        why=(
            "The famous one: the 2012 insertion triggered a Linux kernel "
            "livelock that took down airline reservation systems and major "
            "websites -- the canonical case for smearing or pausing around "
            "insertions."
        ),
        source="IERS Bulletin C 43",
        tags=("historical", "second-60", "outage"),
        verify="calendar",
    ),
    Case(
        id="leap-second-tokyo-2017",
        category="leap-second",
        zone="Asia/Tokyo",
        literal="2017-01-01T08:59:60+09:00",
        expect={
            "kind": "leap-second",
            "utc_date": "2016-12-31",
            "tai_utc_after": 37,
            "next_utc": "2017-01-01T00:00:00Z",
        },
        why=(
            "The 2016 leap second as Tokyo saw it: 08:59:60 on the morning "
            "of January 1 -- validators that only allow :60 at 23:59 UTC "
            "shapes reject a correctly-written local timestamp."
        ),
        source="IERS Bulletin C 52; JST is UTC+09:00",
        tags=("historical", "second-60", "local-representation"),
        verify="calendar",
    ),
    # ------------------------------------------------------------------
    # epoch-boundary: integer cliffs and sentinel instants
    # ------------------------------------------------------------------
    Case(
        id="epoch-unix-zero",
        category="epoch-boundary",
        utc=("1970-01-01T00:00:00Z",),
        expect={"kind": "epoch", "unix_seconds": 0},
        why=(
            "Epoch zero is where nulls go to be reborn: uninitialized "
            "fields render as 1970-01-01 (or 1969-12-31 across the date "
            "line), so a cluster of records 'created in 1970' almost always "
            "means missing data, not history."
        ),
        source="POSIX epoch definition (IEEE 1003.1)",
        tags=("sentinel", "unix-epoch"),
        verify="calendar",
    ),
    Case(
        id="epoch-minus-one",
        category="epoch-boundary",
        utc=("1969-12-31T23:59:59Z",),
        expect={"kind": "epoch", "unix_seconds": -1},
        why=(
            "The instant one second before the epoch is also the integer "
            "-1, the error return of C time APIs: a legitimate 1969 "
            "timestamp is indistinguishable from failure, and stores that "
            "reject negative epochs cannot hold it at all."
        ),
        source="POSIX epoch definition; C time_t error convention",
        tags=("sentinel", "negative-epoch", "pre-epoch"),
        verify="calendar",
    ),
    Case(
        id="y2k38-int32-max",
        category="epoch-boundary",
        utc=("2038-01-19T03:14:07Z",),
        expect={"kind": "epoch", "unix_seconds": 2147483647},
        why=(
            "The last second a signed 32-bit time_t can hold. Anything "
            "computing a future date past it today -- 15-year mortgages, "
            "20-year certificates -- already overflows on 32-bit fields "
            "long before 2038 arrives."
        ),
        source="Signed 32-bit time_t arithmetic",
        tags=("future", "int32", "y2k38"),
        verify="calendar",
    ),
    Case(
        id="y2k38-wraparound",
        category="epoch-boundary",
        utc=("2038-01-19T03:14:08Z",),
        expect={
            "kind": "epoch",
            "unix_seconds": 2147483648,
            "wrapped_int32_utc": "1901-12-13T20:45:52Z",
        },
        why=(
            "One second later, a wrapping 32-bit counter reads "
            "-2147483648: December 13, 1901. Timestamps that jump 136 "
            "years into the past are the signature of this overflow in "
            "logs, databases, and embedded devices."
        ),
        source="Signed 32-bit time_t arithmetic (two's complement wrap)",
        tags=("future", "int32", "y2k38", "wraparound"),
        verify="calendar",
    ),
    Case(
        id="gps-week-rollover-2019",
        category="epoch-boundary",
        utc=("2019-04-06T23:59:42Z",),
        expect={"kind": "epoch", "unix_seconds": 1554595182},
        why=(
            "GPS week numbers are 10 bits: at this instant week 1023 rolled "
            "to week 0 and unpatched receivers jumped to 1999, feeding "
            "20-year-old timestamps into anything trusting GPS time. The "
            "42-second lag from midnight is the GPS-UTC leap-second offset."
        ),
        source="GPS ICD-200 (10-bit week number); rollover of 2019-04-06/07",
        tags=("historical", "rollover", "gps"),
        verify="calendar",
    ),
    Case(
        id="ntp-era0-end-2036",
        category="epoch-boundary",
        utc=("2036-02-07T06:28:16Z",),
        expect={"kind": "epoch", "unix_seconds": 2085978496},
        why=(
            "NTP's 32-bit seconds count from 1900 wraps here -- two years "
            "before Y2K38, so time-sync infrastructure hits its cliff "
            "first; era-unaware NTP consumers will see 1900 and slew clocks "
            "violently."
        ),
        source="RFC 5905 (NTP era 0 ends 2^32 s after 1900-01-01)",
        tags=("future", "rollover", "ntp"),
        verify="calendar",
    ),
    Case(
        id="cocoa-epoch-2001",
        category="epoch-boundary",
        utc=("2001-01-01T00:00:00Z",),
        expect={"kind": "epoch", "unix_seconds": 978307200},
        why=(
            "Apple's reference date is 2001-01-01, so a raw number crossing "
            "an ecosystem boundary is ambiguous by 31 years: Cocoa seconds "
            "read as Unix seconds put events in 2001 when they happened "
            "today."
        ),
        source="Core Foundation absolute time reference date",
        tags=("sentinel", "epoch-confusion", "apple"),
        verify="calendar",
    ),
    Case(
        id="datetime-max-9999",
        category="epoch-boundary",
        utc=("9999-12-31T23:59:59Z",),
        expect={"kind": "epoch", "unix_seconds": 253402300799},
        why=(
            "The ceiling of four-digit-year systems (Python datetime.max, "
            ".NET DateTime.MaxValue, SQL 'forever' sentinels): adding any "
            "duration to it overflows, and 'no expiry' rows stored this way "
            "explode in date arithmetic."
        ),
        source="ISO 8601 four-digit year range; stdlib datetime.max",
        tags=("sentinel", "overflow", "max-value"),
        verify="calendar",
    ),
    Case(
        id="datetime-min-0001",
        category="epoch-boundary",
        utc=("0001-01-01T00:00:00Z",),
        expect={"kind": "epoch", "unix_seconds": -62135596800},
        why=(
            "The floor of the proleptic Gregorian calendar (Python "
            "datetime.min, .NET DateTime.MinValue): converting it into any "
            "zone west of Greenwich underflows the representable range and "
            "raises where a plain default value was expected."
        ),
        source="Proleptic Gregorian calendar; stdlib datetime.min",
        tags=("sentinel", "underflow", "min-value"),
        verify="calendar",
    ),
)


def all_cases() -> Tuple[Case, ...]:
    """Return the full corpus in stable, category-grouped order."""
    return _CASES
