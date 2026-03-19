"""Comprehensive tests for deterministic_checker.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills.autoresearch.scripts.deterministic_checker import (
    MISSING,
    _resolve_path,
    merge_deterministic_into_grading,
    run_deterministic_checks,
)


# =========================================================================
# Path Resolution Tests
# =========================================================================


class TestResolvePath:
    def test_resolve_path_simple(self):
        data = {"name": "foo"}
        assert _resolve_path(data, ".name") == "foo"

    def test_resolve_path_nested(self):
        data = {"server": {"type": "node"}}
        assert _resolve_path(data, ".server.type") == "node"

    def test_resolve_path_array_index(self):
        data = {"tools": [{"name": "grep"}, {"name": "find"}]}
        assert _resolve_path(data, ".tools[0].name") == "grep"

    def test_resolve_path_missing_key(self):
        data = {"name": "foo"}
        assert _resolve_path(data, ".missing") is MISSING

    def test_resolve_path_empty(self):
        data = {"name": "foo"}
        assert _resolve_path(data, "") is data
        assert _resolve_path(data, ".") is data


# =========================================================================
# json_valid
# =========================================================================


class TestJsonValid:
    def test_pass_valid_json(self, tmp_path: Path):
        (tmp_path / "data.json").write_text('{"key": "value"}')
        result = run_deterministic_checks(
            [{"type": "json_valid", "file": "data.json"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_invalid_json(self, tmp_path: Path):
        (tmp_path / "bad.json").write_text("{not valid json")
        result = run_deterministic_checks(
            [{"type": "json_valid", "file": "bad.json"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is False
        assert "Invalid JSON" in result["expectations"][0]["evidence"]

    def test_fail_missing_file(self, tmp_path: Path):
        result = run_deterministic_checks(
            [{"type": "json_valid", "file": "nope.json"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is False
        assert "not found" in result["expectations"][0]["evidence"]


# =========================================================================
# json_field_equals
# =========================================================================


class TestJsonFieldEquals:
    def test_pass_string_value(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"name": "foo"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_equals",
                    "file": "d.json",
                    "path": ".name",
                    "expected": "foo",
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_pass_numeric_value(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"count": 42}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_equals",
                    "file": "d.json",
                    "path": ".count",
                    "expected": 42,
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_value_mismatch(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"name": "bar"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_equals",
                    "file": "d.json",
                    "path": ".name",
                    "expected": "foo",
                }
            ],
            tmp_path,
        )
        exp = result["expectations"][0]
        assert exp["passed"] is False
        assert "bar" in exp["evidence"]

    def test_fail_path_not_found(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"name": "foo"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_equals",
                    "file": "d.json",
                    "path": ".missing",
                    "expected": "x",
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False
        assert "not found" in result["expectations"][0]["evidence"]


# =========================================================================
# json_field_exists
# =========================================================================


class TestJsonFieldExists:
    def test_pass_path_exists(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"server": {"type": "node"}}')
        result = run_deterministic_checks(
            [{"type": "json_field_exists", "file": "d.json", "path": ".server.type"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_path_missing(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"server": {}}')
        result = run_deterministic_checks(
            [{"type": "json_field_exists", "file": "d.json", "path": ".server.type"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False


# =========================================================================
# json_field_absent
# =========================================================================


class TestJsonFieldAbsent:
    def test_pass_path_does_not_exist(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"name": "foo"}')
        result = run_deterministic_checks(
            [{"type": "json_field_absent", "file": "d.json", "path": ".missing"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_path_exists(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"name": "foo"}')
        result = run_deterministic_checks(
            [{"type": "json_field_absent", "file": "d.json", "path": ".name"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False


# =========================================================================
# json_field_matches
# =========================================================================


class TestJsonFieldMatches:
    def test_pass_regex_matches(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"version": "1.2.3"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_matches",
                    "file": "d.json",
                    "path": ".version",
                    "pattern": r"^\d+\.\d+\.\d+$",
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_regex_no_match(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"version": "abc"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_matches",
                    "file": "d.json",
                    "path": ".version",
                    "pattern": r"^\d+$",
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False

    def test_fail_path_not_found(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"name": "foo"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_matches",
                    "file": "d.json",
                    "path": ".missing",
                    "pattern": ".*",
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False
        assert "not found" in result["expectations"][0]["evidence"]


# =========================================================================
# json_field_count
# =========================================================================


class TestJsonFieldCount:
    def test_pass_eq(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"items": [1, 2, 3]}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_count",
                    "file": "d.json",
                    "path": ".items",
                    "op": "eq",
                    "expected": 3,
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_pass_gte(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"items": [1, 2, 3]}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_count",
                    "file": "d.json",
                    "path": ".items",
                    "op": "gte",
                    "expected": 2,
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_pass_lte(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"items": [1, 2]}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_count",
                    "file": "d.json",
                    "path": ".items",
                    "op": "lte",
                    "expected": 5,
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_count_mismatch(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"items": [1]}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_field_count",
                    "file": "d.json",
                    "path": ".items",
                    "op": "eq",
                    "expected": 3,
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False


# =========================================================================
# json_array_contains
# =========================================================================


class TestJsonArrayContains:
    def test_pass_matching_element(self, tmp_path: Path):
        data = {"tools": [{"name": "grep", "lang": "c"}, {"name": "find", "lang": "c"}]}
        (tmp_path / "d.json").write_text(json.dumps(data))
        result = run_deterministic_checks(
            [
                {
                    "type": "json_array_contains",
                    "file": "d.json",
                    "path": ".tools",
                    "match": {"name": "grep"},
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail_no_matching_element(self, tmp_path: Path):
        data = {"tools": [{"name": "grep"}]}
        (tmp_path / "d.json").write_text(json.dumps(data))
        result = run_deterministic_checks(
            [
                {
                    "type": "json_array_contains",
                    "file": "d.json",
                    "path": ".tools",
                    "match": {"name": "sed"},
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False

    def test_fail_path_not_array(self, tmp_path: Path):
        (tmp_path / "d.json").write_text('{"tools": "not an array"}')
        result = run_deterministic_checks(
            [
                {
                    "type": "json_array_contains",
                    "file": "d.json",
                    "path": ".tools",
                    "match": {"name": "x"},
                }
            ],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False
        assert "not an array" in result["expectations"][0]["evidence"]


# =========================================================================
# file_exists / file_not_exists
# =========================================================================


class TestFileExists:
    def test_pass(self, tmp_path: Path):
        (tmp_path / "readme.md").write_text("hello")
        result = run_deterministic_checks(
            [{"type": "file_exists", "file": "readme.md"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail(self, tmp_path: Path):
        result = run_deterministic_checks(
            [{"type": "file_exists", "file": "nope.txt"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is False


class TestFileNotExists:
    def test_pass(self, tmp_path: Path):
        result = run_deterministic_checks(
            [{"type": "file_not_exists", "file": "nope.txt"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail(self, tmp_path: Path):
        (tmp_path / "exists.txt").write_text("hi")
        result = run_deterministic_checks(
            [{"type": "file_not_exists", "file": "exists.txt"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is False


# =========================================================================
# file_contains / file_not_contains
# =========================================================================


class TestFileContains:
    def test_pass(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text("hello world")
        result = run_deterministic_checks(
            [{"type": "file_contains", "file": "log.txt", "literal": "hello"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text("hello world")
        result = run_deterministic_checks(
            [{"type": "file_contains", "file": "log.txt", "literal": "goodbye"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False


class TestFileNotContains:
    def test_pass(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text("hello world")
        result = run_deterministic_checks(
            [{"type": "file_not_contains", "file": "log.txt", "literal": "goodbye"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text("hello world")
        result = run_deterministic_checks(
            [{"type": "file_not_contains", "file": "log.txt", "literal": "hello"}],
            tmp_path,
        )
        assert result["expectations"][0]["passed"] is False


# =========================================================================
# regex_match
# =========================================================================


class TestRegexMatch:
    def test_pass(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text("error code 404 found")
        result = run_deterministic_checks(
            [{"type": "regex_match", "file": "log.txt", "pattern": r"\d{3}"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is True

    def test_fail(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text("no numbers here")
        result = run_deterministic_checks(
            [{"type": "regex_match", "file": "log.txt", "pattern": r"\d+"}], tmp_path
        )
        assert result["expectations"][0]["passed"] is False


# =========================================================================
# shell_command
# =========================================================================


class TestShellCommand:
    def test_pass_exit_zero(self, tmp_path: Path):
        result = run_deterministic_checks(
            [{"type": "shell_command", "command": "echo hello"}], tmp_path
        )
        exp = result["expectations"][0]
        assert exp["passed"] is True
        assert "Exit 0" in exp["evidence"]

    def test_fail_exit_nonzero(self, tmp_path: Path):
        result = run_deterministic_checks(
            [{"type": "shell_command", "command": "exit 1"}], tmp_path
        )
        exp = result["expectations"][0]
        assert exp["passed"] is False
        assert "Exit 1" in exp["evidence"]


# =========================================================================
# Integration: run_deterministic_checks
# =========================================================================


class TestRunDeterministicChecks:
    def test_mixed_results(self, tmp_path: Path):
        (tmp_path / "data.json").write_text('{"name": "foo"}')
        checks = [
            {"type": "json_valid", "file": "data.json"},
            {"type": "file_exists", "file": "missing.txt"},
            {
                "type": "json_field_equals",
                "file": "data.json",
                "path": ".name",
                "expected": "foo",
            },
            {"type": "file_exists", "file": "also_missing.txt"},
        ]
        result = run_deterministic_checks(checks, tmp_path)
        summary = result["summary"]
        assert summary["passed"] == 2
        assert summary["failed"] == 2
        assert summary["total"] == 4
        assert summary["pass_rate"] == 0.5

    def test_all_pass(self, tmp_path: Path):
        (tmp_path / "a.json").write_text('{"k": "v"}')
        checks = [
            {"type": "json_valid", "file": "a.json"},
            {"type": "file_exists", "file": "a.json"},
        ]
        result = run_deterministic_checks(checks, tmp_path)
        assert result["summary"]["pass_rate"] == 1.0

    def test_empty_checks(self, tmp_path: Path):
        result = run_deterministic_checks([], tmp_path)
        assert result["summary"]["total"] == 0
        assert result["summary"]["pass_rate"] == 0.0

    def test_unknown_check_type(self, tmp_path: Path):
        checks = [{"type": "bogus_check", "description": "A bogus check"}]
        result = run_deterministic_checks(checks, tmp_path)
        exp = result["expectations"][0]
        assert exp["passed"] is False
        assert "Unknown check type" in exp["evidence"]
        assert exp["text"] == "A bogus check"


# =========================================================================
# Merge: merge_deterministic_into_grading
# =========================================================================


class TestMergeDeterministicIntoGrading:
    def test_combines_expectations_deterministic_first(self, tmp_path: Path):
        det = {
            "expectations": [
                {
                    "text": "det1",
                    "passed": True,
                    "evidence": "ok",
                    "source": "deterministic",
                }
            ]
        }
        grading = {
            "expectations": [{"text": "llm1", "passed": False, "evidence": "bad"}],
            "summary": {"passed": 0, "failed": 1, "total": 1, "pass_rate": 0.0},
        }
        det_path = tmp_path / "det.json"
        grading_path = tmp_path / "grading.json"
        det_path.write_text(json.dumps(det))
        grading_path.write_text(json.dumps(grading))

        merge_deterministic_into_grading(det_path, grading_path)

        merged = json.loads(grading_path.read_text())
        assert len(merged["expectations"]) == 2
        assert merged["expectations"][0]["text"] == "det1"
        assert merged["expectations"][1]["text"] == "llm1"

    def test_recomputes_pass_rate(self, tmp_path: Path):
        det = {
            "expectations": [
                {
                    "text": "d1",
                    "passed": True,
                    "evidence": "ok",
                    "source": "deterministic",
                },
                {
                    "text": "d2",
                    "passed": True,
                    "evidence": "ok",
                    "source": "deterministic",
                },
            ]
        }
        grading = {
            "expectations": [
                {"text": "l1", "passed": False, "evidence": "bad"},
                {"text": "l2", "passed": True, "evidence": "good"},
            ],
            "summary": {"passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5},
        }
        det_path = tmp_path / "det.json"
        grading_path = tmp_path / "grading.json"
        det_path.write_text(json.dumps(det))
        grading_path.write_text(json.dumps(grading))

        merge_deterministic_into_grading(det_path, grading_path)

        merged = json.loads(grading_path.read_text())
        assert merged["summary"]["total"] == 4
        assert merged["summary"]["passed"] == 3
        assert merged["summary"]["failed"] == 1
        assert merged["summary"]["pass_rate"] == 0.75

    def test_tags_llm_expectations_with_source(self, tmp_path: Path):
        det = {
            "expectations": [
                {
                    "text": "d1",
                    "passed": True,
                    "evidence": "ok",
                    "source": "deterministic",
                }
            ]
        }
        grading = {
            "expectations": [
                {"text": "l1", "passed": True, "evidence": "good"},
                {
                    "text": "l2",
                    "passed": True,
                    "evidence": "good",
                    "source": "existing",
                },
            ],
            "summary": {"passed": 2, "failed": 0, "total": 2, "pass_rate": 1.0},
        }
        det_path = tmp_path / "det.json"
        grading_path = tmp_path / "grading.json"
        det_path.write_text(json.dumps(det))
        grading_path.write_text(json.dumps(grading))

        merge_deterministic_into_grading(det_path, grading_path)

        merged = json.loads(grading_path.read_text())
        # l1 had no source -> tagged "llm"
        assert merged["expectations"][1]["source"] == "llm"
        # l2 already had "existing" source -> unchanged
        assert merged["expectations"][2]["source"] == "existing"


# =========================================================================
# Description field
# =========================================================================


class TestDescriptionField:
    def test_description_used_as_text(self, tmp_path: Path):
        (tmp_path / "f.json").write_text('{"a": 1}')
        checks = [
            {
                "type": "json_valid",
                "file": "f.json",
                "description": "Manifest must be valid JSON",
            }
        ]
        result = run_deterministic_checks(checks, tmp_path)
        assert result["expectations"][0]["text"] == "Manifest must be valid JSON"
