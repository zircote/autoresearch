---
diataxis_type: explanation
title: "Convergence and Scoring"
description: "How composite scores are calculated and when the improvement loop converges"
---

# Convergence and Scoring

## Composite Score Calculation

The score for each iteration is the **mean pass_rate** across all eval cases:

```
score = mean([grading.summary.pass_rate for each eval case])
```

Where each `pass_rate` is:

```
pass_rate = passed_expectations / total_expectations
```

### Example

Three eval cases in an iteration:

| Eval | Passed | Total | pass_rate |
|---|---|---|---|
| eval-1 | 4 | 6 | 0.667 |
| eval-2 | 3 | 4 | 0.750 |
| eval-3 | 5 | 5 | 1.000 |

Composite score: `(0.667 + 0.750 + 1.000) / 3 = 0.806`

### Why Mean?

The mean gives equal weight to each eval case regardless of how many expectations it has. This prevents an eval with 10 expectations from dominating one with 3. Each eval case tests a distinct scenario; they should contribute equally to the overall score.

## Convergence Detection

The loop tracks convergence through the keep/revert sequence and the `best_score` trajectory.

### Perfect Convergence

```
best_score reaches 1.0
```

All expectations pass in all evals. The loop stops immediately.

### Plateau

```
best_score stops increasing but loop hasn't hit abort condition
```

The score stabilized — the improver can still find changes but none beat the current best. The loop runs to `max_iterations` and the convergence report classifies this as "plateau."

### Stuck

```
3 consecutive reverts
```

The improver tried 3 different approaches and none improved the score. This triggers an early abort. The convergence report classifies this as "stuck."

Stuck doesn't mean the skill can't be improved — it means the improver, given its current instructions and the current eval signal, can't find a better approach. Possible next steps:
- Run eval-doctor to recalibrate evals
- Manually edit the skill to address structural issues
- Run the loop again (the improver is non-deterministic, may try new approaches)

### Rapid Improvement

```
Most iterations kept, score rose quickly
```

The skill had clear issues that the improver identified and fixed. Common when the skill has missing sections, wrong output formats, or incomplete instructions.

## Score Non-Determinism

LLM execution is non-deterministic. Running the same skill on the same eval twice may produce different outputs and different scores. This means:

- A score of 0.78 and 0.80 are effectively the same
- Small score drops (0.02-0.05) after a change may be noise, not regression
- The keep/discard threshold is strict (`>`, not `>=`) to avoid accepting noise as improvement

Autoresearch accepts this by using a simple comparison: `score_i > best_score`. A tie is treated as no improvement, which biases toward keeping proven changes rather than accepting uncertain ones.

### Implications

- Don't read too much into single-iteration score changes of < 0.05
- The overall trajectory (across multiple iterations) is more meaningful than any single data point
- If scores bounce randomly with no trend, the evals may have subjective expectations that different grader runs evaluate inconsistently

## Snapshot Rollback Safety

The keep/discard mechanism provides safety through snapshots:

1. **Before improvement**: The candidate is in a known-good state (best version so far)
2. **After improvement**: The improver modifies the candidate freely
3. **After evaluation**: If the score improved, the new state is snapshotted. If not, the candidate is restored from the best snapshot.

This means:
- The candidate can never degrade below the best-known version
- Bad experiments are free — they cost compute time but can't damage the artifact
- Every snapshot is immutable after creation — you can always go back

The `restore()` function in `snapshot.py` does an exact restore: it copies all files from the snapshot AND removes files in the candidate that aren't in the snapshot. This prevents accumulated cruft from failed experiments.

## Related

- [Algorithm](../reference/algorithm.md) — Formal loop specification
- [The Autoresearch Pattern](the-autoresearch-pattern.md) — Design philosophy
- [Expected Results](expected-results.md) — Typical score trajectories
