"""Query layer: filtered access to the corpus.

All lookups validate their inputs against the corpus so that a typo in a
category or zone name fails loudly (with suggestions) instead of silently
returning zero fixtures — a corpus that quietly filters down to nothing would
give a test suite false confidence.
"""

from __future__ import annotations

import difflib
from typing import Dict, Optional, Tuple

from .corpus import CATEGORIES, LEAP_SECONDS, all_cases
from .errors import UnknownCaseError, UnknownFilterError
from .model import Case

_BY_ID: Dict[str, Case] = {c.id: c for c in all_cases()}


def cases(
    category: Optional[str] = None,
    zone: Optional[str] = None,
    tag: Optional[str] = None,
    kind: Optional[str] = None,
) -> Tuple[Case, ...]:
    """Return corpus cases, optionally filtered; filters are ANDed.

    Raises :class:`UnknownFilterError` for a filter value that matches
    nothing anywhere in the corpus (as opposed to a valid combination that
    happens to be empty).
    """
    if category is not None and category not in CATEGORIES:
        raise UnknownFilterError("category", category, tuple(CATEGORIES))
    if zone is not None and zone not in zones():
        raise UnknownFilterError("zone", zone, zones())
    if tag is not None and tag not in tags():
        raise UnknownFilterError("tag", tag, tags())
    if kind is not None and kind not in kinds():
        raise UnknownFilterError("kind", kind, kinds())

    selected = []
    for item in all_cases():
        if category is not None and item.category != category:
            continue
        if zone is not None and item.zone != zone:
            continue
        if tag is not None and tag not in item.tags:
            continue
        if kind is not None and item.kind != kind:
            continue
        selected.append(item)
    return tuple(selected)


def case(case_id: str) -> Case:
    """Return one case by id, or raise :class:`UnknownCaseError` with hints."""
    try:
        return _BY_ID[case_id]
    except KeyError:
        hints = difflib.get_close_matches(case_id, _BY_ID, n=3, cutoff=0.5)
        raise UnknownCaseError(case_id, tuple(hints)) from None


def categories() -> Dict[str, str]:
    """Return the category registry as ``{slug: description}``."""
    return dict(CATEGORIES)


def zones() -> Tuple[str, ...]:
    """Return every IANA zone referenced by the corpus, sorted."""
    return tuple(sorted({c.zone for c in all_cases() if c.zone is not None}))


def tags() -> Tuple[str, ...]:
    """Return every tag used in the corpus, sorted."""
    found = set()
    for item in all_cases():
        found.update(item.tags)
    return tuple(sorted(found))


def kinds() -> Tuple[str, ...]:
    """Return every ``expect['kind']`` present in the corpus, sorted."""
    return tuple(sorted({c.kind for c in all_cases()}))


def leap_seconds() -> Tuple[Tuple[str, int], ...]:
    """Return the full IERS leap-second table: ``(date, TAI-UTC after)``."""
    return LEAP_SECONDS
