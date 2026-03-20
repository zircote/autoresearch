# Convergence Reporter Agent

## Context

This agent is spawned when:
1. The improvement loop completes (either by reaching max iterations, perfect score, or stuck condition)
2. The user runs `/autoresearch --report <workspace>` to view results

## Role

Read the results of an autoresearch run and produce a clear convergence report for the user, including score trajectory, before/after comparison, and a recommendation.

## Inputs

You receive these in your prompt:
- **workspace**: Path to the autoresearch workspace directory
- **v0_path**: Path to the v0 (baseline) snapshot
- **best_path**: Path to the best version snapshot
- **dashboard_path** (optional): Path to the generated HTML dashboard file

## Process

### Step 1: Read Results

1. Read `results.tsv` from the workspace
2. Parse each row: iteration, timestamp, score, best_score, action (kept/reverted), changelog
3. **Display ALL iterations** found in results.tsv — the trajectory table must include every row, not just a subset. This is critical for the report's accuracy.
4. **Include a single-line iteration summary** above the trajectory table in the format: "Iterations covered: Iteration 0, Iteration 1, Iteration 2" (listing every iteration number). This line must appear on one line so it can be scanned quickly. This is required — do not omit it.

### Step 2: Compute Trajectory

1. Track score progression: starting score, peak score, final best score
2. Count: total iterations, kept iterations, reverted iterations
3. For each kept iteration, explicitly state the score improvement: "score improved from {previous_best} to {new_score}"
4. For each reverted iteration, explicitly state it was reverted and why the score regressed
5. Identify convergence pattern:
   - **Rapid improvement**: Most iterations kept, score rose quickly
   - **Plateau**: Score stopped improving after initial gains
   - **Stuck**: 3+ consecutive reverts (the abort condition)
   - **Perfect**: Achieved 1.0

### Step 3: Generate Diff

Run the diff_report.py script to compare v0 vs best:

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, '<scripts_dir>')
from diff_report import diff_report
print(diff_report(Path('<v0_path>'), Path('<best_path>')))
"
```

### Step 4: Analyze Remaining Weaknesses

1. Read the most recent grading.json files
2. List expectations that still fail
3. Categorize: are these hard problems, edge cases, or fundamental skill limitations?

### Step 5: Write Report

Present to the user:

```
## Autoresearch Convergence Report

### Score Trajectory

Iterations covered: Iteration 0, Iteration 1, Iteration 2 (list ALL iteration numbers on this single line)

| Iteration | Score | Best | Action | Summary |
|-----------|-------|------|--------|---------|
| 0 (baseline) | 0.45 | 0.45 | — | Initial evaluation |
| 1 | 0.65 | 0.65 | kept | Added output formatting |
| 2 | 0.55 | 0.65 | reverted | Regression in edge cases |
| 3 | 0.75 | 0.75 | kept | Fixed edge case handling |

### Summary
- **Starting score**: 0.45
- **Final best score**: 0.75 (+0.30, +67%)
- **Iterations**: 3 of 5 (2 kept, 1 reverted)
- **Convergence**: Improving (not yet plateaued)

### Changes (v0 → best)
<unified diff here>

### Remaining Weaknesses
- Expectation "handles Unicode input" still fails (eval 3)
- Expectation "produces valid JSON output" intermittent (eval 2)

### Recommendation
Score improved significantly (0.45 → 0.75). The changes look safe to apply.
Run `/autoresearch <skill-path>` again for further improvement, or apply now.

### Full Dashboard
Open the interactive HTML dashboard for detailed heatmaps, metrics, and claim tracking:
`open <dashboard_path>`
```

### Step 6: Apply Recommendation

Based on the results, recommend one of:
- **Apply**: Score improved meaningfully, changes look good
- **Continue**: Score is improving but hasn't plateaued — more iterations may help
- **Investigate**: Score plateaued with significant failures remaining — may need eval-doctor or manual review
- **Reject**: Score didn't improve or regressed — changes not worth applying

## Output

The formatted convergence report as shown above, written to the console for the user to review.
