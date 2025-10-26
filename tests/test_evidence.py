from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

pytest.importorskip("frictionless")

from hotpass.evidence import record_consent_audit_log, record_export_access_event  # noqa: E402


def test_record_consent_audit_log_deterministic(tmp_path):
    """Consent audit logging accepts a deterministic clock for reproducible tests."""

    fixed_time = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    def _clock() -> datetime:
        return fixed_time

    path = record_consent_audit_log(
        {"status": "ok"},
        base_dir=tmp_path,
        run_id="run-42",
        clock=_clock,
    )

    assert path.name == "consent_audit_run-42_20250101T120000Z.json"

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["recorded_at"] == fixed_time.isoformat()
    assert payload["run_id"] == "run-42"
    assert payload["report"] == {"status": "ok"}


def test_record_export_access_event_deterministic(tmp_path):
    """Export access logging accepts deterministic timestamps and digests."""

    output_file = tmp_path / "refined.xlsx"
    output_file.write_bytes(b"data")

    fixed_time = datetime(2025, 1, 2, 6, 30, tzinfo=UTC)

    def _clock() -> datetime:
        return fixed_time

    log_path = record_export_access_event(
        output_file,
        total_records=3,
        log_dir=tmp_path / "logs",
        context={"task": "prefect"},
        clock=_clock,
    )

    assert log_path.parent == tmp_path / "logs"
    assert log_path.name == "export_access_20250102T063000Z.json"

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["recorded_at"] == fixed_time.isoformat()
    assert payload["total_records"] == 3
    # pragma: allowlist nextline secret
    expected_sha = "3a6eb0790f39ac87c94f3856b2dd2c5d110e6811602261a9a923d3bb23adc8b7"
    assert payload["sha256"] == expected_sha
    assert payload["context"] == {"task": "prefect"}
    assert payload["output_path"] == str(output_file.resolve())
