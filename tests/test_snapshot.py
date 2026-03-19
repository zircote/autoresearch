"""Tests for snapshot.py — SHA-safe directory copying and restoration."""

import sys
import time
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "autoresearch")
)

from scripts.snapshot import snapshot, restore


def test_sha_skip_preserves_mtime(tmp_path):
    """Writing identical content doesn't change mtime."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "a.txt").write_text("hello")

    snapshot(src, dst)
    mtime1 = (dst / "a.txt").stat().st_mtime

    # Small sleep to ensure mtime would differ if file were rewritten
    time.sleep(0.05)
    snapshot(src, dst)
    mtime2 = (dst / "a.txt").stat().st_mtime

    assert mtime1 == mtime2, "File with same SHA should not be rewritten"


def test_idempotent(tmp_path):
    """snapshot(a,b) twice produces the same result."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "f.txt").write_text("data")
    (src / "g.txt").write_text("more")

    snapshot(src, dst)
    contents1 = {p.name: p.read_text() for p in dst.iterdir()}

    snapshot(src, dst)
    contents2 = {p.name: p.read_text() for p in dst.iterdir()}

    assert contents1 == contents2


def test_roundtrip_restore(tmp_path):
    """snapshot → modify candidate → restore preserves original."""
    src = tmp_path / "src"
    snap = tmp_path / "snap"
    candidate = tmp_path / "candidate"
    src.mkdir()
    (src / "a.txt").write_text("original")

    snapshot(src, snap)

    # Create a candidate and modify it
    snapshot(src, candidate)
    (candidate / "a.txt").write_text("modified")

    restore(snap, candidate)
    assert (candidate / "a.txt").read_text() == "original"


def test_nested_directories(tmp_path):
    """Handles nested directory structures."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "sub" / "deep").mkdir(parents=True)
    (src / "sub" / "deep" / "file.txt").write_text("nested")
    (src / "top.txt").write_text("top")

    snapshot(src, dst)

    assert (dst / "sub" / "deep" / "file.txt").read_text() == "nested"
    assert (dst / "top.txt").read_text() == "top"


def test_restore_removes_extra_files(tmp_path):
    """restore() removes files in candidate not in snapshot."""
    snap = tmp_path / "snap"
    candidate = tmp_path / "candidate"
    snap.mkdir()
    candidate.mkdir()

    (snap / "keep.txt").write_text("keep")
    (candidate / "keep.txt").write_text("keep")
    (candidate / "extra.txt").write_text("should be removed")

    restore(snap, candidate)

    assert (candidate / "keep.txt").exists()
    assert not (candidate / "extra.txt").exists()
