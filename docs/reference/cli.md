---
diataxis_type: reference
title: "CLI Reference"
description: "Complete command-line interface reference for the /autoresearch command"
---

# CLI Reference

## Command

```
/autoresearch [OPTIONS] <path>
```

## Modes

### Full Improvement Loop (default)

```
/autoresearch <skill-path>
/autoresearch <skill-path> --iterations <N>
```

Runs the complete improvement cycle on a skill.

**Arguments:**
- `<skill-path>` — Path to the skill directory (must contain `SKILL.md`)

**Options:**
- `--iterations <N>` — Maximum number of improvement iterations. Default: 5. Range: 1-10.

**Requires:**
- `evals/evals.json` must exist in the skill directory
- The `skill-creator` plugin must be installed

**Creates:**
- `{skill-name}-autoresearch/` workspace directory (sibling to skill directory)

### Eval Doctor

```
/autoresearch --eval-doctor <skill-path>
```

Creates or improves evaluation cases for a skill. Does not run the improvement loop.

**Arguments:**
- `<skill-path>` — Path to the skill directory

**Options:**
- `--eval-doctor` — Activates eval doctor mode

**Creates/Modifies:**
- `{skill-path}/evals/evals.json`
- `{skill-path}/evals/trigger-eval.json` (optional)

### Report

```
/autoresearch --report <workspace-path>
```

Generates a convergence report from an existing autoresearch workspace.

**Arguments:**
- `<workspace-path>` — Path to the autoresearch workspace (the `{skill-name}-autoresearch/` directory)

**Options:**
- `--report` — Activates report mode

**Requires:**
- `results.tsv` must exist in the workspace
- At least `v0/` snapshot must exist

## Examples

```bash
# Run with defaults (5 iterations)
/autoresearch ./skills/my-skill

# Run with more iterations
/autoresearch ./skills/my-skill --iterations 10

# Create evals for a bare skill
/autoresearch --eval-doctor ./skills/my-skill

# Review previous run results
/autoresearch --report ./skills/my-skill-autoresearch
```

## Exit Conditions

The improvement loop exits when:

| Condition | Trigger |
|---|---|
| Perfect score | `best_score >= 1.0` |
| Stuck | Last 3 consecutive actions are `reverted` |
| Max iterations | Iteration count reaches `--iterations` value |

## Environment

- `CLAUDE_PLUGIN_ROOT` — Set automatically by Claude Code. Points to the plugin installation directory.
- Python 3.8+ required for scripts (snapshot, scoring, reporting)
- skill-creator plugin must be installed for grading

## Related

- [Algorithm](algorithm.md) — Formal loop specification
- [File Formats](file-formats.md) — Workspace layout and file schemas
- [Agents](agents.md) — Agent specifications
