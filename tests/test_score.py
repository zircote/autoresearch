"""Tests for score.py — composite score computation from grading.json files."""

import json
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "autoresearch")
)

from scripts.score import compute_score


def _write_grading(path: Path, pass_rate: float):
    """Helper to write a grading.json file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"summary": {"pass_rate": pass_rate, "passed": 1, "failed": 0, "total": 1}}
        )
    )


def test_mean_pass_rate(tmp_path):
    """Mean pass_rate from multiple grading.json files."""
    iter_dir = tmp_path / "iteration-1"
    _write_grading(iter_dir / "eval1" / "grading.json", 0.8)
    _write_grading(iter_dir / "eval2" / "grading.json", 0.6)

    score = compute_score(tmp_path, 1)
    assert abs(score - 0.7) < 1e-9


def test_empty_directory(tmp_path):
    """Empty iteration directory returns 0.0."""
    (tmp_path / "iteration-0").mkdir()
    assert compute_score(tmp_path, 0) == 0.0


def test_missing_directory(tmp_path):
    """Non-existent iteration directory returns 0.0."""
    assert compute_score(tmp_path, 99) == 0.0


def test_malformed_grading(tmp_path):
    """Malformed grading.json is skipped gracefully."""
    iter_dir = tmp_path / "iteration-1"
    iter_dir.mkdir(parents=True)
    (iter_dir / "grading.json").write_text("not json at all")

    assert compute_score(tmp_path, 1) == 0.0


def test_missing_pass_rate_key(tmp_path):
    """grading.json without summary.pass_rate is skipped."""
    iter_dir = tmp_path / "iteration-1"
    iter_dir.mkdir(parents=True)
    (iter_dir / "grading.json").write_text(json.dumps({"summary": {}}))

    assert compute_score(tmp_path, 1) == 0.0


def test_single_file(tmp_path):
    """Single grading.json returns its pass_rate directly."""
    _write_grading(tmp_path / "iteration-0" / "grading.json", 0.95)
    assert abs(compute_score(tmp_path, 0) - 0.95) < 1e-9


def test_various_pass_rates(tmp_path):
    """Various pass_rate values produce correct mean."""
    iter_dir = tmp_path / "iteration-2"
    rates = [0.0, 0.5, 1.0]
    for i, rate in enumerate(rates):
        _write_grading(iter_dir / f"eval{i}" / "grading.json", rate)

    score = compute_score(tmp_path, 2)
    assert abs(score - 0.5) < 1e-9
