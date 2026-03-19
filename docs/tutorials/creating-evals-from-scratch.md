---
diataxis_type: tutorial
title: "Building Evals for a Skill That Has None"
description: "Learn how to create evaluation cases for a skill using the eval-doctor agent"
---

# Building Evals for a Skill That Has None

This tutorial walks through creating evaluation cases for a skill that doesn't have any. The eval-doctor agent does the heavy lifting, but you'll learn what good evals look like and how to review them.

**Prerequisites:**
- A skill directory with `SKILL.md` but no `evals/evals.json`
- The autoresearch plugin installed

## Step 1: Run the Eval Doctor

```bash
/autoresearch --eval-doctor path/to/my-skill
```

The eval-doctor reads your skill's `SKILL.md`, scripts, and references to understand what the skill does, then generates eval cases.

## Step 2: What the Eval Doctor Produces

The eval-doctor creates two files:

### evals/evals.json

The main evaluation file. Each eval case has:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic user prompt that exercises the skill",
      "expected_output": "What success looks like in plain English",
      "files": [],
      "expectations": [
        "The output contains a valid JSON object with a 'results' key",
        "Each result has 'name', 'score', and 'timestamp' fields",
        "The total count matches the number of input records"
      ]
    }
  ]
}
```

### evals/trigger-eval.json (optional)

Tests whether the skill's description causes Claude to invoke it for the right prompts:

```json
[
  {"query": "analyze my sales data and create a report", "should_trigger": true},
  {"query": "what's the weather in Tokyo", "should_trigger": false}
]
```

## Step 3: Reviewing the Evals

Don't blindly accept what the eval-doctor produces. Check each eval case:

### Are prompts realistic?

Good prompts sound like a real user:

```
"ok I have this CSV of employee data at ~/hr/employees.csv and I need to
find everyone who joined in the last 90 days and generate onboarding
checklists for each of them"
```

Bad prompts are generic:

```
"Process the input file and generate output"
```

### Are expectations discriminating?

Each expectation should fail if the skill does the wrong thing. Test mentally: would this pass even if the output were garbage?

| Expectation | Verdict |
|---|---|
| "A file was created" | Too weak — passes for any file |
| "Output CSV has columns: name, start_date, department, checklist_status" | Good — specific and verifiable |
| "The output looks professional" | Bad — subjective, unverifiable |

### Is there edge case coverage?

A good eval suite isn't all happy paths. Look for:
- Empty or missing inputs
- Unusual formats (Unicode, large files)
- Ambiguous instructions
- Multi-step tasks where errors can cascade

## Step 4: Editing Evals

The eval-doctor gets you 80% of the way. Edit `evals/evals.json` to:

1. **Tighten weak expectations** — replace vague checks with structural ones
2. **Add edge cases** — include at least 2 evals that test failure modes
3. **Fix unrealistic prompts** — add specific file paths, context, casual language
4. **Remove redundant evals** — 5-8 cases is ideal, each testing something different

See the [Eval Quality Rubric](../reference/eval-schema.md) for the complete checklist.

## Step 5: What Good Evals Look Like

Here's a complete eval case for a "CSV analyzer" skill:

```json
{
  "id": 3,
  "prompt": "I have a CSV at ./data/sales-q4.csv with columns date, region, product, revenue, units. Can you tell me which region had the highest total revenue and break down the top 3 products by units sold?",
  "expected_output": "Analysis identifying top region by revenue and top 3 products by units",
  "files": ["./data/sales-q4.csv"],
  "expectations": [
    "Output identifies a specific region as having the highest total revenue",
    "Output includes the actual revenue total for the top region",
    "Output lists exactly 3 products ranked by units sold",
    "Each product entry includes the unit count",
    "Output does NOT contain placeholder values like 'X' or 'N/A' for numeric fields"
  ]
}
```

Notice:
- Prompt is specific and natural
- Expectations check content accuracy, not just format
- Negative expectation catches placeholder output
- Multiple aspects covered: identification, quantification, ranking

## Step 6: Running the Loop

Once you're satisfied with the evals:

```bash
/autoresearch path/to/my-skill
```

The improvement loop uses your evals as the fixed benchmark. See [Getting Started](getting-started.md) for what happens next.

## Tips

- **Start with 5-6 eval cases** — you can always add more later
- **Run eval-doctor again** after a loop completes — it can use grading feedback from the run to improve evals
- **Don't aim for perfection** — evals that are 80% good are enough to start the loop. The grader's `eval_feedback` will tell you what to fix.

## Next Steps

- Ready to improve? See [Getting Started](getting-started.md)
- Want to understand why evals and skills improve separately? See [Eval-Skill Separation](../explanation/eval-skill-separation.md)
