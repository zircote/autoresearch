---
diataxis_type: tutorial
title: "Your First Autoresearch Loop"
description: "Step-by-step walkthrough of running your first autoresearch improvement loop on an existing skill"
---

# Your First Autoresearch Loop

This tutorial walks you through running autoresearch on a skill that already has evals. You'll see the full cycle: workspace creation, baseline evaluation, iterative improvement, and the convergence report.

**Prerequisites:**
- Claude Code with plugin support
- The `skill-creator` plugin installed (`claude plugins add skill-creator`)
- The `autoresearch` plugin installed (`claude plugins add ./`)
- A skill with `evals/evals.json` already defined

## Step 1: Install the Plugin

If you haven't already:

```bash
claude plugins add ./
```

Verify skill-creator is installed too — autoresearch depends on its grader agent:

```bash
claude plugins list
```

You should see both `autoresearch` and `skill-creator` in the output.

## Step 2: Choose a Skill

Pick a skill that has evals defined. Check for the eval file:

```bash
ls path/to/my-skill/evals/evals.json
```

If the file doesn't exist, see [Creating Evals from Scratch](creating-evals-from-scratch.md) first.

## Step 3: Run Autoresearch

```bash
/autoresearch path/to/my-skill
```

That's it. Autoresearch takes over from here.

## Step 4: What You'll See

### Workspace creation

Autoresearch creates a workspace directory next to your skill:

```
path/to/my-skill-autoresearch/
├── v0/           # Immutable copy of your original skill
├── candidate/    # Mutable working copy
└── results.tsv   # Score progression log
```

Your original skill is **never modified** during the loop.

### Baseline evaluation

Autoresearch runs every eval case against the unmodified skill and records the baseline score. You'll see output like:

```
Baseline evaluation: 3 eval cases
  eval-1: pass_rate 0.67 (4/6 expectations)
  eval-2: pass_rate 0.50 (3/6 expectations)
  eval-3: pass_rate 0.80 (4/5 expectations)

Baseline score: 0.66
```

### Iteration progress

Each iteration follows the same pattern:

1. **Improve**: The improver agent reads failures and modifies the candidate skill
2. **Evaluate**: All evals run against the modified candidate
3. **Keep or discard**: If the score improved, the changes are kept (snapshotted). If not, the candidate reverts to the best version.

```
Iteration 1:
  Improver: Added output format specification, fixed edge case handling
  Score: 0.78 (was 0.66) → KEPT (snapshot v1)

Iteration 2:
  Improver: Rewrote error handling section
  Score: 0.72 (best: 0.78) → REVERTED to v1

Iteration 3:
  Improver: Added examples, clarified ambiguous instructions
  Score: 0.85 (was 0.78) → KEPT (snapshot v3)
```

### Stopping conditions

The loop stops when any of these occur:
- **Perfect score** (1.0) — all expectations pass
- **Stuck** — 3 consecutive reverts with no improvement
- **Max iterations** reached (default: 5)

## Step 5: Reading results.tsv

After the loop, open `results.tsv` in the workspace:

```
iteration  timestamp                  score  best_score  action    changelog
0          2025-01-15T10:30:00+00:00  0.66   0.66        baseline  Initial evaluation
1          2025-01-15T10:35:00+00:00  0.78   0.78        kept      Added output format spec
2          2025-01-15T10:40:00+00:00  0.72   0.78        reverted  Error handling rewrite
3          2025-01-15T10:45:00+00:00  0.85   0.85        kept      Added examples, clarified
```

Each row is one iteration. The `best_score` column tracks the high-water mark. See [File Formats](../reference/file-formats.md) for the complete schema.

## Step 6: Reviewing the Convergence Report

After the loop finishes, the convergence reporter produces a summary:

```
## Autoresearch Convergence Report

### Score Trajectory
| Iteration | Score | Best  | Action   | Summary                        |
|-----------|-------|-------|----------|--------------------------------|
| 0         | 0.66  | 0.66  | baseline | Initial evaluation             |
| 1         | 0.78  | 0.78  | kept     | Added output format spec       |
| 2         | 0.72  | 0.78  | reverted | Error handling rewrite         |
| 3         | 0.85  | 0.85  | kept     | Added examples, clarified      |

### Summary
- Starting score: 0.66
- Final best score: 0.85 (+0.19, +29%)
- Iterations: 3 of 5 (2 kept, 1 reverted)

### Remaining Weaknesses
- Expectation "handles empty input gracefully" still fails (eval 3)

### Recommendation
Score improved significantly. Apply changes and consider another run.
```

The report also includes a unified diff showing exactly what changed between v0 and the best version.

## Step 7: Approving or Rejecting Changes

After the report, autoresearch asks:

```
Apply the best version (v3, score 0.85) to the original skill? [y/n]
```

- **Yes**: Copies the best version back to your original skill directory
- **No**: Changes stay in the workspace for manual review

Either way, the workspace is preserved. You can always:
- Inspect any snapshot (`v0/`, `v1/`, `v3/`)
- Re-run the report: `/autoresearch --report path/to/my-skill-autoresearch`
- Run the loop again for further improvement

## Next Steps

- Score below 0.85? See [Improving an Existing Skill](improving-an-existing-skill.md)
- Evals feel too easy? See [Managing Evals](../how-to/manage-evals.md)
- Want to understand the algorithm? See [The Autoresearch Pattern](../explanation/the-autoresearch-pattern.md)
