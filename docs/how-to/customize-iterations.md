---
diataxis_type: how-to
title: "How to Customize Iterations"
description: "Configure iteration count and choose the right number for your scenario"
---

# How to Customize Iterations

## Setting Max Iterations

```bash
/autoresearch path/to/my-skill --iterations 8
```

- **Default**: 5
- **Minimum**: 1
- **Maximum**: 10

## Choosing the Right Number

| Scenario | Recommended | Why |
|---|---|---|
| First run on a skill | 5 (default) | See how far the improver gets |
| Score still climbing at end | 8-10 | More room to converge |
| Score plateaued early | 3-5 | More iterations won't help |
| Quick sanity check | 1-2 | Just see if improvement is possible |
| Starting below 0.40 | Fix evals first | Low scores usually mean eval problems |

## Understanding Abort Thresholds

The loop stops early in two cases:

### Perfect Score (1.0)

All expectations pass in all evals. The loop stops immediately — no point continuing.

### Stuck Detection (3 Consecutive Reverts)

If the last 3 iterations were all reverted (score didn't improve), the loop aborts. This means the improver tried 3 different approaches and none beat the current best.

When stuck:
1. Check remaining weaknesses in the convergence report
2. Run eval-doctor to recalibrate evals if needed
3. Manually edit the skill to address structural issues
4. Run the loop again

## Iteration Timing

Each iteration involves:
1. Improver agent analyzing failures and modifying the candidate
2. Running all eval cases (each spawns a Claude execution + grading)
3. Score computation and keep/revert decision

Wall-clock time depends on:
- Number of eval cases (3 evals ≈ 2-3 min per iteration, 8 evals ≈ 5-8 min)
- Complexity of the skill
- Claude API latency

A typical 5-iteration run with 5 evals takes 15-30 minutes.

## Running Multiple Rounds

You can run autoresearch multiple times on the same skill:

```bash
# First run: 0.65 → 0.82
/autoresearch path/to/my-skill
# Apply changes: y

# Second run: 0.82 → 0.91
/autoresearch path/to/my-skill
# Apply changes: y
```

Each run creates a fresh workspace. The previous workspace is preserved for reference.
