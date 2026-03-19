---
diataxis_type: explanation
title: "Why Evals and Skills Improve Separately"
description: "Why changing evals and skills simultaneously undermines improvement measurement"
---

# Why Evals and Skills Improve Separately

## The Moving Goalposts Anti-Pattern

Imagine improving a skill and its evals at the same time:

```
Iteration 1: Skill passes 4/6 expectations
  → Improve skill AND weaken 2 hard expectations
Iteration 2: Skill passes 5/5 expectations
  → Score went up! But did the skill get better, or did the bar get lower?
```

When both the artifact and the measurement change simultaneously, you can't attribute improvement to either one. The score becomes meaningless.

This is the "moving goalposts" problem. It's the most common failure mode in self-improving systems.

## The Two-Phase Workflow

Autoresearch solves this by strictly separating the two activities:

### Phase A: Fix Evals (Eval Doctor)

```bash
/autoresearch --eval-doctor path/to/my-skill
```

- Only `evals/evals.json` is modified
- The skill itself is not touched
- Goal: make evals discriminating, realistic, and verifiable
- Run this BEFORE the improvement loop

### Phase B: Improve Skill (Improvement Loop)

```bash
/autoresearch path/to/my-skill
```

- Only the skill (`SKILL.md`, scripts, references) is modified
- Evals are frozen — the improver agent cannot touch `evals/`
- Goal: maximize pass_rate against fixed evals
- Any score change is attributable to skill changes

## How Simultaneous Improvement Creates Unmeasurable Progress

Consider a concrete example. A "report generator" skill starts at 0.60:

**Simultaneous (wrong):**
```
Iter 1: Improve skill formatting + loosen "output is well-formatted" expectation
  Score: 0.75 — but 0.10 of that is from easier evals
Iter 2: Add error handling to skill + remove "handles empty input" expectation
  Score: 0.85 — but the test suite lost coverage
```

Final score is 0.85 but actual skill quality may be worse — you removed the hard tests.

**Separated (correct):**
```
Phase A: Eval doctor tightens expectations, adds edge cases
  Skill score drops to 0.50 — evals are now harder but more realistic

Phase B: Improvement loop with frozen evals
  Iter 1: 0.65 — addressed formatting failures
  Iter 2: 0.72 — fixed error handling
  Iter 3: 0.80 — added missing output sections
```

Final score is 0.80 against tougher evals. Every point of improvement is real.

## When to Switch Phases

The key insight is recognizing which side of the measurement needs work: is the skill underperforming, or are the evals poorly calibrated? A plateau with "trivially satisfied" grading feedback points to eval problems; a plateau with clear remaining weaknesses points to skill problems.

For practical steps on when and how to switch between eval and skill improvement phases, see [Manage Evals](../how-to/manage-evals.md).

## The Enforcement Mechanism

Autoresearch doesn't just suggest separation — it enforces it:

- The improver agent spec explicitly states: "NEVER modify files in the evals/ directory"
- The convergence report compares snapshots; eval changes would be visible
- Eval-doctor mode never touches SKILL.md, scripts, or references

This isn't a guideline. It's a hard constraint built into the system.
