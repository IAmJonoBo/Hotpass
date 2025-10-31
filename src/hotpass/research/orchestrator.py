"""Adaptive research orchestrator coordinating deterministic and network passes."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from hotpass.config import IndustryProfile
from hotpass.enrichment.pipeline import enrich_row
from hotpass.normalization import slugify

try:  # pragma: no cover - optional dependency
    from scrapy.crawler import CrawlerProcess
    from scrapy.spiders import Spider  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    CrawlerProcess = None
    Spider = object

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)

StepStatus = Literal["success", "skipped", "error"]


@dataclass(slots=True)
class AuthoritySnapshot:
    """Snapshot describing an authority source defined by the active profile."""

    name: str
    cache_key: str | None = None
    url: str | None = None
    description: str | None = None


@dataclass(slots=True)
class RateLimitPolicy:
    """Rate limit policy derived from the active profile."""

    min_interval_seconds: float
    burst: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_interval_seconds": self.min_interval_seconds,
            "burst": self.burst,
        }


@dataclass(slots=True)
class ResearchPlan:
    """Execution plan derived from the entity context and profile configuration."""

    entity_name: str
    entity_slug: str
    query: str | None
    target_urls: tuple[str, ...]
    row: pd.Series | None
    profile: IndustryProfile
    allow_network: bool
    authority_sources: tuple[AuthoritySnapshot, ...]
    backfill_fields: tuple[str, ...]
    rate_limit: RateLimitPolicy | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "entity_slug": self.entity_slug,
            "query": self.query,
            "target_urls": list(self.target_urls),
            "allow_network": self.allow_network,
            "authority_sources": [
                {
                    "name": snapshot.name,
                    "cache_key": snapshot.cache_key,
                    "url": snapshot.url,
                    "description": snapshot.description,
                }
            for snapshot in self.authority_sources
        ],
        "backfill_fields": list(self.backfill_fields),
        "rate_limit": self.rate_limit.to_dict() if self.rate_limit else None,
    }


@dataclass(slots=True)
class ResearchContext:
    """Inputs supplied by the CLI or MCP caller."""

    profile: IndustryProfile
    row: pd.Series | None = None
    entity_name: str | None = None
    query: str | None = None
    urls: Sequence[str] = ()
    allow_network: bool = False
    backfill_fields: Sequence[str] = ()


@dataclass(slots=True)
class ResearchStepResult:
    """Outcome of a single orchestrator step."""

    name: str
    status: StepStatus
    message: str
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResearchOutcome:
    """Aggregate result produced by the orchestrator."""

    plan: ResearchPlan
    steps: tuple[ResearchStepResult, ...]
    enriched_row: dict[str, Any] | None
    provenance: dict[str, Any] | None
    elapsed_seconds: float
    artifact_path: str | None = None

    @property
    def success(self) -> bool:
        return all(step.status != "error" for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "message": step.message,
                    "artifacts": step.artifacts,
                }
                for step in self.steps
            ],
            "enriched_row": self.enriched_row,
            "provenance": self.provenance,
            "elapsed_seconds": self.elapsed_seconds,
            "success": self.success,
            "artifact_path": self.artifact_path,
        }


class ResearchOrchestrator:
    """Coordinate adaptive research loops across local, deterministic, and network passes."""

    def __init__(
        self,
        *,
        cache_root: Path | None = None,
        audit_log: Path | None = None,
        artefact_root: Path | None = None,
    ) -> None:
        self.cache_root = cache_root or Path(".hotpass")
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.audit_log = audit_log or (self.cache_root / "mcp-audit.log")
        self.artefact_root = artefact_root or (self.cache_root / "research_runs")
        self.artefact_root.mkdir(parents=True, exist_ok=True)
        self._last_network_call: float | None = None
        self._rate_limit_policy: RateLimitPolicy | None = None
        self._burst_tokens: int | None = None

    def plan(self, context: ResearchContext) -> ResearchOutcome:
        """Build and execute a research plan."""

        plan = self._build_plan(context)
        outcome = self._execute(plan)
        self._write_audit_entry("plan", outcome)
        return outcome

    def crawl(
        self,
        *,
        profile: IndustryProfile,
        query_or_url: str,
        allow_network: bool,
    ) -> ResearchOutcome:
        """Execute a crawl-only flow for MCP and CLI surfaces."""

        urls: list[str] = []
        query: str | None = None
        if query_or_url.startswith(("http://", "https://")):
            urls.append(query_or_url)
        else:
            query = query_or_url
        context = ResearchContext(
            profile=profile,
            query=query,
            urls=urls,
            allow_network=allow_network,
        )
        plan = self._build_plan(context)
        outcome = self._execute(plan, crawl_only=True)
        self._write_audit_entry("crawl", outcome)
        return outcome

    # --------------------------------------------------------------------- #
    # Plan construction
    # --------------------------------------------------------------------- #

    def _build_plan(self, context: ResearchContext) -> ResearchPlan:
        row = context.row
        entity_name = (
            context.entity_name
            or (
                str(row["organization_name"])
                if row is not None and "organization_name" in row
                else None
            )
            or context.query
            or "unknown-entity"
        )
        entity_slug = slugify(entity_name) or "entity"

        urls = list(_filter_blank(context.urls))
        if row is not None:
            website_value = row.get("website")
            if isinstance(website_value, str) and website_value.strip():
                urls.append(self._ensure_protocol(website_value.strip()))

        profile_backfill_fields = getattr(
            context.profile,
            "backfill_fields",
            tuple(context.profile.optional_fields),
        )

        authority_sources = tuple(
            AuthoritySnapshot(
                name=source.name,
                cache_key=source.cache_key,
                url=source.url,
                description=source.description,
            )
            for source in getattr(context.profile, "authority_sources", tuple())
        )

        backfill_fields = tuple(
            _filter_blank(context.backfill_fields or profile_backfill_fields)
        )

        rate_limit_policy: RateLimitPolicy | None = None
        profile_rate_limit = getattr(context.profile, "research_rate_limit", None)
        if profile_rate_limit is not None:
            candidate = getattr(profile_rate_limit, "min_interval_seconds", None)
            burst_candidate = getattr(profile_rate_limit, "burst", None)
            if isinstance(candidate, (int, float)) and candidate > 0:
                burst_value: int | None = None
                if isinstance(burst_candidate, int) and burst_candidate > 0:
                    burst_value = burst_candidate
                rate_limit_policy = RateLimitPolicy(
                    min_interval_seconds=float(candidate),
                    burst=burst_value,
                )

        return ResearchPlan(
            entity_name=entity_name,
            entity_slug=entity_slug,
            query=context.query,
            target_urls=tuple(
                dict.fromkeys(urls)
            ),  # preserve order while removing duplicates
            row=row,
            profile=context.profile,
            allow_network=context.allow_network,
            authority_sources=authority_sources,
            backfill_fields=backfill_fields,
            rate_limit=rate_limit_policy,
        )

    # --------------------------------------------------------------------- #
    # Execution
    # --------------------------------------------------------------------- #

    def _execute(
        self, plan: ResearchPlan, *, crawl_only: bool = False
    ) -> ResearchOutcome:
        start = time.perf_counter()
        steps: list[ResearchStepResult] = []
        enriched_row: dict[str, Any] | None = None
        provenance: dict[str, Any] | None = None

        self._rate_limit_policy = plan.rate_limit
        if plan.rate_limit and plan.rate_limit.burst is not None:
            self._burst_tokens = plan.rate_limit.burst
        else:
            self._burst_tokens = None
        self._last_network_call = None

        if not crawl_only:
            steps.append(self._run_local_snapshot(plan))
            steps.append(self._run_authority_pass(plan))
            deterministic_step = self._run_deterministic_enrichment(plan)
            steps.append(deterministic_step)
            if deterministic_step.artifacts.get("enriched_row"):
                enriched_row = deterministic_step.artifacts["enriched_row"]
                provenance = deterministic_step.artifacts.get("provenance")

        network_step = self._run_network_enrichment(plan, enriched_row=enriched_row)
        steps.append(network_step)
        if network_step.status == "success" and network_step.artifacts.get(
            "enriched_row"
        ):
            enriched_row = network_step.artifacts["enriched_row"]
            provenance = network_step.artifacts.get("provenance", provenance)

        steps.append(self._run_native_crawl(plan))
        if not crawl_only:
            steps.append(self._run_backfill_plan(plan, enriched_row=enriched_row))

        elapsed = time.perf_counter() - start
        outcome = ResearchOutcome(
            plan=plan,
            steps=tuple(steps),
            enriched_row=enriched_row,
            provenance=provenance,
            elapsed_seconds=elapsed,
        )
        self._persist_outcome(outcome)
        return outcome

    # --------------------------------------------------------------------- #
    # Individual steps
    # --------------------------------------------------------------------- #

    def _run_local_snapshot(self, plan: ResearchPlan) -> ResearchStepResult:
        slug = plan.entity_slug
        snapshot_path = self.cache_root / "snapshots" / f"{slug}.json"
        if snapshot_path.exists():
            try:
                payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:  # pragma: no cover - corrupted cache
                LOGGER.warning("Failed to parse cached snapshot for %s: %s", slug, exc)
                return ResearchStepResult(
                    name="local_snapshot",
                    status="error",
                    message=f"Cached snapshot exists but is invalid: {snapshot_path}",
                    artifacts={"path": str(snapshot_path)},
                )
            return ResearchStepResult(
                name="local_snapshot",
                status="success",
                message="Loaded cached snapshot",
                artifacts={
                    "path": str(snapshot_path),
                    "snapshot": payload,
                },
            )
        return ResearchStepResult(
            name="local_snapshot",
            status="skipped",
            message="No cached snapshot available",
            artifacts={"path": str(snapshot_path)},
        )

    def _run_authority_pass(self, plan: ResearchPlan) -> ResearchStepResult:
        slug = plan.entity_slug
        authority_hits: list[dict[str, Any]] = []
        for source in plan.authority_sources:
            cache_key = source.cache_key or slugify(source.name) or "default"
            path = self.cache_root / "authority" / cache_key / f"{slug}.json"
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:  # pragma: no cover - corrupted cache
                LOGGER.warning("Unable to parse authority snapshot %s: %s", path, exc)
                continue
            authority_hits.append(
                {
                    "source": source.name,
                    "path": str(path),
                    "snapshot": payload,
                }
            )

        if not authority_hits:
            return ResearchStepResult(
                name="authority_sources",
                status="skipped",
                message="No authority snapshots found for entity",
                artifacts={
                    "authority_sources": [
                        snapshot.name for snapshot in plan.authority_sources
                    ],
                },
            )

        return ResearchStepResult(
            name="authority_sources",
            status="success",
            message=f"Loaded {len(authority_hits)} authority snapshots",
            artifacts={"snapshots": authority_hits},
        )

    def _run_deterministic_enrichment(self, plan: ResearchPlan) -> ResearchStepResult:
        if plan.row is None:
            return ResearchStepResult(
                name="deterministic_enrichment",
                status="skipped",
                message="No dataset row supplied – skipping deterministic enrichment",
            )

        try:
            enriched_row, provenance = enrich_row(
                plan.row,
                plan.profile,
                allow_network=False,
                confidence_threshold=0.7,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            LOGGER.error("Deterministic enrichment failed: %s", exc, exc_info=True)
            return ResearchStepResult(
                name="deterministic_enrichment",
                status="error",
                message=f"Deterministic enrichment failed: {exc}",
            )

        updated = _diff_row(plan.row, enriched_row)
        message = "Deterministic enrichment executed without updates"
        status: StepStatus = "skipped"
        if updated:
            message = f"Deterministic enrichment updated {len(updated)} fields"
            status = "success"

        return ResearchStepResult(
            name="deterministic_enrichment",
            status=status,
            message=message,
            artifacts={
                "updated_fields": updated,
                "enriched_row": enriched_row.to_dict(),
                "provenance": provenance,
            },
        )

    def _run_network_enrichment(
        self,
        plan: ResearchPlan,
        *,
        enriched_row: dict[str, Any] | None,
    ) -> ResearchStepResult:
        if not plan.allow_network:
            return ResearchStepResult(
                name="network_enrichment",
                status="skipped",
                message="Network enrichment disabled via flags",
            )

        if plan.row is None:
            return ResearchStepResult(
                name="network_enrichment",
                status="skipped",
                message="No dataset row supplied – skipping network enrichment",
            )

        self._maybe_throttle(plan.rate_limit)
        try:
            enriched_series, provenance = enrich_row(
                plan.row,
                plan.profile,
                allow_network=True,
                confidence_threshold=0.8,
            )
        except Exception as exc:  # pragma: no cover - network failure
            LOGGER.warning("Network enrichment failed: %s", exc)
            self._last_network_call = time.monotonic()
            return ResearchStepResult(
                name="network_enrichment",
                status="error",
                message=f"Network enrichment failed: {exc}",
            )

        self._last_network_call = time.monotonic()

        updated = _diff_row(plan.row, enriched_series)
        message = "Network enrichment executed without updates"
        status: StepStatus = "skipped"
        if updated:
            message = f"Network enrichment updated {len(updated)} fields"
            status = "success"

        return ResearchStepResult(
            name="network_enrichment",
            status=status,
            message=message,
            artifacts={
                "updated_fields": updated,
                "enriched_row": enriched_series.to_dict(),
                "provenance": provenance,
            },
        )

    def _run_native_crawl(self, plan: ResearchPlan) -> ResearchStepResult:
        if not plan.allow_network:
            return ResearchStepResult(
                name="native_crawl",
                status="skipped",
                message="Network disabled; crawler not executed",
            )

        if not plan.target_urls and not plan.query:
            return ResearchStepResult(
                name="native_crawl",
                status="skipped",
                message="No URLs or query provided for crawl step",
            )

        if CrawlerProcess is None:
            if requests is None or not plan.target_urls:
                return ResearchStepResult(
                    name="native_crawl",
                    status="skipped",
                    message="Scrapy not installed; emit plan for external crawler",
                    artifacts={
                        "urls": list(plan.target_urls),
                        "query": plan.query,
                    },
                )
            try:
                self._maybe_throttle(plan.rate_limit)
                response = requests.get(plan.target_urls[0], timeout=10)
                self._last_network_call = time.monotonic()
                crawl_artifact = self._persist_crawl_results(
                    plan,
                    {
                        "results": [
                            {
                                "url": response.url,
                                "status": response.status_code,
                                "content_length": len(response.content),
                            }
                        ],
                        "query": plan.query,
                    },
                )
                artifacts = {
                    "results": [
                        {
                            "url": response.url,
                            "status": response.status_code,
                            "content_length": len(response.content),
                        }
                    ],
                    "query": plan.query,
                }
                if crawl_artifact:
                    artifacts["results_path"] = crawl_artifact
                return ResearchStepResult(
                    name="native_crawl",
                    status="success",
                    message="Fetched metadata via requests fallback",
                    artifacts=artifacts,
                )
            except Exception as exc:  # pragma: no cover - network failure
                LOGGER.warning("Requests crawl failed: %s", exc)
                self._last_network_call = time.monotonic()
                return ResearchStepResult(
                    name="native_crawl",
                    status="skipped",
                    message=f"Requests crawl failed (non-fatal): {exc}",
                    artifacts={"urls": list(plan.target_urls)},
                )

        # Construct a minimal spider when Scrapy is available. The spider gathers basic metadata
        # (status code, content length) so downstream steps can reason about completeness.
        results: list[dict[str, Any]] = []

        class MetadataSpider(Spider):  # type: ignore[misc]
            name = "hotpass_metadata_spider"

            def start_requests(self_inner):  # type: ignore[override]
                for url in plan.target_urls:
                    yield self_inner.make_requests_from_url(url)

            def parse(self_inner, response):  # type: ignore[override]
                results.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "content_length": len(response.body),
                    }
                )

        process = CrawlerProcess(settings={"LOG_ENABLED": False})
        try:
            self._maybe_throttle(plan.rate_limit)
            process.crawl(MetadataSpider)
            process.start()
            self._last_network_call = time.monotonic()
        except Exception as exc:  # pragma: no cover - defensive guard
            LOGGER.warning("Scrapy crawl failed: %s", exc)
            self._last_network_call = time.monotonic()
            return ResearchStepResult(
                name="native_crawl",
                status="skipped",
                message=f"Scrapy crawl failed (non-fatal): {exc}",
                artifacts={"urls": list(plan.target_urls)},
            )

        message = "Scrapy crawl completed with metadata snapshots"
        if not results:
            message = "Scrapy crawl executed but yielded no metadata"

        crawl_artifact = self._persist_crawl_results(
            plan,
            {
                "results": results,
                "query": plan.query,
            },
        )

        artifacts = {
            "results": results,
            "query": plan.query,
        }
        if crawl_artifact:
            artifacts["results_path"] = crawl_artifact

        return ResearchStepResult(
            name="native_crawl",
            status="success",
            message=message,
            artifacts=artifacts,
        )

    def _run_backfill_plan(
        self,
        plan: ResearchPlan,
        *,
        enriched_row: dict[str, Any] | None,
    ) -> ResearchStepResult:
        if not plan.backfill_fields:
            return ResearchStepResult(
                name="backfill",
                status="skipped",
                message="Profile does not declare backfillable fields",
            )

        if plan.row is None:
            return ResearchStepResult(
                name="backfill",
                status="skipped",
                message="No dataset row supplied – skipping backfill planning",
            )

        missing = _fields_requiring_backfill(plan.row, plan.backfill_fields)
        if not missing:
            return ResearchStepResult(
                name="backfill",
                status="skipped",
                message="No backfillable fields require action",
            )

        return ResearchStepResult(
            name="backfill",
            status="success",
            message=f"Identified {len(missing)} fields for backfill attempts",
            artifacts={
                "fields": sorted(missing),
                "allow_network": plan.allow_network,
                "enriched_row": enriched_row,
            },
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _write_audit_entry(self, action: str, outcome: ResearchOutcome) -> None:
        try:
            entry = {
                "action": action,
                "timestamp": time.time(),
                "entity": outcome.plan.entity_slug,
                "success": outcome.success,
                "steps": [
                    {"name": step.name, "status": step.status, "message": step.message}
                    for step in outcome.steps
                ],
            }
            with self.audit_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry))
                handle.write("\n")
        except Exception:  # pragma: no cover - audit logging is best effort
            LOGGER.debug("Failed to persist research audit entry", exc_info=True)

    def _persist_crawl_results(self, plan: ResearchPlan, payload: dict[str, Any]) -> str | None:
        try:
            timestamp = datetime.now(UTC)
            directory = self.artefact_root / plan.entity_slug / "crawl"
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
            enriched_payload = {
                "entity": plan.entity_slug,
                "profile": getattr(plan.profile, "name", "unknown"),
                "query": plan.query,
                "target_urls": list(plan.target_urls),
                "recorded_at": timestamp.isoformat(),
            }
            enriched_payload.update(payload)
            path.write_text(json.dumps(enriched_payload, indent=2), encoding="utf-8")
            return str(path)
        except Exception:  # pragma: no cover - best effort persistence
            LOGGER.debug("Failed to persist crawl artefact", exc_info=True)
            return None

    def _persist_outcome(self, outcome: ResearchOutcome) -> None:
        try:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            filename = f"{outcome.plan.entity_slug}-{timestamp}.json"
            path = self.artefact_root / filename
            path.write_text(json.dumps(outcome.to_dict(), indent=2), encoding="utf-8")
            outcome.artifact_path = str(path)
        except Exception:  # pragma: no cover - best effort persistence
            LOGGER.debug("Failed to persist research artefact", exc_info=True)

    def _maybe_throttle(self, rate_limit: RateLimitPolicy | None) -> None:
        if rate_limit is None:
            return

        min_interval = rate_limit.min_interval_seconds
        if min_interval <= 0:
            return

        now = time.monotonic()

        if rate_limit.burst is not None:
            if self._rate_limit_policy is not rate_limit:
                self._rate_limit_policy = rate_limit
                self._burst_tokens = rate_limit.burst
                self._last_network_call = None

            if self._burst_tokens is None:
                self._burst_tokens = rate_limit.burst

            if self._last_network_call is not None:
                elapsed = now - self._last_network_call
                if elapsed >= min_interval:
                    self._burst_tokens = rate_limit.burst

            if self._burst_tokens > 0:
                self._burst_tokens -= 1
                self._last_network_call = time.monotonic()
                return

            wait_for = min_interval
            if self._last_network_call is not None:
                elapsed = now - self._last_network_call
                if elapsed < min_interval:
                    wait_for = min_interval - elapsed
            if wait_for > 0:
                time.sleep(wait_for)
                now = time.monotonic()
            self._burst_tokens = rate_limit.burst - 1 if rate_limit.burst > 0 else 0
            self._last_network_call = now
            return

        if self._last_network_call is not None:
            elapsed = now - self._last_network_call
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
                now = time.monotonic()
        self._last_network_call = now

    @staticmethod
    def _ensure_protocol(url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"https://{url}"


def _filter_blank(values: Iterable[str]) -> Iterable[str]:
    for value in values:
        if value:
            candidate = str(value).strip()
            if candidate:
                yield candidate


def _diff_row(original: pd.Series, enriched: pd.Series) -> dict[str, tuple[Any, Any]]:
    updated: dict[str, tuple[Any, Any]] = {}
    for key, original_value in original.items():
        enriched_value = enriched.get(key)
        if pd.isna(original_value) and pd.isna(enriched_value):
            continue
        if original_value != enriched_value:
            updated[key] = (original_value, enriched_value)
    return updated


def _fields_requiring_backfill(row: pd.Series, fields: Sequence[str]) -> set[str]:
    missing: set[str] = set()
    for field in fields:
        if field not in row:
            continue
        value = row[field]
        if (
            value is None
            or (isinstance(value, float) and pd.isna(value))
            or (isinstance(value, str) and not value.strip())
        ):
            missing.add(field)
    return missing
