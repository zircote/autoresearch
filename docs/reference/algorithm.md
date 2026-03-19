---
diataxis_type: reference
title: "Algorithm Reference"
description: "User-facing overview of the modify-evaluate-decide improvement loop algorithm"
---

# Algorithm Reference

This document provides a user-facing overview of the autoresearch improvement loop algorithm. For the complete formal specification, see the [internal algorithm spec](../../skills/autoresearch/references/algorithm.md).

## Overview

The autoresearch loop applies a modify-evaluate-decide cycle to iteratively improve Claude Code skills. The core guarantee: your original skill is never modified until you explicitly approve.

## Phases

### 1. Initialization

```
INPUT:  skill_path, max_iterations (default 5)
OUTPUT: workspace with v0/ snapshot, candidate/ working copy, baseline score

1. Create workspace directory: {skill-name}-autoresearch/
2. Snapshot skill → workspace/v0/  (immutable baseline)
3. Snapshot skill → workspace/candidate/  (mutable working copy)
4. Evaluate candidate → score_0
5. Log: iteration=0, score=score_0, action=baseline
6. Set best = {version: 0, score: score_0}
```

### 2. Evaluation

```
INPUT:  candidate skill directory
OUTPUT: composite score (mean pass_rate across all evals)

For each eval case in evals/evals.json:
  1. Execute: run the eval prompt with the candidate skill loaded
  2. Grade: spawn skill-creator's grader agent
  3. Collect: grading.json with per-expectation pass/fail
  4. Extract: summary.pass_rate

Score = mean(all pass_rates)
```

### 3. Improvement Loop

```
FOR i = 1 to max_iterations:
  1. IMPROVE: spawn improver agent with failure data → modifies candidate/
  2. EVALUATE: run all evals on modified candidate → score_i
  3. DECIDE:
     - If score_i > best.score → KEEP (snapshot candidate → v{i}/, update best)
     - If score_i ≤ best.score → REVERT (restore candidate from best snapshot)
  4. LOG: append to results.tsv
  5. CHECK ABORT:
     - best.score ≥ 1.0 → stop (perfect)
     - last 3 actions all "reverted" → stop (stuck)
```

### 4. Finalization

```
1. Generate convergence report (score trajectory, diff, weaknesses)
2. Show report and unified diff to user
3. Ask: apply best version to original skill? [y/n]
4. If yes: restore(best_snapshot → skill_path)
```

## Score Computation

```
score = mean([grading.summary.pass_rate for grading in iteration_grading_files])
```

Where `pass_rate = passed_expectations / total_expectations` for each eval case.

## Safety Invariants

1. **Original skill immutable** during the loop — only `candidate/` is modified
2. **Snapshots immutable** — once `v{N}/` is created, never modified
3. **Evals frozen** during improvement — the improver cannot touch `evals/`
4. **SHA-compare** before write — `snapshot()` skips unchanged files
5. **User confirmation** required before applying changes to the original
6. **Regression abort** — 3 consecutive reverts stops the loop

## Related

- [Internal algorithm spec](../../skills/autoresearch/references/algorithm.md) — Full formal specification
- [Convergence and Scoring](../explanation/convergence-and-scoring.md) — Detailed scoring explanation
- [Lifecycle](../explanation/lifecycle.md) — End-to-end lifecycle description
