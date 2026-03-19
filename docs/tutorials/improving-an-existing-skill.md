---
diataxis_type: tutorial
title: "Taking a Working Skill from 65% to 90%+"
description: "Tutorial for improving mediocre skill scores through the full autoresearch loop"
---

# Taking a Working Skill from 65% to 90%+

This tutorial is for skills that already have evals and produce mediocre scores. You'll run the full loop, interpret keep/revert decisions, and know when to stop.

**Prerequisites:**
- A skill with `evals/evals.json` that has been evaluated at least once
- Baseline score between 0.40 and 0.85

## Step 1: Assess Your Starting Point

Before running the loop, understand where you are. If you've run autoresearch before, check the existing workspace:

```bash
/autoresearch --report path/to/my-skill-autoresearch
```

If starting fresh, just run the loop — iteration 0 establishes the baseline.

## Step 2: Run the Full Loop

```bash
/autoresearch path/to/my-skill --iterations 8
```

For a skill starting at 65%, 5 iterations (the default) may not be enough. Use `--iterations 8` to give the improver more room to work.

## Step 3: Interpreting Keep/Revert Decisions

Watch the iteration log as it progresses:

```
Iteration 1: 0.72 (was 0.65) → KEPT
Iteration 2: 0.68 (best: 0.72) → REVERTED
Iteration 3: 0.78 (was 0.72) → KEPT
Iteration 4: 0.78 (best: 0.78) → REVERTED (tie = no improvement)
Iteration 5: 0.82 (was 0.78) → KEPT
```

Key patterns:

| Pattern | Meaning |
|---|---|
| Steady keeps | Improver is finding real issues and fixing them |
| Alternating keep/revert | Improver is trying approaches at the boundary — some work, some don't |
| 2+ reverts in a row | Improver is stuck — may need different eval signal or manual help |
| Score jumps > 0.15 | Improver found a fundamental issue (missing section, wrong format) |
| Score inches up by 0.02-0.05 | Incremental refinement — normal in the 0.75-0.90 range |

## Step 4: The Convergence Report

When the loop finishes, the convergence report tells you what happened:

```
### Summary
- Starting score: 0.65
- Final best score: 0.88 (+0.23, +35%)
- Iterations: 5 of 8 (3 kept, 2 reverted)
- Convergence: Plateau (last kept iteration was 5, 3 more reverts followed)
```

The report also lists **remaining weaknesses** — expectations that still fail:

```
### Remaining Weaknesses
- "Handles Unicode filenames" — eval 4, consistently fails
- "Produces valid JSON when input is malformed" — eval 6, intermittent
```

These tell you what the improver couldn't fix automatically. They may need:
- Better skill instructions (manual edit)
- Script changes that are too complex for the improver
- Eval adjustments (the expectation may be unrealistic)

## Step 5: Deciding Whether to Stop or Run Again

For guidance on when to stop iterating, when to run again, and when to switch to eval-doctor, see [Customize Iterations](../how-to/customize-iterations.md).

## Step 6: Applying the Best Version

If you're happy with the improvement:

```
Apply the best version (v5, score 0.88) to the original skill? [y/n]
```

Type `y`. The best snapshot replaces your original skill files.

After applying, consider:
1. **Run the loop again** — starting from 0.88, you may reach 0.92+
2. **Update the skill description** — use skill-creator to optimize the trigger description
3. **Commit the changes** — the skill directory now reflects the improved version

## Typical Score Trajectories

For what to expect from score trajectories and common patterns, see [Expected Results](../explanation/expected-results.md).

## Next Steps

- Want to fine-tune evals? See [Managing Evals](../how-to/manage-evals.md)
- Curious how scoring works? See [Convergence and Scoring](../explanation/convergence-and-scoring.md)
- Need to inspect snapshots? See [Recover from Failure](../how-to/recover-from-failure.md)
