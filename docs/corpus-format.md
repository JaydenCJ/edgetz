# The edgetz corpus format

This document specifies the shape of an emitted case (what `edgetz emit
--format json|jsonl|csv` produces and what `Case.as_dict()` returns) and the
curation policy behind it. The wire format is versioned by the package
version in the JSON wrapper (`"version"`); field semantics only change with
a minor version bump.

## Case object

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable kebab-case identifier, e.g. `gap-new-york-2026`. Never reused or renamed. |
| `category` | string | One of the 10 registered categories (below). |
| `kind` | string | The failure-mode kind driving verification (below). Convenience copy of `expect.kind`. |
| `zone` | string or null | IANA zone name when the case is zone-bound. |
| `local` | string or null | Naive wall-clock ISO 8601 string. **Always parseable**; the pathological-as-text cases use `literal` instead. |
| `literal` | string or null | A raw timestamp string that is pathological as text (`23:59:60Z`, `1900-02-29`). Guaranteed to be rejected by strict ISO parsers. |
| `utc` | array of string | Corresponding UTC instants (`YYYY-MM-DDTHH:MM:SSZ`): empty for nonexistent local times, two (earlier first) for ambiguous ones, one otherwise. |
| `expect` | object | Machine-checkable ground truth; keys depend on `kind` (below). |
| `why` | string | The bug class this case triggers, in one or two sentences. |
| `source` | string | Provenance: tzdata region file, IERS bulletin, spec, or calendar rule. |
| `tags` | array of string | Kebab-case facets (`recurring`, `half-hour-dst`, `date-line`, …). |
| `verify` | string | How the ground truth is re-checked: `tzdata`, `calendar`, or `none`. |

## Categories

`dst-gap`, `dst-fold`, `missing-midnight`, `skipped-date`, `offset-shift`,
`weird-dst`, `leap-day`, `week-53`, `leap-second`, `epoch-boundary`.
Categories group by *failure mode a test suite hits*, not by zone quirk: a
political 30-minute move lives in `offset-shift` even though it mechanically
produces a gap or fold. Tags carry the quirk facets.

## `expect` keys by kind

| Kind | Keys |
|---|---|
| `gap` | `offset_before`, `offset_after`, `gap_seconds`, `transition_utc`, optional `first_valid_local` |
| `fold` | `offset_before`, `offset_after`, `fold_seconds`, `transition_utc` (the two instants live in `utc`) |
| `skipped-date` | `date`, `offset_before`, `offset_after`, `gap_seconds` (86400), `transition_utc` |
| `extreme-offset` | `offset`, `aoe_equivalent` |
| `negative-dst` | `probe_winter`/`probe_summer` with `offset_*` and `tzname_*` pairs |
| `leap-day` | `valid`, `reason`, optional `anniversary_candidates` |
| `iso-week` | `iso_year`, `iso_week`, `iso_weekday` |
| `leap-second` | `utc_date`, `tai_utc_after`, `next_utc` |
| `epoch` | `unix_seconds`, optional `wrapped_int32_utc` |

Offsets are `±HH:MM` or `±HH:MM:SS` (Monrovia needs the seconds). All widths
are integer seconds, because real transitions include 900 s, 1800 s, 2670 s,
and 7200 s — "minutes" would already have failed.

## Curation policy

1. **Real events only.** Every case is a transition that happened (or is
   scheduled under current law), a published bulletin entry, or a calendar
   rule. No synthetic datetimes.
2. **Ground truth is transcribed, then proven.** tzdata-level facts were
   transcribed from the IANA database and re-verified against a host build
   (2025b) before release; `edgetz verify` repeats that proof on your
   machine, and the test suite runs it on every change.
3. **`why` names the bug class**, never restates the data. If a case cannot
   be tied to a class of production failure, it does not ship.
4. **`verify: none` is exceptional** and reserved for events outside
   tzdata's model (currently one: Sweden's 1712 February 30).
5. **Ids are permanent.** Corrections change fields, never ids, so fixture
   references in downstream suites survive upgrades.

## A note on future transitions

Cases dated 2026 reflect the rules in force in tzdata 2025b. Governments do
change rules with short notice — that is half the reason this corpus exists.
If a rule changes, `edgetz verify` on an updated host will flag the case,
and the corpus will be corrected in a patch release.
