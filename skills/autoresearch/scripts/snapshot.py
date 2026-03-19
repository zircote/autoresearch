"""Snapshot management for skill directories.

Provides SHA-256-safe copying of skill directories for the autoresearch
improvement loop. snapshot() creates an immutable copy, restore() reverts
a candidate directory to a prior snapshot. Both are idempotent — files
with matching SHA-256 hashes are not rewritten.

Inputs:
    src: Path to source skill directory
    dst: Path to destination snapshot directory

Outputs:
    snapshot() copies all files from src to dst, skipping unchanged files
    restore() copies all files from snapshot to candidate, removing extras
"""

import hashlib
import shutil
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(src: Path, dst: Path) -> None:
    """Copy src directory to dst, skipping files with matching SHA-256."""
    src = Path(src)
    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for src_file in src.rglob("*"):
        if src_file.is_dir():
            continue
        rel = src_file.relative_to(src)
        dst_file = dst / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if dst_file.exists() and _sha256(src_file) == _sha256(dst_file):
            continue
        shutil.copy2(src_file, dst_file)


def restore(snapshot_dir: Path, candidate_dir: Path) -> None:
    """Restore candidate_dir to match snapshot_dir exactly.

    Copies files from snapshot, removes files in candidate not in snapshot.
    """
    snapshot_dir = Path(snapshot_dir)
    candidate_dir = Path(candidate_dir)

    # Remove files in candidate not in snapshot
    if candidate_dir.exists():
        snapshot_files = {f.relative_to(snapshot_dir) for f in snapshot_dir.rglob("*") if not f.is_dir()}
        for cand_file in list(candidate_dir.rglob("*")):
            if cand_file.is_dir():
                continue
            rel = cand_file.relative_to(candidate_dir)
            if rel not in snapshot_files:
                cand_file.unlink()
        # Clean empty dirs
        for d in sorted(candidate_dir.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()

    snapshot(snapshot_dir, candidate_dir)
