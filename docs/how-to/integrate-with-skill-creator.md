---
diataxis_type: how-to
title: "How to Integrate with Skill Creator"
description: "Use autoresearch alongside the skill-creator plugin for end-to-end skill development"
---

# How to Integrate with Skill Creator

Autoresearch depends on the skill-creator plugin and works well as part of a broader skill development workflow.

## Dependencies on Skill Creator

Autoresearch uses skill-creator's **grader agent** to evaluate skill outputs. The grader:
- Reads eval expectations and the skill's execution transcript
- Produces `grading.json` with pass/fail for each expectation
- Provides `eval_feedback` with suggestions for improving evals

Autoresearch locates skill-creator automatically:

```bash
${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator/
```

If not found, autoresearch tells you to install it.

## Post-Loop Description Optimization

After a successful autoresearch run, the skill's behavior may have changed significantly. The trigger description in SKILL.md's frontmatter may no longer accurately describe what the skill does.

Use skill-creator to re-optimize the description:

```bash
/skill-creator optimize-description path/to/my-skill
```

This analyzes the updated SKILL.md and rewrites the `description` field in the frontmatter to better match the skill's current capabilities.

## Recommended Workflow

### New skill (from scratch)

1. **Create the skill**: `/skill-creator path/to/my-skill`
2. **Create evals**: `/autoresearch --eval-doctor path/to/my-skill`
3. **Improve the skill**: `/autoresearch path/to/my-skill`
4. **Apply changes**: Confirm when prompted
5. **Optimize description**: `/skill-creator optimize-description path/to/my-skill`

### Existing skill (improvement)

1. **Check evals**: Verify `evals/evals.json` exists and is adequate
2. **Run improvement loop**: `/autoresearch path/to/my-skill`
3. **Review and apply**: Check convergence report, apply if satisfied
4. **Update description if needed**: `/skill-creator optimize-description path/to/my-skill`

## Eval Schemas

Autoresearch uses the same eval schemas as skill-creator. See [Eval Schema](../reference/eval-schema.md) for the `evals.json` and `trigger-eval.json` formats.

The grading.json output schema is defined in skill-creator's `references/schemas.md`.
