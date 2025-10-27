"""Tests for agent-gated Prefect orchestration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

pytest.importorskip("frictionless")

import hotpass.orchestration as orchestration

AgenticRequest = orchestration.AgenticRequest
AgentToolPolicy = orchestration.AgentToolPolicy
AgentApprovalDecision = orchestration.AgentApprovalDecision
AgentApprovalError = orchestration.AgentApprovalError
PipelineRunSummary = orchestration.PipelineRunSummary


def _make_request(
    *,
    tool: str = "prefect",
    role: str = "analyst",
    action: str = "run_pipeline",
    pipeline_overrides: dict[str, Any] | None = None,
) -> AgenticRequest:
    payload = {
        "pipeline": {
            "input_dir": "./data/inbox",
            "output_path": "./dist/from-agent.xlsx",
            "profile_name": "aviation",
            "excel_chunk_size": None,
            "archive": False,
        }
    }
    if pipeline_overrides:
        payload["pipeline"].update(pipeline_overrides)

    return AgenticRequest(
        request_id="req-123",
        agent_name="hotpass-agent",
        role=role,
        tool=tool,
        action=action,
        parameters=payload,
    )


def test_broker_agent_run_denies_unlisted_tool() -> None:
    """Requests for tools that are not permitted for the role are rejected."""

    policy = AgentToolPolicy(
        allowed_tools_by_role={"analyst": frozenset({"prefect", "github"})},
        auto_approved_roles=frozenset({"analyst"}),
    )
    request = _make_request(tool="drive")
    log_sink: list[orchestration.AgentAuditRecord] = []

    with pytest.raises(AgentApprovalError, match="not permitted"):
        orchestration.broker_agent_run(
            request,
            policy,
            log_sink=log_sink,
        )

    assert log_sink, "a denial should be logged"
    denial_entry = log_sink[0]
    assert denial_entry.status == "denied"
    assert denial_entry.approved is False
    assert "not permitted" in (denial_entry.notes or "")


def test_broker_agent_run_requires_manual_approval() -> None:
    """Roles that require manual approval cannot proceed automatically."""

    policy = AgentToolPolicy(
        allowed_tools_by_role={"operator": frozenset({"prefect"})},
        auto_approved_roles=frozenset(),
    )
    request = _make_request(role="operator")
    log_sink: list[orchestration.AgentAuditRecord] = []

    with pytest.raises(AgentApprovalError, match="Manual approval"):
        orchestration.broker_agent_run(
            request,
            policy,
            log_sink=log_sink,
        )

    assert log_sink, "a manual approval denial should be logged"
    denial_entry = log_sink[0]
    assert denial_entry.status == "denied"
    assert denial_entry.approver == "manual"


def test_broker_agent_run_executes_pipeline_with_approval() -> None:
    """Approved requests invoke the pipeline and record audit entries."""

    policy = AgentToolPolicy(
        allowed_tools_by_role={"operator": frozenset({"prefect"})},
        auto_approved_roles=frozenset(),
    )
    request = _make_request(role="operator")
    approval = AgentApprovalDecision(
        approved=True,
        approver="ops.lead",
        notes="Change ticket CHG-42",
    )
    summary = PipelineRunSummary(
        success=True,
        total_records=12,
        elapsed_seconds=1.5,
        output_path=Path("./dist/from-agent.xlsx"),
        quality_report={"expectations_passed": True},
        archive_path=None,
    )
    log_sink: list[orchestration.AgentAuditRecord] = []

    with patch("hotpass.orchestration.run_pipeline_once", return_value=summary) as mock_runner:
        result = orchestration.broker_agent_run(
            request,
            policy,
            approval=approval,
            log_sink=log_sink,
        )

    assert result is summary
    mock_runner.assert_called_once()
    options_arg = mock_runner.call_args[0][0]
    assert options_arg.profile_name == "aviation"
    assert options_arg.config.pipeline.input_dir == Path("./data/inbox")

    assert len(log_sink) >= 2
    assert log_sink[0].status == "approved"
    assert log_sink[0].approved is True
    assert log_sink[1].status == "executed"
    assert log_sink[1].result is not None
    assert log_sink[1].result.get("success") is True
