"""Structural integrity of the shipped corpus.

These tests are the contract the corpus makes with downstream consumers:
stable ids, registered categories, parseable timestamps, and non-empty
provenance. A curation slip that would ship a malformed fixture fails here,
not in some user's CI.
"""

from __future__ import annotations

import re
from datetime import datetime

import pytest

import edgetz
from edgetz.model import KINDS, VERIFY_LEVELS, parse_offset, parse_utc

_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def test_corpus_is_substantial(corpus):
    # The whole point is breadth: a tiny corpus would not be worth shipping.
    assert len(corpus) >= 50


def test_case_ids_are_unique_kebab_slugs(corpus):
    ids = [item.id for item in corpus]
    assert len(ids) == len(set(ids))
    for case_id in ids:
        assert _SLUG.match(case_id), f"bad id: {case_id}"


def test_categories_are_registered_and_populated(corpus):
    for item in corpus:
        assert item.category in edgetz.categories(), item.id
    # A category with fewer than three cases is a stub, not a category.
    for name in edgetz.categories():
        assert len(edgetz.cases(category=name)) >= 3, name


def test_all_timestamp_fields_parse(corpus):
    for item in corpus:
        assert item.local or item.literal or item.utc, f"{item.id}: no timestamp at all"
        if item.local is not None:
            assert datetime.fromisoformat(item.local).tzinfo is None, item.id
        for instant in item.utc:
            assert instant.endswith("Z"), item.id
            parse_utc(instant)  # raises on malformation
        for key in ("offset_before", "offset_after", "offset"):
            if key in item.expect:
                parse_offset(item.expect[key])


def test_literals_are_pathological_on_purpose(corpus):
    # A literal exists precisely because `local` must stay parseable;
    # every literal must therefore be rejected by fromisoformat.
    literals = [item for item in corpus if item.literal is not None]
    assert literals, "corpus should contain parse-hostile literals"
    for item in literals:
        with pytest.raises(ValueError):
            datetime.fromisoformat(item.literal.replace("Z", "+00:00"))


def test_every_case_has_a_registered_kind(corpus):
    for item in corpus:
        assert item.kind in KINDS, item.id


def test_utc_instant_count_matches_kind(corpus):
    for item in corpus:
        if item.kind in ("gap", "skipped-date"):
            # A nonexistent wall clock has no instant; shipping one is a lie.
            assert item.utc == (), item.id
        elif item.kind == "fold":
            assert len(item.utc) == 2, item.id
            first, second = item.utc_datetimes()
            assert first < second, item.id


def test_every_case_names_the_bug_class_and_its_source(corpus):
    for item in corpus:
        assert len(item.why) >= 60, f"{item.id}: why is too thin to be useful"
        assert len(item.source) >= 10, item.id
        assert item.verify in VERIFY_LEVELS, item.id


def test_tags_are_kebab_case_and_present(corpus):
    for item in corpus:
        assert item.tags, f"{item.id}: untagged"
        for tag in item.tags:
            assert _SLUG.match(tag), f"{item.id}: bad tag {tag!r}"


def test_zones_are_iana_names(corpus):
    for item in corpus:
        if item.zone is not None:
            assert "/" in item.zone, item.id


def test_leap_second_table_is_complete_and_ordered():
    table = edgetz.leap_seconds()
    assert len(table) == 27  # every insertion 1972-2016, per IERS Bulletin C
    dates = [entry[0] for entry in table]
    assert dates == sorted(dates)
    offsets = [entry[1] for entry in table]
    assert offsets == list(range(11, 38))  # TAI-UTC grew monotonically 11..37
    lookup = dict(table)
    for item in edgetz.cases(category="leap-second"):
        assert item.expect["utc_date"] in lookup, item.id


def test_corpus_order_is_grouped_by_category(corpus):
    # Stable, grouped ordering keeps emitted fixture diffs reviewable.
    seen = []
    for item in corpus:
        if not seen or seen[-1] != item.category:
            seen.append(item.category)
    assert len(seen) == len(set(seen)), "categories are interleaved"
