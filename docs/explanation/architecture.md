---
diataxis_type: explanation
title: "Component Architecture"
description: "How the autoresearch orchestrator, agents, and scripts interact to form the improvement loop"
---

# Component Architecture

Autoresearch is a coordination system: a central orchestrator dispatches work to specialized agents and utility scripts, all operating on a shared workspace. This document explains how the pieces fit together and why they're separated the way they are.

## Overview

The SKILL.md orchestrator is the control plane. It doesn't do the actual improvement work — it sequences the steps, makes keep/discard decisions, and spawns agents when domain expertise is needed. The agents are the workers. The scripts are the plumbing.

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         SKILL.md Orchestrator                        │
│                    (control flow, keep/discard gate)                  │
└──────┬───────────┬───────────────┬──────────────────┬────────────────┘
       │           │               │                  │
       │ spawns    │ spawns        │ spawns           │ calls
       ▼           ▼               ▼                  ▼
┌────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌────────────────┐
│  Improver  │ │ Eval Doctor  │ │   Convergence    │ │   Utility      │
│   Agent    │ │    Agent     │ │    Reporter      │ │   Scripts      │
│            │ │              │ │    Agent         │ │                │
│ Modifies   │ │ Creates/     │ │ Reads results,   │ │ snapshot.py    │
│ candidate  │ │ fixes evals  │ │ generates report │ │ score.py       │
│ skill      │ │              │ │                  │ │ results_log.py │
│            │ │              │ │                  │ │ diff_report.py │
└──────┬─────┘ └──────┬───────┘ └────────┬─────────┘ └───────┬────────┘
       │               │                  │                    │
       │               │                  │                    │
       ▼               ▼                  ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          Workspace (shared state)                     │
│                                                                      │
│  candidate/        v0/ v1/ v2/...       results.tsv                  │
│  (mutable skill)   (immutable snapshots) (append-only log)           │
│                                                                      │
│  grading.json files   evals/evals.json                               │
│  (eval outputs)       (frozen during improvement)                    │
└──────────────────────────────────────────────────────────────────────┘
       ▲
       │ provides grader
┌──────┴─────────────────────┐
│  skill-creator plugin      │
│  (external dependency)     │
│                            │
│  grader agent              │
│  run_eval / run_loop       │
│  schemas                   │
└────────────────────────────┘
```

## Data Flow

Information flows through the system in a predictable sequence during each iteration of the improvement loop:

### 1. Workspace Setup

The orchestrator calls `snapshot.py` to create the workspace and baseline snapshot (`v0/`). This is a SHA-256 verified copy — the snapshot is immutable from this point forward.

### 2. Evaluation

The orchestrator invokes skill-creator's eval infrastructure to run the candidate skill against each eval case in `evals/evals.json`. Each eval produces a transcript and outputs. The **grader agent** (from skill-creator) then evaluates the outputs against expectations, producing `grading.json` files.

### 3. Scoring

`grading.json` files flow into `score.py`, which computes a composite score — the mean `pass_rate` across all eval cases. This single number is the improvement signal.

### 4. Improvement (or Diagnosis)

Depending on the mode:

- **Full loop**: The orchestrator spawns the **improver agent** with the grading results and score history. The improver reads the failures, plans changes, and modifies files in `candidate/`. It never touches `evals/`.
- **Eval doctor mode**: The orchestrator spawns the **eval doctor agent** to create or fix eval cases. It never touches the skill.

### 5. Logging

After each iteration, `results_log.py` appends a row to `results.tsv` — iteration number, score, best score, action taken (kept/reverted), and a summary. This log is append-only and never modified.

### 6. Convergence Reporting

After the loop completes (or is aborted), the orchestrator spawns the **convergence reporter agent**. It reads `results.tsv`, compares `v0/` against the best snapshot using `diff_report.py`, analyzes remaining failures, and produces a formatted report.

## Why Agents vs. Scripts

The division between agents and scripts follows a clear principle: **agents reason, scripts compute**.

**Scripts** handle deterministic operations:
- `snapshot.py` — file copying with integrity verification
- `score.py` — arithmetic on grading data
- `results_log.py` — structured logging
- `diff_report.py` — text differencing

These could be shell commands, but Python scripts are more portable, testable, and precise about edge cases (Unicode, symlinks, empty directories).

**Agents** handle tasks requiring judgment:
- The **improver** must analyze failure patterns, hypothesize root causes, and decide what to change — this is inherently a reasoning task
- The **eval doctor** must understand what a skill does and write eval cases that meaningfully test it
- The **convergence reporter** must interpret trends and make a recommendation

## Why Three Separate Agents

Each agent has a fundamentally different stance toward the workspace:

| Agent | Reads | Writes | Stance |
|---|---|---|---|
| Improver | grading.json, results.tsv, candidate/ | candidate/ only | "Fix the skill" |
| Eval Doctor | SKILL.md, existing evals | evals/ only | "Fix the tests" |
| Convergence Reporter | results.tsv, snapshots, grading.json | nothing (output only) | "Report the findings" |

Combining these into one agent would create conflicting incentives. An agent that can modify both evals and skills could "cheat" by weakening evals instead of strengthening the skill. Separation enforces the [eval-skill separation](eval-skill-separation.md) principle architecturally, not just by instruction.

## The Workspace as Shared State

The workspace directory is the coordination mechanism between all components. Rather than passing complex data structures between agents, everything is written to files in a known layout:

```
workspace/
├── candidate/          # Mutable skill copy (improver writes here)
├── v0/                 # Baseline snapshot (immutable)
├── v1/, v2/, ...       # Iteration snapshots (immutable)
├── results.tsv         # Score log (append-only)
├── evals/              # Eval cases (frozen during improvement loop)
└── eval-outputs/       # Grading results per iteration
    ├── iter-0/
    │   ├── case-1/grading.json
    │   └── case-2/grading.json
    └── iter-1/
        └── ...
```

This file-based coordination is intentional: it's inspectable, debuggable, and survives agent crashes. If a run is interrupted, the workspace contains everything needed to understand what happened and resume.

## External Dependency: skill-creator

Autoresearch does not include its own grading or eval execution infrastructure. It depends on the **skill-creator plugin** for:

- **Grader agent** — evaluates outputs against expectations, produces grading.json
- **Eval execution** — runs the skill against eval prompts, captures transcripts
- **Schemas** — defines the structure of evals.json, grading.json, and related formats

This is a deliberate dependency, not an oversight. The grader and eval runner are general-purpose tools that work across all skills. Autoresearch adds the improvement loop on top.

See the [grader cross-reference in agents.md](../reference/agents.md#external-grader-from-skill-creator) for discovery paths and expected interfaces.

## Further Reading

- [Agents Reference](../reference/agents.md) — Detailed specs for each agent
- [Scripts Reference](../reference/scripts.md) — API documentation for utility scripts
- [Lifecycle](lifecycle.md) — Full phase-by-phase walkthrough of the loop
- [Eval-Skill Separation](eval-skill-separation.md) — The principle behind agent separation
