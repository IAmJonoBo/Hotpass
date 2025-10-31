#!/usr/bin/env python3
"""Summarise Technical Acceptance (TA) history artefacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise dist/quality-gates/history.ndjson entries",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("dist/quality-gates/history.ndjson"),
        help="Path to TA history NDJSON file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of most recent entries to display in text mode (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary",
    )
    return parser.parse_args(argv)


def _load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            entries.append(payload)
    return entries


def _build_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(entries)
    passed = sum(1 for entry in entries if entry.get("summary", {}).get("all_passed"))
    failed = total - passed
    last_entry = entries[-1] if entries else None
    return {
        "total_runs": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total) if total else None,
        "latest": last_entry,
    }


def _format_timestamp(value: Any) -> str:
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.isoformat()
        except ValueError:
            return value
    return str(value)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    entries = _load_entries(args.path)
    summary = _build_summary(entries)

    if args.json:
        print(json.dumps(summary, indent=2))
        return 0

    if not entries:
        print(f"No TA history entries found at {args.path}")
        return 0

    print(f"TA history summary ({args.path}):")
    print(f"  Total runs: {summary['total_runs']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    if summary["pass_rate"] is not None:
        print(f"  Pass rate: {summary['pass_rate'] * 100:.1f}%")

    latest = summary.get("latest") or {}
    timestamp = _format_timestamp(latest.get("timestamp"))
    status = "passed" if latest.get("summary", {}).get("all_passed") else "failed"
    print(f"  Latest run: {timestamp} ({status})")

    limit = max(args.limit, 1)
    print()
    print(f"Most recent {min(limit, len(entries))} entries:")
    for entry in entries[-limit:]:
        ts = _format_timestamp(entry.get("timestamp"))
        gate_summary = entry.get("summary", {})
        passed = gate_summary.get("all_passed")
        print(f"- {ts}: {'PASS' if passed else 'FAIL'} ({gate_summary.get('passed')} passed / {gate_summary.get('total')} total)")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
