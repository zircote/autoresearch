"""Tests for dashboard.py — HTML dashboard generation from autoresearch workspaces."""

import json
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "autoresearch")
)

from scripts.dashboard import collect_dashboard_data, generate_dashboard

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sample-skill-autoresearch"


# ---------------------------------------------------------------------------
# collect_dashboard_data tests
# ---------------------------------------------------------------------------


class TestCollectDashboardData:
    """Tests for data collection from workspace."""

    def test_reads_results_tsv(self):
        """Rows from results.tsv are parsed correctly."""
        data = collect_dashboard_data(FIXTURES)
        assert len(data["rows"]) == 3
        assert data["rows"][0]["iteration"] == "0"
        assert data["rows"][0]["action"] == "baseline"

    def test_reads_all_gradings(self):
        """All grading.json files across iterations are collected."""
        data = collect_dashboard_data(FIXTURES)
        assert set(data["gradings"].keys()) == {0, 1, 2}

    def test_iterations_sorted(self):
        """Iterations list is sorted numerically."""
        data = collect_dashboard_data(FIXTURES)
        assert data["iterations"] == [0, 1, 2]

    def test_eval_ids_collected(self):
        """Eval IDs are discovered from grading directories."""
        data = collect_dashboard_data(FIXTURES)
        assert "eval-1" in data["eval_ids"]

    def test_expectations_timeline_populated(self):
        """Expectation timeline tracks pass/fail across iterations."""
        data = collect_dashboard_data(FIXTURES)
        timeline = data["expectations_timeline"]
        assert len(timeline) > 0
        # "The output addresses 'Bob' by name..." passes in all 3 iterations
        bob_key = next(k for k in timeline if "Bob" in k)
        assert timeline[bob_key][0] is True
        assert timeline[bob_key][1] is True
        assert timeline[bob_key][2] is True

    def test_expectations_timeline_tracks_regressions(self):
        """Timeline captures when a passing expectation regresses."""
        data = collect_dashboard_data(FIXTURES)
        timeline = data["expectations_timeline"]
        # "consistent bullet markers" passes in iter 1 but fails in iter 2
        bullet_key = next(k for k in timeline if "bullet" in k.lower())
        assert timeline[bullet_key][0] is False
        assert timeline[bullet_key][1] is True
        assert timeline[bullet_key][2] is False

    def test_source_counts_all_untagged(self):
        """Fixture expectations have no source tag, all counted as untagged."""
        data = collect_dashboard_data(FIXTURES)
        for it in data["iterations"]:
            counts = data["source_counts"][it]
            assert counts["deterministic"] == 0
            assert counts["untagged"] > 0

    def test_empty_workspace(self, tmp_path):
        """Empty workspace returns empty data structures."""
        data = collect_dashboard_data(tmp_path)
        assert data["rows"] == []
        assert data["gradings"] == {}
        assert data["iterations"] == []
        assert data["expectations_timeline"] == {}

    def test_missing_grading_json(self, tmp_path):
        """Iteration dirs without grading.json are skipped."""
        (tmp_path / "iteration-0" / "eval-1").mkdir(parents=True)
        data = collect_dashboard_data(tmp_path)
        assert data["gradings"] == {}

    def test_malformed_grading_json(self, tmp_path):
        """Malformed grading.json files are skipped."""
        eval_dir = tmp_path / "iteration-0" / "eval-1"
        eval_dir.mkdir(parents=True)
        (eval_dir / "grading.json").write_text("not valid json")
        data = collect_dashboard_data(tmp_path)
        assert data["gradings"] == {}

    def test_claims_log_empty_when_no_claims(self):
        """Claims log is empty when grading.json has no claims field."""
        data = collect_dashboard_data(FIXTURES)
        # Our fixture grading.json files don't have claims
        assert data["claims_log"] == []

    def test_eval_feedback_log_empty_when_no_feedback(self):
        """Eval feedback log is empty when no eval_feedback in gradings."""
        data = collect_dashboard_data(FIXTURES)
        assert data["eval_feedback_log"] == []

    def test_metrics_timeline_zero_when_no_metrics(self):
        """Metrics timeline has zero values when grading lacks metrics."""
        data = collect_dashboard_data(FIXTURES)
        for it in data["iterations"]:
            mt = data["metrics_timeline"][it]
            assert mt["metrics"]["total_tool_calls"] == 0
            assert mt["timing"]["total_duration_seconds"] == 0.0


class TestCollectWithRichGrading:
    """Tests with grading.json that includes claims, metrics, feedback."""

    def _write_rich_grading(self, workspace: Path, iteration: int, eval_id: str):
        """Write a grading.json with all optional fields populated."""
        grading = {
            "summary": {"pass_rate": 0.75, "passed": 3, "failed": 1, "total": 4},
            "expectations": [
                {
                    "text": "Output is valid JSON",
                    "passed": True,
                    "evidence": "Parsed successfully",
                    "source": "deterministic",
                },
                {
                    "text": "Contains name field",
                    "passed": True,
                    "evidence": "name field present",
                    "source": "deterministic",
                },
                {
                    "text": "Tone is professional",
                    "passed": True,
                    "evidence": "Formal language used",
                    "source": "llm",
                },
                {
                    "text": "Handles edge case",
                    "passed": False,
                    "evidence": "Crashed on empty input",
                    "source": "llm",
                },
            ],
            "execution_metrics": {
                "tool_calls": {"Read": 3, "Write": 1, "Bash": 5},
                "total_tool_calls": 9,
                "output_chars": 5000,
                "transcript_chars": 2000,
            },
            "timing": {
                "executor_duration_seconds": 45.0,
                "grader_duration_seconds": 12.0,
                "total_duration_seconds": 57.0,
            },
            "claims": [
                {
                    "claim": "Processed 10 records",
                    "type": "factual",
                    "verified": True,
                    "evidence": "Count matches",
                },
                {
                    "claim": "All fields valid",
                    "type": "quality",
                    "verified": False,
                    "evidence": "Missing email field",
                },
            ],
            "eval_feedback": {
                "suggestions": [
                    {
                        "assertion": "Output is valid JSON",
                        "reason": "Too easy — any JSON string passes",
                    }
                ],
                "overall": "Needs stricter content validation",
            },
        }
        path = workspace / f"iteration-{iteration}" / eval_id
        path.mkdir(parents=True)
        (path / "grading.json").write_text(json.dumps(grading))

    def test_source_counts_split(self, tmp_path):
        """Deterministic and LLM expectations are counted separately."""
        self._write_rich_grading(tmp_path, 0, "eval-1")
        data = collect_dashboard_data(tmp_path)
        counts = data["source_counts"][0]
        assert counts["deterministic"] == 2
        assert counts["llm"] == 2
        assert counts["untagged"] == 0

    def test_claims_collected(self, tmp_path):
        """Claims are extracted from grading.json."""
        self._write_rich_grading(tmp_path, 0, "eval-1")
        data = collect_dashboard_data(tmp_path)
        assert len(data["claims_log"]) == 2
        verified = [c for c in data["claims_log"] if c["verified"]]
        unverified = [c for c in data["claims_log"] if not c["verified"]]
        assert len(verified) == 1
        assert len(unverified) == 1

    def test_eval_feedback_collected(self, tmp_path):
        """Eval feedback suggestions are extracted."""
        self._write_rich_grading(tmp_path, 0, "eval-1")
        data = collect_dashboard_data(tmp_path)
        assert len(data["eval_feedback_log"]) == 1
        entry = data["eval_feedback_log"][0]
        assert entry["iteration"] == 0
        assert entry["eval_id"] == "eval-1"
        assert len(entry["suggestions"]) == 1

    def test_metrics_collected(self, tmp_path):
        """Execution metrics and timing are aggregated."""
        self._write_rich_grading(tmp_path, 0, "eval-1")
        data = collect_dashboard_data(tmp_path)
        mt = data["metrics_timeline"][0]
        assert mt["metrics"]["total_tool_calls"] == 9
        assert mt["metrics"]["output_chars"] == 5000
        assert mt["timing"]["executor_duration_seconds"] == 45.0

    def test_metrics_aggregate_across_evals(self, tmp_path):
        """Metrics from multiple evals in same iteration are summed."""
        self._write_rich_grading(tmp_path, 0, "eval-1")
        self._write_rich_grading(tmp_path, 0, "eval-2")
        data = collect_dashboard_data(tmp_path)
        mt = data["metrics_timeline"][0]
        assert mt["metrics"]["total_tool_calls"] == 18  # 9 + 9
        assert mt["timing"]["total_duration_seconds"] == 114.0  # 57 + 57


# ---------------------------------------------------------------------------
# generate_dashboard tests
# ---------------------------------------------------------------------------


class TestGenerateDashboard:
    """Tests for the HTML dashboard output."""

    def test_returns_valid_html(self):
        """Dashboard output is a complete HTML document."""
        html = generate_dashboard(FIXTURES)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_title(self):
        """Dashboard contains the skill name in the title."""
        html = generate_dashboard(FIXTURES)
        assert "sample-skill" in html

    def test_contains_score_trajectory(self):
        """Dashboard includes score trajectory section."""
        html = generate_dashboard(FIXTURES)
        assert "Score Trajectory" in html

    def test_contains_all_iterations_in_table(self):
        """Trajectory table has rows for all iterations."""
        html = generate_dashboard(FIXTURES)
        assert "baseline" in html
        assert "kept" in html
        assert "reverted" in html

    def test_contains_expectation_heatmap(self):
        """Dashboard includes expectation heatmap."""
        html = generate_dashboard(FIXTURES)
        assert "Expectation Heatmap" in html
        assert "PASS" in html
        assert "FAIL" in html

    def test_contains_per_eval_breakdown(self):
        """Dashboard includes per-eval breakdown."""
        html = generate_dashboard(FIXTURES)
        assert "Per-Eval Breakdown" in html
        assert "eval-1" in html

    def test_contains_svg_chart(self):
        """Dashboard includes an SVG line chart."""
        html = generate_dashboard(FIXTURES)
        assert "<svg" in html
        assert "viewBox" in html

    def test_contains_stats_cards(self):
        """Dashboard includes stat cards with scores."""
        html = generate_dashboard(FIXTURES)
        assert "Starting Score" in html
        assert "Best Score" in html
        assert "Improvement" in html

    def test_no_external_dependencies(self):
        """Dashboard has no external stylesheet or script links."""
        html = generate_dashboard(FIXTURES)
        assert 'rel="stylesheet"' not in html
        assert "<script src=" not in html
        assert "cdn" not in html.lower()

    def test_empty_workspace(self, tmp_path):
        """Empty workspace produces valid HTML with no-data messages."""
        html = generate_dashboard(tmp_path)
        assert "<!DOCTYPE html>" in html
        assert "No data" in html or "No iterations" in html

    def test_single_iteration(self, tmp_path):
        """Single iteration workspace produces valid dashboard."""
        eval_dir = tmp_path / "iteration-0" / "eval-1"
        eval_dir.mkdir(parents=True)
        (eval_dir / "grading.json").write_text(
            json.dumps(
                {
                    "summary": {"pass_rate": 0.8, "passed": 4, "failed": 1, "total": 5},
                    "expectations": [
                        {"text": "Test exp", "passed": True, "evidence": "ok"}
                    ],
                }
            )
        )
        html = generate_dashboard(tmp_path)
        assert "<!DOCTYPE html>" in html
        assert "Iter 0" in html

    def test_html_escapes_special_chars(self, tmp_path):
        """Special HTML characters in expectations are escaped."""
        eval_dir = tmp_path / "iteration-0" / "eval-1"
        eval_dir.mkdir(parents=True)
        (eval_dir / "grading.json").write_text(
            json.dumps(
                {
                    "summary": {"pass_rate": 1.0, "passed": 1, "failed": 0, "total": 1},
                    "expectations": [
                        {
                            "text": 'Output contains <script>alert("xss")</script>',
                            "passed": True,
                            "evidence": "found",
                        }
                    ],
                }
            )
        )
        html = generate_dashboard(tmp_path)
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_writes_to_file(self, tmp_path):
        """Dashboard can be written to a file and read back."""
        html = generate_dashboard(FIXTURES)
        out = tmp_path / "dashboard.html"
        out.write_text(html)
        content = out.read_text()
        assert content.startswith("<!DOCTYPE html>")
        assert len(content) > 1000


class TestGenerateDashboardWithRichData:
    """Tests for dashboard with claims, metrics, and feedback."""

    def _setup_rich_workspace(self, workspace: Path):
        """Create a workspace with rich grading data."""
        import csv

        # Write results.tsv
        tsv = workspace / "results.tsv"
        with open(tsv, "w", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "iteration", "timestamp", "score", "best_score", "action", "changelog"
                ],
                delimiter="\t",
            )
            w.writeheader()
            w.writerow(
                {
                    "iteration": "0",
                    "timestamp": "2026-03-20T10:00:00Z",
                    "score": "0.75",
                    "best_score": "0.75",
                    "action": "baseline",
                    "changelog": "Initial",
                }
            )

        # Write grading with all fields
        eval_dir = workspace / "iteration-0" / "eval-1"
        eval_dir.mkdir(parents=True)
        (eval_dir / "grading.json").write_text(
            json.dumps(
                {
                    "summary": {"pass_rate": 0.75, "passed": 3, "failed": 1, "total": 4},
                    "expectations": [
                        {
                            "text": "Valid JSON",
                            "passed": True,
                            "evidence": "ok",
                            "source": "deterministic",
                        },
                        {
                            "text": "Good tone",
                            "passed": False,
                            "evidence": "too casual",
                            "source": "llm",
                        },
                    ],
                    "execution_metrics": {
                        "total_tool_calls": 12,
                        "output_chars": 8000,
                        "transcript_chars": 3000,
                    },
                    "timing": {
                        "executor_duration_seconds": 60.0,
                        "grader_duration_seconds": 15.0,
                        "total_duration_seconds": 75.0,
                    },
                    "claims": [
                        {
                            "claim": "Used correct API",
                            "type": "process",
                            "verified": True,
                            "evidence": "API call in transcript",
                        }
                    ],
                    "eval_feedback": {
                        "suggestions": [
                            {"reason": "Add content validation assertion"}
                        ],
                        "overall": "Needs more depth",
                    },
                }
            )
        )

    def test_contains_claims_section(self, tmp_path):
        """Dashboard shows claims verification table."""
        self._setup_rich_workspace(tmp_path)
        html = generate_dashboard(tmp_path)
        assert "Claims Verification" in html
        assert "Used correct API" in html

    def test_contains_metrics_section(self, tmp_path):
        """Dashboard shows execution metrics."""
        self._setup_rich_workspace(tmp_path)
        html = generate_dashboard(tmp_path)
        assert "Execution Metrics" in html
        assert "Tool Calls" in html

    def test_contains_timing(self, tmp_path):
        """Dashboard shows timing data."""
        self._setup_rich_workspace(tmp_path)
        html = generate_dashboard(tmp_path)
        assert "Executor (s)" in html
        assert "60.0" in html

    def test_contains_eval_feedback(self, tmp_path):
        """Dashboard shows eval feedback log."""
        self._setup_rich_workspace(tmp_path)
        html = generate_dashboard(tmp_path)
        assert "Eval Feedback Log" in html
        assert "Add content validation assertion" in html

    def test_contains_source_counts(self, tmp_path):
        """Dashboard shows deterministic vs LLM split."""
        self._setup_rich_workspace(tmp_path)
        html = generate_dashboard(tmp_path)
        assert "Deterministic vs LLM" in html
