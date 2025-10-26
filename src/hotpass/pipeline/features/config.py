"""Configuration objects for pipeline feature orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ...linkage import LinkageConfig


@dataclass(slots=True)
class EnhancedPipelineConfig:
    """Configuration for optional enhanced pipeline features."""

    enable_entity_resolution: bool = False
    enable_geospatial: bool = False
    enable_enrichment: bool = False
    enable_compliance: bool = False
    enable_observability: bool = False
    entity_resolution_threshold: float = 0.75
    use_splink: bool = False
    geocode_addresses: bool = False
    enrich_websites: bool = False
    detect_pii: bool = False
    cache_path: str = "data/.cache/enrichment.db"
    consent_overrides: Mapping[str, str] | None = None
    enrichment_concurrency: int = 8
    linkage_config: LinkageConfig | None = None
    linkage_output_dir: str | None = None
    linkage_match_threshold: float | None = None
    telemetry_attributes: Mapping[str, str] = field(default_factory=dict)
