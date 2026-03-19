"""Append-only TSV results log for the autoresearch improvement loop.

Tracks iteration results in a tab-separated file with columns:
iteration, timestamp, score, best_score, action, changelog

Inputs:
    tsv_path: Path to the results.tsv file
    row: Dict with keys matching the TSV columns

Outputs:
    append() writes a row to the file (creates with headers if missing)
    read() returns all rows as a list of dicts
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = ["iteration", "timestamp", "score", "best_score", "action", "changelog"]


def append(tsv_path: Path, row: dict) -> None:
    """Append a row to the results TSV file.

    Creates the file with headers if it doesn't exist.
    Adds a timestamp if not provided in the row.
    """
    tsv_path = Path(tsv_path)
    tsv_path.parent.mkdir(parents=True, exist_ok=True)

    if "timestamp" not in row:
        row["timestamp"] = datetime.now(timezone.utc).isoformat()

    write_header = not tsv_path.exists() or tsv_path.stat().st_size == 0

    with open(tsv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t",
                                extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def read(tsv_path: Path) -> list[dict]:
    """Read all rows from the results TSV file.

    Returns a list of dicts with string values. Returns empty list if
    the file doesn't exist.
    """
    tsv_path = Path(tsv_path)
    if not tsv_path.exists():
        return []

    with open(tsv_path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)
