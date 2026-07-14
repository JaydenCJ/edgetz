"""CLI behavior, driven in-process through ``edgetz.cli.main``.

In-process invocation keeps the suite fast and lets capsys capture output;
the subprocess path (console script, ``python -m edgetz``) is exercised
end-to-end by ``scripts/smoke.sh``.
"""

from __future__ import annotations

import json

import pytest

import edgetz
from edgetz.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip() == f"edgetz {edgetz.__version__}"


def test_list_shows_all_cases(capsys):
    code, out, _ = run(capsys, "list")
    assert code == 0
    assert f"{len(edgetz.cases())} case(s)" in out
    assert "gap-new-york-2026" in out


def test_list_filters_compose(capsys):
    code, out, _ = run(capsys, "list", "--category", "skipped-date")
    assert code == 0
    assert "3 case(s)" in out and "skip-samoa-2011-12-30" in out
    code, out, _ = run(
        capsys, "list", "--zone", "America/New_York", "--tag", "war-time"
    )
    assert code == 0
    assert "gap-new-york-war-time-1942" in out and "1 case(s)" in out


def test_list_rejects_unknown_category_with_exit_2(capsys):
    code, _, err = run(capsys, "list", "--category", "dst-gaps")
    assert code == 2
    assert "unknown category" in err


def test_show_prints_ground_truth(capsys):
    code, out, _ = run(capsys, "show", "fold-havana-double-midnight-2026")
    assert code == 0
    assert "America/Havana" in out
    assert "2026-11-01T04:00:00Z, 2026-11-01T05:00:00Z" in out
    assert "why:" in out
    _, out, _ = run(capsys, "show", "gap-new-york-2026")
    assert "(does not exist)" in out


def test_show_unknown_id_suggests_and_exits_2(capsys):
    code, _, err = run(capsys, "show", "gap-new-york")
    assert code == 2
    assert "did you mean" in err and "gap-new-york-2026" in err


def test_emit_json_to_stdout_is_the_default(capsys):
    code, out, _ = run(capsys, "emit")
    assert code == 0
    document = json.loads(out)
    assert document["generator"] == "edgetz"
    assert document["count"] == len(edgetz.cases())


def test_emit_writes_file_with_confirmation_on_stderr(capsys, tmp_path):
    target = tmp_path / "fixtures.jsonl"
    code, out, err = run(capsys, "emit", "--format", "jsonl", "-o", str(target))
    assert code == 0
    assert out == ""  # data goes to the file, not stdout
    assert str(target) in err
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(edgetz.cases())


def test_emit_filtered_pytest_module(capsys, tmp_path):
    target = tmp_path / "test_dst_gaps.py"
    code, _, _ = run(
        capsys, "emit", "--format", "pytest", "--category", "dst-gap",
        "-o", str(target),
    )
    assert code == 0
    source = target.read_text(encoding="utf-8")
    compile(source, str(target), "exec")
    assert source.count("'category': 'dst-gap'") == 6


def test_usage_errors_exit_2(capsys):
    for argv in (["emit", "--format", "yaml"], []):
        with pytest.raises(SystemExit) as excinfo:
            main(argv)
        assert excinfo.value.code == 2


def test_vocabulary_commands(capsys):
    code, out, _ = run(capsys, "categories")
    assert code == 0
    assert len(out.strip().splitlines()) == 10
    code, out, _ = run(capsys, "zones")
    assert code == 0
    assert "Africa/Monrovia" in out
    assert len(out.strip().splitlines()) == len(edgetz.zones())


def test_stats_summarizes_corpus(capsys):
    code, out, _ = run(capsys, "stats")
    assert code == 0
    assert f"{len(edgetz.cases())} cases" in out
    assert "10 categories" in out
    assert "leap-second table: 27 entries" in out


def test_verify_reports_agreement_and_exits_0(capsys):
    code, out, _ = run(capsys, "verify")
    assert code == 0
    assert "corpus agrees with this host" in out
    code, out, _ = run(capsys, "verify", "--category", "week-53")
    assert code == 0
    assert "5 ok, 0 mismatched, 0 skipped of 5 case(s)" in out


def test_verify_strict_fails_on_unverifiable_cases(capsys):
    # The Swedish-calendar case can never be machine-verified; --strict
    # deliberately turns that skip into a failure signal.
    code, out, _ = run(capsys, "verify", "--strict", "--category", "leap-day")
    assert code == 1
    assert "DISAGREES" in out
