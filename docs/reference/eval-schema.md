---
diataxis_type: reference
title: "Eval Schema Reference"
description: "JSON schema specification for evals.json evaluation case files"
---

# Eval Schema Reference

## evals.json

Located at `{skill-path}/evals/evals.json`.

### Schema

```json
{
  "skill_name": "string — must match SKILL.md frontmatter name",
  "evals": [
    {
      "id": "integer — unique within the file, starting at 1",
      "prompt": "string — realistic user prompt that exercises the skill",
      "expected_output": "string — human-readable description of what success looks like",
      "files": ["string — paths to input files needed by the eval (optional, can be empty)"],
      "expectations": [
        "string — specific, verifiable assertion about the output"
      ]
    }
  ]
}
```

### Field Details

#### `id`
Unique integer identifier for the eval case. Used in directory naming (`eval-{id}/`) and logging. Must be unique within the file.

#### `prompt`
The text passed to Claude as the user's request. Should be realistic — the kind of thing a real user would type. Include:
- Specific file paths and names
- Context about why they need the task done
- Natural language with appropriate detail

#### `expected_output`
Plain English description of what a successful execution looks like. Used for human review, not automated grading. The `expectations` array handles grading.

#### `files`
Array of file paths that the eval requires as input. These files must exist (or be created by the eval setup) for the eval to run. Empty array if no input files needed.

#### `expectations`
Array of specific, verifiable assertions. Each string should describe a checkable property of the output. The grader evaluates each independently as pass/fail.

Good expectations:
- "The output CSV has columns: name, email, department"
- "The total revenue value matches the sum of line items"
- "Output does NOT contain placeholder text like 'TODO' or 'FIXME'"

Bad expectations:
- "The output looks correct" (subjective)
- "A file was created" (trivially satisfied)
- "The code is efficient" (unverifiable from output)

### Sizing Guidelines

| Metric | Minimum | Ideal | Maximum |
|---|---|---|---|
| Eval cases | 3 | 5-8 | 12 |
| Expectations per case | 2 | 3-6 | 8 |

### Example

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV at ./data/sales.csv with columns date, region, product, revenue. What region had the highest total revenue last quarter?",
      "expected_output": "Analysis identifying the top region by revenue with supporting numbers",
      "files": ["./data/sales.csv"],
      "expectations": [
        "Output identifies a specific region as having the highest revenue",
        "Output includes the actual revenue total for that region",
        "Output specifies the time period analyzed",
        "Output does NOT contain 'I cannot' or 'I don't have access'"
      ]
    },
    {
      "id": 2,
      "prompt": "analyze this empty CSV file at ./data/empty.csv and tell me what you find",
      "expected_output": "Graceful handling of empty input with clear message",
      "files": ["./data/empty.csv"],
      "expectations": [
        "Output acknowledges the file is empty or has no data rows",
        "Output does NOT produce an error traceback",
        "Output suggests next steps or asks for clarification"
      ]
    }
  ]
}
```

## trigger-eval.json

Located at `{skill-path}/evals/trigger-eval.json`. Tests whether the skill's description causes Claude to invoke it for the right prompts.

### Schema

```json
[
  {
    "query": "string — user prompt to test",
    "should_trigger": "boolean — true if this prompt should invoke the skill"
  }
]
```

### Guidelines

- Include 8-10 `should_trigger: true` queries (diverse phrasings, formal and casual)
- Include 8-10 `should_trigger: false` queries (near-misses that share keywords)
- Make negative cases challenging — obviously unrelated queries don't test anything

### Example

```json
[
  {"query": "analyze the sales data in my spreadsheet and find trends", "should_trigger": true},
  {"query": "can you look at this CSV and tell me which products are selling best", "should_trigger": true},
  {"query": "I need to convert this CSV to JSON format", "should_trigger": false},
  {"query": "help me write a Python script to parse CSV files", "should_trigger": false}
]
```

## Quality Rubric

For detailed guidance on writing good evals, see the [eval quality rubric](../../skills/autoresearch/references/eval-quality-rubric.md). Key qualities:

1. **Discriminating** — Fails when the skill does the wrong thing
2. **Realistic prompts** — Sound like real users
3. **Verifiable outcomes** — Grader can check pass/fail objectively
4. **Edge case coverage** — Not just happy paths
5. **Independence** — Each eval tests something different
