---
name: sample-skill
description: A sample skill for testing autoresearch.
---

# Sample Skill

This skill helps with basic text formatting.

## Process

1. Read the input text
2. Identify the format type (email, list, table, meeting notes, contact card, paragraph)
3. Apply format-specific rules
4. Return the result

## Format-Specific Rules

### Emails
- Use a proper salutation addressing the recipient by name
- Organize body into clear paragraphs covering each topic
- End with a professional closing and signature

### Lists
- Use consistent bullet markers for each item
- Place each item on its own line
- Preserve annotations or parenthetical notes from the original

### Meeting Notes
- Create distinct labeled sections: attendees, date, discussion, decisions, next steps
- Attribute action items to the correct person

### Tables
- Include headers/column labels
- Maintain consistent alignment across rows

### Edge Cases
- If the input is empty or blank, respond with a message indicating no text was provided
- Never fabricate content that was not in the original input
- Normalize extra whitespace to single spaces
- Fix missing spaces between sentences
