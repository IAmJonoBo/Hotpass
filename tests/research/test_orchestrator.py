from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from hotpass.config import IndustryProfile
from hotpass.research import ResearchContext, ResearchOrchestrator


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_plan_offline_path(tmp_path):
    cache_root = tmp_path / ".hotpass"
    cache_root.mkdir()
    snapshots_dir = cache_root / "snapshots"
    snapshots_dir.mkdir()

    profile = IndustryProfile.from_dict(
        {
            "name": "test",
            "display_name": "Test Profile",
            "authority_sources": [
                {
                    "name": "Test Registry",
                    "cache_key": "registry",
                }
            ],
            "research_backfill": {
                "fields": ["contact_primary_email", "website"],
                "confidence_threshold": 0.7,
            },
            "research_rate_limit": {
                "min_interval_seconds": 1.0,
            },
        }
    )

    row = pd.Series(
        {
            "organization_name": "Example Flight School",
            "contact_primary_email": "",
            "website": "example.com",
        }
    )

    slug = "example-flight-school"
    snapshot_path = snapshots_dir / f"{slug}.json"
    snapshot_path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    authority_dir = cache_root / "authority" / "registry"
    authority_dir.mkdir(parents=True)
    (authority_dir / f"{slug}.json").write_text(
        json.dumps({"registry": "hit"}),
        encoding="utf-8",
    )

    orchestrator = ResearchOrchestrator(cache_root=cache_root, audit_log=cache_root / "audit.log")
    context = ResearchContext(profile=profile, row=row, allow_network=False)
    outcome = orchestrator.plan(context)

    expect(outcome.plan.entity_slug == slug, "Entity slug should derive from organization name")
    statuses = {step.name: step.status for step in outcome.steps}
    expect(statuses.get("local_snapshot") == "success", "Local snapshot should load")
    expect(statuses.get("authority_sources") == "success", "Authority snapshot should load")
    expect(statuses.get("network_enrichment") == "skipped", "Network step disabled offline")
    expect(statuses.get("native_crawl") == "skipped", "Crawl skipped without network")
    expect(statuses.get("backfill") == "success", "Backfill step should flag missing fields")
    expect(outcome.plan.rate_limit_seconds == 1.0, "Rate limit should propagate into the plan")
    expect(outcome.artifact_path is not None, "Outcome should persist an artefact path")
    expect(Path(outcome.artifact_path).exists(), "Artefact file should be written to disk")

    audit_path = cache_root / "audit.log"
    expect(audit_path.exists(), "Audit log should be written")
    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    expect(len(lines) == 1, "Audit log should contain a single entry")


def test_crawl_summary_without_network(tmp_path):
    cache_root = tmp_path / ".hotpass"
    cache_root.mkdir()
    profile = IndustryProfile.from_dict({"name": "generic", "display_name": "Generic"})

    orchestrator = ResearchOrchestrator(cache_root=cache_root, audit_log=cache_root / "audit.log")
    outcome = orchestrator.crawl(
        profile=profile,
        query_or_url="https://example.test",
        allow_network=False,
    )

    statuses = {step.name: step.status for step in outcome.steps}
    expect(statuses.get("network_enrichment") == "skipped", "Network enrichment should skip when disabled")
    expect(statuses.get("native_crawl") == "skipped", "Crawl should skip without network access")
    if outcome.artifact_path:
        expect(Path(outcome.artifact_path).exists(), "Crawl artefact should be written")
