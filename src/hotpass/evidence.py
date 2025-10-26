"""Evidence logging helpers for compliance and export activities."""

from __future__ import annotations

import datetime as dt
import json
import os
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _serialise_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def _current_time(clock: Callable[[], dt.datetime] | None = None) -> dt.datetime:
    """Return an aware UTC timestamp from the provided clock."""

    candidate = clock() if clock is not None else dt.datetime.now(dt.UTC)
    if candidate.tzinfo is None:
        return candidate.replace(tzinfo=dt.UTC)
    return candidate.astimezone(dt.UTC)


def record_consent_audit_log(
    report: Mapping[str, Any],
    *,
    base_dir: str | Path | None = None,
    run_id: str | None = None,
    clock: Callable[[], dt.datetime] | None = None,
) -> Path:
    """Persist a compliance report to the evidence directory.

    Args:
        report: POPIA compliance report payload.
        base_dir: Base directory for evidence logs. Defaults to ``data/logs/prefect``.
        run_id: Optional run identifier to include in the filename.

    Returns:
        Path to the persisted audit log file.
    """

    evidence_root = Path(base_dir or "data/logs/prefect").expanduser().resolve()
    _ensure_directory(evidence_root)

    now = _current_time(clock)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{run_id}" if run_id else ""
    filename = f"consent_audit{suffix}_{timestamp}.json"
    output_path = evidence_root / filename

    payload: dict[str, Any] = {
        "recorded_at": now.isoformat(),
        "run_id": run_id,
        "report": dict(report),
    }

    output_path.write_text(_serialise_payload(payload), encoding="utf-8")
    return output_path


def record_export_access_event(
    output_path: Path,
    *,
    total_records: int,
    log_dir: Path | None = None,
    digest: str | None = None,
    context: Mapping[str, Any] | None = None,
    clock: Callable[[], dt.datetime] | None = None,
) -> Path:
    """Record an access log entry for a refined export."""

    export_path = output_path.expanduser().resolve()
    access_root = (
        log_dir.expanduser().resolve()
        if log_dir is not None
        else export_path.parent / "logs" / "access"
    )
    _ensure_directory(access_root)

    if digest is None and export_path.exists():
        hash_obj = sha256()
        with export_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8192), b""):
                hash_obj.update(chunk)
        digest = hash_obj.hexdigest()

    now = _current_time(clock)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    filename = f"export_access_{timestamp}.json"
    log_path = access_root / filename

    payload: dict[str, Any] = {
        "recorded_at": now.isoformat(),
        "output_path": str(export_path),
        "total_records": total_records,
        "sha256": digest,
        "context": dict(context or {}),
        "worker": os.getenv("HOSTNAME"),
    }

    log_path.write_text(_serialise_payload(payload), encoding="utf-8")
    return log_path


__all__ = [
    "record_consent_audit_log",
    "record_export_access_event",
]
