"""Unit tests for the Case model and the offset/UTC string plumbing.

The offset helpers must survive the corpus's own extremes: seconds-precision
offsets (Monrovia -00:44:30), :45 offsets (Kathmandu), and year 1.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

import edgetz
from edgetz.errors import EdgetzError
from edgetz.model import Case, format_offset, format_utc, parse_offset, parse_utc


def test_parse_offset_handles_every_real_world_shape():
    assert parse_offset("+05:00") == timedelta(hours=5)
    assert parse_offset("-04:30") == -timedelta(hours=4, minutes=30)
    assert parse_offset("+05:45") == timedelta(hours=5, minutes=45)
    # Monrovia ran at -00:44:30 until 1972; HH:MM-only parsers reject it.
    assert parse_offset("-00:44:30") == -timedelta(minutes=44, seconds=30)


def test_parse_offset_rejects_garbage():
    for bad in ("05:00", "+5:00", "+05", "+05:99", "+05:00:99", "UTC+5", ""):
        with pytest.raises(EdgetzError):
            parse_offset(bad)


def test_format_offset_roundtrips_every_corpus_offset(corpus):
    for item in corpus:
        for key in ("offset_before", "offset_after", "offset"):
            if key in item.expect:
                text = item.expect[key]
                assert format_offset(parse_offset(text)) == text, item.id


def test_parse_utc_requires_bare_z_suffix():
    moment = parse_utc("2026-03-08T07:00:00Z")
    assert moment == datetime(2026, 3, 8, 7, tzinfo=timezone.utc)
    for bad in ("2026-03-08T07:00:00", "2026-03-08T07:00:00+00:00Z"):
        with pytest.raises(EdgetzError):
            parse_utc(bad)


def test_format_utc_pads_year_one_and_rejects_naive():
    # glibc strftime prints year 1 as "1"; the corpus needs "0001".
    assert format_utc(datetime(1, 1, 1, tzinfo=timezone.utc)) == "0001-01-01T00:00:00Z"
    with pytest.raises(EdgetzError):
        format_utc(datetime(2026, 1, 1))


def test_case_is_frozen():
    item = edgetz.case("gap-new-york-2026")
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.id = "something-else"


def test_kind_and_when_are_derived_views():
    assert edgetz.case("fold-new-york-2026").kind == "fold"
    assert edgetz.case("gap-new-york-2026").when == "2026-03-08T02:30:00"
    assert edgetz.case("leap-day-1900-invalid").when == "1900-02-29"
    assert edgetz.case("y2k38-int32-max").when == "2038-01-19T03:14:07Z"


def test_local_datetime_parses_naive_or_refuses():
    parsed = edgetz.case("gap-new-york-2026").local_datetime()
    assert parsed == datetime(2026, 3, 8, 2, 30) and parsed.tzinfo is None
    with pytest.raises(EdgetzError):
        edgetz.case("leap-second-2016").local_datetime()  # literal-only case


def test_utc_datetimes_returns_aware_pairs_for_folds():
    first, second = edgetz.case("fold-new-york-2026").utc_datetimes()
    assert second - first == timedelta(hours=1)
    assert first.tzinfo is timezone.utc


def test_as_dict_is_json_shaped_and_defensive():
    entry = edgetz.case("skip-samoa-2011-12-30").as_dict()
    assert entry["kind"] == "skipped-date"
    assert isinstance(entry["utc"], list) and isinstance(entry["tags"], list)
    # as_dict must copy, never alias, the frozen case's mutable expect dict.
    entry["expect"]["kind"] = "tampered"
    assert edgetz.case("skip-samoa-2011-12-30").expect["kind"] == "skipped-date"


def test_default_case_is_minimal_but_valid():
    item = Case(id="x", category="dst-gap", why="w" * 60, source="somewhere real")
    assert item.kind == "unknown"
    assert item.when == "-"
    assert item.utc_datetimes() == ()
