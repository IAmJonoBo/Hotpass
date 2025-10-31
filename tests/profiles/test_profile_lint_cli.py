from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _run_linter(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "tools/profile_lint.py", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_profile_lint_json_summary(tmp_path: Path) -> None:
    result = _run_linter("--json")
    expect(
        result.returncode == 0,
        f"profile_lint --json should succeed (stderr={result.stderr})",
    )
    payload = json.loads(result.stdout)
    summary = payload.get("summary", {})
    expect(isinstance(summary, dict), "Summary should be a dict")
    expect(summary.get("total", 0) >= 1, "Summary should include total profiles")
    expect(
        summary.get("passed") == summary.get("total"),
        "All profiles should currently pass lint",
    )
    expect(summary.get("all_passed") is True, "all_passed flag should be True")
    profiles = payload.get("profiles", [])
    expect(
        isinstance(profiles, list) and bool(profiles),
        "Profiles list should be populated",
    )
    first = profiles[0]
    expect(
        "name" in first and "passed" in first,
        "Profile entry should include name and passed fields",
    )


def test_profile_lint_schema_json() -> None:
    result = _run_linter("--schema-json")
    expect(
        result.returncode == 0,
        f"profile_lint --schema-json should succeed (stderr={result.stderr})",
    )
    payload = json.loads(result.stdout)
    expect("required" in payload, "Schema should expose required keys")
    expect(
        "ingest" in payload and "enrich" in payload,
        "Schema should document core blocks",
    )
