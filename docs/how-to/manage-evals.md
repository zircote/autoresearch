---
diataxis_type: how-to
title: "How to Manage Evals"
description: "Create, improve, and maintain evaluation cases for skills"
---

# How to Manage Evals

## Create Evals for a Bare Skill

```bash
/autoresearch --eval-doctor path/to/my-skill
```

The eval-doctor reads the skill and generates `evals/evals.json` with 5-8 eval cases. See the [Creating Evals tutorial](../tutorials/creating-evals-from-scratch.md) for a walkthrough.

## Improve Existing Evals

Run eval-doctor on a skill that already has evals:

```bash
/autoresearch --eval-doctor path/to/my-skill
```

If prior grading results exist (from a previous autoresearch run), the eval-doctor reads `eval_feedback` from the grading.json files to identify:

- Expectations that pass trivially (would pass for wrong output)
- Important outcomes with no assertion coverage
- Expectations that can't be verified from available outputs

## Edit Evals Manually

Open `evals/evals.json` in your editor. The schema:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic user prompt",
      "expected_output": "Plain English description of success",
      "files": [],
      "expectations": [
        "Specific, verifiable assertion"
      ]
    }
  ]
}
```

See [Eval Schema](../reference/eval-schema.md) for the full specification.

## Quality Checklist

For each eval case, verify:

| Check | Question |
|---|---|
| Discriminating | Would this fail if the skill produced garbage in the right format? |
| Realistic prompt | Does this sound like something a real user would type? |
| Verifiable | Can the grader check this by reading the output? |
| Independent | Does this test something different from other evals? |
| Edge coverage | Are failure modes and edge cases represented? |

## How Many Evals?

- **Minimum**: 3 (fewer = unreliable signal)
- **Ideal**: 5-8 (good coverage without slow iterations)
- **Maximum**: 12 (more = diminishing returns)
- **Expectations per eval**: 3-6

## Trigger Evals

To test whether the skill's description triggers correctly:

```bash
# Edit evals/trigger-eval.json
```

```json
[
  {"query": "prompt that should invoke this skill", "should_trigger": true},
  {"query": "similar prompt that should NOT invoke", "should_trigger": false}
]
```

Include 8-10 should-trigger and 8-10 should-not-trigger queries. Make negative cases near-misses, not obviously unrelated.

## Common Problems

| Problem | Fix |
|---|---|
| All evals pass at baseline | Expectations are too weak — tighten them |
| All evals fail at baseline | Expectations may be unrealistic, or skill needs major work |
| Score bounces randomly | Expectations may be subjective — make them more objective |
| Improver can't make progress | Evals may test things outside the skill's control |
