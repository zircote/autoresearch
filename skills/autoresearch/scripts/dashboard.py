"""HTML dashboard generator for autoresearch improvement loops.

Reads results.tsv and all grading.json files from a workspace to produce
a self-contained HTML dashboard with score trajectory, expectation heatmap,
per-iteration breakdowns, and execution metrics.

Inputs:
    workspace: Path to the autoresearch workspace directory

Outputs:
    generate_dashboard() returns a self-contained HTML string
    collect_dashboard_data() returns the raw data dict for testing
"""

import json
from html import escape
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------


def _read_results_tsv(workspace: Path) -> list[dict]:
    """Parse results.tsv into a list of row dicts."""
    tsv = workspace / "results.tsv"
    if not tsv.exists():
        return []
    import csv

    with open(tsv, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _read_all_gradings(workspace: Path) -> dict[int, dict[str, Any]]:
    """Read all grading.json files, keyed by (iteration, eval_id).

    Returns: {iteration_num: {eval_id: grading_dict}}
    """
    result: dict[int, dict[str, Any]] = {}
    for iter_dir in sorted(workspace.glob("iteration-*")):
        try:
            iteration = int(iter_dir.name.split("-", 1)[1])
        except (ValueError, IndexError):
            continue
        evals: dict[str, Any] = {}
        for grading_file in sorted(iter_dir.rglob("grading.json")):
            eval_id = grading_file.parent.name
            try:
                evals[eval_id] = json.loads(grading_file.read_text())
            except (json.JSONDecodeError, OSError):
                continue
        if evals:
            result[iteration] = evals
    return result


def collect_dashboard_data(workspace: Path) -> dict[str, Any]:
    """Collect all data needed to render the dashboard.

    Returns a dict with:
        rows: list of results.tsv row dicts
        gradings: {iteration: {eval_id: grading_dict}}
        expectations_timeline: {expectation_text: {iteration: bool}}
        eval_ids: sorted list of all eval ids seen
        iterations: sorted list of all iteration numbers
    """
    workspace = Path(workspace)
    rows = _read_results_tsv(workspace)
    gradings = _read_all_gradings(workspace)

    iterations = sorted(gradings.keys())
    eval_ids: set[str] = set()
    for evals in gradings.values():
        eval_ids.update(evals.keys())
    eval_ids_sorted = sorted(eval_ids)

    # Build expectation timeline: track each unique expectation across iterations
    expectations_timeline: dict[str, dict[int, bool | None]] = {}
    for iteration, evals in sorted(gradings.items()):
        for grading in evals.values():
            for exp in grading.get("expectations", []):
                text = exp.get("expectation") or exp.get("text", "")
                if text not in expectations_timeline:
                    expectations_timeline[text] = {}
                expectations_timeline[text][iteration] = exp.get("passed")

    # Collect execution metrics and timing per iteration
    metrics_timeline: dict[int, dict[str, Any]] = {}
    for iteration, evals in sorted(gradings.items()):
        combined_metrics: dict[str, Any] = {
            "total_tool_calls": 0,
            "output_chars": 0,
            "transcript_chars": 0,
        }
        combined_timing: dict[str, float] = {
            "executor_duration_seconds": 0.0,
            "grader_duration_seconds": 0.0,
            "total_duration_seconds": 0.0,
        }
        for grading in evals.values():
            em = grading.get("execution_metrics", {})
            for key in combined_metrics:
                combined_metrics[key] += em.get(key, 0)
            tm = grading.get("timing", {})
            for key in combined_timing:
                combined_timing[key] += tm.get(key, 0.0)
        metrics_timeline[iteration] = {
            "metrics": combined_metrics,
            "timing": combined_timing,
        }

    # Collect eval feedback across iterations
    eval_feedback_log: list[dict[str, Any]] = []
    for iteration, evals in sorted(gradings.items()):
        for eval_id, grading in sorted(evals.items()):
            feedback = grading.get("eval_feedback", {})
            suggestions = feedback.get("suggestions", [])
            if suggestions:
                eval_feedback_log.append(
                    {
                        "iteration": iteration,
                        "eval_id": eval_id,
                        "suggestions": suggestions,
                        "overall": feedback.get("overall", ""),
                    }
                )

    # Count deterministic vs LLM expectations per iteration
    source_counts: dict[int, dict[str, int]] = {}
    for iteration, evals in sorted(gradings.items()):
        counts = {"deterministic": 0, "llm": 0, "untagged": 0}
        for grading in evals.values():
            for exp in grading.get("expectations", []):
                source = exp.get("source", "untagged")
                if source == "deterministic":
                    counts["deterministic"] += 1
                elif source == "llm":
                    counts["llm"] += 1
                else:
                    counts["untagged"] += 1
        source_counts[iteration] = counts

    # Collect claims across iterations
    claims_log: list[dict[str, Any]] = []
    for iteration, evals in sorted(gradings.items()):
        for eval_id, grading in sorted(evals.items()):
            for claim in grading.get("claims", []):
                claims_log.append(
                    {
                        "iteration": iteration,
                        "eval_id": eval_id,
                        **claim,
                    }
                )

    return {
        "rows": rows,
        "gradings": gradings,
        "expectations_timeline": expectations_timeline,
        "eval_ids": eval_ids_sorted,
        "iterations": iterations,
        "metrics_timeline": metrics_timeline,
        "eval_feedback_log": eval_feedback_log,
        "source_counts": source_counts,
        "claims_log": claims_log,
    }


# ---------------------------------------------------------------------------
# SVG chart helpers
# ---------------------------------------------------------------------------


def _svg_line_chart(
    points: list[tuple[int, float]],
    width: int = 600,
    height: int = 200,
    color: str = "#2563eb",
) -> str:
    """Generate an SVG line chart from (x_index, y_value) points.

    y values are expected in [0.0, 1.0].
    """
    if not points:
        return "<p>No data for chart.</p>"

    pad_left = 50
    pad_right = 20
    pad_top = 20
    pad_bottom = 40
    chart_w = width - pad_left - pad_right
    chart_h = height - pad_top - pad_bottom

    x_count = max(p[0] for p in points) + 1 if points else 1

    def tx(x: int) -> float:
        return pad_left + (x / max(x_count - 1, 1)) * chart_w

    def ty(y: float) -> float:
        return pad_top + (1.0 - y) * chart_h

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'style="max-width:{width}px;width:100%;height:auto;font-family:system-ui,sans-serif;font-size:11px">'
    )

    # Grid lines
    for pct in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = ty(pct)
        lines.append(
            f'<line x1="{pad_left}" y1="{y}" x2="{width - pad_right}" y2="{y}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{pad_left - 5}" y="{y + 4}" text-anchor="end" fill="#6b7280">'
            f"{pct:.0%}</text>"
        )

    # X axis labels
    for p in points:
        x = tx(p[0])
        lines.append(
            f'<text x="{x}" y="{height - 8}" text-anchor="middle" fill="#6b7280">'
            f"Iter {p[0]}</text>"
        )

    # Line path
    if len(points) > 1:
        path_d = " ".join(
            f"{'M' if i == 0 else 'L'} {tx(p[0]):.1f} {ty(p[1]):.1f}"
            for i, p in enumerate(points)
        )
        lines.append(
            f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2.5" '
            f'stroke-linejoin="round"/>'
        )

    # Data points
    for p in points:
        x, y = tx(p[0]), ty(p[1])
        lines.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
        lines.append(
            f'<text x="{x}" y="{y - 10}" text-anchor="middle" fill="{color}" '
            f'font-weight="600">{p[1]:.0%}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_CSS = """
:root {
    --pass: #16a34a; --fail: #dc2626; --neutral: #9ca3af;
    --bg: #ffffff; --bg2: #f9fafb; --border: #e5e7eb;
    --text: #111827; --text2: #6b7280;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, -apple-system, sans-serif; color: var(--text);
       background: var(--bg); padding: 24px; max-width: 1100px; margin: 0 auto;
       line-height: 1.5; }
h1 { font-size: 1.5rem; margin-bottom: 4px; }
h2 { font-size: 1.15rem; margin: 28px 0 12px; border-bottom: 2px solid var(--border);
     padding-bottom: 6px; }
.subtitle { color: var(--text2); margin-bottom: 20px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
         gap: 12px; margin-bottom: 24px; }
.stat { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px;
        padding: 14px; }
.stat .label { font-size: 0.8rem; color: var(--text2); text-transform: uppercase;
               letter-spacing: 0.05em; }
.stat .value { font-size: 1.4rem; font-weight: 700; margin-top: 2px; }
.stat .value.up { color: var(--pass); }
.stat .value.down { color: var(--fail); }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-bottom: 16px; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }
th { background: var(--bg2); font-weight: 600; position: sticky; top: 0; }
tr:hover { background: #f3f4f6; }
.pass { color: var(--pass); font-weight: 600; }
.fail { color: var(--fail); font-weight: 600; }
.cell-pass { background: #dcfce7; text-align: center; }
.cell-fail { background: #fee2e2; text-align: center; }
.cell-na { background: var(--bg2); text-align: center; color: var(--neutral); }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem;
         font-weight: 600; }
.badge-kept { background: #dcfce7; color: var(--pass); }
.badge-reverted { background: #fee2e2; color: var(--fail); }
.badge-baseline { background: #e0e7ff; color: #4338ca; }
details { margin-bottom: 8px; }
summary { cursor: pointer; font-weight: 600; padding: 6px 0; }
.chart-container { margin: 16px 0; }
.feedback-item { background: var(--bg2); border-left: 3px solid #2563eb;
                 padding: 10px 14px; margin-bottom: 8px; border-radius: 0 6px 6px 0; }
.claim-verified { color: var(--pass); }
.claim-unverified { color: var(--fail); }
footer { margin-top: 32px; padding-top: 12px; border-top: 1px solid var(--border);
         color: var(--text2); font-size: 0.8rem; }
"""


def _render_score_trajectory(data: dict) -> str:
    """Render the score trajectory section."""
    rows = data["rows"]
    if not rows:
        return "<p>No results data available.</p>"

    points = []
    for row in rows:
        try:
            points.append((int(row["iteration"]), float(row["score"])))
        except (ValueError, KeyError):
            continue

    chart = _svg_line_chart(points)

    # Stats cards
    scores = [p[1] for p in points]
    start = scores[0] if scores else 0
    best = max(scores) if scores else 0
    improvement = best - start
    kept = sum(1 for r in rows if r.get("action") == "kept")
    reverted = sum(1 for r in rows if r.get("action") == "reverted")

    pct = f"+{improvement / start:.0%}" if start > 0 else "N/A"
    css_class = "up" if improvement > 0 else ("down" if improvement < 0 else "")

    stats_html = f"""<div class="stats">
<div class="stat"><div class="label">Starting Score</div><div class="value">{start:.0%}</div></div>
<div class="stat"><div class="label">Best Score</div><div class="value {css_class}">{best:.0%}</div></div>
<div class="stat"><div class="label">Improvement</div><div class="value {css_class}">{improvement:+.0%} ({pct})</div></div>
<div class="stat"><div class="label">Kept / Reverted</div><div class="value">{kept} / {reverted}</div></div>
</div>"""

    # Trajectory table
    table_rows = []
    for row in rows:
        action = row.get("action", "")
        badge_cls = f"badge-{action}" if action in ("kept", "reverted", "baseline") else ""
        badge = f'<span class="badge {badge_cls}">{escape(action)}</span>'
        table_rows.append(
            f"<tr><td>{escape(row.get('iteration', ''))}</td>"
            f"<td>{escape(row.get('score', ''))}</td>"
            f"<td>{escape(row.get('best_score', ''))}</td>"
            f"<td>{badge}</td>"
            f"<td>{escape(row.get('changelog', ''))}</td></tr>"
        )

    return f"""<h2>Score Trajectory</h2>
{stats_html}
<div class="chart-container">{chart}</div>
<table>
<thead><tr><th>Iter</th><th>Score</th><th>Best</th><th>Action</th><th>Changelog</th></tr></thead>
<tbody>{''.join(table_rows)}</tbody>
</table>"""


def _render_expectation_heatmap(data: dict) -> str:
    """Render the expectation pass/fail heatmap across iterations."""
    timeline = data["expectations_timeline"]
    iterations = data["iterations"]
    if not timeline or not iterations:
        return ""

    header = "".join(f"<th>Iter {i}</th>" for i in iterations)
    rows = []
    for exp_text, iter_map in sorted(timeline.items()):
        cells = []
        for it in iterations:
            val = iter_map.get(it)
            if val is True:
                cells.append('<td class="cell-pass">PASS</td>')
            elif val is False:
                cells.append('<td class="cell-fail">FAIL</td>')
            else:
                cells.append('<td class="cell-na">—</td>')
        # Truncate long expectation text
        display = escape(exp_text[:80] + ("..." if len(exp_text) > 80 else ""))
        rows.append(f"<tr><td title=\"{escape(exp_text)}\">{display}</td>{''.join(cells)}</tr>")

    return f"""<h2>Expectation Heatmap</h2>
<div style="overflow-x:auto">
<table>
<thead><tr><th>Expectation</th>{header}</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>"""


def _render_per_eval_breakdown(data: dict) -> str:
    """Render per-eval pass rates across iterations."""
    gradings = data["gradings"]
    eval_ids = data["eval_ids"]
    iterations = data["iterations"]
    if not gradings or not eval_ids:
        return ""

    header = "".join(f"<th>Iter {i}</th>" for i in iterations)
    rows = []
    for eid in eval_ids:
        cells = []
        for it in iterations:
            grading = gradings.get(it, {}).get(eid)
            if grading:
                rate = grading.get("summary", {}).get("pass_rate", 0)
                css = "pass" if rate >= 0.7 else ("fail" if rate < 0.5 else "")
                cells.append(f'<td class="{css}">{rate:.0%}</td>')
            else:
                cells.append('<td class="cell-na">—</td>')
        rows.append(f"<tr><td>{escape(eid)}</td>{''.join(cells)}</tr>")

    return f"""<h2>Per-Eval Breakdown</h2>
<table>
<thead><tr><th>Eval</th>{header}</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>"""


def _render_source_counts(data: dict) -> str:
    """Render deterministic vs LLM expectation counts."""
    source_counts = data["source_counts"]
    iterations = data["iterations"]
    if not source_counts:
        return ""

    header = "".join(f"<th>Iter {i}</th>" for i in iterations)
    det_cells = []
    llm_cells = []
    for it in iterations:
        counts = source_counts.get(it, {})
        d = counts.get("deterministic", 0)
        l = counts.get("llm", 0)
        u = counts.get("untagged", 0)
        det_cells.append(f"<td>{d}</td>")
        llm_cells.append(f"<td>{l + u}</td>")

    return f"""<h2>Deterministic vs LLM Expectations</h2>
<table>
<thead><tr><th>Source</th>{header}</tr></thead>
<tbody>
<tr><td>Deterministic</td>{''.join(det_cells)}</tr>
<tr><td>LLM</td>{''.join(llm_cells)}</tr>
</tbody>
</table>"""


def _render_metrics(data: dict) -> str:
    """Render execution metrics timeline."""
    metrics_timeline = data["metrics_timeline"]
    iterations = data["iterations"]
    if not metrics_timeline:
        return ""

    # Only show if at least one iteration has non-zero metrics
    has_metrics = any(
        mt["metrics"].get("total_tool_calls", 0) > 0
        for mt in metrics_timeline.values()
    )
    has_timing = any(
        mt["timing"].get("total_duration_seconds", 0) > 0
        for mt in metrics_timeline.values()
    )

    if not has_metrics and not has_timing:
        return ""

    parts = []
    if has_metrics:
        header = "".join(f"<th>Iter {i}</th>" for i in iterations)
        metric_keys = ["total_tool_calls", "output_chars", "transcript_chars"]
        metric_labels = ["Tool Calls", "Output Chars", "Transcript Chars"]
        rows = []
        for key, label in zip(metric_keys, metric_labels):
            cells = []
            for it in iterations:
                val = metrics_timeline.get(it, {}).get("metrics", {}).get(key, 0)
                cells.append(f"<td>{val:,}</td>")
            rows.append(f"<tr><td>{label}</td>{''.join(cells)}</tr>")
        parts.append(
            f"""<table>
<thead><tr><th>Metric</th>{header}</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>"""
        )

    if has_timing:
        header = "".join(f"<th>Iter {i}</th>" for i in iterations)
        timing_keys = [
            "executor_duration_seconds",
            "grader_duration_seconds",
            "total_duration_seconds",
        ]
        timing_labels = ["Executor (s)", "Grader (s)", "Total (s)"]
        rows = []
        for key, label in zip(timing_keys, timing_labels):
            cells = []
            for it in iterations:
                val = metrics_timeline.get(it, {}).get("timing", {}).get(key, 0.0)
                cells.append(f"<td>{val:.1f}</td>")
            rows.append(f"<tr><td>{label}</td>{''.join(cells)}</tr>")
        parts.append(
            f"""<table>
<thead><tr><th>Timing</th>{header}</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>"""
        )

    return f"<h2>Execution Metrics</h2>\n" + "\n".join(parts)


def _render_claims(data: dict) -> str:
    """Render claims verification log."""
    claims = data["claims_log"]
    if not claims:
        return ""

    rows = []
    for c in claims:
        verified = c.get("verified", False)
        css = "claim-verified" if verified else "claim-unverified"
        icon = "&#10003;" if verified else "&#10007;"
        rows.append(
            f"<tr><td>{c.get('iteration', '')}</td>"
            f"<td>{escape(c.get('eval_id', ''))}</td>"
            f"<td>{escape(c.get('claim', ''))}</td>"
            f"<td>{escape(c.get('type', ''))}</td>"
            f'<td class="{css}">{icon}</td>'
            f"<td>{escape(c.get('evidence', ''))}</td></tr>"
        )

    return f"""<h2>Claims Verification</h2>
<table>
<thead><tr><th>Iter</th><th>Eval</th><th>Claim</th><th>Type</th><th>Verified</th><th>Evidence</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>"""


def _render_eval_feedback(data: dict) -> str:
    """Render accumulated eval feedback from the grader."""
    feedback_log = data["eval_feedback_log"]
    if not feedback_log:
        return ""

    items = []
    for entry in feedback_log:
        it = entry["iteration"]
        eid = entry["eval_id"]
        overall = escape(entry.get("overall", ""))
        suggestions_html = "".join(
            f"<li>{escape(s.get('reason', ''))}"
            + (
                f" <em>(re: {escape(s['assertion'])})</em>"
                if s.get("assertion")
                else ""
            )
            + "</li>"
            for s in entry["suggestions"]
        )
        items.append(
            f'<div class="feedback-item">'
            f"<strong>Iteration {it} / {escape(eid)}</strong>"
            + (f" — {overall}" if overall else "")
            + f"<ul>{suggestions_html}</ul></div>"
        )

    return f"<h2>Eval Feedback Log</h2>\n" + "\n".join(items)


def generate_dashboard(workspace: Path) -> str:
    """Generate a self-contained HTML dashboard from an autoresearch workspace.

    Args:
        workspace: Path to the autoresearch workspace directory containing
                   results.tsv and iteration-*/eval-*/grading.json files.

    Returns:
        A complete HTML string that can be written to a file and opened
        in any browser. All CSS is embedded — no external dependencies.
    """
    data = collect_dashboard_data(workspace)

    skill_name = workspace.name.replace("-autoresearch", "")
    iterations = data["iterations"]
    iter_range = (
        f"Iterations 0–{max(iterations)}" if iterations else "No iterations"
    )

    sections = [
        _render_score_trajectory(data),
        _render_expectation_heatmap(data),
        _render_per_eval_breakdown(data),
        _render_source_counts(data),
        _render_metrics(data),
        _render_claims(data),
        _render_eval_feedback(data),
    ]

    body = "\n".join(s for s in sections if s)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Autoresearch Dashboard — {escape(skill_name)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Autoresearch Dashboard</h1>
<p class="subtitle">{escape(skill_name)} &middot; {iter_range}</p>
{body}
<footer>Generated by autoresearch &middot; Self-contained HTML — no external dependencies</footer>
</body>
</html>"""
