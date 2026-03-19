---
name: sample-skill
description: A sample skill for testing autoresearch.
---

# Text Formatting Skill

This skill transforms unstructured or informal text into clean, well-formatted output. The key principle is **content preservation with structural improvement** — every piece of information from the input must appear in the output, reorganized into the appropriate format.

## General Principles

1. **Preserve all content**: Never drop information from the input. Every fact, name, number, annotation, and qualifier must appear in the output. If the input mentions "Q4 numbers," the output must mention Q4 numbers.
2. **Infer the target format**: Determine from the prompt whether the user wants an email, a list, a report, a summary, or another format. Apply the matching format rules below.
3. **Elevate tone when reformatting**: Replace casual or sloppy language with clear, professional language while keeping the meaning identical.
4. **Use Markdown**: All output should be valid Markdown unless the prompt specifies otherwise.

## Format: Professional Email

When the prompt asks for an email, produce output with ALL of these components in order:

1. **Subject line**: `Subject: <concise topic>` — derived from the input content. Must reflect the actual subject matter.
2. **Blank line** after subject.
3. **Greeting**: Address the recipient by name if one is provided in the input (e.g., `Hi Bob,`). Capitalize the name. Use "Hi" or "Dear" — never "Hey."
4. **Blank line** after greeting.
5. **Body paragraphs**: One or more paragraphs that convey the full content of the input in professional language. Each paragraph should cover a single point. Separate paragraphs with blank lines.
6. **Call to action** (if the email implies one): A clear sentence asking for a next step, such as scheduling a meeting or providing information.
7. **Blank line** before closing.
8. **Sign-off and sender name**: A professional closing like `Best regards,` followed by a newline and the sender's name. If no sender name is provided in the input, use `[Your Name]` as a placeholder — never omit the name line entirely.

**Quality checks for emails:**
- Does the subject line match the email's content?
- Is every fact from the input represented in the body?
- Is the tone consistently professional (no slang, no lowercase "i")?
- Does the closing include both a sign-off phrase AND a name?

## Format: Bulleted List

When the prompt asks for a list, produce output following these rules:

1. **One item per line**, each prefixed with `- ` (Markdown dash bullet).
2. **Capitalize** the first letter of each item.
3. **Preserve annotations**: Parenthetical notes, qualifiers, or metadata (e.g., `(maybe)`, `(optional)`, `(2 lbs)`) stay inline with their item — do not drop them or split them into separate items.
4. **Deduplicate**: If the input contains obvious duplicates, include the item only once.
5. **Consistent punctuation**: Either end all items with periods or none. Default to no trailing periods for short items (single words or short phrases).
6. **Ordering**: Maintain the original order from the input unless the prompt requests sorting.

**Quality checks for lists:**
- Does the output item count match the number of distinct items in the input?
- Are all annotations preserved with their parent items?
- Is formatting consistent across all items?

## Format: General Text

For any other formatting request (reports, summaries, paragraphs, etc.):

1. Use clear paragraph breaks between distinct ideas.
2. Use headings (`##`, `###`) when the content has natural sections.
3. Preserve all factual content from the input.
4. Improve grammar, spelling, and punctuation.
5. Use active voice where possible.

## Process

1. **Read** the input text carefully. Identify every piece of information it contains.
2. **Identify the target format** from the prompt (email, list, report, etc.).
3. **Apply the matching format rules** above to transform the input.
4. **Run quality checks** for the chosen format before returning.
5. **Write** the formatted output to the appropriate file.
