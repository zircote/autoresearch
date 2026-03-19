"""Unified diff between two skill directories.

Compares all text files (.md, .py, .json, .txt, .yaml, .yml) recursively
and produces a unified diff report.

Inputs:
    dir_a: Path to first skill directory (typically v0/baseline)
    dir_b: Path to second skill directory (typically best version)

Outputs:
    String containing unified diff of all changed files
"""

import difflib
from pathlib import Path

TEXT_EXTENSIONS = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml"}


def diff_report(dir_a: Path, dir_b: Path) -> str:
    """Generate unified diff between two skill directories.

    Compares text files recursively. Shows added, removed, and modified files.
    """
    dir_a = Path(dir_a)
    dir_b = Path(dir_b)

    files_a = {f.relative_to(dir_a) for f in dir_a.rglob("*")
               if not f.is_dir() and f.suffix in TEXT_EXTENSIONS}
    files_b = {f.relative_to(dir_b) for f in dir_b.rglob("*")
               if not f.is_dir() and f.suffix in TEXT_EXTENSIONS}

    all_files = sorted(files_a | files_b)
    diffs = []

    for rel_path in all_files:
        file_a = dir_a / rel_path
        file_b = dir_b / rel_path

        lines_a = file_a.read_text().splitlines(keepends=True) if file_a.exists() else []
        lines_b = file_b.read_text().splitlines(keepends=True) if file_b.exists() else []

        if lines_a == lines_b:
            continue

        diff = difflib.unified_diff(
            lines_a, lines_b,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
        diff_text = "".join(diff)
        if diff_text:
            diffs.append(diff_text)

    return "\n".join(diffs) if diffs else "No differences found."
