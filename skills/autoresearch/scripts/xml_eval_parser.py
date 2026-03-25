"""XML evaluation parser and grading adapter for MCP server mode.

Parses evaluation.xml QA pairs, scores answers via exact string comparison,
and produces grading.json-compatible output so that score.py, dashboard.py,
and all other infrastructure scripts work unchanged.

Inputs:
    evaluation.xml with <evaluation>/<qa_pair> elements, each having
    <question> and <answer> children.

Outputs:
    Per-question grading.json files in iteration-{i}/eval-{id}/ directories,
    using the same schema that score.py reads (summary.pass_rate).
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_evaluation_xml(xml_path: str | Path) -> list[dict]:
    """Parse evaluation.xml into a list of QA pair dicts.

    Args:
        xml_path: Path to evaluation.xml file.

    Returns:
        List of dicts with keys: id, question, expected_answer.

    Raises:
        FileNotFoundError: If xml_path does not exist.
        ET.ParseError: If XML is malformed.
    """
    xml_path = Path(xml_path)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    qa_pairs = []
    used_ids = set()
    auto_id = 0

    for qa_elem in root.findall(".//qa_pair"):
        explicit_id = qa_elem.get("id")
        if explicit_id:
            qa_id = explicit_id
            used_ids.add(qa_id)
        else:
            auto_id += 1
            while str(auto_id) in used_ids:
                auto_id += 1
            qa_id = str(auto_id)
            used_ids.add(qa_id)

        question_elem = qa_elem.find("question")
        answer_elem = qa_elem.find("answer")

        if question_elem is None or answer_elem is None:
            continue

        question = (question_elem.text or "").strip()
        expected = (answer_elem.text or "").strip()

        if not question:
            continue

        qa_pairs.append({
            "id": str(qa_id),
            "question": question,
            "expected_answer": expected,
        })

    return qa_pairs


def compare_answer(expected: str, actual: str) -> tuple[bool, float, str]:
    """Compare expected and actual answers via normalized string match.

    Normalization: strip whitespace, case-insensitive comparison.

    Args:
        expected: The expected answer string.
        actual: The actual answer string from the MCP subagent.

    Returns:
        Tuple of (passed, score, evidence).
        passed: True if answers match after normalization.
        score: 1.0 if passed, 0.0 if not.
        evidence: Human-readable explanation of the comparison.
    """
    norm_expected = expected.strip().lower()
    norm_actual = actual.strip().lower()

    if norm_expected == norm_actual:
        return (True, 1.0, f"Exact match: '{actual.strip()}'")
    else:
        return (False, 0.0, f"Expected: '{expected.strip()}', Got: '{actual.strip()}'")


def qa_results_to_grading(results: list[dict]) -> dict:
    """Convert QA results to a grading.json-compatible dict.

    Produces the exact schema that score.py reads: summary.pass_rate,
    summary.passed, summary.failed, summary.total, plus expectations[].

    Args:
        results: List of dicts with keys: id, question, expected, actual.

    Returns:
        Dict compatible with grading.json schema.
    """
    if not results:
        return {
            "expectations": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "total": 0,
                "pass_rate": 0.0,
            },
        }

    expectations = []
    passed_count = 0

    for r in results:
        passed, score, evidence = compare_answer(
            r.get("expected", ""), r.get("actual", "")
        )
        if passed:
            passed_count += 1

        expectations.append({
            "text": r.get("question", ""),
            "passed": passed,
            "score": score,
            "evidence": evidence,
            "source": "deterministic",
        })

    total = len(results)
    return {
        "expectations": expectations,
        "summary": {
            "passed": passed_count,
            "failed": total - passed_count,
            "total": total,
            "pass_rate": passed_count / total if total > 0 else 0.0,
        },
    }


def write_per_question_grading(results: list[dict], iteration_dir: Path) -> None:
    """Write one grading.json per QA pair into eval-{id}/ directories.

    This mirrors the existing skill mode layout where each eval case gets
    its own eval-{id}/grading.json. score.py's rglob('grading.json')
    discovers them identically.

    Args:
        results: List of dicts with keys: id, question, expected, actual.
        iteration_dir: Path to the iteration-{i}/ directory.
    """
    iteration_dir = Path(iteration_dir)

    for r in results:
        qa_id = r.get("id", "unknown")
        grading = qa_results_to_grading([r])

        eval_dir = iteration_dir / f"eval-{qa_id}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "grading.json").write_text(json.dumps(grading, indent=2))
