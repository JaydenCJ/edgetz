"""Verification: re-check the curated corpus against independent sources.

Two independent checkers back the corpus:

- ``tzdata`` cases are recomputed from the host's IANA time zone database via
  :mod:`zoneinfo` (PEP 495 fold semantics). If the host disagrees with the
  corpus, either the host tzdata is stale or a government changed the rules —
  both are things a backend team wants to hear about before production does.
- ``calendar`` cases are recomputed with pure datetime arithmetic: leap-year
  rules, ISO week dates, epoch math, and the embedded IERS leap-second table.

``classify`` is exported as a small public helper because gap/fold detection
is the single most reused three lines of timezone code in existence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence, Tuple

from .corpus import LEAP_SECONDS
from .errors import EdgetzError
from .model import Case, format_offset, format_utc, parse_offset, parse_utc

try:  # zoneinfo is stdlib on every supported Python (>=3.9)
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    _ZONEINFO_IMPORTED = True
except ImportError:  # pragma: no cover - only on broken installs
    _ZONEINFO_IMPORTED = False

_UTC = timezone.utc
_ZONE_CACHE: Dict[str, object] = {}


def _zone(key: str):
    """Load a ZoneInfo, returning None when the host has no tzdata for it."""
    if not _ZONEINFO_IMPORTED:
        return None
    if key not in _ZONE_CACHE:
        try:
            _ZONE_CACHE[key] = ZoneInfo(key)
        except ZoneInfoNotFoundError:
            _ZONE_CACHE[key] = None
    return _ZONE_CACHE[key]


def tzdata_available() -> bool:
    """True when the host can resolve IANA zones at all."""
    return _zone("UTC") is not None


def tzdata_version() -> str:
    """Best-effort host tzdata version (e.g. ``2025b``), else ``unknown``.

    Tries the ``tzdata`` PyPI package first, then the ``tzdata.zi`` header
    that system packages install next to the compiled zone files.
    """
    try:
        import importlib.metadata as md

        return md.version("tzdata")
    except Exception:  # noqa: BLE001 - any failure just means "not pip tzdata"
        pass
    try:
        import zoneinfo

        for root in zoneinfo.TZPATH:
            try:
                with open(f"{root}/tzdata.zi", encoding="utf-8") as handle:
                    first = handle.readline().strip()
                if first.startswith("# version"):
                    return first.split()[-1]
            except OSError:
                continue
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


def classify(local: datetime, zone_key: str) -> str:
    """Classify a naive wall-clock time in a zone: ``unique``/``gap``/``fold``.

    Implements PEP 495: attach the zone with ``fold=0`` and ``fold=1`` and
    compare the resulting UTC offsets. Equal offsets mean the time exists
    exactly once; a smaller ``fold=0`` offset means the clock jumped forward
    over it (gap); a larger one means the clock fell back through it (fold).
    """
    if local.tzinfo is not None:
        raise EdgetzError("classify() wants a naive datetime (the wall clock)")
    zone = _zone(zone_key)
    if zone is None:
        raise EdgetzError(f"no tzdata available for zone {zone_key!r}")
    off0 = local.replace(tzinfo=zone, fold=0).utcoffset()
    off1 = local.replace(tzinfo=zone, fold=1).utcoffset()
    if off0 == off1:
        return "unique"
    return "gap" if off0 < off1 else "fold"


@dataclass
class CheckResult:
    """Outcome of verifying one case: ``ok``, ``mismatch``, or ``skipped``."""

    case_id: str
    status: str
    details: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "ok"


class _Checker:
    """Accumulates mismatch details for one case."""

    def __init__(self, item: Case):
        self.item = item
        self.problems: List[str] = []

    def expect_equal(self, label: str, actual, expected) -> None:
        if actual != expected:
            self.problems.append(f"{label}: expected {expected!r}, host says {actual!r}")

    def offsets_at(self, local: datetime, zone_key: str) -> Tuple[timedelta, timedelta]:
        zone = _zone(zone_key)
        assert zone is not None  # caller guards availability
        return (
            local.replace(tzinfo=zone, fold=0).utcoffset(),
            local.replace(tzinfo=zone, fold=1).utcoffset(),
        )

    def check_transition_boundary(self) -> None:
        """The instants straddling ``transition_utc`` must carry the curated offsets."""
        expect = self.item.expect
        if "transition_utc" not in expect or self.item.zone is None:
            return
        zone = _zone(self.item.zone)
        at = parse_utc(expect["transition_utc"])
        before = (at - timedelta(seconds=1)).astimezone(zone).utcoffset()
        after = at.astimezone(zone).utcoffset()
        self.expect_equal("offset just before transition", format_offset(before), expect["offset_before"])
        self.expect_equal("offset at transition", format_offset(after), expect["offset_after"])


def _check_gap(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    local = item.local_datetime()
    chk.expect_equal("classification", classify(local, item.zone), "gap")
    off0, off1 = chk.offsets_at(local, item.zone)
    chk.expect_equal("offset before (fold=0)", format_offset(off0), expect["offset_before"])
    chk.expect_equal("offset after (fold=1)", format_offset(off1), expect["offset_after"])
    width = parse_offset(expect["offset_after"]) - parse_offset(expect["offset_before"])
    chk.expect_equal("gap width (s)", int(width.total_seconds()), expect["gap_seconds"])
    chk.check_transition_boundary()
    first_valid = expect.get("first_valid_local")
    if first_valid is not None:
        chk.expect_equal(
            "first valid local time",
            classify(datetime.fromisoformat(first_valid), item.zone),
            "unique",
        )


def _check_fold(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    local = item.local_datetime()
    zone = _zone(item.zone)
    chk.expect_equal("classification", classify(local, item.zone), "fold")
    off0, off1 = chk.offsets_at(local, item.zone)
    chk.expect_equal("offset first (fold=0)", format_offset(off0), expect["offset_before"])
    chk.expect_equal("offset second (fold=1)", format_offset(off1), expect["offset_after"])
    width = parse_offset(expect["offset_before"]) - parse_offset(expect["offset_after"])
    chk.expect_equal("fold width (s)", int(width.total_seconds()), expect["fold_seconds"])
    first = local.replace(tzinfo=zone, fold=0).astimezone(_UTC)
    second = local.replace(tzinfo=zone, fold=1).astimezone(_UTC)
    chk.expect_equal("utc instants", tuple(item.utc), tuple(
        format_utc(moment) for moment in (first, second)
    ))
    chk.check_transition_boundary()


def _check_skipped_date(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    day = date.fromisoformat(expect["date"])
    # Every wall-clock hour of the skipped date must be nonexistent.
    for probe in (
        datetime(day.year, day.month, day.day, 0, 0, 0),
        datetime(day.year, day.month, day.day, 12, 0, 0),
        datetime(day.year, day.month, day.day, 23, 59, 59),
    ):
        chk.expect_equal(f"classification at {probe.time()}", classify(probe, item.zone), "gap")
    chk.check_transition_boundary()


def _check_extreme_offset(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    zone = _zone(item.zone)
    local = item.local_datetime().replace(tzinfo=zone)
    chk.expect_equal("offset", format_offset(local.utcoffset()), expect["offset"])
    chk.expect_equal(
        "utc instant",
        format_utc(local),
        item.utc[0],
    )
    aoe = datetime.fromisoformat(expect["aoe_equivalent"])
    chk.expect_equal("anywhere-on-earth equivalent", aoe.astimezone(_UTC), local.astimezone(_UTC))


def _check_negative_dst(chk: _Checker) -> None:
    """Negative-DST modeling is lossy in compiled tzdata, so verify what is
    stable everywhere: the seasonal offsets and abbreviations, which invert
    the usual 'winter is standard time' expectation."""
    item, expect = chk.item, chk.item.expect
    zone = _zone(item.zone)
    for season in ("winter", "summer"):
        probe = datetime.fromisoformat(expect[f"probe_{season}"]).replace(tzinfo=zone)
        chk.expect_equal(f"{season} offset", format_offset(probe.utcoffset()), expect[f"offset_{season}"])
        chk.expect_equal(f"{season} tzname", probe.tzname(), expect[f"tzname_{season}"])


def _check_leap_day(chk: _Checker) -> None:
    import calendar

    item, expect = chk.item, chk.item.expect
    text = item.local if item.local is not None else item.literal
    year = int(text[:4])
    if expect["valid"]:
        chk.expect_equal("calendar.isleap", calendar.isleap(year), True)
        try:
            date(year, 2, 29)
        except ValueError:
            chk.problems.append(f"February 29, {year} should construct but raised")
    else:
        chk.expect_equal("calendar.isleap", calendar.isleap(year), False)
        month, day = int(text[5:7]), int(text[8:10])
        try:
            date(year, month, day)
            chk.problems.append(f"{text} should be invalid but constructed")
        except ValueError:
            pass
    for candidate in expect.get("anniversary_candidates", ()):
        parsed = date.fromisoformat(candidate)
        chk.expect_equal(f"candidate year for {candidate}", parsed.year, year + 1)


def _check_iso_week(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    calendar_tuple = item.local_datetime().date().isocalendar()
    actual = (calendar_tuple[0], calendar_tuple[1], calendar_tuple[2])
    chk.expect_equal(
        "isocalendar()",
        actual,
        (expect["iso_year"], expect["iso_week"], expect["iso_weekday"]),
    )


def _check_leap_second(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    table = dict(LEAP_SECONDS)
    chk.expect_equal("date is in IERS table", expect["utc_date"] in table, True)
    if expect["utc_date"] in table:
        chk.expect_equal("TAI-UTC after insertion", table[expect["utc_date"]], expect["tai_utc_after"])
    if ":60" not in (item.literal or ""):
        chk.problems.append("literal does not contain the :60 second")
    # The trap itself: stdlib parsing must reject the 61st second.
    try:
        datetime.fromisoformat((item.literal or "").replace("Z", "+00:00"))
        chk.problems.append("literal unexpectedly parsed; it should be rejected")
    except ValueError:
        pass
    next_utc = parse_utc(expect["next_utc"])
    day_after = datetime.fromisoformat(expect["utc_date"]).replace(tzinfo=_UTC) + timedelta(days=1)
    chk.expect_equal("instant after the leap second", next_utc, day_after)


def _check_epoch(chk: _Checker) -> None:
    item, expect = chk.item, chk.item.expect
    moment = datetime.fromtimestamp(expect["unix_seconds"], tz=_UTC)
    chk.expect_equal("fromtimestamp", format_utc(moment), item.utc[0])
    wrapped = expect.get("wrapped_int32_utc")
    if wrapped is not None:
        rewound = datetime.fromtimestamp(expect["unix_seconds"] - 2**32, tz=_UTC)
        chk.expect_equal("int32 wraparound", format_utc(rewound), wrapped)


_CHECKERS = {
    "gap": _check_gap,
    "fold": _check_fold,
    "skipped-date": _check_skipped_date,
    "extreme-offset": _check_extreme_offset,
    "negative-dst": _check_negative_dst,
    "leap-day": _check_leap_day,
    "iso-week": _check_iso_week,
    "leap-second": _check_leap_second,
    "epoch": _check_epoch,
}


def verify_case(item: Case) -> CheckResult:
    """Verify one case against its declared verification level."""
    if item.verify == "none":
        return CheckResult(item.id, "skipped", ["curated-only (no independent checker)"])
    if item.verify == "tzdata" and (_zone(item.zone or "UTC") is None):
        return CheckResult(item.id, "skipped", ["host has no tzdata for this zone"])
    checker = _CHECKERS.get(item.kind)
    if checker is None:
        return CheckResult(item.id, "mismatch", [f"no checker for kind {item.kind!r}"])
    chk = _Checker(item)
    checker(chk)
    if chk.problems:
        return CheckResult(item.id, "mismatch", chk.problems)
    return CheckResult(item.id, "ok")


def verify_corpus(items: Optional[Sequence[Case]] = None) -> List[CheckResult]:
    """Verify many cases (default: the whole corpus), preserving order."""
    if items is None:
        from .corpus import all_cases

        items = all_cases()
    return [verify_case(item) for item in items]
