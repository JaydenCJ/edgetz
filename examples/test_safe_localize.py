"""Example: harden a localizer against every DST trap in the corpus.

``safe_localize`` below is the ~10 lines every backend eventually needs:
attach a zone to a naive wall clock without crashing on nonexistent times or
silently picking a random side of ambiguous ones. The edgetz corpus is the
test data that proves it right — including the 30-minute, 44.5-minute, and
2-hour transitions a hand-written fixture list always forgets.

Run from the repository root: ``pytest examples/test_safe_localize.py``
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

import edgetz

# Categories whose `local` field is a wall clock worth localizing.
_DST_CATEGORIES = ("dst-gap", "dst-fold", "missing-midnight", "weird-dst")


def safe_localize(naive: datetime, zone_key: str) -> datetime:
    """Attach a zone, resolving gaps forward and folds to the first pass.

    - unique time: attach as-is.
    - fold: keep ``fold=0`` (the earlier occurrence) — an explicit policy.
    - gap: shift forward by the gap width, the same policy most schedulers
      settle on after their first spring-forward incident.
    """
    kind = edgetz.classify(naive, zone_key)
    zone = ZoneInfo(zone_key)
    if kind == "gap":
        width = (
            naive.replace(tzinfo=zone, fold=1).utcoffset()
            - naive.replace(tzinfo=zone, fold=0).utcoffset()
        )
        return (naive + width).replace(tzinfo=zone, fold=1)
    return naive.replace(tzinfo=zone, fold=0)


def _dst_cases():
    selected = []
    for category in _DST_CATEGORIES:
        for item in edgetz.cases(category=category):
            if item.local is not None and item.kind in ("gap", "fold"):
                selected.append(item)
    return selected


def test_corpus_supplies_a_meaningful_workload():
    # If this shrinks, the example (and its guarantees) silently weakens.
    assert len(_dst_cases()) >= 20


def test_safe_localize_roundtrips_every_dst_case():
    # The correctness bar: converting the result to UTC and back must be a
    # fixed point. Naive `replace(tzinfo=...)` fails this inside every gap.
    for item in _dst_cases():
        resolved = safe_localize(item.local_datetime(), item.zone)
        roundtripped = resolved.astimezone(timezone.utc).astimezone(resolved.tzinfo)
        assert roundtripped == resolved, item.id


def test_safe_localize_picks_the_documented_fold_instant():
    # Policy check: for ambiguous times we promise the earlier instant,
    # which the corpus ships precomputed as utc[0].
    for item in _dst_cases():
        if item.kind != "fold":
            continue
        resolved = safe_localize(item.local_datetime(), item.zone)
        assert resolved.astimezone(timezone.utc) == item.utc_datetimes()[0], item.id


def test_naive_localization_really_is_broken_inside_gaps():
    # The motivation, demonstrated: plain replace() round-trips to a
    # *different* wall clock for nonexistent times.
    item = edgetz.case("gap-new-york-2026")
    naive = item.local_datetime()
    pretending = naive.replace(tzinfo=ZoneInfo(item.zone))
    roundtripped = pretending.astimezone(timezone.utc).astimezone(pretending.tzinfo)
    assert roundtripped.replace(tzinfo=None) != naive
    with pytest.raises(AssertionError):
        assert roundtripped == pretending
