---
diataxis_type: reference
title: "Agents Reference"
description: "Specification of the three specialized agents used by the autoresearch orchestrator"
---

# Agents Reference

Autoresearch uses three specialized agents. Each is spawned by the orchestrator (SKILL.md) as a subagent with specific inputs and constraints.

## Improver Agent

**Source:** `skills/autoresearch/agents/improver.md`

### Role

Analyzes eval failures and modifies the candidate skill to achieve higher pass rates. Runs once per iteration.

### Inputs

| Parameter | Description |
|---|---|
| `candidate_path` | Path to `workspace/candidate/` — the mutable skill directory |
| `grading_results` | Paths to `grading.json` files from the most recent eval run |
| `history` | Path to `results.tsv` — score progression across iterations |
| `iteration` | Current iteration number |

### Process

1. **Analyze failures** — Read grading.json files, focus on `passed: false` expectations, group failures by pattern
2. **Review history** — Check results.tsv for score trajectory, avoid repeating reverted approaches
3. **Plan changes** — Write a changelog describing what to change and why
4. **Modify candidate** — Edit SKILL.md, scripts, references as needed
5. **Verify** — Confirm changes are syntactically correct and evals/ is untouched

### Outputs

- Modified files in `candidate/`
- Changelog (2-3 sentences per change)
- List of modified files
- Impact prediction (which failures should now pass)

### Constraints

- **Never modify `evals/`** — evals are frozen during improvement
- **Generalize, don't overfit** — fix root causes, not specific test cases
- **Preserve working behavior** — don't break passing evals
- **Keep it lean** — remove instructions that aren't working

---

## Eval Doctor Agent

**Source:** `skills/autoresearch/agents/eval-doctor.md`

### Role

Creates, fixes, and improves evaluation cases. Never modifies the skill itself.

### Inputs

| Parameter | Description |
|---|---|
| `skill_path` | Path to the skill directory |
| `prior_grading` | (optional) Paths to grading.json files with `eval_feedback` from previous runs |

### Process

1. **Understand the skill** — Read SKILL.md, scripts, references
2. **Review existing evals** — Assess against quality rubric if evals exist
3. **Create or improve evals** — Write `evals/evals.json` with 5-10 eval cases
4. **Write quality expectations** — 3-6 per case: discriminating, verifiable, independent
5. **Create trigger eval** (optional) — Write `evals/trigger-eval.json`
6. **Validate** — Check JSON validity, required fields, expectation quality

### Outputs

- `evals/evals.json` — Created or updated
- `evals/trigger-eval.json` — Created if applicable
- Summary: count of cases, what each tests, coverage gaps

### Constraints

- **Never modify the skill** — only works on evals
- **5-10 eval cases** for a typical skill
- **Realistic prompts** — the kind of thing a real user would type
- **Objective expectations** — same grader should reach same conclusion

---

## Convergence Reporter Agent

**Source:** `skills/autoresearch/agents/convergence-reporter.md`

### Role

Reads autoresearch results and produces a convergence report for the user.

### Inputs

| Parameter | Description |
|---|---|
| `workspace` | Path to the autoresearch workspace directory |
| `v0_path` | Path to `workspace/v0/` — the baseline snapshot |
| `best_path` | Path to `workspace/v{best}/` — the best version snapshot |

### Process

1. **Read results** — Parse results.tsv for all iteration data
2. **Compute trajectory** — Track score progression, count kept/reverted, classify convergence
3. **Generate diff** — Compare v0 vs best using `diff_report.py`
4. **Analyze weaknesses** — Read most recent grading.json files, list remaining failures
5. **Write report** — Formatted table, summary stats, diff, recommendation

### Outputs

Formatted convergence report containing:
- Score trajectory table (iteration, score, best, action, summary)
- Summary statistics (start/end score, kept/reverted counts)
- Unified diff between baseline and best version
- Remaining weaknesses with categorization
- Recommendation: apply, continue, investigate, or reject

### Convergence Classifications

| Pattern | Description |
|---|---|
| Rapid improvement | Most iterations kept, score rose quickly |
| Plateau | Score stopped improving after initial gains |
| Stuck | 3+ consecutive reverts (the abort condition) |
| Perfect | Achieved score of 1.0 |

---

## External: Grader (from skill-creator)

The grader agent is not part of autoresearch — it comes from the skill-creator plugin. Autoresearch discovers it at:
`${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator/agents/grader.md`

**Expected inputs**: expectations (list of strings), transcript_path, outputs_dir
**Expected output**: grading.json with expectations array ({text, passed, evidence}), summary ({passed, failed, total, pass_rate}), and optional eval_feedback
**Schema**: See skill-creator's `references/schemas.md` for the complete grading.json specification.
