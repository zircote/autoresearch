"""Composite score computation from grading.json files.

Reads grading.json files from a workspace iteration directory and computes
the mean pass_rate across all eval cases.

Inputs:
    workspace: Path to the autoresearch workspace
    iteration: Iteration number (0 for baseline, 1+ for improvements)

Outputs:
    Float between 0.0 and 1.0 representing mean pass_rate
"""

import json
from pathlib import Path


def compute_score(workspace: Path, iteration: int) -> float:
    """Compute mean pass_rate from grading.json files in an iteration directory.

    Searches for grading.json files in workspace/iteration-{N}/ directories.
    Each grading.json has a summary.pass_rate field (0.0 to 1.0).
    Returns the mean across all found grading files, or 0.0 if none found.
    """
    workspace = Path(workspace)
    iter_dir = workspace / f"iteration-{iteration}"

    if not iter_dir.exists():
        return 0.0

    pass_rates = []
    for grading_file in iter_dir.rglob("grading.json"):
        try:
            data = json.loads(grading_file.read_text())
            rate = data.get("summary", {}).get("pass_rate")
            if rate is not None:
                pass_rates.append(float(rate))
        except (json.JSONDecodeError, ValueError, OSError):
            continue

    if not pass_rates:
        return 0.0

    return sum(pass_rates) / len(pass_rates)
