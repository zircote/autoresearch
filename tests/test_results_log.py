"""Tests for results_log.py — append-only TSV results logging."""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "autoresearch")
)

from scripts.results_log import append, read, COLUMNS


def test_creates_file_with_headers(tmp_path):
    """Creates file with headers if missing."""
    tsv = tmp_path / "results.tsv"
    append(
        tsv,
        {
            "iteration": "0",
            "score": "0.5",
            "best_score": "0.5",
            "action": "baseline",
            "changelog": "initial",
        },
    )

    lines = tsv.read_text().splitlines()
    assert lines[0] == "\t".join(COLUMNS)
    assert len(lines) == 2


def test_append_adds_row(tmp_path):
    """Append adds a row with correct values."""
    tsv = tmp_path / "results.tsv"
    append(
        tsv,
        {
            "iteration": "0",
            "score": "0.75",
            "best_score": "0.75",
            "action": "baseline",
            "changelog": "init",
        },
    )

    rows = read(tsv)
    assert len(rows) == 1
    assert rows[0]["iteration"] == "0"
    assert rows[0]["score"] == "0.75"
    assert rows[0]["action"] == "baseline"


def test_read_returns_list_of_dicts(tmp_path):
    """Read returns list of dicts with string values."""
    tsv = tmp_path / "results.tsv"
    append(tsv, {"iteration": "0", "score": "0.5", "action": "baseline"})

    rows = read(tsv)
    assert isinstance(rows, list)
    assert isinstance(rows[0], dict)
    assert "iteration" in rows[0]
    assert "timestamp" in rows[0]


def test_multiple_appends_maintain_order(tmp_path):
    """Multiple appends maintain insertion order."""
    tsv = tmp_path / "results.tsv"
    for i in range(3):
        append(
            tsv,
            {
                "iteration": str(i),
                "score": str(i * 0.1),
                "best_score": str(i * 0.1),
                "action": f"step{i}",
                "changelog": f"change {i}",
            },
        )

    rows = read(tsv)
    assert len(rows) == 3
    assert [r["iteration"] for r in rows] == ["0", "1", "2"]
    assert [r["action"] for r in rows] == ["step0", "step1", "step2"]


def test_read_missing_file(tmp_path):
    """Reading a missing file returns empty list."""
    tsv = tmp_path / "nonexistent.tsv"
    assert read(tsv) == []


def test_auto_timestamp(tmp_path):
    """Timestamp is auto-added if not provided."""
    tsv = tmp_path / "results.tsv"
    append(tsv, {"iteration": "0", "score": "0.5"})

    rows = read(tsv)
    assert rows[0]["timestamp"] != ""
