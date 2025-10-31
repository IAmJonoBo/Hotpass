from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pandas as pd
import pytest

from hotpass.mcp.server import HotpassMCPServer


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_dataset(tmp_path: Path) -> Path:
    path = tmp_path / "mcp-research-input.xlsx"
    df = pd.DataFrame(
        {
            "organization_name": ["Example Research Org"],
            "contact_primary_email": [""],
            "website": ["example.org"],
        }
    )
    df.to_excel(path, index=False)
    return path


@pytest.mark.asyncio
async def test_plan_research_tool(tmp_path, monkeypatch):
    dataset = _write_dataset(tmp_path)
    monkeypatch.delenv("FEATURE_ENABLE_REMOTE_RESEARCH", raising=False)
    monkeypatch.delenv("ALLOW_NETWORK_RESEARCH", raising=False)

    server = HotpassMCPServer()
    result = await server._execute_tool(  # pylint: disable=protected-access
        "hotpass.plan.research",
        {
            "dataset_path": str(dataset),
            "row_id": "0",
            "allow_network": True,
        },
    )

    expect(result["success"] is True, "Plan research tool should succeed")
    outcome = result["outcome"]
    expect("plan" in outcome, "Outcome should include plan metadata")
    expect(
        any(step["status"] == "success" for step in outcome["steps"]),
        "At least one step should succeed",
    )


@pytest.mark.asyncio
async def test_crawl_tool(monkeypatch):
    monkeypatch.delenv("FEATURE_ENABLE_REMOTE_RESEARCH", raising=False)
    monkeypatch.delenv("ALLOW_NETWORK_RESEARCH", raising=False)

    server = HotpassMCPServer()
    result = await server._execute_tool(  # pylint: disable=protected-access
        "hotpass.crawl",
        {
            "query_or_url": "https://example.org",
            "allow_network": True,
        },
    )

    expect(result["success"] is True, "Crawl tool should succeed")
    outcome = result["outcome"]
    expect(outcome["plan"]["entity_name"], "Crawl outcome should include entity name")


@pytest.mark.asyncio
async def test_ta_check_tool(monkeypatch, tmp_path):
    artifact = tmp_path / "latest-ta.json"
    artifact.write_text("{}", encoding="utf-8")
    history = tmp_path / "history.ndjson"
    history.write_text("", encoding="utf-8")

    async def fake_run_command(self, cmd):  # type: ignore[override]
        payload = {
            "summary": {"total": 5, "passed": 5, "failed": 0, "all_passed": True},
            "gates": [
                {"id": "QG-1", "name": "CLI Integrity", "passed": True, "message": "ok"},
                {"id": "QG-2", "name": "Data Quality", "passed": True, "message": "ok"},
            ],
            "artifact_path": str(artifact),
            "history_path": str(history),
        }
        return {"returncode": 0, "stdout": json.dumps(payload), "stderr": ""}

    monkeypatch.setattr(HotpassMCPServer, "_run_command", fake_run_command)

    server = HotpassMCPServer()
    result = await server._execute_tool(  # pylint: disable=protected-access
        "hotpass.ta.check",
        {},
    )

    expect(result["success"] is True, "TA check tool should report success")
    expect(result["summary"]["all_passed"] is True, "Summary should indicate all gates passed")
    expect(Path(result["artifact_path"]).exists(), "Artifact path returned by TA tool must exist")
    expect(Path(result.get("history_path", history)).exists(), "History path should be present and exist")
