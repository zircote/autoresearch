---
diataxis_type: how-to
title: "How to Apply Changes"
description: "Apply the best improvement snapshot back to your original skill directory"
---

# How to Apply Changes

## After the Loop Completes

Autoresearch asks:

```
Apply the best version (v3, score 0.85) to the original skill? [y/n]
```

### Applying (y)

The best snapshot replaces files in your original skill directory. This uses the `restore()` function, which:

1. Copies all files from the best snapshot to the original skill
2. Removes files in the original that aren't in the snapshot
3. Skips files with matching SHA-256 hashes (no unnecessary writes)

Your original skill now reflects the improved version.

### Declining (n)

Nothing changes. The workspace remains intact for manual review:

```
path/to/my-skill-autoresearch/
├── v0/           # Your original, untouched
├── v3/           # The best version
├── candidate/    # Same as v3 (or the last attempted version)
└── results.tsv   # Full history
```

## Manual Application

If you declined but later want to apply:

```bash
# Review the diff first
/autoresearch --report path/to/my-skill-autoresearch

# Then manually copy the best version
# (Replace v3 with your actual best version number from results.tsv)
cp -r path/to/my-skill-autoresearch/v3/* path/to/my-skill/
```

Or cherry-pick specific files:

```bash
# Only apply SKILL.md changes
cp path/to/my-skill-autoresearch/v3/SKILL.md path/to/my-skill/SKILL.md
```

## Partial Application

Sometimes the best version improves some things but changes others you don't want. To apply selectively:

1. Run the report to see the diff: `/autoresearch --report path/to/my-skill-autoresearch`
2. Identify which files you want
3. Copy only those files from the best snapshot

## After Applying

1. **Verify**: Read the modified skill files to confirm they look right
2. **Test manually**: Run the skill on a few prompts to sanity check
3. **Commit**: Add the changes to version control
4. **Consider another round**: Starting from a higher baseline, a second run often finds more improvements
5. **Update description**: Use skill-creator to re-optimize the trigger description if SKILL.md changed significantly
