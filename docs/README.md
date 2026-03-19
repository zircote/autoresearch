# Documentation

Autoresearch documentation follows the [Diataxis](https://diataxis.fr/) framework — four quadrants organized by user need.

```
                 LEARNING                          WORKING
            ┌───────────────────────┐          ┌──────────────────────┐
            │                       │          │                      │
  PRACTICAL │    Tutorials          │          │   How-To Guides      │ 
            │  learning-oriented    │          │  task-oriented       │
            │                       │          │                      │
            └───────────────────────┘          └──────────────────────┘
            ┌────────────────────────┐         ┌──────────────────────┐
            │                        │         │                      │
THEORETICAL │   Explanation          │         │    Reference         │
            │ understanding-oriented │         │ information-oriented │
            │                        │         │                      │
            └────────────────────────┘         └──────────────────────┘
```

## Tutorials — Learn by doing

Step-by-step lessons that take you through a complete experience.

| Document | Description |
|----------|-------------|
| [Getting Started](tutorials/getting-started.md) | Your first autoresearch loop — install, run, review, approve |
| [Creating Evals from Scratch](tutorials/creating-evals-from-scratch.md) | Build evals for a skill that has none using `--eval-doctor` |
| [Improving an Existing Skill](tutorials/improving-an-existing-skill.md) | Take a working skill from 65% to 90%+ |

## How-To Guides — Solve specific problems

Practical steps for accomplishing a particular goal.

| Document | Description |
|----------|-------------|
| [Run the Improvement Loop](how-to/run-improvement-loop.md) | Execute the core loop with all available options |
| [Manage Evals](how-to/manage-evals.md) | Create, fix, and update evaluation cases |
| [Interpret Results](how-to/interpret-results.md) | Read results.tsv, convergence reports, and diffs |
| [Customize Iterations](how-to/customize-iterations.md) | Change max iterations and understand abort thresholds |
| [Apply Changes](how-to/apply-changes.md) | Review and apply the best version to your original skill |
| [Recover from Failure](how-to/recover-from-failure.md) | Resume after interruption, inspect snapshots, manually revert |
| [Integrate with Skill Creator](how-to/integrate-with-skill-creator.md) | Post-loop description optimization with skill-creator |

## Reference — Look up details

Precise, complete descriptions of the machinery.

| Document | Description |
|----------|-------------|
| [CLI Reference](reference/cli.md) | Complete `/autoresearch` command reference with all flags and modes |
| [Algorithm](reference/algorithm.md) | Formal specification of the improvement loop |
| [File Formats](reference/file-formats.md) | results.tsv schema, workspace layout, snapshot format |
| [Eval Schema](reference/eval-schema.md) | evals.json and trigger-eval.json schemas |
| [Agents](reference/agents.md) | Agent specs: improver, eval-doctor, convergence-reporter, grader |
| [Scripts](reference/scripts.md) | Script API: snapshot.py, score.py, results_log.py, diff_report.py |

## Explanation — Understand the design

Discussion and context that illuminate concepts.

| Document | Description |
|----------|-------------|
| [The Autoresearch Pattern](explanation/the-autoresearch-pattern.md) | Karpathy's pattern, its philosophy, and how it maps to skills |
| [Eval-Skill Separation](explanation/eval-skill-separation.md) | Why evals and skills are improved separately |
| [Convergence and Scoring](explanation/convergence-and-scoring.md) | How scoring works, what convergence means, non-determinism |
| [Lifecycle](explanation/lifecycle.md) | Full lifecycle from eval readiness through the meta-loop |
| [Component Architecture](explanation/architecture.md) | How orchestrator, agents, and scripts interact |
| [Expected Results](explanation/expected-results.md) | Typical score trajectories, "good enough", common failures |
