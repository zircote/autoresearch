# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-19

### Added
- Initial release of the autoresearch plugin
- Three operating modes: full improvement loop, eval doctor, convergence report
- SKILL.md orchestrator with argument hinting and mode detection
- Improver agent for modifying candidate skills based on eval failures
- Eval doctor agent for creating, fixing, and improving evaluation cases
- Convergence reporter agent for summarizing loop results
- Four utility scripts: snapshot.py (SHA-256 safe copy), score.py (composite scoring), results_log.py (TSV logging), diff_report.py (unified diff)
- Integration with skill-creator plugin (grader, schemas, run_eval, run_loop)
- Safety rails: immutable snapshots, candidate-only modification, user confirmation, regression abort
- Complete Diataxis documentation suite: 3 tutorials, 7 how-to guides, 6 reference docs, 5 explanation docs
- 18 unit tests covering all scripts (snapshot, score, results_log)
- Test fixtures: sample skill, sample grading data, sample workspace
