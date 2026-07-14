"""The ``edgetz`` command-line interface.

Subcommands mirror the Python API: browse (``list``, ``show``, ``categories``,
``zones``, ``stats``), export (``emit``), and audit (``verify``). Exit codes:
0 success, 1 verification mismatch, 2 bad usage or unknown identifier.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from typing import List, Optional, Sequence

from . import __version__
from .corpus import LEAP_SECONDS
from .emit import EMITTERS, emit
from .errors import EdgetzError
from .model import Case
from .query import case, cases, categories, kinds, tags, zones
from .verify import tzdata_available, tzdata_version, verify_corpus


def _add_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--category", help="only cases in this category")
    parser.add_argument("--zone", help="only cases in this IANA zone")
    parser.add_argument("--tag", help="only cases carrying this tag")
    parser.add_argument("--kind", help="only cases with this expect-kind")


def _filtered(args: argparse.Namespace) -> Sequence[Case]:
    return cases(
        category=args.category, zone=args.zone, tag=args.tag, kind=args.kind
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edgetz",
        description="Curated pathological datetimes as test fixtures.",
    )
    parser.add_argument(
        "--version", action="version", version=f"edgetz {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list cases (optionally filtered)")
    _add_filters(p_list)

    p_show = sub.add_parser("show", help="show one case in full")
    p_show.add_argument("id", help="case id, e.g. gap-new-york-2026")

    p_emit = sub.add_parser("emit", help="export cases as fixtures")
    _add_filters(p_emit)
    p_emit.add_argument(
        "--format",
        default="json",
        choices=sorted(EMITTERS),
        help="output format (default: json)",
    )
    p_emit.add_argument(
        "-o", "--output", help="write to this file instead of stdout"
    )

    sub.add_parser("categories", help="list categories with descriptions")
    sub.add_parser("zones", help="list IANA zones used by the corpus")
    sub.add_parser("stats", help="corpus summary counts")

    p_verify = sub.add_parser(
        "verify", help="re-check the corpus against host tzdata and calendar math"
    )
    _add_filters(p_verify)
    p_verify.add_argument(
        "--strict",
        action="store_true",
        help="treat skipped checks (missing tzdata) as failures",
    )
    return parser


def _cmd_list(args: argparse.Namespace) -> int:
    selected = _filtered(args)
    width_id = max([len(item.id) for item in selected], default=2)
    width_cat = max([len(item.category) for item in selected], default=8)
    width_zone = max([len(item.zone or "-") for item in selected], default=4)
    print(f"{'ID':<{width_id}}  {'CATEGORY':<{width_cat}}  {'ZONE':<{width_zone}}  WHEN")
    for item in selected:
        print(
            f"{item.id:<{width_id}}  {item.category:<{width_cat}}  "
            f"{(item.zone or '-'):<{width_zone}}  {item.when}"
        )
    print(f"{len(selected)} case(s)")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    item = case(args.id)
    rows = [
        ("id", item.id),
        ("category", item.category),
        ("kind", item.kind),
        ("zone", item.zone or "-"),
    ]
    if item.local is not None:
        note = " (does not exist)" if not item.utc and item.kind in ("gap", "skipped-date") else ""
        rows.append(("local", item.local + note))
    if item.literal is not None:
        rows.append(("literal", item.literal))
    rows.append(("utc", ", ".join(item.utc) if item.utc else "- (no representable instant)"))
    for key in sorted(item.expect):
        if key == "kind":
            continue
        rows.append((f"expect.{key}", str(item.expect[key])))
    rows.append(("tags", ", ".join(item.tags)))
    rows.append(("verify", item.verify))
    rows.append(("source", item.source))
    label_width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"{label:<{label_width}}  {value}")
    print()
    print(textwrap.fill("why: " + item.why, width=78, subsequent_indent="     "))
    return 0


def _cmd_emit(args: argparse.Namespace) -> int:
    rendered = emit(_filtered(args), args.format, __version__)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


def _cmd_categories(_: argparse.Namespace) -> int:
    registry = categories()
    width = max(len(name) for name in registry)
    for name, description in registry.items():
        count = len(cases(category=name))
        print(f"{name:<{width}}  {count:>2}  {description}")
    return 0


def _cmd_zones(_: argparse.Namespace) -> int:
    for zone_name in zones():
        print(f"{zone_name:<22}  {len(cases(zone=zone_name))} case(s)")
    return 0


def _cmd_stats(_: argparse.Namespace) -> int:
    everything = cases()
    print(
        f"edgetz {__version__}: {len(everything)} cases, "
        f"{len(categories())} categories, {len(zones())} zones, "
        f"{len(tags())} tags, {len(kinds())} kinds"
    )
    for name in categories():
        print(f"  {name:<18} {len(cases(category=name)):>2}")
    print(
        f"leap-second table: {len(LEAP_SECONDS)} entries "
        f"({LEAP_SECONDS[0][0]} .. {LEAP_SECONDS[-1][0]}, TAI-UTC now {LEAP_SECONDS[-1][1]}s)"
    )
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    selected = _filtered(args)
    print(f"[verify] host tzdata: {tzdata_version() if tzdata_available() else 'unavailable'}")
    results = verify_corpus(selected)
    counts = {"ok": 0, "mismatch": 0, "skipped": 0}
    for result in results:
        counts[result.status] += 1
        if result.status == "mismatch":
            print(f"[verify] MISMATCH {result.case_id}")
            for detail in result.details:
                print(f"           - {detail}")
    print(
        f"[verify] {counts['ok']} ok, {counts['mismatch']} mismatched, "
        f"{counts['skipped']} skipped of {len(results)} case(s)"
    )
    if counts["mismatch"] or (args.strict and counts["skipped"]):
        print("[verify] corpus DISAGREES with this host — "
              "your tzdata may be stale, or the rules changed")
        return 1
    print("[verify] corpus agrees with this host")
    return 0


_COMMANDS = {
    "list": _cmd_list,
    "show": _cmd_show,
    "emit": _cmd_emit,
    "categories": _cmd_categories,
    "zones": _cmd_zones,
    "stats": _cmd_stats,
    "verify": _cmd_verify,
}


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point; returns the process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except EdgetzError as error:
        print(f"edgetz: {error}", file=sys.stderr)
        return 2
    except BrokenPipeError:  # `edgetz emit | head` is normal usage
        return 0


if __name__ == "__main__":  # pragma: no cover - exercised via __main__.py
    sys.exit(main())
