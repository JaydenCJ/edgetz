"""Data model for edgetz fixtures.

A :class:`Case` is one curated pathological datetime: a stable id, the
wall-clock or instant that misbehaves, machine-checkable ground truth in
``expect``, and a ``why`` sentence naming the bug class it triggers. Cases are
frozen dataclasses so a test suite can share them freely between tests.

This module also owns the tiny amount of datetime plumbing the package needs:
UTC-offset parsing that keeps seconds precision (Africa/Monrovia ran at
-00:44:30 until 1972) and a ``Z``-suffix ISO parser that works on Python 3.9,
where ``datetime.fromisoformat`` does not yet accept ``Z``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from .errors import EdgetzError

#: The verification levels a case can declare.
#: - ``tzdata``:   checkable against the host IANA time zone database.
#: - ``calendar``: checkable with pure calendar arithmetic (no tzdata needed).
#: - ``none``:     curated-only (historical calendars outside tzdata's model).
VERIFY_LEVELS: Tuple[str, ...] = ("tzdata", "calendar", "none")

#: Every ``expect["kind"]`` value used in the corpus.
KINDS: Tuple[str, ...] = (
    "gap",
    "fold",
    "skipped-date",
    "extreme-offset",
    "negative-dst",
    "leap-day",
    "iso-week",
    "leap-second",
    "epoch",
)

_OFFSET_RE = re.compile(r"^([+-])(\d{2}):(\d{2})(?::(\d{2}))?$")


def parse_offset(text: str) -> timedelta:
    """Parse ``+HH:MM`` or ``+HH:MM:SS`` into a :class:`timedelta`.

    Seconds precision matters: real zones have carried offsets such as
    ``-00:44:30`` (Monrovia) that ``%z``-style parsers routinely reject.
    """
    m = _OFFSET_RE.match(text)
    if not m:
        raise EdgetzError(f"malformed UTC offset: {text!r} (want [+-]HH:MM[:SS])")
    sign = 1 if m.group(1) == "+" else -1
    hours, minutes = int(m.group(2)), int(m.group(3))
    seconds = int(m.group(4) or 0)
    if minutes > 59 or seconds > 59:
        raise EdgetzError(f"malformed UTC offset: {text!r} (minutes/seconds out of range)")
    return sign * timedelta(hours=hours, minutes=minutes, seconds=seconds)


def format_offset(delta: timedelta) -> str:
    """Format a :class:`timedelta` as ``+HH:MM`` (``+HH:MM:SS`` when needed)."""
    total = int(delta.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    if seconds:
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{sign}{hours:02d}:{minutes:02d}"


def parse_utc(text: str) -> datetime:
    """Parse ``YYYY-MM-DDTHH:MM:SSZ`` into an aware UTC datetime (3.9-safe)."""
    if not text.endswith("Z"):
        raise EdgetzError(f"UTC instant must end with 'Z': {text!r}")
    naive = datetime.fromisoformat(text[:-1])
    if naive.tzinfo is not None:
        raise EdgetzError(f"UTC instant must not carry an offset besides 'Z': {text!r}")
    return naive.replace(tzinfo=timezone.utc)


def format_utc(moment: datetime) -> str:
    """Format an aware datetime as a corpus-style ``...Z`` string.

    Built by hand rather than ``strftime`` because glibc does not zero-pad
    ``%Y`` for years below 1000 — and year 1 is in the corpus.
    """
    if moment.tzinfo is None:
        raise EdgetzError("format_utc needs an aware datetime")
    utc_moment = moment.astimezone(timezone.utc)
    return (
        f"{utc_moment.year:04d}-{utc_moment.month:02d}-{utc_moment.day:02d}"
        f"T{utc_moment.hour:02d}:{utc_moment.minute:02d}:{utc_moment.second:02d}Z"
    )


@dataclass(frozen=True)
class Case:
    """One curated pathological datetime with machine-checkable ground truth.

    Exactly which fields are populated depends on the failure mode:

    - Time-zone traps set ``zone`` and ``local`` (a naive wall-clock string).
      ``utc`` holds the matching instants: none for a nonexistent local time,
      two for an ambiguous one, one otherwise.
    - Strings that are pathological *as text* (leap seconds, February 30)
      set ``literal`` instead, because ``local`` is guaranteed parseable.
    - Pure-instant traps (Y2K38, epoch sentinels) set only ``utc``.
    """

    id: str
    category: str
    why: str
    source: str
    zone: Optional[str] = None
    local: Optional[str] = None
    literal: Optional[str] = None
    utc: Tuple[str, ...] = ()
    expect: Dict[str, Any] = field(default_factory=dict)
    tags: Tuple[str, ...] = ()
    verify: str = "none"

    @property
    def kind(self) -> str:
        """The failure-mode kind, taken from ``expect["kind"]``."""
        return str(self.expect.get("kind", "unknown"))

    @property
    def when(self) -> str:
        """The most human-relevant timestamp string, for listings."""
        if self.local is not None:
            return self.local
        if self.literal is not None:
            return self.literal
        if self.utc:
            return self.utc[0]
        return "-"

    def local_datetime(self) -> datetime:
        """Return ``local`` parsed as a naive datetime.

        Raises :class:`EdgetzError` when the case has no ``local`` field
        (leap seconds and invalid dates are literals by design).
        """
        if self.local is None:
            raise EdgetzError(f"case {self.id} has no parseable local time")
        return datetime.fromisoformat(self.local)

    def utc_datetimes(self) -> Tuple[datetime, ...]:
        """Return every entry of ``utc`` as an aware UTC datetime."""
        return tuple(parse_utc(item) for item in self.utc)

    def as_dict(self) -> Dict[str, Any]:
        """A JSON-ready plain-dict view (lists instead of tuples)."""
        return {
            "id": self.id,
            "category": self.category,
            "kind": self.kind,
            "zone": self.zone,
            "local": self.local,
            "literal": self.literal,
            "utc": list(self.utc),
            "expect": dict(self.expect),
            "why": self.why,
            "source": self.source,
            "tags": list(self.tags),
            "verify": self.verify,
        }
