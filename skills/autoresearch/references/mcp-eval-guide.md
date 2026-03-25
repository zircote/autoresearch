# MCP Server Evaluation Guide

Guide for creating and running QA-pair evaluations for MCP servers in autoresearch.

## Overview

MCP server evaluation uses XML QA pairs instead of the JSON evals used for skills. Each QA pair is a question that an LLM should be able to answer using the MCP server's tools, paired with an expected answer verified via exact string comparison.

This differs from skill evaluation in three ways:
1. **Format**: XML (`evaluation.xml`) instead of JSON (`evals.json`)
2. **Scoring**: Deterministic exact-match instead of LLM-graded expectations
3. **Target**: The artifact being improved is MCP server source code, not SKILL.md

## evaluation.xml Schema

```xml
<evaluation>
   <qa_pair id="1">
      <question>Your question here</question>
      <answer>Single verifiable answer</answer>
   </qa_pair>
   <qa_pair id="2">
      <question>Another question</question>
      <answer>Another answer</answer>
   </qa_pair>
</evaluation>
```

- `<evaluation>`: Root element containing all QA pairs
- `<qa_pair>`: One question-answer pair. Optional `id` attribute (auto-generated if omitted)
- `<question>`: The question text. Must be answerable using the MCP server's tools
- `<answer>`: The expected answer. Must be a single, verifiable string value

## QA Pair Authoring Guidelines

### Core Requirements

1. **Questions must be answerable using the MCP tools** — each question should exercise one or more tools provided by the server
2. **Answers must be deterministic** — the same question should always produce the same answer
3. **Answers must be exact strings** — verified via case-insensitive comparison after whitespace stripping
4. **Questions should specify answer format** when ambiguous (e.g., "Answer as YYYY-MM-DD", "Respond True or False")

### Question Categories

- **Tool invocation**: Direct use of a specific tool with specific inputs
- **Multi-tool**: Requires combining results from multiple tool calls
- **Error handling**: What happens with invalid inputs or edge cases
- **Edge cases**: Boundary conditions, empty inputs, large datasets

### Answer Format

- Single values: names, numbers, dates, IDs, booleans
- Case-insensitive comparison: "Paris" matches "paris" and "PARIS"
- Whitespace stripped: " Paris \n" matches "Paris"
- Avoid lists or complex structures — use counts or superlatives instead

### Anti-Patterns to Avoid

- **Time-dependent answers**: "How many items exist?" changes over time
- **Non-deterministic answers**: Random outputs, LLM-generated text
- **Ambiguous answers**: Multiple valid interpretations
- **Too-easy questions**: Solvable without using any tools
- **List answers**: "List all X" — use "How many X?" or "Which X has the most Y?" instead

## Scoring

Answers are compared using normalized exact string match:

```
normalize(s) = s.strip().lower()
passed = normalize(actual) == normalize(expected)
score = 1.0 if passed else 0.0
```

The overall score is: `count(passed) / count(total)`, normalized to 0.0–1.0.

## Grading Adapter

QA results are converted to grading.json format so that all existing infrastructure (score.py, dashboard.py, convergence-reporter) works unchanged.

Field mapping:

| grading.json field | Source |
|---|---|
| `expectations[].text` | `qa.question` |
| `expectations[].passed` | `normalize(actual) == normalize(expected)` |
| `expectations[].evidence` | `"Expected: X, Got: Y"` or `"Exact match: X"` |
| `expectations[].source` | `"deterministic"` (always) |
| `summary.pass_rate` | `count(passed) / count(total)` |
| `summary.passed` | Count of passed expectations |
| `summary.failed` | Count of failed expectations |
| `summary.total` | Total QA pairs |

## Example evaluation.xml

```xml
<evaluation>
   <qa_pair id="1">
      <question>What does the get-weather tool return for location "London"? Provide just the temperature in Celsius as a number.</question>
      <answer>15</answer>
   </qa_pair>
   <qa_pair id="2">
      <question>How many tools are available in the MCP server? Answer with just the number.</question>
      <answer>5</answer>
   </qa_pair>
   <qa_pair id="3">
      <question>What error message is returned when calling get-weather with an empty location? Provide the exact error text.</question>
      <answer>Location parameter is required</answer>
   </qa_pair>
   <qa_pair id="4">
      <question>What is the name of the tool that retrieves forecast data?</question>
      <answer>get-forecast</answer>
   </qa_pair>
   <qa_pair id="5">
      <question>Using get-weather for "Tokyo" and "London", which city has the higher temperature? Answer with just the city name.</question>
      <answer>Tokyo</answer>
   </qa_pair>
</evaluation>
```
