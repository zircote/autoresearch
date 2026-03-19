---
diataxis_type: explanation
title: "Lifecycle"
description: "The full autoresearch lifecycle from eval readiness through improvement to completion"
---

# Lifecycle

The full autoresearch lifecycle from start to finish. Each phase builds on the previous one.

## Phase 1: Eval Readiness

Before the improvement loop can run, the skill needs evals.

**Check**: Does `{skill-path}/evals/evals.json` exist with 3+ eval cases?

- **Yes** → Proceed to Phase 2
- **No** → Run eval-doctor first: `/autoresearch --eval-doctor path/to/my-skill`

The eval-doctor reads the skill, generates eval cases with realistic prompts and discriminating expectations, and writes `evals/evals.json`. Optionally creates `evals/trigger-eval.json` for description testing.

**Output**: A skill directory with well-formed evals ready for the improvement loop.

**Why eval quality comes first**: If evals are weak or miscalibrated, the improvement loop optimizes against a moving or misleading target. This is the "moving goalposts" problem — when both the artifact and the measurement change together, score improvements become meaningless. Locking down good evals before entering the loop ensures every score change reflects a real change in skill quality.

## Phase 2: Baseline

The first step of the improvement loop establishes where the skill currently stands.

1. **Create workspace**: `{skill-name}-autoresearch/` directory
2. **Snapshot v0**: Immutable copy of the original skill
3. **Copy candidate**: Mutable working copy
4. **Run all evals**: Execute each eval prompt with the skill, grade the outputs
5. **Compute score**: Mean pass_rate across all grading results
6. **Log**: Record baseline in results.tsv

**Output**: A workspace with baseline snapshot, initial score, and grading details for every eval case.

**Key insight**: The baseline score tells you how much room there is for improvement. A 0.90 baseline has less room than a 0.50.

**Why an immutable baseline matters**: The v0 snapshot is never modified. This gives you a fixed reference point for regression detection — the convergence report diffs against v0, so you always know exactly what changed. Without a stable baseline, you couldn't tell whether a score drop came from a bad improvement or from the reference itself shifting.

## Phase 3: Improvement Iterations

The core loop. For each iteration:

### 3a. Improve

The improver agent:
1. Reads grading.json files from the previous iteration
2. Identifies failed expectations and groups them by pattern
3. Reviews results.tsv for score history (avoids repeating reverted approaches)
4. Modifies the candidate skill: SKILL.md, scripts, references
5. Reports a changelog of what changed and why

### 3b. Evaluate

All evals run against the modified candidate, producing new grading.json files and a new composite score.

### 3c. Decide

- **Score improved** (`score_i > best_score`) → KEEP
  - Snapshot the candidate to `v{i}/`
  - Update best version and best score
- **Score didn't improve** (`score_i ≤ best_score`) → REVERT
  - Restore candidate from best snapshot
  - Candidate returns to the last known-good state

### 3d. Log

Append to results.tsv: iteration number, timestamp, score, best score, action, changelog.

### 3e. Check Abort

- `best_score ≥ 1.0` → Perfect. Stop.
- Last 3 actions all "reverted" → Stuck. Stop.
- Otherwise → Continue to next iteration.

**Output**: A results.tsv tracking every iteration, snapshots of kept versions, and full eval results per iteration.

**Why keep/discard beats always-forward**: A naive loop would always keep changes and hope for the best. The keep/revert mechanism prevents score regression — if an iteration makes things worse, the candidate snaps back to the last known-good state. This means the best_score monotonically increases, and the improver never compounds a bad change with another bad change on top of it.

## Phase 4: Convergence and Decision

After the loop finishes (by reaching max iterations, perfect score, or stuck condition):

1. **Convergence report**: The convergence reporter agent analyzes results.tsv, generates a diff between v0 and the best version, lists remaining weaknesses, and recommends an action.

2. **User decision**: "Apply the best version (v{N}, score {S}) to the original skill? [y/n]"
   - **Apply**: Best snapshot replaces original skill files
   - **Decline**: Changes stay in workspace for manual review

**Output**: A convergence report and an explicit user decision.

**Why human confirmation is required**: The loop can improve a skill's eval scores, but scores don't capture everything — readability, tone, approach, and alignment with the user's intent are judgment calls. Automated systems shouldn't modify production artifacts without approval. The explicit apply/decline step ensures a human validates that the changes are actually desirable, not just higher-scoring.

## Phase 5: Post-Loop (Description Tuning)

After applying changes, the skill's behavior may have changed enough that its trigger description no longer matches. Use skill-creator to re-optimize:

```bash
/skill-creator optimize-description path/to/my-skill
```

This is optional but recommended when the skill's SKILL.md changed significantly.

**Output**: Updated description in SKILL.md frontmatter.

## Phase 6: Re-evaluation (Meta-Loop)

For sustained improvement, alternate between fixing evals and improving the skill:

```
┌──────────────┐     ┌──────────────┐
│  EVAL DOCTOR │────▶│  IMPROVEMENT │──┐
│  (fix evals) │     │  LOOP        │  │
└──────────────┘     └──────────────┘  │
       ▲                               │
       │    ┌──────────────┐           │
       └────│  REVIEW      │◀──────────┘
            │  (evals ok?) │
            └──────────────┘
```

Each cycle through this meta-loop:
1. Eval-doctor tightens evals (score may drop as expectations get harder)
2. Improvement loop raises the skill to meet the new bar
3. Review whether evals are still appropriate

Stop when the score on tough evals meets your quality target (typically 0.85+).

## Related

- [The Autoresearch Pattern](the-autoresearch-pattern.md) — Design philosophy
- [Algorithm](../reference/algorithm.md) — Formal specification
- [Expected Results](expected-results.md) — What to expect at each phase
