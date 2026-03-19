---
diataxis_type: reference
title: "Scripts Reference"
description: "API reference for Python utility scripts including snapshot, scoring, and results logging"
---

# Scripts Reference

All scripts are in `skills/autoresearch/scripts/`. They are pure Python with no external dependencies beyond the standard library.

## snapshot.py

SHA-256-safe copying of skill directories.

### `snapshot(src: Path, dst: Path) -> None`

Copy `src` directory to `dst`, skipping files with matching SHA-256 hashes.

**Parameters:**
- `src` — Source skill directory
- `dst` — Destination snapshot directory (created if missing)

**Behavior:**
- Recursively copies all files from `src` to `dst`
- Creates parent directories as needed
- Skips files where source and destination have identical SHA-256 hashes
- Uses `shutil.copy2` to preserve metadata

### `restore(snapshot_dir: Path, candidate_dir: Path) -> None`

Restore `candidate_dir` to match `snapshot_dir` exactly.

**Parameters:**
- `snapshot_dir` — Source snapshot to restore from
- `candidate_dir` — Target directory to restore (typically `candidate/`)

**Behavior:**
- Removes files in `candidate_dir` that don't exist in `snapshot_dir`
- Cleans up empty directories after removal
- Copies all files from `snapshot_dir` using `snapshot()` (SHA-256 dedup)

### Internal: `_sha256(path: Path) -> str`

Compute SHA-256 hex digest of a file. Reads in 8KB chunks.

---

## score.py

Composite score computation from grading results.

### `compute_score(workspace: Path, iteration: int) -> float`

Compute mean pass_rate from grading.json files in an iteration directory.

**Parameters:**
- `workspace` — Path to the autoresearch workspace root
- `iteration` — Iteration number (0 for baseline, 1+ for improvements)

**Returns:** Float between 0.0 and 1.0 representing mean pass_rate. Returns 0.0 if no grading files found.

**Behavior:**
- Searches `workspace/iteration-{N}/` for all `grading.json` files (recursive)
- Extracts `summary.pass_rate` from each
- Returns the arithmetic mean
- Silently skips malformed or unreadable files

---

## results_log.py

Append-only TSV results log.

### Constants

```python
COLUMNS = ["iteration", "timestamp", "score", "best_score", "action", "changelog"]
```

### `append(tsv_path: Path, row: dict) -> None`

Append a row to the results TSV file.

**Parameters:**
- `tsv_path` — Path to the results.tsv file
- `row` — Dict with keys matching `COLUMNS`. Missing `timestamp` is auto-filled with UTC ISO-8601.

**Behavior:**
- Creates the file with headers if it doesn't exist or is empty
- Appends the row as a tab-separated line
- Extra keys in `row` are ignored

### `read(tsv_path: Path) -> list[dict]`

Read all rows from the results TSV file.

**Parameters:**
- `tsv_path` — Path to the results.tsv file

**Returns:** List of dicts with string values. Empty list if the file doesn't exist.

---

## diff_report.py

Unified diff between two skill directories.

### Constants

```python
TEXT_EXTENSIONS = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml"}
```

### `diff_report(dir_a: Path, dir_b: Path) -> str`

Generate unified diff between two skill directories.

**Parameters:**
- `dir_a` — First directory (typically `v0/` baseline)
- `dir_b` — Second directory (typically best version)

**Returns:** String containing unified diff of all changed text files. Returns `"No differences found."` if directories are identical.

**Behavior:**
- Recursively finds all files with text extensions in both directories
- Compares each file using `difflib.unified_diff`
- Reports added files (in `dir_b` but not `dir_a`), removed files, and modifications
- Only processes files with extensions in `TEXT_EXTENSIONS`
- Binary files and other extensions are ignored

---

## Usage from the Orchestrator

Scripts are invoked via inline Python from SKILL.md:

```bash
python3 -c "
import sys; sys.path.insert(0, '${SCRIPTS_DIR}')
from snapshot import snapshot; from pathlib import Path
snapshot(Path('src'), Path('dst'))
"
```

Where `SCRIPTS_DIR` is `${CLAUDE_PLUGIN_ROOT}/skills/autoresearch/scripts`.
