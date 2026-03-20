# Autoresearch Improvement Loop Algorithm

This document specifies the complete algorithm for the autoresearch skill improvement loop. It is referenced by the improver agent, the SKILL.md orchestrator, and the documentation.

## Overview

The autoresearch loop applies Karpathy's autoresearch pattern to Claude Code skills. The core insight: autonomous agents can iterate on artifacts (skills) while humans sleep, as long as there's a reliable evaluation metric to guide improvement.

- **train.py** → SKILL.md (the artifact being improved)
- **val_bpb** → expectation pass_rate from grading.json
- **program.md** → SKILL.md orchestrator (the loop instructions)

## Initialization

```
INPUTS:
  skill_path     = path to the original skill directory
  max_iterations = 5 (default)

INIT:
  workspace = {skill_name}-autoresearch/   # sibling to skill directory

  # Create immutable baseline
  snapshot(skill_path → workspace/v0/)

  # Create mutable working copy
  snapshot(skill_path → workspace/candidate/)

  # Establish baseline score
  score_0 = evaluate(workspace/candidate/)
  best = {version: 0, score: score_0}

  # Initialize results log
  append(results.tsv, {iteration: 0, score: score_0, best_score: score_0,
                        action: "baseline", changelog: "Initial evaluation"})
```

## Evaluation Procedure

Evaluation runs the skill's evals and grades the outputs:

```
FUNCTION evaluate(candidate_path):
  evals = load(candidate_path/evals/evals.json)
  scores = []

  FOR EACH eval_case IN evals:
    # Run the skill on the eval prompt
    run_dir = workspace/iteration-{i}/eval-{eval_case.id}/

    # Execute: claude -p with the candidate skill available
    # This runs the eval prompt with the skill loaded
    execute_eval(eval_case.prompt, candidate_path, run_dir)

    # Grade: use skill-creator's grader agent
    grade(run_dir, eval_case.expectations)
    # Produces: run_dir/grading.json

    scores.append(grading.json.summary.pass_rate)

  RETURN mean(scores)
```

### Discovering skill-creator

The grader agent lives in the skill-creator plugin:

```
SKILL_CREATOR = find first match:
  ${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator/
```

Use `agents/grader.md` from skill-creator to grade eval outputs. The grading.json schema is defined in skill-creator's `references/schemas.md`.

### Running evals

For each eval case:
1. Create run directory: `workspace/iteration-{i}/eval-{id}/`
2. Run: `claude -p "{eval_case.prompt}" --allowedTools "Skill,Read,Write,Bash,Glob,Grep,Edit"` with the candidate skill available
3. Capture transcript to `run_dir/transcript.md`
4. Save outputs to `run_dir/outputs/`
5. Spawn grader with: expectations, transcript_path, outputs_dir
6. Grader writes `run_dir/grading.json`

## Main Loop

```
FOR i IN 1..max_iterations:

  # MODIFY: improver agent reads failures, edits candidate
  spawn improver(
    candidate_path = workspace/candidate/,
    grading_results = workspace/iteration-{i-1}/*/grading.json,
    history = workspace/results.tsv,
    iteration = i
  )
  # Improver modifies files in workspace/candidate/

  # EVALUATE: run evals on modified candidate
  score_i = evaluate(workspace/candidate/)

  # KEEP or DISCARD
  IF score_i > best.score:
    # Keep: snapshot the improved version
    snapshot(workspace/candidate/ → workspace/v{i}/)
    best = {version: i, score: score_i}
    action = "kept"
  ELSE:
    # Discard: restore candidate from best version
    restore(workspace/v{best.version}/ → workspace/candidate/)
    action = "reverted"

  # Log results
  append(results.tsv, {iteration: i, score: score_i, best_score: best.score,
                        action: action, changelog: improver.changelog})

  # ABORT CONDITIONS
  IF best.score >= 1.0:
    BREAK  # Perfect score achieved

  IF last 3 actions are all "reverted":
    BREAK  # Stuck — 3 consecutive reverts
```

## Finalization

```
FINALIZE:
  # Generate convergence report
  spawn convergence_reporter(
    workspace = workspace,
    v0_path = workspace/v0/,
    best_path = workspace/v{best.version}/
  )

  # Show diff between baseline and best
  diff = diff_report(workspace/v0/, workspace/v{best.version}/)

  # Ask user to confirm applying changes
  IF user confirms:
    restore(workspace/v{best.version}/ → skill_path)
    # Original skill is now updated

  # Always clean up workspace — it is transient and must not persist
  rm -rf workspace/
```

## Three Modes

### Mode 1: Full Improvement Loop (default)
```
/autoresearch <skill-path>
```
Runs the complete init → loop → finalize sequence.

### Mode 2: Eval Doctor
```
/autoresearch --eval-doctor <skill-path>
```
Spawns the eval-doctor agent to create/fix/improve evals. Does NOT run the improvement loop. Use this first when a skill has no evals or poor evals.

### Mode 3: Report
```
/autoresearch --report <workspace>
```
Spawns the convergence reporter on an existing workspace. Use to review results after a run.

## Safety Invariants

1. **Original skill is never modified during the loop** — only workspace/candidate/ is mutable
2. **Snapshots are immutable** — once v{N}/ is created, it is never modified
3. **Evals are frozen during improvement** — the improver agent must not touch evals/
4. **SHA-compare before write** — snapshot() skips unchanged files
5. **User confirmation required** — changes are only applied to the original after explicit approval
6. **Regression abort** — 3 consecutive reverts stops the loop to prevent wasted computation
7. **Workspace cleanup mandatory** — the workspace directory is removed after finalization; it must never persist on disk or be committed

## Score Computation

The score is the mean pass_rate across all grading.json files for an iteration:

```
score = mean([g.summary.pass_rate for g in iteration_grading_files])
```

Where pass_rate is: passed_expectations / total_expectations for each eval case.

## Workspace Layout

```
{skill-name}-autoresearch/
├── results.tsv              # Score progression log
├── v0/                      # Immutable baseline snapshot
│   ├── SKILL.md
│   ├── scripts/
│   └── ...
├── candidate/               # Mutable working copy
│   ├── SKILL.md
│   ├── scripts/
│   └── ...
├── v1/                      # Snapshot of iteration 1 (if kept)
├── v3/                      # Snapshot of iteration 3 (if kept, 2 was reverted)
├── iteration-0/             # Baseline eval results
│   ├── eval-1/
│   │   ├── transcript.md
│   │   ├── outputs/
│   │   └── grading.json
│   └── eval-2/
│       └── ...
├── iteration-1/             # Iteration 1 eval results
│   └── ...
└── iteration-2/
    └── ...
```
