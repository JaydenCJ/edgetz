"""Independent re-derivations of the corpus's calendar and epoch claims.

test_verify.py trusts edgetz's own checkers; this file re-proves the same
facts directly with the stdlib, so a bug in the verify engine cannot mask a
bug in the corpus (two independent witnesses per claim).
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone

import pytest

import edgetz

UTC = timezone.utc


def test_century_leap_year_rule_1900_2000_2100():
    # The pair of traps: 1900 and 2100 (divisible by 100) no, 2000 (by 400) yes.
    assert calendar.isleap(2000) and calendar.isleap(2024)
    assert not calendar.isleap(1900) and not calendar.isleap(2100)
    with pytest.raises(ValueError):
        date(1900, 2, 29)
    with pytest.raises(ValueError):
        date(2100, 2, 29)


def test_feb_29_plus_365_days_is_feb_28():
    # One flavor of "+1 year"; the corpus documents how libraries diverge.
    assert date(2024, 2, 29) + timedelta(days=365) == date(2025, 2, 28)


def test_53_week_years_in_corpus_really_have_53_weeks():
    for item in edgetz.cases(tag="53-week-year"):
        year = item.expect["iso_year"]
        # Dec 28 is always in the year's last ISO week, by construction.
        assert date(year, 12, 28).isocalendar()[1] == 53


def test_week_year_diverges_from_calendar_year_at_both_ends():
    assert date(2021, 1, 1).isocalendar()[:2] == (2020, 53)  # January in last year
    assert date(2024, 12, 31).isocalendar()[:2] == (2025, 1)  # December in next year
    assert date(2025, 12, 29).isocalendar()[:3] == (2026, 1, 1)  # W1 starts in December


def test_python_rejects_the_61st_second():
    # The leap-second cases are literals precisely because of this.
    with pytest.raises(ValueError):
        datetime.fromisoformat("2016-12-31T23:59:60+00:00")


def test_leap_second_table_matches_known_anchor_points():
    table = dict(edgetz.leap_seconds())
    assert table["1972-06-30"] == 11  # first insertion
    assert table["2012-06-30"] == 35  # the outage-famous one
    assert table["2016-12-31"] == 37  # most recent; TAI-UTC still 37 today


def test_int32_second_boundary_and_wraparound():
    assert datetime.fromtimestamp(2**31 - 1, tz=UTC) == datetime(
        2038, 1, 19, 3, 14, 7, tzinfo=UTC
    )
    wrapped = datetime.fromtimestamp((2**31) - 2**32, tz=UTC)
    assert wrapped == datetime(1901, 12, 13, 20, 45, 52, tzinfo=UTC)


def test_epoch_minus_one_is_a_real_1969_timestamp():
    assert datetime.fromtimestamp(-1, tz=UTC) == datetime(
        1969, 12, 31, 23, 59, 59, tzinfo=UTC
    )


def test_gps_rollover_instant_and_weekday():
    # 2019-04-06T23:59:42Z: GPS week 1023 -> 0; 42 s was the GPS-UTC offset.
    moment = datetime(2019, 4, 6, 23, 59, 42, tzinfo=UTC)
    assert int(moment.timestamp()) == 1554595182
    assert moment.strftime("%A") == "Saturday"  # GPS weeks roll at Sat/Sun midnight


def test_ntp_era_0_is_exactly_2_to_32_seconds_after_1900():
    era_start = datetime(1900, 1, 1, tzinfo=UTC)
    assert era_start + timedelta(seconds=2**32) == datetime(
        2036, 2, 7, 6, 28, 16, tzinfo=UTC
    )


def test_cocoa_epoch_offset_from_unix_epoch():
    assert int(datetime(2001, 1, 1, tzinfo=UTC).timestamp()) == 978307200


def test_datetime_range_edges_blow_up_exactly_as_documented():
    # The corpus's why-texts for datetime-min/max, demonstrated live.
    aware_min = datetime.min.replace(tzinfo=UTC)
    with pytest.raises(OverflowError):
        aware_min.astimezone(timezone(timedelta(hours=-5)))
    with pytest.raises(OverflowError):
        datetime.max + timedelta(seconds=1)
