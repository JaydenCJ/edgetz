# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-12

### Added

- Curated corpus of 58 real pathological datetimes across 10 categories:
  `dst-gap`, `dst-fold`, `missing-midnight`, `skipped-date`, `offset-shift`,
  `weird-dst`, `leap-day`, `week-53`, `leap-second`, and `epoch-boundary` —
  every case with a stable id, machine-checkable `expect` ground truth
  (UTC instants, offsets to the second, transition instants, gap/fold
  widths), a `why` naming the bug class, provenance, and tags.
- Highlights: Samoa's deleted 2011-12-30, Liberia's -00:44:30 offset,
  Nepal's missing 1986 midnight, Havana's double midnight, Antarctica's
  2-hour DST, Lord Howe's 30-minute DST, Dublin's negative-DST modeling,
  Sweden's February 30, the Y2K38 pair, and GPS/NTP rollovers.
- Embedded IERS leap-second table: all 27 insertions with TAI-UTC offsets,
  exposed as `edgetz.leap_seconds()`.
- Query API: `cases()` with ANDed category/zone/tag/kind filters that fail
  loudly on unknown values, `case()` with did-you-mean suggestions, and
  vocabulary helpers (`categories`, `zones`, `tags`, `kinds`).
- `classify()`: PEP 495 gap/fold/unique detection for any naive wall clock.
- Verification engine: `verify_case()`/`verify_corpus()` recompute every
  tzdata-level claim against the host zone database and every calendar-level
  claim with pure arithmetic; graceful skips when tzdata is absent.
- Deterministic emitters: `json`, `jsonl`, `csv`, `markdown`, and a
  self-contained `pytest` parametrization module (vendorable, no edgetz
  import required).
- `edgetz` CLI: `list`, `show`, `emit`, `categories`, `zones`, `stats`, and
  `verify [--strict]`, with exit codes 0/1/2 and typo suggestions.
- Runnable examples: a gap/fold-safe localizer test suite and a polyglot
  fixture exporter.
- 89 deterministic offline tests (including the README quickstart executed
  verbatim) and `scripts/smoke.sh`, which exercises the CLI end to end and
  prints `SMOKE OK`.

### Notes

- The repository ships no CI workflow; verification is local — `pip install -e '.[dev]' && pytest && bash scripts/smoke.sh`.
- Corpus ground truth was transcribed from and re-verified against IANA tzdata 2025b.

[0.1.0]: https://github.com/JaydenCJ/edgetz/releases/tag/v0.1.0
