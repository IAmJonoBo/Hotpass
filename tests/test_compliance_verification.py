"""Tests for the compliance verification cadence helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

pytest.importorskip("frictionless")

from hotpass.compliance_verification import (  # noqa: E402
    DEFAULT_FRAMEWORKS,
    frameworks_due,
    generate_summary,
    is_framework_due,
    load_verification_log,
    record_verification_run,
)


@pytest.fixture()
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "verification-log.json"


def test_framework_due_when_no_history(log_path: Path) -> None:
    """Without history the framework should be due immediately."""

    assert load_verification_log(log_path) == []
    assert is_framework_due("POPIA", log_path=log_path) is True


def test_record_run_marks_framework_not_due_until_next_quarter(log_path: Path) -> None:
    """Recording a run should reset the cadence window for all frameworks."""

    timestamp = datetime(2024, 10, 1, tzinfo=UTC)
    record_verification_run(
        frameworks=("POPIA", "SOC 2"),
        reviewers=("Alice", "Bob"),
        findings=("Consent logs reviewed",),
        notes="Quarterly verification completed",
        log_path=log_path,
        timestamp=timestamp,
    )

    ninety_days_later = timestamp + timedelta(days=90)
    soon_after = timestamp + timedelta(days=1)
    assert is_framework_due("POPIA", log_path=log_path, now=soon_after) is False
    assert is_framework_due("SOC 2", log_path=log_path, now=soon_after) is False
    assert is_framework_due("ISO 27001", log_path=log_path, now=soon_after) is True
    assert is_framework_due("POPIA", log_path=log_path, now=ninety_days_later) is True


def test_generate_summary_reflects_latest_run(log_path: Path) -> None:
    """The summary should surface the last reviewers and findings per framework."""

    ts = datetime(2024, 1, 15, tzinfo=UTC)
    record_verification_run(
        frameworks=DEFAULT_FRAMEWORKS,
        reviewers=("Alice",),
        findings=("Updated evidence catalog", "Verified DSAR backlog"),
        notes="Cadence executed",
        log_path=log_path,
        timestamp=ts,
    )

    summary = generate_summary(log_path=log_path, now=ts + timedelta(days=10))
    framework_summary = summary["frameworks"]["POPIA"]
    assert framework_summary["due"] is False
    assert framework_summary["reviewers"] == ["Alice"]
    assert "Updated evidence catalog" in framework_summary["findings"]
    assert framework_summary["notes"] == "Cadence executed"

    # Move past the cadence window and ensure due flips to True
    overdue_summary = generate_summary(log_path=log_path, now=ts + timedelta(days=200))
    assert overdue_summary["frameworks"]["POPIA"]["due"] is True


def test_frameworks_due_handles_case_insensitivity(log_path: Path) -> None:
    """Framework lookups should not be case-sensitive."""

    timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    record_verification_run(frameworks=("popia",), log_path=log_path, timestamp=timestamp)

    due_frameworks = frameworks_due(
        ("POPIA",), log_path=log_path, now=timestamp + timedelta(days=30)
    )
    assert due_frameworks == []
    due_frameworks = frameworks_due(
        ("POPIA",), log_path=log_path, now=timestamp + timedelta(days=120)
    )
    assert due_frameworks == ["POPIA"]
