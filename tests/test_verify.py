"""Verification engine tests: classify() semantics and corpus/host agreement.

The heavyweight test here — the whole corpus verifying cleanly against the
host tzdata — is the project's central claim. If a tzdata update ever changes
a rule we curated, this fails and the corpus must be corrected, exactly as it
would for a user running `edgetz verify` in CI.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest

import edgetz
from edgetz.errors import EdgetzError
from edgetz.verify import tzdata_available, tzdata_version, verify_case, verify_corpus

needs_tzdata = pytest.mark.skipif(
    not tzdata_available(), reason="host has no IANA tzdata"
)


@needs_tzdata
def test_classify_gap_fold_and_unique():
    assert edgetz.classify(datetime(2026, 6, 15, 12, 0), "America/New_York") == "unique"
    assert edgetz.classify(datetime(2026, 3, 8, 2, 30), "America/New_York") == "gap"
    assert edgetz.classify(datetime(2026, 11, 1, 1, 30), "America/New_York") == "fold"


@needs_tzdata
def test_classify_boundaries_are_exact():
    # 01:59:59 exists; 02:00:00 is the first nonexistent second; 03:00:00 exists.
    assert edgetz.classify(datetime(2026, 3, 8, 1, 59, 59), "America/New_York") == "unique"
    assert edgetz.classify(datetime(2026, 3, 8, 2, 0, 0), "America/New_York") == "gap"
    assert edgetz.classify(datetime(2026, 3, 8, 3, 0, 0), "America/New_York") == "unique"


@needs_tzdata
def test_classify_handles_sub_hour_transitions():
    # Lord Howe's 30-minute DST: half-width, still a gap.
    assert edgetz.classify(datetime(2026, 10, 4, 2, 15), "Australia/Lord_Howe") == "gap"
    # Monrovia's 44.5-minute jump off a seconds-precision offset.
    assert edgetz.classify(datetime(1972, 1, 7, 0, 20), "Africa/Monrovia") == "gap"


def test_classify_rejects_aware_datetimes_and_unknown_zones():
    aware = datetime(2026, 3, 8, 2, 30).astimezone()
    with pytest.raises(EdgetzError):
        edgetz.classify(aware, "America/New_York")
    with pytest.raises(EdgetzError):
        edgetz.classify(datetime(2026, 3, 8, 2, 30), "Not/AZone")


@needs_tzdata
def test_whole_corpus_agrees_with_host_tzdata(corpus):
    results = verify_corpus(corpus)
    mismatched = [r for r in results if r.status == "mismatch"]
    assert mismatched == [], "; ".join(
        f"{r.case_id}: {r.details}" for r in mismatched
    )


@needs_tzdata
def test_only_curated_only_cases_are_skipped(corpus):
    skipped = [r.case_id for r in verify_corpus(corpus) if r.status == "skipped"]
    assert skipped == ["leap-day-sweden-1712"]


@needs_tzdata
def test_verify_detects_a_doctored_offset():
    # Flip one curated offset and the checker must call it out — this is the
    # same code path a genuine tzdata rule change would take.
    real = edgetz.case("gap-new-york-2026")
    doctored = dataclasses.replace(
        real, expect={**real.expect, "offset_after": "-03:00"}
    )
    result = verify_case(doctored)
    assert result.status == "mismatch"
    assert any("offset" in detail for detail in result.details)


@needs_tzdata
def test_verify_detects_a_doctored_utc_instant():
    real = edgetz.case("fold-new-york-2026")
    doctored = dataclasses.replace(
        real, utc=("2026-11-01T05:30:00Z", "2026-11-01T07:30:00Z")
    )
    assert verify_case(doctored).status == "mismatch"


def test_verify_detects_a_doctored_week_number():
    real = edgetz.case("week53-2020")
    doctored = dataclasses.replace(real, expect={**real.expect, "iso_week": 52})
    result = verify_case(doctored)
    assert result.status == "mismatch"
    assert "isocalendar" in result.details[0]


def test_verify_detects_a_doctored_epoch():
    real = edgetz.case("y2k38-int32-max")
    doctored = dataclasses.replace(
        real, expect={**real.expect, "unix_seconds": 2147483646}
    )
    assert verify_case(doctored).status == "mismatch"


def test_verify_detects_a_fabricated_leap_second():
    # 2013 had no leap second; a case claiming one must be flagged.
    real = edgetz.case("leap-second-2016")
    doctored = dataclasses.replace(
        real,
        literal="2013-12-31T23:59:60Z",
        expect={**real.expect, "utc_date": "2013-12-31", "next_utc": "2014-01-01T00:00:00Z"},
    )
    assert verify_case(doctored).status == "mismatch"


def test_curated_only_case_is_skipped_not_failed():
    result = verify_case(edgetz.case("leap-day-sweden-1712"))
    assert result.status == "skipped"
    assert not result.ok


def test_calendar_cases_verify_without_touching_tzdata():
    for category in ("leap-day", "week-53", "leap-second", "epoch-boundary"):
        for item in edgetz.cases(category=category):
            if item.verify == "calendar":
                assert verify_case(item).ok, item.id


def test_tzdata_version_returns_a_string():
    version = tzdata_version()
    assert isinstance(version, str) and version
