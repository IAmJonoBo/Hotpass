from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_history(path: Path) -> None:
    entries = [
        {
            "timestamp": "2025-10-30T10:00:00Z",
            "summary": {"total": 5, "passed": 5, "failed": 0, "all_passed": True},
            "gates": [],
            "artifact_path": "dist/quality-gates/latest-ta.json",
        },
        {
            "timestamp": "2025-10-31T10:00:00Z",
            "summary": {"total": 5, "passed": 4, "failed": 1, "all_passed": False},
            "gates": [],
            "artifact_path": "dist/quality-gates/latest-ta.json",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry))
            handle.write("\n")


def test_ta_history_report_json(tmp_path):
    history_path = tmp_path / "history.ndjson"
    _write_history(history_path)

    result = subprocess.run(
        [
            sys.executable,
            "ops/quality/ta_history_report.py",
            "--path",
            str(history_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    expect(
        result.returncode == 0,
        f"ta_history_report --json should succeed (stderr={result.stderr})",
    )
    payload = json.loads(result.stdout)
    expect(payload["total_runs"] == 2, "Summary should count total runs")
    expect(payload["passed"] == 1, "Summary should count passes")
    expect(payload["failed"] == 1, "Summary should count failures")
    expect(
        payload["latest"]["timestamp"] == "2025-10-31T10:00:00Z",
        "Latest entry should be returned",
    )


def test_ta_history_report_text(tmp_path):
    history_path = tmp_path / "history.ndjson"
    _write_history(history_path)

    result = subprocess.run(
        [
            sys.executable,
            "ops/quality/ta_history_report.py",
            "--path",
            str(history_path),
            "--limit",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    expect(
        result.returncode == 0,
        f"ta_history_report text mode should succeed (stderr={result.stderr})",
    )
    output = result.stdout
    expect("Total runs: 2" in output, "Text output should include totals")
    expect("Most recent 1 entries" in output, "Text output should honour limit")
