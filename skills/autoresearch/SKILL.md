---
name: autoresearch
description: Autonomous skill and MCP server improvement loop inspired by Karpathy's autoresearch pattern. Iteratively modifies skills or MCP server code, evaluates against fixed evals, keeps or discards changes to converge on higher quality. Supports skill evals (evals.json) and MCP server evals (evaluation.xml with QA pairs). Includes eval management and convergence reporting. Use when users want to automatically improve a skill's quality, improve an MCP server, create or fix evals for a skill or MCP server, or view improvement loop results. Triggers on "autoresearch", "improve skill automatically", "auto-improve", "skill improvement loop", "run improvement loop", "eval doctor", "fix evals", "create evals for skill", "skill quality", "autonomous improvement", "improve MCP server", "MCP eval".
argument-hint: [--eval-doctor | --report | --iterations N] <skill-path>
---

# Autoresearch

Autonomous skill improvement loop. Modify → evaluate → keep/discard → repeat.

**CRITICAL: This skill MUST actually execute all commands and create real files on disk.** Do NOT simulate, describe, or document what "would" happen. Every `mkdir`, `python3`, `rm`, and file write must be a real tool invocation that produces real filesystem artifacts. If a step says "create directory X," you must run `mkdir -p X` via a Bash tool call and verify it exists. Transcripts must reflect actual execution, not hypothetical walkthroughs.

## Mode Detection

Parse the user's input to determine which mode to run:

1. **Full loop** (default): `/autoresearch <skill-path>` or `/autoresearch <skill-path> --iterations N`
2. **Eval doctor**: `/autoresearch --eval-doctor <skill-path>`
3. **Report**: `/autoresearch --report <workspace-path>`

Extract:
- `skill_path`: Path to the skill or MCP server directory
- `mode`: One of `loop`, `eval-doctor`, `report`
- `max_iterations`: Number of iterations (default: 5, max: 10)

## Prerequisites

Before running any mode, locate skill-creator:

```bash
SKILL_CREATOR=$(find ${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/plugins/cache/claude-plugins-official/skill-creator/ -name "SKILL.md" -path "*/skills/skill-creator/*" -print -quit 2>/dev/null | xargs dirname)
```

If not found, tell the user: "The skill-creator plugin is required. Install it with: `claude plugins add skill-creator`"

Also verify the skill path and detect artifact type:
1. If `{skill_path}/evals/evaluation.xml` exists → set `ARTIFACT_TYPE=mcp-server`
   Else if `{skill_path}/evals/evals.json` exists → set `ARTIFACT_TYPE=skill`
   Else → error: "No evals found. Run `/autoresearch --eval-doctor {skill_path}` to create them."
2. For `ARTIFACT_TYPE=skill`: Check `{skill_path}/SKILL.md` exists
3. For `ARTIFACT_TYPE=mcp-server`: Verify a server entry point exists (package.json, main .py/.ts file)

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

Run these commands via Bash tool calls (do NOT just describe them — actually execute them):

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

**If `ARTIFACT_TYPE=mcp-server`**: Use MCP QA evaluation (see Step 2-MCP below).
**If `ARTIFACT_TYPE=skill`**: Use skill evaluation (this section).

**CRITICAL: Each eval execution MUST produce visible tool calls in the transcript.** The eval subagent must actually run Bash commands, read files, and write outputs using real tool invocations. The transcript must show these tool calls — not narrative summaries like "Eval 1: scored 4/5". If the transcript only contains descriptions of what happened without visible Bash/Read/Write tool calls for each eval, the evaluation is invalid.

For each eval case in `evals/evals.json`:

1. Create run directory via Bash: `mkdir -p ${WORKSPACE}/iteration-{i}/eval-{id}/outputs/`
2. Execute the eval by spawning a subagent (Agent or Task tool). The subagent MUST use real tool calls (Bash, Read, Write, Edit) to execute the skill and produce outputs — every step must be a visible tool invocation in the transcript, not a narrated summary:

```
Execute this task using REAL tool calls (Bash, Read, Write). Every action must be a visible tool invocation, not a description.
- Read the skill at: ${WORKSPACE}/candidate/SKILL.md
- Follow the skill's instructions to accomplish this task: {eval_case.prompt}
- Input files: {eval_case.files or "none"}
- Deterministic checks: {eval_case.deterministic_checks or "none"} (optional, run automatically in step 3.5)
- Save all outputs to: ${WORKSPACE}/iteration-{i}/eval-{id}/outputs/
- Save a transcript of your work to: ${WORKSPACE}/iteration-{i}/eval-{id}/transcript.md
IMPORTANT: Your transcript must contain actual tool call results, not prose descriptions of what you did.
```

3.5. Run deterministic checks (if the eval case has a `deterministic_checks` field):

```bash
python3 -c "
import sys, json; sys.path.insert(0, '${SCRIPTS_DIR}')
from deterministic_checker import run_deterministic_checks
from pathlib import Path

checks = json.loads(Path('${WORKSPACE}/candidate/evals/evals.json').read_text())
eval_case = [e for e in (checks if isinstance(checks, list) else checks.get('evals', checks)) if str(e.get('id')) == '${eval_id}'][0]
det_checks = eval_case.get('deterministic_checks', [])
if det_checks:
    result = run_deterministic_checks(
        det_checks,
        Path('${WORKSPACE}/iteration-${i}/eval-${eval_id}/outputs/'),
        env={'OUTPUTS_DIR': '${WORKSPACE}/iteration-${i}/eval-${eval_id}/outputs/'}
    )
    Path('${WORKSPACE}/iteration-${i}/eval-${eval_id}/deterministic-results.json').write_text(
        json.dumps(result, indent=2)
    )
    print(f'Deterministic: {result[\"summary\"][\"passed\"]}/{result[\"summary\"][\"total\"]} passed')
"
```

4. Grade by spawning a grader subagent that reads `${SKILL_CREATOR}/agents/grader.md`:

```
You are a grader. Read and follow the instructions in: ${SKILL_CREATOR}/agents/grader.md

Grade these expectations against the execution results:
- expectations: {eval_case.expectations}
- deterministic_checks: {eval_case.deterministic_checks or "none"} (optional, results merged in step 4.5)
- transcript_path: ${WORKSPACE}/iteration-{i}/eval-{id}/transcript.md
- outputs_dir: ${WORKSPACE}/iteration-{i}/eval-{id}/outputs/

Write grading.json to: ${WORKSPACE}/iteration-{i}/eval-{id}/grading.json
```

4.5. Merge deterministic results into grading (if deterministic-results.json exists):

```bash
python3 -c "
import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
from deterministic_checker import merge_deterministic_into_grading
from pathlib import Path

det = Path('${WORKSPACE}/iteration-${i}/eval-${eval_id}/deterministic-results.json')
grading = Path('${WORKSPACE}/iteration-${i}/eval-${eval_id}/grading.json')
if det.exists() and grading.exists():
    merge_deterministic_into_grading(det, grading)
    print('Merged deterministic results into grading.json')
"
```

5. Compute composite score:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from score import compute_score; from pathlib import Path
   print(compute_score(Path('${WORKSPACE}'), ${iteration}))
   "
   ```

### Step 2-MCP: Evaluate Candidate (MCP Server Mode)

When `ARTIFACT_TYPE=mcp-server`, use XML QA evaluation instead of skill evals:

1. Parse the evaluation file:
   ```bash
   python3 -c "
   import sys, json; sys.path.insert(0, '${SCRIPTS_DIR}')
   from xml_eval_parser import parse_evaluation_xml
   qa_pairs = parse_evaluation_xml('${WORKSPACE}/candidate/evals/evaluation.xml')
   print(json.dumps(qa_pairs, indent=2))
   "
   ```

2. For each QA pair, create the run directory and spawn a subagent that uses the MCP tools:
   ```bash
   mkdir -p ${WORKSPACE}/iteration-{i}/eval-{qa_id}/outputs/
   ```

   Spawn a subagent:
   ```
   You are evaluating an MCP server. Use the available MCP tools to answer this question.

   Question: {qa_pair.question}

   Think step by step. Use the MCP tools available to you.
   When you have your final answer, write ONLY the answer (nothing else) to:
   ${WORKSPACE}/iteration-{i}/eval-{qa_id}/outputs/answer.txt

   Also save a transcript of your work to:
   ${WORKSPACE}/iteration-{i}/eval-{qa_id}/transcript.md
   ```

3. After all QA pairs are evaluated, convert results to grading.json:
   ```bash
   python3 -c "
   import sys, json; sys.path.insert(0, '${SCRIPTS_DIR}')
   from xml_eval_parser import parse_evaluation_xml, write_per_question_grading
   from pathlib import Path

   qa_pairs = parse_evaluation_xml('${WORKSPACE}/candidate/evals/evaluation.xml')
   results = []
   for qa in qa_pairs:
       answer_file = Path('${WORKSPACE}/iteration-${i}/eval-' + qa['id'] + '/outputs/answer.txt')
       actual = answer_file.read_text().strip() if answer_file.exists() else ''
       results.append({
           'id': qa['id'], 'question': qa['question'],
           'expected': qa['expected_answer'], 'actual': actual
       })

   write_per_question_grading(results, Path('${WORKSPACE}/iteration-${i}'))
   from xml_eval_parser import qa_results_to_grading
   summary = qa_results_to_grading(results)['summary']
   print(f'MCP Eval: {summary[\"passed\"]}/{summary[\"total\"]} QA pairs correct')
   "
   ```

4. Compute score using the SAME `score.py` (unchanged):
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from score import compute_score; from pathlib import Path
   print(compute_score(Path('${WORKSPACE}'), ${iteration}))
   "
   ```

**Note**: After the improver modifies MCP server source code, wait for the dev server to reload before evaluating:
```bash
sleep ${RELOAD_DELAY_SECONDS:-3}
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

**3d½. Update Dashboard** — Regenerate the HTML dashboard after each iteration so it can be viewed mid-loop:
```bash
python3 -c "
import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
from dashboard import generate_dashboard; from pathlib import Path
html = generate_dashboard(Path('${WORKSPACE}'))
Path('${WORKSPACE}/dashboard.html').write_text(html)
print('Dashboard updated: ${WORKSPACE}/dashboard.html')
"
```

**3e. Check Abort Conditions**:
- `best_score >= 1.0` → Stop (perfect)
- Last 3 actions all "reverted" → Stop (stuck)

### Step 4: Finalize

1. Generate final dashboard and copy to a persistent location (before workspace cleanup):
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from dashboard import generate_dashboard; from pathlib import Path
   html = generate_dashboard(Path('${WORKSPACE}'))
   Path('${WORKSPACE}/dashboard.html').write_text(html)
   # Copy to sibling of skill so it survives workspace cleanup
   out = Path('${skill_path}').parent / '$(basename ${skill_path})-dashboard.html'
   out.write_text(html)
   print(f'Dashboard saved: {out}')
   "
   ```

2. Spawn convergence reporter (read `agents/convergence-reporter.md`):
   ```
   You are a convergence reporter. Read and follow:
   ${PLUGIN_ROOT}/skills/autoresearch/agents/convergence-reporter.md

   Inputs:
   - workspace: ${WORKSPACE}
   - v0_path: ${WORKSPACE}/v0/
   - best_path: ${WORKSPACE}/v{best_version}/
   - dashboard_path: ${skill_path}/../$(basename ${skill_path})-dashboard.html
   ```

3. Show the report and diff to the user
4. Ask: "Apply the best version (v{N}, score {S}) to the original skill? [y/n]"
5. If confirmed:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
   from snapshot import restore; from pathlib import Path
   restore(Path('${WORKSPACE}/v${best_version}'), Path('${skill_path}'))
   "
   ```

6. **Open and clean up dashboard** — the persistent dashboard copy is a viewing artifact, not a repo resource. Open it for the user, then offer to remove it:
   ```bash
   DASHBOARD_FILE="${skill_path}/../$(basename ${skill_path})-dashboard.html"
   if [ -f "${DASHBOARD_FILE}" ]; then
     open "${DASHBOARD_FILE}"
   fi
   ```
   Ask: "Remove `$(basename ${skill_path})-dashboard.html`? [y/n]"
   If confirmed:
   ```bash
   rm -f "${DASHBOARD_FILE}"
   ```
   The dashboard file must never be committed — it is gitignored via `*-dashboard.html` as a safety net.

7. **Clean up workspace** — always remove the workspace after finalization, regardless of whether changes were applied:
   ```bash
   rm -rf "${WORKSPACE}"
   ```
   The workspace is a transient working directory. It must never persist after the loop completes — results are captured in the convergence report and applied changes live in the skill directory.

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

**If `ARTIFACT_TYPE=skill`** (default):
1. Validate `evals/evals.json` has valid JSON with required fields
2. Verify each eval case has at least one `deterministic_check` entry — deterministic checks are the primary value-add of the eval-doctor. Aim for at least 50% deterministic coverage (deterministic checks / total assertions). String-presence checks (`file_contains`, `file_not_contains`) should be used wherever an expectation uses "must contain" / "must NOT contain" language, reserving LLM expectations only for semantic or structural judgments.
3. Report how many eval cases were created/modified and the deterministic check ratio

**If `ARTIFACT_TYPE=mcp-server`**:
1. Validate `evals/evaluation.xml` has valid XML with `<evaluation>/<qa_pair>` elements
2. Verify each `<qa_pair>` has `<question>` and `<answer>` children
3. Report QA pair count (aim for 8-15 pairs for a typical MCP server)

4. **MANDATORY — suggest running the full loop.** You MUST end your response with this exact suggestion (substituting the actual path): "Evals ready. Run `/autoresearch ${skill_path}` to start the improvement loop." This line must appear as the final output so the user knows the next step. Do not omit it.

---

## Mode 3: Report

Read `results.tsv` to determine the best version number before spawning.

The report MUST display every iteration present in `results.tsv` — show the complete score trajectory table with all rows. For each iteration, show the score, best score, action (kept/reverted/baseline), and changelog summary. If a version was reverted, explicitly state it was reverted and why. If a version was kept, state the score improvement (e.g., "score improved from X to Y").

Generate the HTML dashboard first:
```bash
python3 -c "
import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
from dashboard import generate_dashboard; from pathlib import Path
html = generate_dashboard(Path('${workspace_path}'))
out = Path('${workspace_path}/dashboard.html')
out.write_text(html)
print(f'Dashboard: {out}')
"
```

Spawn the convergence reporter (read `agents/convergence-reporter.md`):

```
You are a convergence reporter. Read and follow:
${PLUGIN_ROOT}/skills/autoresearch/agents/convergence-reporter.md

Inputs:
- workspace: ${workspace_path}
- v0_path: ${workspace_path}/v0/
- best_path: ${workspace_path}/v{best_version}/
- dashboard_path: ${workspace_path}/dashboard.html
```

---

## Safety Rails

- **Never modify the original skill** during the loop — work only on `candidate/`
- **Snapshots are immutable** — never write to `v{N}/` after creation
- **Evals frozen during improvement** — the improver must not touch `evals/`
- **User confirmation required** before applying changes to the original
- **Abort on stuck** — 3 consecutive reverts stops the loop
- **Workspace cleanup mandatory** — `rm -rf ${WORKSPACE}` after finalization; workspaces are transient and must never persist

## References

- `references/algorithm.md` — Complete loop algorithm specification
- `references/eval-quality-rubric.md` — What makes good evals
- `agents/improver.md` — How the improver modifies skills
- `agents/eval-doctor.md` — How the eval-doctor creates/fixes evals
- `agents/convergence-reporter.md` — How convergence reports are generated
- `references/mcp-eval-guide.md` — MCP server evaluation format and QA pair authoring guide
