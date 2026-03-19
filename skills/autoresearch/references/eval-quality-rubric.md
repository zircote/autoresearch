# Eval Quality Rubric

This rubric defines what makes good evaluation cases for the autoresearch improvement loop. The eval-doctor agent references this when creating or improving evals.

## Why Eval Quality Matters

The improvement loop can only be as good as its evals. If evals are too easy, every iteration "passes" and no improvement happens. If evals are too hard or poorly defined, the improver can't make progress. If evals are inconsistent, scores bounce randomly and the keep/discard signal is noise.

Good evals are the single most important factor in successful autoresearch runs.

## The Five Qualities of Good Evals

### 1. Discriminating

An expectation is discriminating if it passes when the skill genuinely succeeds and fails when it doesn't.

**Good**: "The output CSV has exactly 5 columns: name, email, phone, company, role"
- Fails if columns are wrong, missing, or extra

**Bad**: "The output is a CSV file"
- Passes for any CSV, even one with completely wrong content

**Test**: Would this expectation pass if the skill produced garbage output in the right format? If yes, it's not discriminating enough.

### 2. Realistic Prompts

Eval prompts should be the kind of thing a real user would actually type.

**Good**: "ok so I have this spreadsheet of customer feedback (it's at ~/Downloads/feedback-Q4.xlsx) and I need to pull out all the complaints about shipping delays and put them in a new sheet with the customer name and date"

**Bad**: "Process the input file and extract relevant data"

Real prompts have:
- Specific file paths and names
- Context about why they need the task done
- Casual language, abbreviations, typos
- Detail about what they want but possibly ambiguous

### 3. Verifiable Outcomes

Each expectation must be checkable by the grader (an LLM reading the transcript and outputs).

**Good**: "The output file contains the text 'Total Revenue: $X' where X is a number"
- Grader can search the output and verify

**Bad**: "The output looks professional"
- Subjective, different graders would disagree

**Good for scripts**: "The Python script exits with code 0 and prints 'Success' to stdout"
- Programmatically verifiable

### 4. Edge Case Coverage

Don't just test the happy path. Include evals for:
- Empty or missing inputs
- Unusual formats (Unicode, very large files, nested structures)
- Ambiguous instructions where the skill must make reasonable choices
- Multi-step tasks where intermediate failures could cascade

A good eval suite has 1-2 happy path cases and 3-4 edge cases.

### 5. Independence

Each eval case should test a distinct aspect of the skill. Don't create 5 evals that all test the same thing with slightly different inputs — the improvement loop can't learn from redundant signal.

## Deterministic vs. LLM Expectations

Expectations fall into two categories:

### Deterministic Checks (preferred when applicable)
Programmatic validation that produces identical results every time. These live in the `deterministic_checks` array on each eval case and run before the LLM grader.

Advantages:
- Zero variance — same output, same grade, every time
- Fast — no LLM call needed
- Precise — exact field values, regex patterns, file existence

Use for:
- JSON field equality: "manifest_version is 0.3"
- File existence: ".mcpbignore exists"
- Pattern matching: "name matches ^[a-z0-9-]+$"
- Array membership: "tools array contains search_files"
- String presence: "file contains 'node_modules/'"
- Validation scripts: "passes validate-manifest.sh"

### LLM Expectations (for semantic judgment)
The LLM grader reads transcripts and outputs to make qualitative judgments. Keep these for things that require understanding context.

Use for:
- Transcript behavior: "the skill asked before creating files"
- Semantic correctness: "the recommendation is appropriate"
- Complex multi-file reasoning: "the workflow references the correct action"
- Intent verification: "the skill followed the correct execution order"

### Migration Rule
When reviewing existing evals, convert LLM expectations to deterministic checks wherever possible. A good eval suite should have 60-80% deterministic checks. This reduces score variance and makes the improvement loop signal more reliable.

## Expectation Anti-Patterns

### Trivially Satisfied
- "The skill produced output" — almost always passes
- "A file was created" — checks existence, not correctness
- "The output contains text" — any text satisfies this

### Untestable
- "The output is well-organized" — subjective
- "The code is efficient" — can't verify from output alone
- "The user would be satisfied" — requires human judgment

### Overly Specific
- "The output contains exactly 'Hello, John! Welcome to...' " — brittle, fails on minor wording changes
- "Line 47 contains X" — breaks if anything shifts

### LLM-Graded When Deterministic Would Suffice
- "manifest.json contains 'manifest_version': '0.3'" — use `json_field_equals`
- "The file .mcpbignore exists" — use `file_exists`
- "The name is lowercase" — use `json_field_matches` with regex `^[a-z0-9-]+$`
- "Version is valid semver" — use `regex_match` with semver pattern

These waste LLM grading cycles and introduce unnecessary score variance.

### Correct Approach
- Check structural properties: "output has N sections", "each section has a header"
- Check content accuracy: "output mentions X from the input", "total matches sum of line items"
- Check format compliance: "output is valid JSON", "CSV has correct column headers"
- Check negative cases: "output does NOT contain placeholder text", "no TODO markers remain"

## How Many Evals?

- **Minimum**: 3 eval cases (too few = unreliable signal)
- **Ideal**: 5-8 eval cases (good coverage without excessive runtime)
- **Maximum**: 12 eval cases (more = slower iterations, diminishing returns)

Each eval case should have 3-6 expectations.

## Using Grader Feedback

After each autoresearch run, the grader produces `eval_feedback` in grading.json:
- **suggestions**: Specific improvements to individual assertions
- **overall**: Assessment of eval quality

Common grader feedback patterns:
- "This assertion passed but would also pass for wrong output" → Make it more discriminating
- "Important outcome X has no assertion" → Add coverage
- "This assertion can't be verified from outputs" → Rewrite to be verifiable or add output capture

Always read eval_feedback before creating new evals — it's the most actionable signal for improvement.

## Trigger Evals

Trigger evals (trigger-eval.json) test whether the skill's description causes Claude to invoke it for the right prompts. These follow a different schema:

```json
[
  {"query": "prompt text", "should_trigger": true},
  {"query": "prompt text", "should_trigger": false}
]
```

For trigger evals:
- Should-trigger queries should be diverse (formal, casual, different phrasings)
- Should-not-trigger queries should be near-misses (share keywords but need different skills)
- Both should be realistic — complex enough that Claude would actually consider a skill
