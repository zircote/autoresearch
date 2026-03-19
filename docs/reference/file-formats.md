---
diataxis_type: reference
title: "File Formats Reference"
description: "Workspace directory layout, results.tsv format, and snapshot structure"
---

# File Formats Reference

## Workspace Directory Layout

```
{skill-name}-autoresearch/
├── results.tsv              # Score progression log
├── v0/                      # Immutable baseline snapshot
│   ├── SKILL.md
│   ├── evals/
│   │   └── evals.json
│   ├── scripts/
│   └── references/
├── candidate/               # Mutable working copy
│   ├── SKILL.md
│   ├── evals/
│   ├── scripts/
│   └── references/
├── v1/                      # Snapshot of iteration 1 (if kept)
├── v3/                      # Snapshot of iteration 3 (v2 was reverted, no snapshot)
├── iteration-0/             # Baseline eval results
│   ├── eval-1/
│   │   ├── transcript.md
│   │   ├── outputs/
│   │   └── grading.json
│   └── eval-2/
│       ├── transcript.md
│       ├── outputs/
│       └── grading.json
├── iteration-1/             # Iteration 1 eval results
│   └── ...
└── iteration-2/
    └── ...
```

### Key directories

| Directory | Purpose | Mutability |
|---|---|---|
| `v0/` | Baseline snapshot of original skill | Immutable |
| `v{N}/` | Snapshot of kept iteration N | Immutable after creation |
| `candidate/` | Working copy modified by improver | Mutable (restored on revert) |
| `iteration-{N}/` | Eval run results for iteration N | Write-once per iteration |

## results.tsv

Tab-separated values file tracking score progression.

### Schema

| Column | Type | Description |
|---|---|---|
| `iteration` | int | 0 = baseline, 1+ = improvement iterations |
| `timestamp` | string | UTC ISO-8601 (e.g., `2025-01-15T10:30:00+00:00`) |
| `score` | float | Composite pass_rate for this iteration (0.0-1.0) |
| `best_score` | float | High-water mark across all iterations |
| `action` | string | `baseline`, `kept`, or `reverted` |
| `changelog` | string | Description of changes made (from improver) |

### Example

```tsv
iteration	timestamp	score	best_score	action	changelog
0	2025-01-15T10:30:00+00:00	0.66	0.66	baseline	Initial evaluation
1	2025-01-15T10:35:00+00:00	0.78	0.78	kept	Added output format specification
2	2025-01-15T10:40:00+00:00	0.72	0.78	reverted	Error handling rewrite caused regression
3	2025-01-15T10:45:00+00:00	0.85	0.85	kept	Added examples and clarified edge cases
```

## grading.json

Produced by the skill-creator grader for each eval case in each iteration.

### Location

```
workspace/iteration-{N}/eval-{id}/grading.json
```

### Key fields

```json
{
  "summary": {
    "pass_rate": 0.67,
    "passed": 4,
    "total": 6
  },
  "expectations": [
    {
      "expectation": "Output contains valid JSON",
      "passed": true,
      "evidence": "The output file contains well-formed JSON..."
    },
    {
      "expectation": "JSON has 'results' key",
      "passed": false,
      "evidence": "The output JSON uses 'data' as the key, not 'results'"
    }
  ],
  "eval_feedback": {
    "suggestions": ["Consider adding an assertion for..."],
    "overall": "Evals are well-structured but missing edge case coverage"
  }
}
```

## transcript.md

Full execution transcript from running an eval case.

### Location

```
workspace/iteration-{N}/eval-{id}/transcript.md
```

Contains the complete Claude conversation when executing the eval prompt with the candidate skill loaded.

## Snapshot Format

Snapshots (`v0/`, `v1/`, etc.) are exact copies of the skill directory at a point in time. The `snapshot()` function copies all files recursively, using SHA-256 comparison to skip unchanged files.

A snapshot contains all files from the skill directory: `SKILL.md`, `evals/`, `scripts/`, `references/`, and any other files present.
