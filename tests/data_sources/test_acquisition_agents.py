from __future__ import annotations

import json
from pathlib import Path

from hotpass.data_sources.agents import (
    AcquisitionPlan,
    AgentDefinition,
    AgentTaskDefinition,
    AgentTaskKind,
    ProviderDefinition,
    TargetDefinition,
    run_plan,
)
from hotpass.pipeline.base import PipelineConfig, _load_sources


def _build_sample_plan() -> AcquisitionPlan:
    fixture = (
        Path(__file__).resolve().parent.parent / "fixtures" / "acquisition" / "blended_plan.json"
    )
    payload = json.loads(fixture.read_text())
    search_options = payload["search"]
    crawl_options = payload["crawl"]
    providers = payload["providers"]
    return AcquisitionPlan(
        enabled=True,
        agents=(
            AgentDefinition(
                name="prospector",
                search_terms=("hotpass",),
                providers=(
                    ProviderDefinition(name="linkedin", options=providers["linkedin"]),
                    ProviderDefinition(name="clearbit", options=providers["clearbit"]),
                    ProviderDefinition(
                        name="aviation_registry", options=providers["aviation_registry"]
                    ),
                ),
                targets=(TargetDefinition(identifier="hotpass", domain="hotpass.example"),),
                tasks=(
                    AgentTaskDefinition(
                        name="seed-search",
                        kind=AgentTaskKind.SEARCH,
                        options=search_options,
                    ),
                    AgentTaskDefinition(
                        name="seed-crawl",
                        kind=AgentTaskKind.CRAWL,
                        options=crawl_options,
                    ),
                    AgentTaskDefinition(
                        name="linkedin-api",
                        kind=AgentTaskKind.API,
                        provider="linkedin",
                    ),
                    AgentTaskDefinition(
                        name="clearbit-api",
                        kind=AgentTaskKind.API,
                        provider="clearbit",
                    ),
                    AgentTaskDefinition(
                        name="aviation-api",
                        kind=AgentTaskKind.API,
                        provider="aviation_registry",
                    ),
                ),
            ),
        ),
    )


def test_run_plan_collects_records_with_provenance() -> None:
    plan = _build_sample_plan()
    frame, timings, warnings = run_plan(plan, country_code="ZA")

    assert not frame.empty
    assert "provenance" in frame.columns
    flattened_provenance = [
        entry for records in frame["provenance"] if isinstance(records, list) for entry in records
    ]
    assert flattened_provenance
    assert any(entry.get("provider") == "linkedin" for entry in flattened_provenance)
    assert any(
        entry.get("compliance", {}).get("robots_allowed") is True for entry in flattened_provenance
    )
    datasets = set(frame["source_dataset"])
    assert {"Web Crawl", "LinkedIn", "Clearbit", "Aviation Registry"} <= datasets
    assert any(timing.agent_name == "prospector" for timing in timings)
    assert warnings == []


def test_load_sources_includes_agent_results(tmp_path: Path) -> None:
    plan = _build_sample_plan()
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=tmp_path / "refined.xlsx",
        acquisition_plan=plan,
    )
    frame, timings = _load_sources(config)

    assert not frame.empty
    assert "LinkedIn" in frame["source_dataset"].unique()
    assert any(key.startswith("agent:") for key in timings)
    assert config.preloaded_agent_frame is not None
    assert config.preloaded_agent_timings
    assert config.preloaded_agent_warnings == []
