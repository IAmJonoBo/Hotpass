from __future__ import annotations

from pathlib import Path

from hotpass.data_sources.agents import (
    AcquisitionPlan,
    AgentDefinition,
    ProviderDefinition,
    TargetDefinition,
    run_plan,
)
from hotpass.pipeline.base import PipelineConfig, _load_sources


def _build_sample_plan() -> AcquisitionPlan:
    linkedin_options = {
        "profiles": {
            "hotpass": {
                "organization": "Hotpass Aero",
                "website": "https://hotpass.example",
                "profile_url": "https://linkedin.com/company/hotpass",
                "contacts": [
                    {
                        "name": "Pat Agent",
                        "title": "Director",
                        "email": "pat.agent@hotpass.example",
                        "phone": "+27 11 123 4567",
                        "confidence": 0.92,
                    }
                ],
            }
        }
    }
    clearbit_options = {
        "companies": {
            "hotpass.example": {
                "name": "Hotpass Aero",
                "domain": "hotpass.example",
                "description": "Aviation analytics",
                "category": "aviation",
                "tags": ["Aviation", "Analytics"],
                "confidence": 0.88,
            }
        }
    }
    return AcquisitionPlan(
        enabled=True,
        agents=(
            AgentDefinition(
                name="prospector",
                search_terms=("hotpass",),
                providers=(
                    ProviderDefinition(name="linkedin", options=linkedin_options),
                    ProviderDefinition(name="clearbit", options=clearbit_options),
                ),
                targets=(TargetDefinition(identifier="hotpass", domain="hotpass.example"),),
            ),
        ),
    )


def test_run_plan_collects_records_with_provenance() -> None:
    plan = _build_sample_plan()
    frame, timings, warnings = run_plan(plan, country_code="ZA")

    assert not frame.empty
    assert "provenance" in frame.columns
    first_provenance = frame.iloc[0]["provenance"]
    assert isinstance(first_provenance, list) and first_provenance
    assert any(entry.get("provider") == "linkedin" for entry in first_provenance)
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
