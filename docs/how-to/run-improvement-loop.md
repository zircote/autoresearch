---
diataxis_type: how-to
title: "How to Run the Improvement Loop"
description: "Run the autoresearch improvement loop with default or custom settings"
---

# How to Run the Improvement Loop

## Basic Usage

```bash
/autoresearch path/to/my-skill
```

This runs the full loop with default settings (5 iterations).

## With Custom Iterations

```bash
/autoresearch path/to/my-skill --iterations 8
```

Range: 1-10. Default: 5. Higher values give the improver more attempts but take longer.

## What Happens

1. **Workspace creation** — A `{skill-name}-autoresearch/` directory is created as a sibling to the skill directory
2. **Baseline snapshot** — Your skill is copied to `v0/` (immutable) and `candidate/` (mutable)
3. **Baseline evaluation** — All evals run against the unmodified skill. Score recorded in `results.tsv`
4. **Iteration loop** — For each iteration:
   - Improver agent reads failures and modifies `candidate/`
   - Evals run against the modified candidate
   - If score improved: snapshot to `v{N}/`, update best
   - If score didn't improve: restore candidate from best snapshot
5. **Convergence report** — Score trajectory, diff, remaining weaknesses, recommendation
6. **User decision** — Apply best version to original skill, or leave in workspace

## Prerequisites

- Skill must have `SKILL.md` at the root
- Skill must have `evals/evals.json` with at least 3 eval cases
- The `skill-creator` plugin must be installed (provides the grader)

If evals are missing, use [eval-doctor mode](manage-evals.md) first.

## Stopping Conditions

The loop stops early when:
- **Perfect score** (1.0) — all expectations pass in all evals
- **Stuck** — 3 consecutive reverts with no improvement
- **Max iterations** reached

## Output

- `{skill-name}-autoresearch/results.tsv` — Score log
- `{skill-name}-autoresearch/v0/` through `v{N}/` — Snapshots of kept versions
- `{skill-name}-autoresearch/iteration-{N}/` — Eval run results per iteration
- Convergence report printed to console

See [File Formats](../reference/file-formats.md) for detailed schemas.

## Tips

- Start with default 5 iterations. Increase to 8-10 only if the score is still climbing at the end.
- If starting below 0.50, consider running eval-doctor first — low scores often indicate eval problems.
- The workspace persists after the loop. You can re-run `/autoresearch --report` to review results later.
