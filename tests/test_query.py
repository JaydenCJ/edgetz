"""Query-layer behavior: filtering, validation, and stable ordering.

The critical property is loud failure: a typo in a filter must raise, never
silently return zero fixtures (which would make a downstream suite pass
vacuously).
"""

from __future__ import annotations

import pytest

import edgetz
from edgetz.errors import UnknownCaseError, UnknownFilterError


def test_cases_unfiltered_returns_whole_corpus(corpus):
    assert edgetz.cases() == corpus


def test_single_field_filters():
    assert {c.category for c in edgetz.cases(category="skipped-date")} == {"skipped-date"}
    assert len(edgetz.cases(category="skipped-date")) == 3
    assert {c.zone for c in edgetz.cases(zone="America/New_York")} == {"America/New_York"}
    for item in edgetz.cases(tag="ramadan"):
        assert "ramadan" in item.tags
    assert all(item.kind == "fold" for item in edgetz.cases(kind="fold"))


def test_filters_combine_with_and_semantics():
    selected = edgetz.cases(category="weird-dst", zone="Antarctica/Troll")
    assert {item.id for item in selected} == {
        "weird-troll-gap-2026",
        "weird-troll-fold-2026",
    }


def test_valid_but_empty_combination_returns_empty_not_error():
    # Both filter values exist; their intersection legitimately being empty
    # must not raise — only unknown values are errors.
    assert edgetz.cases(category="leap-day", zone="Pacific/Apia") == ()


def test_unknown_filter_values_raise_loudly():
    with pytest.raises(UnknownFilterError) as excinfo:
        edgetz.cases(category="dst-gaps")
    assert "dst-gap" in str(excinfo.value)  # tells you the valid values
    with pytest.raises(UnknownFilterError):
        edgetz.cases(zone="America/Springfield")
    with pytest.raises(UnknownFilterError):
        edgetz.cases(tag="no-such-tag")
    with pytest.raises(UnknownFilterError):
        edgetz.cases(kind="wormhole")


def test_case_lookup_by_id_and_typo_suggestions():
    assert edgetz.case("gap-berlin-2026").zone == "Europe/Berlin"
    with pytest.raises(UnknownCaseError) as excinfo:
        edgetz.case("gap-new-york-226")
    assert "gap-new-york-2026" in str(excinfo.value)


def test_categories_returns_described_copy():
    registry = edgetz.categories()
    assert len(registry) == 10
    for description in registry.values():
        assert description.endswith(".")
    registry["injected"] = "nope"
    assert "injected" not in edgetz.categories()


def test_vocabularies_are_sorted_and_faithful(corpus):
    zone_names = edgetz.zones()
    assert list(zone_names) == sorted(set(zone_names))
    assert "Australia/Lord_Howe" in zone_names
    tag_names = edgetz.tags()
    assert list(tag_names) == sorted(tag_names)
    assert "spring-forward" in tag_names
    assert set(edgetz.kinds()) == {item.kind for item in corpus}


def test_cases_returns_stable_order_across_calls():
    assert [c.id for c in edgetz.cases()] == [c.id for c in edgetz.cases()]
