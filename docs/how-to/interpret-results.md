---
diataxis_type: how-to
title: "How to Interpret Results"
description: "Read and understand results.tsv, score trends, and iteration outcomes"
---

# How to Interpret Results

## Reading results.tsv

The results log is a tab-separated file in the workspace root:

```
iteration  timestamp                  score  best_score  action    changelog
0          2025-01-15T10:30:00+00:00  0.66   0.66        baseline  Initial evaluation
1          2025-01-15T10:35:00+00:00  0.78   0.78        kept      Added output format spec
2          2025-01-15T10:40:00+00:00  0.72   0.78        reverted  Error handling rewrite
```

**Columns:**
- `iteration` — 0 = baseline, 1+ = improvement iterations
- `timestamp` — UTC ISO-8601
- `score` — Composite pass_rate for this iteration (0.0-1.0)
- `best_score` — High-water mark across all iterations so far
- `action` — `baseline`, `kept`, or `reverted`
- `changelog` — What the improver changed (or "Initial evaluation" for baseline)

## Reading Convergence Reports

Run the reporter on an existing workspace:

```bash
/autoresearch --report path/to/my-skill-autoresearch
```

The report includes:

### Score Trajectory Table

Shows every iteration with score, best score, action, and summary. Look for:
- **Upward trend in best_score** — the loop is working
- **Flat best_score** — plateau, may need eval changes or more iterations
- **Early abort** — 3 consecutive reverts mean the loop gave up

### Summary Statistics

- Starting vs final score with absolute and percentage improvement
- Kept vs reverted ratio — healthy runs have ≥50% kept
- Convergence classification: rapid improvement, plateau, stuck, or perfect

### Changes Diff

Unified diff between v0 (baseline) and the best version. Review this before applying — it shows exactly what the improver changed.

### Remaining Weaknesses

Expectations that still fail in the best version. Categorized as:
- **Hard problems** — the skill may need structural changes
- **Edge cases** — specific scenarios the improver couldn't handle
- **Fundamental limitations** — beyond what skill instructions can address

## Reading grading.json

For the grading.json schema and field details, see [File Formats Reference](../reference/file-formats.md).

## Score Interpretation

As a quick guide: scores below 0.30 indicate fundamental issues, 0.60-0.80 is a typical starting point, and 0.85+ is good quality for most skills. For the full scoring model and what drives convergence, see [Convergence and Scoring](../explanation/convergence-and-scoring.md).

## Inspecting Individual Runs

Each iteration directory contains per-eval results:

```
workspace/iteration-2/
├── eval-1/
│   ├── transcript.md    # Full execution transcript
│   ├── outputs/         # Files the skill produced
│   └── grading.json     # Pass/fail for each expectation
├── eval-2/
│   └── ...
```

Read `transcript.md` to see exactly what happened during an eval execution. Compare transcripts across iterations to understand what the improver changed and whether it helped.

## Related

- [Convergence and Scoring](../explanation/convergence-and-scoring.md) — How scores are computed and what convergence means
- [File Formats Reference](../reference/file-formats.md) — Schema details for grading.json, results.tsv, and other artifacts
