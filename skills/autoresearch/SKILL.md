---
name: autoresearch
description: Autonomous skill improvement loop inspired by Karpathy's autoresearch pattern. Iteratively modifies skills, evaluates against fixed evals, keeps or discards changes to converge on higher quality. Includes eval management and convergence reporting. Use when users want to automatically improve a skill's quality, create or fix evals for a skill, or view improvement loop results. Triggers on "autoresearch", "improve skill automatically", "auto-improve", "skill improvement loop", "run improvement loop", "eval doctor", "fix evals", "create evals for skill", "skill quality", "autonomous improvement".
argument-hint: [--eval-doctor | --report | --iterations N] <skill-path>
---

# Autoresearch

Autonomous skill improvement loop. Modify → evaluate → keep/discard → repeat.

## Mode Detection

Parse the user's input to determine which mode to run:

1. **Full loop** (default): `/autoresearch <skill-path>` or `/autoresearch <skill-path> --iterations N`
2. **Eval doctor**: `/autoresearch --eval-doctor <skill-path>`
3. **Report**: `/autoresearch --report <workspace-path>`

Extract:
- `skill_path`: Path to the skill directory (must contain SKILL.md)
- `mode`: One of `loop`, `eval-doctor`, `report`
- `max_iterations`: Number of iterations (default: 5, max: 10)

## Prerequisites

Before running any mode, locate skill-creator:

```bash
SKILL_CREATOR=$(find ${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/plugins/cache/claude-plugins-official/skill-creator/ -name "SKILL.md" -path "*/skills/skill-creator/*" -print -quit 2>/dev/null | xargs dirname)
```

If not found, tell the user: "The skill-creator plugin is required. Install it with: `claude plugins add skill-creator`"

Also verify the skill path:
1. Check `{skill_path}/SKILL.md` exists
2. Check `{skill_path}/evals/evals.json` exists (required for loop mode, eval-doctor can create it)

## Script Paths

All scripts are in this skill's `scripts/` directory:

```bash
SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/skills/autoresearch/scripts"
```

Usage:
```bash
python3 -c "import sys; sys.path.insert(0, '${SCRIPTS_DIR}'); from snapshot import snapshot; from pathlib import Path; snapshot(Path('src'), Path('dst'))"
```

---

## Mode 1: Full Improvement Loop

Read `references/algorithm.md` for the complete specification. Summary below.

### Step 1: Initialize Workspace

```bash
WORKSPACE="${skill_path}/../$(basename ${skill_path})-autoresearch"
mkdir -p "${WORKSPACE}"
```

1. **Snapshot v0** (immutable baseline):
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from snapshot import snapshot; from pathlib import Path
   snapshot(Path('${skill_path}'), Path('${WORKSPACE}/v0'))
   "
   ```

2. **Copy candidate** (mutable working copy):
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from snapshot import snapshot; from pathlib import Path
   snapshot(Path('${skill_path}'), Path('${WORKSPACE}/candidate'))
   "
   ```

3. **Evaluate baseline** (Step 2 below), get score_0
4. **Log baseline**:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from results_log import append; from pathlib import Path
   append(Path('${WORKSPACE}/results.tsv'), {
       'iteration': '0', 'score': '${score_0}', 'best_score': '${score_0}',
       'action': 'baseline', 'changelog': 'Initial evaluation'
   })
   "
   ```

### Step 2: Evaluate Candidate

For each eval case in `evals/evals.json`:

1. Create run directory: `${WORKSPACE}/iteration-{i}/eval-{id}/`
2. Create `outputs/` subdirectory
3. Execute the eval by spawning a subagent:

```
Execute this task:
- Read the skill at: ${WORKSPACE}/candidate/SKILL.md
- Follow the skill's instructions to accomplish this task: {eval_case.prompt}
- Input files: {eval_case.files or "none"}
- Save all outputs to: ${WORKSPACE}/iteration-{i}/eval-{id}/outputs/
- Save a transcript of your work to: ${WORKSPACE}/iteration-{i}/eval-{id}/transcript.md
```

4. Grade by spawning a grader subagent that reads `${SKILL_CREATOR}/agents/grader.md`:

```
You are a grader. Read and follow the instructions in: ${SKILL_CREATOR}/agents/grader.md

Grade these expectations against the execution results:
- expectations: {eval_case.expectations}
- transcript_path: ${WORKSPACE}/iteration-{i}/eval-{id}/transcript.md
- outputs_dir: ${WORKSPACE}/iteration-{i}/eval-{id}/outputs/

Write grading.json to: ${WORKSPACE}/iteration-{i}/eval-{id}/grading.json
```

5. Compute composite score:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from score import compute_score; from pathlib import Path
   print(compute_score(Path('${WORKSPACE}'), ${iteration}))
   "
   ```

### Step 3: Improvement Loop

For each iteration i = 1 to max_iterations:

**3a. Modify** — Spawn the improver agent (read `agents/improver.md`):

```
You are a skill improver. Read and follow: ${PLUGIN_ROOT}/skills/autoresearch/agents/improver.md

Inputs:
- candidate_path: ${WORKSPACE}/candidate/
- grading_results: ${WORKSPACE}/iteration-{i-1}/*/grading.json
- history: ${WORKSPACE}/results.tsv
- iteration: {i}

Improve the candidate skill to achieve higher eval pass rates.
```

**3b. Evaluate** — Run Step 2 on the modified candidate.

**3c. Keep or Discard**:
- If `score_i > best_score`: snapshot candidate to `v{i}/`, update best
- If `score_i <= best_score`: restore candidate from best snapshot

**3d. Log** — Append to results.tsv

**3e. Check Abort Conditions**:
- `best_score >= 1.0` → Stop (perfect)
- Last 3 actions all "reverted" → Stop (stuck)

### Step 4: Finalize

1. Spawn convergence reporter (read `agents/convergence-reporter.md`):
   ```
   You are a convergence reporter. Read and follow:
   ${PLUGIN_ROOT}/skills/autoresearch/agents/convergence-reporter.md

   Inputs:
   - workspace: ${WORKSPACE}
   - v0_path: ${WORKSPACE}/v0/
   - best_path: ${WORKSPACE}/v{best_version}/
   ```

2. Show the report and diff to the user
3. Ask: "Apply the best version (v{N}, score {S}) to the original skill? [y/n]"
4. If confirmed:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from snapshot import restore; from pathlib import Path
   restore(Path('${WORKSPACE}/v${best_version}'), Path('${skill_path}'))
   "
   ```

---

## Mode 2: Eval Doctor

Spawn the eval-doctor agent (read `agents/eval-doctor.md`):

```
You are an eval doctor. Read and follow:
${PLUGIN_ROOT}/skills/autoresearch/agents/eval-doctor.md

Inputs:
- skill_path: ${skill_path}
- prior_grading: <paths to any existing grading.json files, or "none">

Create or improve evals for this skill.
```

After the eval-doctor completes:
1. Validate `evals/evals.json` has valid JSON with required fields
2. Report how many eval cases were created/modified
3. Suggest running the full loop: "Evals ready. Run `/autoresearch ${skill_path}` to start the improvement loop."

---

## Mode 3: Report

Spawn the convergence reporter (read `agents/convergence-reporter.md`):

```
You are a convergence reporter. Read and follow:
${PLUGIN_ROOT}/skills/autoresearch/agents/convergence-reporter.md

Inputs:
- workspace: ${workspace_path}
- v0_path: ${workspace_path}/v0/
- best_path: ${workspace_path}/v{best_version}/
```

Read `results.tsv` to determine the best version number before spawning.

---

## Safety Rails

- **Never modify the original skill** during the loop — work only on `candidate/`
- **Snapshots are immutable** — never write to `v{N}/` after creation
- **Evals frozen during improvement** — the improver must not touch `evals/`
- **User confirmation required** before applying changes to the original
- **Abort on stuck** — 3 consecutive reverts stops the loop

## References

- `references/algorithm.md` — Complete loop algorithm specification
- `references/eval-quality-rubric.md` — What makes good evals
- `agents/improver.md` — How the improver modifies skills
- `agents/eval-doctor.md` — How the eval-doctor creates/fixes evals
- `agents/convergence-reporter.md` — How convergence reports are generated
