"""Tests for xml_eval_parser.py — MCP server mode adapter.

Tests cover: XML parsing, answer comparison, grading adapter schema,
directory layout, and integration with score.py.
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts dir to path
SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "autoresearch" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from xml_eval_parser import (
    compare_answer,
    parse_evaluation_xml,
    qa_results_to_grading,
    write_per_question_grading,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def make_results(pairs):
    """Helper to create results list from (expected, actual) pairs."""
    return [
        {"id": str(i + 1), "question": f"Q{i + 1}", "expected": e, "actual": a}
        for i, (e, a) in enumerate(pairs)
    ]


# ---------------------------------------------------------------------------
# parse_evaluation_xml tests
# ---------------------------------------------------------------------------

class TestParseEvaluationXml:
    def test_basic_parsing(self):
        """Parse 3 QA pairs from a valid XML file."""
        pairs = parse_evaluation_xml(
            FIXTURES_DIR / "mcp-server-sample" / "evals" / "evaluation.xml"
        )
        assert len(pairs) == 3
        assert pairs[0]["id"] == "1"
        assert pairs[0]["question"] == "What is the capital of France?"
        assert pairs[0]["expected_answer"] == "Paris"

    def test_auto_ids(self):
        """Generate sequential IDs when not in XML attributes."""
        pairs = parse_evaluation_xml(FIXTURES_DIR / "evaluation_edge_cases.xml")
        # Third pair has no id attribute — should get auto-id
        no_id_pair = [p for p in pairs if p["question"] == "Auto-id test (no id attribute)"]
        assert len(no_id_pair) == 1
        assert no_id_pair[0]["id"]  # Should have some ID assigned

    def test_missing_file(self):
        """Raise FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            parse_evaluation_xml("/nonexistent/path/evaluation.xml")

    def test_malformed_xml(self, tmp_path):
        """Raise ParseError for malformed XML."""
        bad_xml = tmp_path / "bad.xml"
        bad_xml.write_text("<evaluation><qa_pair><question>test</broken>")
        with pytest.raises(Exception):  # ET.ParseError
            parse_evaluation_xml(bad_xml)

    def test_empty_evaluation(self, tmp_path):
        """Return empty list for XML with no qa_pair elements."""
        empty_xml = tmp_path / "empty.xml"
        empty_xml.write_text("<evaluation></evaluation>")
        pairs = parse_evaluation_xml(empty_xml)
        assert pairs == []

    def test_single_pair(self, tmp_path):
        """Parse a single QA pair."""
        xml = tmp_path / "single.xml"
        xml.write_text(
            '<evaluation><qa_pair id="1">'
            "<question>Q1</question><answer>A1</answer>"
            "</qa_pair></evaluation>"
        )
        pairs = parse_evaluation_xml(xml)
        assert len(pairs) == 1
        assert pairs[0]["question"] == "Q1"
        assert pairs[0]["expected_answer"] == "A1"

    def test_unicode_content(self):
        """Parse QA pairs with unicode content."""
        pairs = parse_evaluation_xml(FIXTURES_DIR / "evaluation_edge_cases.xml")
        unicode_pair = [p for p in pairs if "café" in p["question"]]
        assert len(unicode_pair) == 1
        assert unicode_pair[0]["expected_answer"] == "café"

    def test_whitespace_stripping(self):
        """Strip whitespace from questions and answers."""
        pairs = parse_evaluation_xml(FIXTURES_DIR / "evaluation_edge_cases.xml")
        ws_pair = [p for p in pairs if "Whitespace" in p["question"]]
        assert len(ws_pair) == 1
        assert ws_pair[0]["question"] == "Whitespace padded question"
        assert ws_pair[0]["expected_answer"] == "whitespace"


# ---------------------------------------------------------------------------
# compare_answer tests
# ---------------------------------------------------------------------------

class TestCompareAnswer:
    def test_exact_match(self):
        passed, score, evidence = compare_answer("Paris", "Paris")
        assert passed is True
        assert score == 1.0
        assert "Exact match" in evidence

    def test_case_insensitive(self):
        passed, score, evidence = compare_answer("Paris", "paris")
        assert passed is True
        assert score == 1.0

    def test_case_insensitive_upper(self):
        passed, score, evidence = compare_answer("paris", "PARIS")
        assert passed is True

    def test_whitespace_strip(self):
        passed, score, _ = compare_answer("Paris", "  Paris  \n")
        assert passed is True
        assert score == 1.0

    def test_mismatch(self):
        passed, score, evidence = compare_answer("Paris", "London")
        assert passed is False
        assert score == 0.0
        assert "Expected" in evidence
        assert "Paris" in evidence
        assert "London" in evidence

    def test_empty_expected_empty_actual(self):
        passed, score, _ = compare_answer("", "")
        assert passed is True

    def test_empty_expected_nonempty_actual(self):
        passed, score, _ = compare_answer("", "something")
        assert passed is False

    def test_nonempty_expected_empty_actual(self):
        passed, score, _ = compare_answer("Paris", "")
        assert passed is False

    def test_evidence_on_match(self):
        _, _, evidence = compare_answer("Paris", "Paris")
        assert "Paris" in evidence

    def test_evidence_on_mismatch(self):
        _, _, evidence = compare_answer("Paris", "London")
        assert "Paris" in evidence
        assert "London" in evidence


# ---------------------------------------------------------------------------
# qa_results_to_grading tests
# ---------------------------------------------------------------------------

class TestQaResultsToGrading:
    def test_all_pass(self):
        results = make_results([("A", "A"), ("B", "B"), ("C", "C")])
        grading = qa_results_to_grading(results)
        assert grading["summary"]["pass_rate"] == 1.0
        assert grading["summary"]["passed"] == 3
        assert grading["summary"]["failed"] == 0
        assert grading["summary"]["total"] == 3

    def test_all_fail(self):
        results = make_results([("A", "X"), ("B", "Y"), ("C", "Z")])
        grading = qa_results_to_grading(results)
        assert grading["summary"]["pass_rate"] == 0.0
        assert grading["summary"]["passed"] == 0
        assert grading["summary"]["failed"] == 3

    def test_partial(self):
        results = make_results([("A", "A"), ("B", "X"), ("C", "C")])
        grading = qa_results_to_grading(results)
        assert abs(grading["summary"]["pass_rate"] - 2 / 3) < 0.001
        assert grading["summary"]["passed"] == 2
        assert grading["summary"]["failed"] == 1

    def test_empty_results(self):
        grading = qa_results_to_grading([])
        assert grading["summary"]["pass_rate"] == 0.0
        assert grading["summary"]["total"] == 0
        assert grading["expectations"] == []

    def test_schema_has_expectations(self):
        results = make_results([("A", "A")])
        grading = qa_results_to_grading(results)
        assert "expectations" in grading
        assert isinstance(grading["expectations"], list)
        assert len(grading["expectations"]) == 1

    def test_schema_has_summary(self):
        results = make_results([("A", "A")])
        grading = qa_results_to_grading(results)
        summary = grading["summary"]
        assert "passed" in summary
        assert "failed" in summary
        assert "total" in summary
        assert "pass_rate" in summary

    def test_expectation_fields(self):
        results = make_results([("A", "A")])
        grading = qa_results_to_grading(results)
        exp = grading["expectations"][0]
        assert "text" in exp
        assert "passed" in exp
        assert "evidence" in exp
        assert "source" in exp
        assert exp["source"] == "deterministic"

    def test_conservation_law(self):
        """passed + failed == total for any input."""
        results = make_results([("A", "A"), ("B", "X"), ("C", "C"), ("D", "Y")])
        grading = qa_results_to_grading(results)
        s = grading["summary"]
        assert s["passed"] + s["failed"] == s["total"]


# ---------------------------------------------------------------------------
# write_per_question_grading tests
# ---------------------------------------------------------------------------

class TestWritePerQuestionGrading:
    def test_creates_directories(self, tmp_path):
        results = make_results([("A", "A"), ("B", "X")])
        write_per_question_grading(results, tmp_path)
        assert (tmp_path / "eval-1" / "grading.json").exists()
        assert (tmp_path / "eval-2" / "grading.json").exists()

    def test_valid_json(self, tmp_path):
        results = make_results([("A", "A")])
        write_per_question_grading(results, tmp_path)
        data = json.loads((tmp_path / "eval-1" / "grading.json").read_text())
        assert "summary" in data
        assert "expectations" in data

    def test_pass_rate_correct(self, tmp_path):
        results = make_results([("A", "A"), ("B", "X")])
        write_per_question_grading(results, tmp_path)

        g1 = json.loads((tmp_path / "eval-1" / "grading.json").read_text())
        assert g1["summary"]["pass_rate"] == 1.0

        g2 = json.loads((tmp_path / "eval-2" / "grading.json").read_text())
        assert g2["summary"]["pass_rate"] == 0.0

    def test_empty_results(self, tmp_path):
        write_per_question_grading([], tmp_path)
        # No directories should be created
        assert list(tmp_path.iterdir()) == []

    def test_creates_n_files(self, tmp_path):
        results = make_results([("A", "A"), ("B", "B"), ("C", "C")])
        write_per_question_grading(results, tmp_path)
        grading_files = list(tmp_path.rglob("grading.json"))
        assert len(grading_files) == 3


# ---------------------------------------------------------------------------
# Integration: XML → grading.json → score.py
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_xml_to_score_pipeline(self, tmp_path):
        """End-to-end: parse XML → mock answers → grading.json → score.py."""
        from score import compute_score

        # Parse the fixture XML
        pairs = parse_evaluation_xml(
            FIXTURES_DIR / "mcp-server-sample" / "evals" / "evaluation.xml"
        )

        # Simulate answers: 2 correct, 1 wrong
        results = []
        for qa in pairs:
            if qa["expected_answer"] == "Paris":
                actual = "Paris"
            elif qa["expected_answer"] == "4":
                actual = "4"
            else:
                actual = "Wrong answer"
            results.append({
                "id": qa["id"],
                "question": qa["question"],
                "expected": qa["expected_answer"],
                "actual": actual,
            })

        # Write grading files into workspace layout
        workspace = tmp_path / "workspace"
        iter_dir = workspace / "iteration-0"
        iter_dir.mkdir(parents=True)
        write_per_question_grading(results, iter_dir)

        # Verify score.py can read them
        score = compute_score(workspace, 0)
        # 2/3 correct: each eval-{id} has pass_rate 1.0 or 0.0
        # mean of [1.0, 1.0, 0.0] = 0.666...
        assert abs(score - 2 / 3) < 0.001

    def test_all_pass_score(self, tmp_path):
        """All QA pairs correct → score 1.0."""
        from score import compute_score

        pairs = parse_evaluation_xml(
            FIXTURES_DIR / "mcp-server-sample" / "evals" / "evaluation.xml"
        )
        results = [
            {"id": qa["id"], "question": qa["question"],
             "expected": qa["expected_answer"], "actual": qa["expected_answer"]}
            for qa in pairs
        ]
        workspace = tmp_path / "workspace"
        iter_dir = workspace / "iteration-0"
        iter_dir.mkdir(parents=True)
        write_per_question_grading(results, iter_dir)
        assert compute_score(workspace, 0) == 1.0

    def test_all_fail_score(self, tmp_path):
        """All QA pairs wrong → score 0.0."""
        from score import compute_score

        pairs = parse_evaluation_xml(
            FIXTURES_DIR / "mcp-server-sample" / "evals" / "evaluation.xml"
        )
        results = [
            {"id": qa["id"], "question": qa["question"],
             "expected": qa["expected_answer"], "actual": "WRONG"}
            for qa in pairs
        ]
        workspace = tmp_path / "workspace"
        iter_dir = workspace / "iteration-0"
        iter_dir.mkdir(parents=True)
        write_per_question_grading(results, iter_dir)
        assert compute_score(workspace, 0) == 0.0

    def test_grading_json_serializable(self, tmp_path):
        """Verify grading.json is valid JSON after write."""
        results = [
            {"id": "1", "question": "Q", "expected": "A", "actual": "A"}
        ]
        write_per_question_grading(results, tmp_path)
        raw = (tmp_path / "eval-1" / "grading.json").read_text()
        data = json.loads(raw)  # Should not raise
        assert isinstance(data, dict)
