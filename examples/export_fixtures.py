#!/usr/bin/env python3
"""Export the edgetz corpus for non-Python test suites.

Writes ``cases.json``, ``cases.jsonl``, and ``cases.csv`` into the directory
given as the first argument, then prints a per-file summary. Everything is
deterministic, so committing the output to another repository produces stable
diffs when a new edgetz release adds cases.

Usage:  python examples/export_fixtures.py OUTDIR [category]
"""

from __future__ import annotations

import sys
from pathlib import Path

import edgetz
from edgetz.emit import emit


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    outdir = Path(argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    category = argv[2] if len(argv) > 2 else None
    selected = edgetz.cases(category=category)

    for fmt, filename in (("json", "cases.json"), ("jsonl", "cases.jsonl"), ("csv", "cases.csv")):
        path = outdir / filename
        path.write_text(emit(selected, fmt, edgetz.__version__), encoding="utf-8")
        print(f"[export] {path} ({len(selected)} cases, {path.stat().st_size} bytes)")

    print(f"[export] categories: {', '.join(sorted({c.category for c in selected}))}")
    print("EXPORT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
