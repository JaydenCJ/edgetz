#!/usr/bin/env bash
# Smoke test for edgetz: browse, export, and verify the corpus end-to-end
# through the real CLI. Self-contained: pure stdlib, no network, idempotent
# (works from a clean tree, no install required).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

# The package has zero runtime dependencies, so running from src/ needs no install.
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/edgetz-smoke.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

fail() { echo "SMOKE FAIL: $1" >&2; exit 1; }

echo "[smoke] python: $("$PYTHON" --version 2>&1)"

# 1. --version agrees with the package metadata.
version_out="$("$PYTHON" -m edgetz --version)"
pkg_version="$("$PYTHON" -c 'import edgetz; print(edgetz.__version__)')"
[ "$version_out" = "edgetz $pkg_version" ] \
  || fail "--version mismatch: '$version_out' vs package '$pkg_version'"

# 2. stats reports a full corpus.
stats_out="$("$PYTHON" -m edgetz stats)"
echo "$stats_out" | sed 's/^/[stats] /'
echo "$stats_out" | grep -q "58 cases, 10 categories" || fail "stats corpus counts wrong"
echo "$stats_out" | grep -q "leap-second table: 27 entries" || fail "leap-second table missing"

# 3. list + filters find the famous cases.
"$PYTHON" -m edgetz list --category dst-gap | grep -q "gap-new-york-2026" \
  || fail "list --category dst-gap missing gap-new-york-2026"
"$PYTHON" -m edgetz list --tag date-line | grep -q "skip-samoa-2011-12-30" \
  || fail "list --tag date-line missing the Samoa date skip"

# 4. show prints curated ground truth for a nonexistent local time.
show_out="$("$PYTHON" -m edgetz show shift-monrovia-1972)"
echo "$show_out" | grep -q -- "-00:44:30" || fail "show lost the seconds-precision offset"
echo "$show_out" | grep -q "does not exist" || fail "show did not flag the gap"

# 5. emit json: valid JSON whose count matches the corpus.
"$PYTHON" -m edgetz emit --format json -o "$WORKDIR/cases.json" 2>/dev/null
"$PYTHON" - "$WORKDIR/cases.json" <<'EOF' || fail "emitted JSON is invalid or short"
import json, sys
doc = json.load(open(sys.argv[1]))
assert doc["count"] == len(doc["cases"]) == 58, doc["count"]
assert doc["generator"] == "edgetz"
EOF

# 6. emit jsonl: exactly one line per case.
jsonl_lines="$("$PYTHON" -m edgetz emit --format jsonl | wc -l | tr -d ' ')"
[ "$jsonl_lines" = "58" ] || fail "jsonl emitted $jsonl_lines lines, want 58"

# 7. emit pytest: generated module is valid Python.
"$PYTHON" -m edgetz emit --format pytest -o "$WORKDIR/test_fixtures.py" 2>/dev/null
"$PYTHON" -c "compile(open('$WORKDIR/test_fixtures.py').read(), 'gen', 'exec')" \
  || fail "generated pytest module does not compile"
grep -q "edge_case" "$WORKDIR/test_fixtures.py" || fail "generated module missing fixture"

# 8. verify: the corpus must agree with this host's tzdata.
verify_out="$("$PYTHON" -m edgetz verify)"
echo "$verify_out" | tail -2 | sed 's/^/[verify] /'
echo "$verify_out" | grep -q "corpus agrees with this host" || fail "verify reported disagreement"

# 9. unknown ids are a usage error (exit 2) with a suggestion.
set +e
err_out="$("$PYTHON" -m edgetz show gap-new-york 2>&1)"
err_rc=$?
set -e
[ "$err_rc" -eq 2 ] || fail "unknown id should exit 2, got $err_rc"
echo "$err_out" | grep -q "did you mean" || fail "unknown id gave no suggestion"

# 10. the polyglot export example runs end to end.
export_out="$("$PYTHON" "$ROOT/examples/export_fixtures.py" "$WORKDIR/fixtures")"
echo "$export_out" | sed 's/^/[export] /'
echo "$export_out" | grep -q "EXPORT OK" || fail "export example did not finish"
[ -s "$WORKDIR/fixtures/cases.csv" ] || fail "export produced no CSV"

echo "SMOKE OK"
