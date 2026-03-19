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
