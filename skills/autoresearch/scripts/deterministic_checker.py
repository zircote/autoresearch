"""Deterministic (programmatic, zero-variance) evaluation checks.

Complements the LLM-based grader by handling checks that can be verified
without LLM judgment. Each check type has a registered handler that returns
a (passed, evidence) tuple.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Sentinel for missing JSON paths (distinct from None / null)
# ---------------------------------------------------------------------------


class _MissingSentinel:
    """Sentinel value distinguishing 'path not found' from JSON null."""

    _instance: _MissingSentinel | None = None

    def __new__(cls) -> _MissingSentinel:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<MISSING>"

    def __bool__(self) -> bool:
        return False


MISSING = _MissingSentinel()

# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

HandlerFn = Callable[[dict, Path, dict], tuple[bool, str]]
_HANDLERS: dict[str, HandlerFn] = {}


def _handler(name: str) -> Callable[[HandlerFn], HandlerFn]:
    """Decorator that registers a check handler under *name*."""

    def decorator(fn: HandlerFn) -> HandlerFn:
        _HANDLERS[name] = fn
        return fn

    return decorator


# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------


def _resolve_path(data: Any, jq_path: str) -> Any:
    """Navigate *data* along a jq-style *jq_path*.

    Supports:
    - Leading-dot stripping: ``.server.type`` -> ``["server", "type"]``
    - Nested objects: ``.server.mcp_config.command``
    - Array indexing: ``.tools[0].name``

    Returns :data:`MISSING` when the path cannot be resolved.
    """
    path = jq_path.lstrip(".")
    if not path:
        return data

    # Tokenise into key / index segments.
    # "tools[0].name" -> ["tools", "[0]", "name"]
    tokens: list[str] = []
    for segment in path.split("."):
        if not segment:
            continue
        # Split array indices out: "tools[0]" -> "tools", "[0]"
        parts = re.split(r"(\[\d+\])", segment)
        for p in parts:
            if p:
                tokens.append(p)

    current: Any = data
    for token in tokens:
        idx_match = re.fullmatch(r"\[(\d+)\]", token)
        if idx_match is not None:
            index = int(idx_match.group(1))
            if not isinstance(current, list) or index >= len(current):
                return MISSING
            current = current[index]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            return MISSING

    return current


def _read_file(outputs_dir: Path, filename: str) -> tuple[str | None, str | None]:
    """Read a file from *outputs_dir*, returning ``(content, error)``."""
    filepath = outputs_dir / filename
    if not filepath.exists():
        return None, f"File not found: {filename}"
    try:
        return filepath.read_text(encoding="utf-8"), None
    except Exception as exc:
        return None, f"Read error: {exc}"


def _load_json(outputs_dir: Path, filename: str) -> tuple[Any, str | None]:
    """Load and parse a JSON file, returning ``(data, error)``."""
    content, err = _read_file(outputs_dir, filename)
    if err is not None:
        return None, err
    try:
        return json.loads(content), None  # type: ignore[arg-type]
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON: {exc}"


def _get_path(check: dict) -> str:
    """Get the jq-style path from a check, accepting both ``path`` and ``field``."""
    return check.get("path") or check.get("field", "")


# ---------------------------------------------------------------------------
# Check handlers
# ---------------------------------------------------------------------------


@_handler("json_valid")
def _check_json_valid(check: dict, outputs_dir: Path, env: dict) -> tuple[bool, str]:
    """Parse *file* as JSON; pass if valid."""
    _, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    return True, "Valid JSON"


@_handler("json_field_equals")
def _check_json_field_equals(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Navigate *path* in *file*; compare value with *expected* using ``==``."""
    data, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    p = _get_path(check)
    value = _resolve_path(data, p)
    if value is MISSING:
        return False, f"Path {p} not found"
    expected = check["expected"]
    if value == expected:
        return True, f"{p} == {json.dumps(expected)}"
    return (
        False,
        f"{p} is {json.dumps(value)}, expected {json.dumps(expected)}",
    )


@_handler("json_field_exists")
def _check_json_field_exists(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Pass if *path* resolves to a non-None value."""
    data, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    p = _get_path(check)
    value = _resolve_path(data, p)
    if value is MISSING or value is None:
        return False, f"Path {p} is missing or null"
    return True, f"Path {p} exists"


@_handler("json_field_absent")
def _check_json_field_absent(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Pass if *path* does NOT exist or is null."""
    data, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    p = _get_path(check)
    value = _resolve_path(data, p)
    if value is MISSING or value is None:
        return True, f"Path {p} is absent or null"
    return False, f"Path {p} exists with value {json.dumps(value)}"


@_handler("json_field_matches")
def _check_json_field_matches(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Resolve *path*, match *pattern* regex against ``str(value)``."""
    data, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    p = _get_path(check)
    value = _resolve_path(data, p)
    if value is MISSING:
        return False, f"Path {p} not found"
    text = str(value)
    if re.search(check["pattern"], text):
        return True, f"{p} matches /{check['pattern']}/"
    return False, f"{p} value {text!r} does not match /{check['pattern']}/"


@_handler("json_field_count")
def _check_json_field_count(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Resolve *path* to array, compare ``len()`` using *op* and *expected*."""
    data, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    p = _get_path(check)
    value = _resolve_path(data, p)
    if value is MISSING:
        return False, f"Path {p} not found"
    if not isinstance(value, list):
        return False, f"Path {p} is not an array"
    length = len(value)
    expected = int(check["expected"])
    op = check["op"]
    ops = {
        "eq": (length == expected, "=="),
        "gte": (length >= expected, ">="),
        "lte": (length <= expected, "<="),
    }
    if op not in ops:
        return False, f"Unknown operator: {op}"
    passed, symbol = ops[op]
    evidence = f"len({p}) = {length} {symbol} {expected}"
    return passed, evidence


@_handler("json_array_contains")
def _check_json_array_contains(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Resolve *path* to array; check if any element is a superset of *match*."""
    data, err = _load_json(outputs_dir, check["file"])
    if err:
        return False, err
    p = _get_path(check)
    value = _resolve_path(data, p)
    if value is MISSING:
        return False, f"Path {p} not found"
    if not isinstance(value, list):
        return False, f"Path {p} is not an array"
    match = check["match"]
    for element in value:
        if isinstance(element, dict) and all(
            element.get(k) == v for k, v in match.items()
        ):
            return True, f"Found matching element in {p}"
    return False, f"No element in {p} matches {json.dumps(match)}"


@_handler("file_exists")
def _check_file_exists(check: dict, outputs_dir: Path, env: dict) -> tuple[bool, str]:
    """Pass if *file* exists in outputs_dir."""
    filepath = outputs_dir / check["file"]
    if filepath.exists():
        return True, f"{check['file']} exists"
    return False, f"File not found: {check['file']}"


@_handler("file_not_exists")
def _check_file_not_exists(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Pass if *file* does NOT exist."""
    filepath = outputs_dir / check["file"]
    if not filepath.exists():
        return True, f"{check['file']} does not exist"
    return False, f"{check['file']} exists (expected absent)"


@_handler("file_contains")
def _check_file_contains(check: dict, outputs_dir: Path, env: dict) -> tuple[bool, str]:
    """Read *file*, check if *literal* string is present."""
    content, err = _read_file(outputs_dir, check["file"])
    if err:
        return False, err
    literal = check["literal"]
    if literal in content:  # type: ignore[operator]
        return True, f"{check['file']} contains {literal!r}"
    return False, f"{check['file']} does not contain {literal!r}"


@_handler("file_not_contains")
def _check_file_not_contains(
    check: dict, outputs_dir: Path, env: dict
) -> tuple[bool, str]:
    """Read *file*, check *literal* is NOT present."""
    content, err = _read_file(outputs_dir, check["file"])
    if err:
        return False, err
    literal = check["literal"]
    if literal not in content:  # type: ignore[operator]
        return True, f"{check['file']} does not contain {literal!r}"
    return False, f"{check['file']} contains {literal!r} (expected absent)"


@_handler("regex_match")
def _check_regex_match(check: dict, outputs_dir: Path, env: dict) -> tuple[bool, str]:
    """Read *file*, check regex *pattern* matches anywhere."""
    content, err = _read_file(outputs_dir, check["file"])
    if err:
        return False, err
    pattern = check["pattern"]
    if re.search(pattern, content):  # type: ignore[arg-type]
        return True, f"{check['file']} matches /{pattern}/"
    return False, f"{check['file']} does not match /{pattern}/"


@_handler("shell_command")
def _check_shell_command(check: dict, outputs_dir: Path, env: dict) -> tuple[bool, str]:
    """Run *command* via subprocess; pass if exit code 0."""
    run_env = os.environ.copy()
    run_env.update(env)
    result = subprocess.run(
        check["command"],
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(outputs_dir),
        env=run_env,
    )
    if result.returncode == 0:
        stdout_snip = result.stdout.strip()[:200] if result.stdout else ""
        return True, f"Exit 0{(': ' + stdout_snip) if stdout_snip else ''}"
    stderr_snip = result.stderr.strip()[:200] if result.stderr else ""
    return (
        False,
        f"Exit {result.returncode}{(': ' + stderr_snip) if stderr_snip else ''}",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_deterministic_checks(
    checks: list[dict],
    outputs_dir: Path,
    env: dict | None = None,
) -> dict:
    """Run deterministic checks against outputs.

    Args:
        checks: List of check descriptors, each containing at least a
            ``"type"`` key matching a registered handler name.
        outputs_dir: Directory containing the output files to check.
        env: Optional environment variables passed to shell_command checks.

    Returns:
        A grading-compatible dict::

            {
                "expectations": [
                    {"text": str, "passed": bool, "evidence": str, "source": "deterministic"}
                ],
                "summary": {"passed": int, "failed": int, "total": int, "pass_rate": float}
            }
    """
    if env is None:
        env = {}

    expectations: list[dict] = []

    for check in checks:
        check_type = check.get("type", "")
        handler = _HANDLERS.get(check_type)

        if handler is None:
            expectations.append(
                {
                    "text": check.get(
                        "description", check.get("text", f"[{check_type}]")
                    ),
                    "passed": False,
                    "evidence": f"Unknown check type: {check_type}",
                    "source": "deterministic",
                }
            )
            continue

        try:
            passed, evidence = handler(check, outputs_dir, env)
        except Exception as exc:
            passed, evidence = False, f"Check error: {exc}"

        expectations.append(
            {
                "text": check.get("description", check.get("text", f"[{check_type}]")),
                "passed": passed,
                "evidence": evidence,
                "source": "deterministic",
            }
        )

    passed_count = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    failed_count = total - passed_count

    return {
        "expectations": expectations,
        "summary": {
            "passed": passed_count,
            "failed": failed_count,
            "total": total,
            "pass_rate": (passed_count / total) if total > 0 else 0.0,
        },
    }


def merge_deterministic_into_grading(det_path: Path, grading_path: Path) -> None:
    """Merge deterministic results into an existing grading.json.

    - Tags existing LLM expectations with ``source: "llm"``
    - Prepends deterministic expectations
    - Recomputes ``summary.pass_rate`` over all expectations
    - Writes updated grading.json back

    Args:
        det_path: Path to the deterministic results JSON file.
        grading_path: Path to the existing grading.json file.
    """
    det_data = json.loads(det_path.read_text(encoding="utf-8"))
    grading_data = json.loads(grading_path.read_text(encoding="utf-8"))

    # Tag existing LLM expectations
    for exp in grading_data.get("expectations", []):
        if "source" not in exp:
            exp["source"] = "llm"

    # Prepend deterministic expectations
    merged_expectations = det_data["expectations"] + grading_data.get(
        "expectations", []
    )
    grading_data["expectations"] = merged_expectations

    # Recompute summary
    total = len(merged_expectations)
    passed_count = sum(1 for e in merged_expectations if e["passed"])
    grading_data["summary"] = {
        "passed": passed_count,
        "failed": total - passed_count,
        "total": total,
        "pass_rate": (passed_count / total) if total > 0 else 0.0,
    }

    grading_path.write_text(
        json.dumps(grading_data, indent=2) + "\n",
        encoding="utf-8",
    )
