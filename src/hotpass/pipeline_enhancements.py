"""Building blocks used by the enhanced pipeline."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pandas import DataFrame

from .compliance import (
    ConsentValidationError,
    POPIAPolicy,
    add_provenance_columns,
    detect_pii_in_dataframe,
)
from .enrichment import (
    CacheManager,
    enrich_dataframe_with_websites,
    enrich_dataframe_with_websites_concurrent,
)
from .entity_resolution import add_ml_priority_scores, resolve_entities_fallback
from .linkage import LinkageConfig, LinkageThresholds, link_entities

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .linkage import LinkageResult
from .geospatial import geocode_dataframe, normalize_address

logger = logging.getLogger(__name__)

TraceFactory = Callable[[str], AbstractContextManager[object]]


@dataclass
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


def apply_entity_resolution(
    df: DataFrame, config: EnhancedPipelineConfig, trace_factory: TraceFactory
) -> tuple[DataFrame, LinkageResult | None]:
    """Resolve duplicate entities and add ML priority scores when enabled."""

    if not config.enable_entity_resolution:
        return df, None

    linkage_result = None
    with trace_factory("entity_resolution"):
        logger.info("Running entity resolution...")
        try:
            match_threshold = config.linkage_match_threshold or max(
                0.9, config.entity_resolution_threshold
            )
            high_value = max(match_threshold, config.entity_resolution_threshold)
            thresholds = LinkageThresholds(
                high=high_value,
                review=config.entity_resolution_threshold,
            )
            base_linkage_config = config.linkage_config or LinkageConfig()
            root_dir = (
                Path(config.linkage_output_dir)
                if config.linkage_output_dir
                else base_linkage_config.persistence.root_dir
            )
            configured = base_linkage_config.with_output_root(root_dir)
            configured.use_splink = config.use_splink
            configured.thresholds = thresholds

            linkage_result = link_entities(df, configured)
            df = linkage_result.deduplicated
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Entity resolution failed: %s", exc)
            df, _ = resolve_entities_fallback(df, config.entity_resolution_threshold)
            linkage_result = None

        df = add_ml_priority_scores(df)
        logger.info("Entity resolution complete: %s unique entities", len(df))

    return df, linkage_result


def apply_geospatial(
    df: DataFrame, config: EnhancedPipelineConfig, trace_factory: TraceFactory
) -> DataFrame:
    """Normalise and geocode addresses when geospatial enrichment is enabled."""

    if not (config.enable_geospatial and config.geocode_addresses):
        return df

    with trace_factory("geospatial"):
        logger.info("Running geospatial enrichment...")
        try:
            if "address_primary" in df.columns:
                df["address_primary"] = df["address_primary"].apply(normalize_address)

            df = geocode_dataframe(df, address_column="address_primary", country_column="country")
            logger.info("Geospatial enrichment complete")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Geospatial enrichment failed: %s", exc)
    return df


def apply_enrichment(
    df: DataFrame, config: EnhancedPipelineConfig, trace_factory: TraceFactory
) -> DataFrame:
    """Enrich organisations with external data when enabled."""

    if not (config.enable_enrichment and config.enrich_websites):
        return df

    with trace_factory("enrichment"):
        logger.info("Running external data enrichment...")
        try:
            cache = CacheManager(db_path=config.cache_path)
            if "website" in df.columns:
                concurrency = max(1, config.enrichment_concurrency)
                if concurrency > 1 and len(df) > 1:
                    df = enrich_dataframe_with_websites_concurrent(
                        df,
                        website_column="website",
                        cache=cache,
                        concurrency=concurrency,
                    )
                else:
                    df = enrich_dataframe_with_websites(
                        df,
                        website_column="website",
                        cache=cache,
                    )
            logger.info("External enrichment complete")
            stats = cache.stats()
            logger.info("Cache stats: %s", stats)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("External enrichment failed: %s", exc)
    return df


def apply_compliance(
    df: DataFrame, config: EnhancedPipelineConfig, trace_factory: TraceFactory
) -> tuple[DataFrame, dict[str, Any] | None]:
    """Run POPIA compliance checks when configured."""

    if not config.enable_compliance:
        return df, None

    with trace_factory("compliance"):
        logger.info("Running compliance checks...")
        policy = POPIAPolicy()
        try:
            df = add_provenance_columns(df, source_name="hotpass_pipeline")

            if config.consent_overrides:
                _apply_consent_overrides(df, policy.consent_status_field, config.consent_overrides)

            if config.detect_pii:
                pii_columns = [
                    "contact_primary_email",
                    "contact_primary_phone",
                    "contact_primary_name",
                ]
                df = detect_pii_in_dataframe(df, columns=pii_columns, threshold=0.5)

            compliance_report = policy.generate_compliance_report(df)
            policy.enforce_consent(compliance_report)
            logger.info("Compliance report generated: %s", compliance_report)
            return df, compliance_report
        except ConsentValidationError as consent_error:
            logger.error("Consent validation failed: %s", consent_error)
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Compliance checks failed: %s", exc)
    return df, None


def _apply_consent_overrides(
    df: DataFrame, consent_field: str, overrides: Mapping[str, str]
) -> None:
    """Apply configured consent overrides to the dataframe in-place."""

    for idx, row in df.iterrows():
        slug = row.get("organization_slug")
        name = row.get("organization_name")
        status: str | None = None
        if slug and slug in overrides:
            status = overrides[slug]
        elif name and name in overrides:
            status = overrides[name]

        if status:
            df.at[idx, consent_field] = status
