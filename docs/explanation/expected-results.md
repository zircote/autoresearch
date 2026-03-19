---
diataxis_type: explanation
title: "Expected Results"
description: "Typical score trajectories, common patterns, and what to expect from autoresearch runs"
---

# Expected Results

What to expect when running autoresearch, based on common scenarios and typical behavior.

## Typical Score Trajectories

### Pattern 1: Steady Climb (most common)

```
Iter 0: 0.55  (baseline)
Iter 1: 0.65  kept   (+0.10)
Iter 2: 0.60  reverted
Iter 3: 0.72  kept   (+0.07)
Iter 4: 0.78  kept   (+0.06)
Iter 5: 0.82  kept   (+0.04)
```

Each kept iteration adds 0.05-0.10. Gains shrink as easy wins are exhausted. Reverts are normal — the improver tries things that don't work and the system recovers.

**When this happens**: Skill has identifiable issues (missing instructions, wrong format, unclear sections) that the improver can fix incrementally.

### Pattern 2: Big Jump + Plateau

```
Iter 0: 0.35  (baseline)
Iter 1: 0.70  kept   (+0.35)
Iter 2: 0.68  reverted
Iter 3: 0.72  kept   (+0.02)
Iter 4: 0.70  reverted
Iter 5: 0.73  kept   (+0.01)
```

A single iteration produces a large improvement, then the score barely moves.

**When this happens**: The skill had a fundamental issue (missing section, completely wrong output format) that the improver fixed in iteration 1. Remaining issues are minor or harder to solve.

### Pattern 3: Quick Convergence

```
Iter 0: 0.80  (baseline)
Iter 1: 0.88  kept
Iter 2: 0.92  kept
Iter 3: 0.95  kept
Iter 4: 1.00  kept (PERFECT — loop stops)
```

The skill was already good; autoresearch polished the remaining issues quickly.

**When this happens**: Skill is well-written but had a few specific gaps that evals caught.

### Pattern 4: Stuck from the Start

```
Iter 0: 0.45  (baseline)
Iter 1: 0.40  reverted
Iter 2: 0.42  reverted
Iter 3: 0.38  reverted (STUCK — loop aborts)
```

Three consecutive reverts, no improvement.

**When this happens**:
- Evals are miscalibrated (too hard, too vague, or testing the wrong things)
- The skill needs structural changes beyond what the improver can do
- Expectations are non-deterministic (subjective or ambiguous)

**What to do**: Run eval-doctor to review and fix evals, then try again.

## What "Good Enough" Looks Like

| Score | Assessment | Action |
|---|---|---|
| 0.85+ | Good for production use | Apply changes, move on |
| 0.90+ | Excellent | Apply, consider the skill done |
| 0.95+ | Near-perfect | Remaining failures are likely edge cases or non-determinism |
| 1.00 | Perfect | All expectations pass — but consider if evals are hard enough |

A score of 0.85 means ~85% of expectations pass across all eval cases. For most skills, this represents reliable behavior with occasional gaps in edge cases.

## Common Failure Modes

### Evals are too easy

**Symptom**: Baseline score is 0.90+ and the loop quickly reaches 1.0.

**Problem**: Expectations don't discriminate between good and bad output. The skill may have issues that evals don't catch.

**Fix**: Run eval-doctor to tighten expectations. Add edge cases. Make prompts more demanding.

### Evals are too hard

**Symptom**: Baseline score is below 0.30 and the loop gets stuck immediately.

**Problem**: Expectations may be unrealistic, or the skill is fundamentally incapable of what evals expect.

**Fix**: Check if the skill works at all when invoked manually. Run eval-doctor to calibrate expectations. Ensure expectations are verifiable from output alone.

### Non-deterministic scoring

**Symptom**: Scores bounce randomly between iterations with no clear trend. Many reverts even though the improver is making reasonable changes.

**Problem**: Expectations may be subjective, or the skill's output varies significantly between runs.

**Fix**: Make expectations more objective ("output contains X" instead of "output is well-organized"). Reduce expectations that depend on exact wording.

### Improver overfitting

**Symptom**: Score improves on one eval but drops on others. Net score barely changes.

**Problem**: The improver is tuning SKILL.md for specific eval cases rather than improving general quality.

**Fix**: This is usually self-correcting — the keep/discard gate prevents overfitted changes from persisting. If it continues, check that evals test independent aspects of the skill.

### Stuck at a ceiling

**Symptom**: Score reaches ~0.75 and plateaus. The improver keeps trying but nothing sticks.

**Problem**: Remaining failures may require:
- Script changes (not just SKILL.md edits)
- New capabilities the skill doesn't have
- Changes to the skill's fundamental approach

**Fix**: Review remaining weaknesses in the convergence report. Make manual edits to address structural issues. Run the loop again from the higher baseline.

## When Autoresearch Helps vs Manual Iteration

### Autoresearch is great for:
- Skills with clear eval failures and identifiable improvement paths
- Polishing a working skill from "good" to "great"
- Overnight improvement runs you don't want to babysit
- Finding non-obvious improvements through systematic experimentation

### Manual iteration is better for:
- Skills that need fundamental architectural changes
- New skills where the right approach isn't clear yet
- Situations where the eval signal is unreliable
- One-off fixes where you already know what's wrong

## Related

- [Convergence and Scoring](convergence-and-scoring.md) — How scoring works
- [The Autoresearch Pattern](the-autoresearch-pattern.md) — Design philosophy
- [Improving an Existing Skill](../tutorials/improving-an-existing-skill.md) — Practical walkthrough
