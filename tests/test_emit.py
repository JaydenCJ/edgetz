"""Emitter behavior: every format must be valid, complete, and deterministic.

Determinism is load-bearing: emitted fixtures are meant to be committed, so
two runs must produce byte-identical output or every re-generation would
create diff noise.
"""

from __future__ import annotations

import csv
import io
import json

import pytest

import edgetz
from edgetz.emit import EMITTERS, FORMATS, emit

VERSION = edgetz.__version__


def test_format_registry_matches_emitters():
    assert set(FORMATS) == set(EMITTERS)
    assert set(FORMATS) == {"json", "jsonl", "csv", "markdown", "pytest"}


def test_every_format_is_deterministic(corpus):
    for fmt in FORMATS:
        assert emit(corpus, fmt, VERSION) == emit(corpus, fmt, VERSION), fmt


def test_json_document_shape_and_sorted_keys(corpus):
    document = json.loads(emit(corpus, "json", VERSION))
    assert document["generator"] == "edgetz"
    assert document["version"] == VERSION
    assert document["count"] == len(corpus) == len(document["cases"])
    first_case = document["cases"][0]
    assert list(first_case) == sorted(first_case)  # clean git diffs


def test_json_preserves_utc_pairs_for_folds(corpus):
    document = json.loads(emit(corpus, "json", VERSION))
    fold = next(c for c in document["cases"] if c["id"] == "fold-new-york-2026")
    assert fold["utc"] == ["2026-11-01T05:30:00Z", "2026-11-01T06:30:00Z"]


def test_jsonl_is_one_compact_line_per_case(corpus):
    lines = emit(corpus, "jsonl", VERSION).splitlines()
    assert len(lines) == len(corpus)
    parsed = [json.loads(line) for line in lines]
    assert [entry["id"] for entry in parsed] == [item.id for item in corpus]
    # Compact separators: re-encoding with them must be byte-identical.
    assert lines[0] == json.dumps(
        parsed[0], sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def test_csv_parses_back_with_stdlib(corpus):
    rows = list(csv.DictReader(io.StringIO(emit(corpus, "csv", VERSION))))
    assert len(rows) == len(corpus)
    monrovia = next(row for row in rows if row["id"] == "shift-monrovia-1972")
    assert monrovia["zone"] == "Africa/Monrovia"
    # expect travels as inline JSON so no ground truth is lost in the flat format
    assert json.loads(monrovia["expect"])["offset_before"] == "-00:44:30"


def test_csv_joins_multivalue_fields_with_pipes(corpus):
    rows = list(csv.DictReader(io.StringIO(emit(corpus, "csv", VERSION))))
    fold = next(row for row in rows if row["id"] == "fold-new-york-2026")
    assert fold["utc"] == "2026-11-01T05:30:00Z|2026-11-01T06:30:00Z"


def test_markdown_table_shape(corpus):
    lines = emit(corpus, "markdown", VERSION).splitlines()
    assert lines[0].startswith("| id |")
    assert set(lines[1].replace("|", "").strip()) <= {"-", " "}
    assert len(lines) == len(corpus) + 2
    # Constant column count despite prose content: pipes must be escaped.
    for line in lines[2:]:
        assert line.count("|") - line.count("\\|") == 7, line


def test_pytest_module_compiles_and_is_self_contained(corpus):
    source = emit(corpus, "pytest", VERSION)
    compile(source, "<emitted>", "exec")  # SyntaxError on failure
    assert "import edgetz" not in source  # vendorable by design
    assert "import pytest" in source
    assert "def edge_case(request):" in source


def test_pytest_module_embeds_all_cases(corpus):
    source = emit(corpus, "pytest", VERSION)
    namespace = {"pytest": pytest}
    exec(compile(source, "<emitted>", "exec"), namespace)  # noqa: S102 - own output
    assert len(namespace["CASES"]) == len(corpus)
    assert namespace["IDS"][0] == corpus[0].id


def test_emitting_a_filtered_subset():
    subset = edgetz.cases(category="week-53")
    document = json.loads(emit(subset, "json", VERSION))
    assert document["count"] == 5
    assert all(entry["category"] == "week-53" for entry in document["cases"])


def test_unknown_format_raises_keyerror(corpus):
    with pytest.raises(KeyError):
        emit(corpus, "yaml", VERSION)
