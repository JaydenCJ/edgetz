"""edgetz — the nastiest real datetimes, curated as test fixtures.

Public API:

- :func:`cases`, :func:`case` — query the corpus (filter by category, zone,
  tag, or kind).
- :func:`categories`, :func:`zones`, :func:`tags`, :func:`kinds` — corpus
  vocabulary.
- :func:`leap_seconds` — the full IERS leap-second table.
- :func:`classify` — PEP 495 gap/fold/unique detection for any wall clock.
- :func:`verify_case`, :func:`verify_corpus` — re-check the curated ground
  truth against the host tzdata and pure calendar math.
- :class:`Case` — the frozen fixture record itself.

Typical pytest use::

    import edgetz, pytest

    @pytest.mark.parametrize("case", edgetz.cases(category="dst-gap"),
                             ids=lambda c: c.id)
    def test_scheduler_survives_gaps(case):
        assert my_scheduler.next_run(case.local_datetime(), case.zone)
"""

from __future__ import annotations

from .errors import EdgetzError, UnknownCaseError, UnknownFilterError
from .model import Case, format_offset, format_utc, parse_offset, parse_utc
from .query import case, cases, categories, kinds, leap_seconds, tags, zones
from .verify import CheckResult, classify, verify_case, verify_corpus

__version__ = "0.1.0"

__all__ = [
    "Case",
    "CheckResult",
    "EdgetzError",
    "UnknownCaseError",
    "UnknownFilterError",
    "__version__",
    "case",
    "cases",
    "categories",
    "classify",
    "format_offset",
    "format_utc",
    "kinds",
    "leap_seconds",
    "parse_offset",
    "parse_utc",
    "tags",
    "verify_case",
    "verify_corpus",
    "zones",
]
