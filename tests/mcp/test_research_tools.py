from __future__ import annotations

import asyncio
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
