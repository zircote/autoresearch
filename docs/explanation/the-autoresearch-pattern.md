---
diataxis_type: explanation
title: "The Autoresearch Pattern"
description: "Origin and architecture of the autoresearch pattern inspired by Andrej Karpathy"
---

# The Autoresearch Pattern

## Origin: Karpathy's Experiment

In January 2025, [Andrej Karpathy](https://karpathy.ai/) — former Director of AI at Tesla, co-founder of OpenAI, and one of the most influential figures in modern deep learning — published an experiment he called **autoresearch**: an autonomous research loop where an LLM agent iteratively improves its own code.

The original repository: **[github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch)**

In [a post describing the experiment](https://x.com/karpathy/status/1886192184808149383), Karpathy described the core idea: let an AI agent run experiments while humans sleep. Set up a reliable evaluation metric, give the agent permission to modify an artifact, and walk away. Come back in the morning to a better result — or at least a detailed log of everything that was tried.

The key insight: **autonomous agents can run experiments while humans sleep, as long as there's a reliable signal to guide improvement.**

## How the Original Worked

Karpathy's autoresearch used three files, each serving a distinct role:

- **`prepare.py`** — Set up the evaluation infrastructure: download datasets, create benchmarks, establish the testing pipeline. Run once by the human, then left untouched.
- **`train.py`** — The artifact being improved. In Karpathy's case, a training script for language models. This is the only file the AI agent was allowed to modify.
- **`program.md`** — Instructions for the AI agent: how to modify `train.py`, how to run training, how to evaluate results, and when to keep vs. discard changes. The "meta-program" that drives the loop.

The AI agent would:
1. Read `program.md` to understand its task
2. Modify `train.py` with a hypothesized improvement
3. Run training and evaluate against the validation metric
4. Compare the result to the previous best
5. Keep the change if it improved, discard if it didn't
6. Repeat

## The val_bpb Metric

In Karpathy's original experiment, the evaluation metric was **`val_bpb`** — validation bits-per-byte. This measures how well a language model predicts held-out text. Lower is better: a model scoring 1.0 val_bpb uses 1 bit per byte to encode text it hasn't seen, meaning it's fairly good at prediction.

Karpathy chose val_bpb because it's:

- **Deterministic** given the same data and model — run it twice, get the same number
- **Sensitive to real improvements** — genuine architectural or training improvements move the needle, while noise doesn't
- **Fast to compute** relative to full training — you can evaluate a checkpoint without completing the entire training run

In autoresearch for skills, the analogous metric is **`pass_rate`** — the fraction of eval expectations that pass. Like val_bpb, it's objective, fast to compute, and sensitive to genuine improvements. The direction is inverted (higher is better for pass_rate, lower for val_bpb), but the role is identical: a single number that answers "did the artifact get better?"

## The Philosophy

Karpathy's core insight was that autonomous improvement works when three conditions are met:

### 1. Fixed Evaluation

The metric doesn't change while the artifact is being improved. If you move the goalposts during the game, you can't tell whether you're getting better or the game is getting easier. In Karpathy's original, `prepare.py` was run once and never touched again. In autoresearch for skills, evals are frozen during the improvement loop.

### 2. Keep/Discard Discipline

Never accept a regression. Always compare against the best-so-far, not just the previous version. This creates a monotonically non-decreasing quality trajectory — bad experiments are free because they're always reverted.

### 3. Human-in-the-Loop at Boundaries

The agent runs autonomously *within* a loop iteration, but humans set the goals, review results, and decide when to apply changes to the real artifact. The agent has freedom to experiment; the human retains control over what ships.

## The Three-Role Architecture

Karpathy's pattern separates the system into three distinct roles:

### Immutable Infrastructure (prepare.py → eval infra)

The evaluation pipeline is fixed. It doesn't change during the experiment. This gives you a stable measuring stick — if the metric improves, the artifact genuinely got better.

In autoresearch for skills, this is:
- `evals/evals.json` — the eval cases and expectations
- The grader agent from skill-creator
- The scoring scripts (`score.py`, `results_log.py`)
- The snapshot/restore infrastructure

### Mutable Artifact (train.py → SKILL.md)

The thing being improved. The agent modifies this freely, guided by eval feedback.

In autoresearch:
- `SKILL.md` — the skill's instructions
- `scripts/` — the skill's helper scripts
- `references/` — the skill's reference material

### Human-Edited Instructions (program.md → SKILL.md orchestrator)

The meta-instructions that tell the agent how to improve. The human writes these once; the agent follows them on every iteration.

In autoresearch:
- The autoresearch SKILL.md orchestrator
- The improver agent spec (`agents/improver.md`)

## Mapping to Skills

| Karpathy's autoresearch | Autoresearch for skills |
|---|---|
| `prepare.py` (eval setup) | Eval infrastructure: evals.json, grader, scoring scripts |
| `train.py` (artifact) | Candidate skill: SKILL.md, scripts, references |
| `program.md` (meta-instructions) | Autoresearch orchestrator and improver agent spec |
| `val_bpb` (metric) | Mean `pass_rate` from grading.json |
| Training run | `claude -p` execution of eval prompts |
| Checkpoint save | Snapshot to `v{N}/` directory |
| Experiment log | `results.tsv` |

## What's Different: Skills vs. ML Training

Skill improvement differs from ML training in several important ways:

**Skills are written in natural language, not code.** Improvements are more qualitative — better phrasing, clearer instructions, more precise constraints. There's no loss function to differentiate through; the improver agent reasons about *why* something failed and *what words* might fix it.

**Evaluation requires an LLM grader, introducing non-determinism.** Where val_bpb is perfectly reproducible, pass_rate depends on an LLM grading the outputs. The same skill run twice might produce slightly different results. Autoresearch handles this by using composite scores across multiple eval cases, which smooths out per-case variance.

**The "training" is prompt execution, not gradient descent.** There are no weights being updated. Each eval runs the skill from scratch. This means there's no concept of "overfitting to the training set" in the traditional ML sense — but there is a risk of overfitting to specific eval case phrasings.

**Improvements compound differently.** A better SKILL.md changes behavior immediately — no retraining, no deployment, no model serving. The artifact *is* the instructions. This makes the feedback loop much tighter than in ML research.

**The improvement agent reasons in natural language.** Instead of backpropagation computing gradients, the improver agent reads failure evidence, hypothesizes about root causes, and decides what to change. It's more like a code reviewer than an optimizer.

## Why Fixed Evaluation Matters

If you change the test while changing the code, you can't tell whether the code got better or the test got easier. This is the "moving goalposts" problem.

Autoresearch enforces this by freezing evals during the improvement loop. The improver agent is explicitly prohibited from touching the `evals/` directory. If evals need work, that happens in a separate phase (eval-doctor mode).

See [Eval-Skill Separation](eval-skill-separation.md) for more on this principle.

## Why Keep/Discard Beats Always-Forward

A naive approach would always keep changes: improve, evaluate, improve, evaluate. But this creates a ratchet problem — one bad change poisons all subsequent iterations.

Autoresearch uses a keep/discard gate:
- If the score improved → keep the changes (snapshot)
- If the score didn't improve → discard the changes (restore from best snapshot)

This means the candidate never degrades below the best-known version. Bad experiments are free — they cost compute time but can't damage the artifact.

## What Makes This Work for Skills

Skills are particularly well-suited to this pattern because:

1. **Skills are text** — SKILL.md is a markdown file that an LLM can read, understand, and modify
2. **Evals are executable** — each eval case runs the skill and produces observable output
3. **Grading is automated** — the grader agent evaluates expectations against outputs
4. **Changes are reversible** — snapshots make it safe to try anything
5. **The feedback loop is tight** — modify SKILL.md, run evals, see score change in minutes

## Why This Matters for 190+ Repos

For a solo maintainer managing ~190 repositories, the autoresearch pattern means skill quality improvement can happen autonomously. Instead of manually reviewing each skill's performance and tweaking instructions, autoresearch runs the loop overnight and presents results in the morning.

This is the same "agents working while humans sleep" philosophy Karpathy demonstrated, applied to the specific problem of maintaining Claude Code skills at scale. One human, 190 repos, dozens of skills — the math only works if improvement is automated.

## Limitations

- The improver can only improve things the evals measure. Unmeasured quality dimensions won't improve.
- Non-determinism in LLM execution means scores can vary slightly between identical runs.
- The improver works within the skill's existing architecture. Fundamental redesigns need human input.
- Eval quality is the ceiling. Bad evals produce bad improvements.

## Further Reading

- [Lifecycle](lifecycle.md) — Full phase-by-phase walkthrough
- [Convergence and Scoring](convergence-and-scoring.md) — How the score works
- [Eval-Skill Separation](eval-skill-separation.md) — Why they improve separately
- [Component Architecture](architecture.md) — How orchestrator, agents, and scripts interact
