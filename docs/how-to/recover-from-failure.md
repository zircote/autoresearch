---
diataxis_type: how-to
title: "How to Recover from Failure"
description: "Resume interrupted runs and recover from crashes or timeouts"
---

# How to Recover from Failure

## Interrupted Runs

If autoresearch is interrupted mid-loop (crash, timeout, Ctrl-C), the workspace preserves all progress:

```
path/to/my-skill-autoresearch/
├── results.tsv        # All completed iterations are logged
├── v0/                # Baseline is always safe
├── v2/                # Last kept snapshot (if any)
├── candidate/         # May be in a modified state
└── iteration-3/       # Partial eval results from interrupted iteration
```

**Your original skill is never modified during the loop.** It's always safe.

### Resume by re-running

```bash
/autoresearch path/to/my-skill
```

This creates a fresh workspace and starts over. The previous workspace is preserved.

There is no resume-from-checkpoint. Each run is self-contained.

### Salvage partial results

If the interrupted run made progress (check `results.tsv`), you can manually apply the best snapshot:

```bash
# Check what was achieved
cat path/to/my-skill-autoresearch/results.tsv

# If v2 had a good score, apply it
cp -r path/to/my-skill-autoresearch/v2/* path/to/my-skill/
```

## Inspecting Snapshots

Each kept iteration creates an immutable snapshot:

```bash
# List all snapshots
ls -d path/to/my-skill-autoresearch/v*/

# Compare baseline to a specific version
diff -r path/to/my-skill-autoresearch/v0/ path/to/my-skill-autoresearch/v2/

# View the report for context
/autoresearch --report path/to/my-skill-autoresearch
```

## Manual Revert

If you applied changes and want to undo:

```bash
# Restore from the baseline snapshot
cp -r path/to/my-skill-autoresearch/v0/* path/to/my-skill/
```

Or if you use version control:

```bash
git checkout -- path/to/my-skill/
```

## Common Failure Scenarios

### Skill-creator not found

```
Error: The skill-creator plugin is required.
```

Install it: `claude plugins add skill-creator`

### No evals found

```
Error: evals/evals.json not found
```

Run eval-doctor first: `/autoresearch --eval-doctor path/to/my-skill`

### All evals fail at baseline

If the baseline score is 0.0, the skill may be fundamentally broken. Check:
1. Does the skill work at all when invoked manually?
2. Are eval prompts appropriate for what the skill does?
3. Are expectations realistic?

### Grading errors

If grading.json files are missing or malformed, check:
1. Is skill-creator installed and accessible?
2. Do eval cases have valid `expectations` arrays?
3. Look at `iteration-{N}/eval-{id}/transcript.md` for execution errors

### Workspace already exists

A new run creates a fresh workspace each time. If a workspace already exists from a previous run, the new one is created alongside it. Check the directory name — it includes the skill name.
