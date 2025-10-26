"""Enhanced pipeline with full integration of all features.

This module extends the base pipeline with:
- Entity resolution
- Geospatial enrichment
- External data enrichment
- Compliance tracking
- Observability integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .compliance import POPIAPolicy, add_provenance_columns, detect_pii_in_dataframe
from .enrichment import CacheManager, enrich_dataframe_with_websites
from .entity_resolution import add_ml_priority_scores, resolve_entities_fallback
from .geospatial import geocode_dataframe, normalize_address
from .observability import (
    get_pipeline_metrics,
    initialize_observability,
    trace_operation,
)
from .pipeline import PipelineConfig, PipelineResult, run_pipeline

logger = logging.getLogger(__name__)


@dataclass
class EnhancedPipelineConfig:
    """Configuration for enhanced pipeline features."""

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


def run_enhanced_pipeline(
    config: PipelineConfig,
    enhanced_config: EnhancedPipelineConfig | None = None,
) -> PipelineResult:
    """Run the enhanced pipeline with all features enabled.

    Args:
        config: Base pipeline configuration
        enhanced_config: Enhanced feature configuration

    Returns:
        Pipeline result with enhanced features applied
    """
    if enhanced_config is None:
        enhanced_config = EnhancedPipelineConfig()

    # Initialize observability if enabled
    if enhanced_config.enable_observability:
        initialize_observability(service_name="hotpass", export_to_console=True)
        metrics = get_pipeline_metrics()
        logger.info("Observability initialized")
    else:
        metrics = None

    # Run base pipeline
    with (
        trace_operation("base_pipeline")
        if enhanced_config.enable_observability
        else _noop()
    ):
        result = run_pipeline(config)
        if metrics:
            metrics.record_records_processed(
                len(result.refined), source="base_pipeline"
            )

    df = result.refined

    # Entity Resolution
    if enhanced_config.enable_entity_resolution:
        with (
            trace_operation("entity_resolution")
            if enhanced_config.enable_observability
            else _noop()
        ):
            logger.info("Running entity resolution...")
            try:
                if enhanced_config.use_splink:
                    try:
                        from .entity_resolution import resolve_entities_with_splink
                    except ImportError as import_err:
                        logger.warning(
                            f"Splink import failed, falling back to rule-based: {import_err}"
                        )
                        df, _ = resolve_entities_fallback(
                            df, enhanced_config.entity_resolution_threshold
                        )
                    else:
                        df, _ = resolve_entities_with_splink(
                            df, enhanced_config.entity_resolution_threshold
                        )
                else:
                    df, _ = resolve_entities_fallback(
                        df, enhanced_config.entity_resolution_threshold
                    )

                # Add ML priority scores
                df = add_ml_priority_scores(df)
                logger.info(f"Entity resolution complete: {len(df)} unique entities")
            except Exception as e:
                logger.error(f"Entity resolution failed: {e}")

    # Geospatial Enrichment
    if enhanced_config.enable_geospatial and enhanced_config.geocode_addresses:
        with (
            trace_operation("geospatial")
            if enhanced_config.enable_observability
            else _noop()
        ):
            logger.info("Running geospatial enrichment...")
            try:
                # Normalize addresses first
                if "address_primary" in df.columns:
                    df["address_primary"] = df["address_primary"].apply(
                        normalize_address
                    )

                # Geocode addresses
                df = geocode_dataframe(
                    df, address_column="address_primary", country_column="country"
                )
                logger.info("Geospatial enrichment complete")
            except Exception as e:
                logger.error(f"Geospatial enrichment failed: {e}")

    # External Data Enrichment
    if enhanced_config.enable_enrichment and enhanced_config.enrich_websites:
        with (
            trace_operation("enrichment")
            if enhanced_config.enable_observability
            else _noop()
        ):
            logger.info("Running external data enrichment...")
            try:
                cache = CacheManager(db_path=enhanced_config.cache_path)

                # Enrich from websites
                if "website" in df.columns:
                    df = enrich_dataframe_with_websites(
                        df, website_column="website", cache=cache
                    )
                logger.info("External enrichment complete")

                # Log cache stats
                stats = cache.stats()
                logger.info(f"Cache stats: {stats}")
            except Exception as e:
                logger.error(f"External enrichment failed: {e}")

    # Compliance and PII Detection
    if enhanced_config.enable_compliance:
        with (
            trace_operation("compliance")
            if enhanced_config.enable_observability
            else _noop()
        ):
            logger.info("Running compliance checks...")
            try:
                # Add provenance tracking
                df = add_provenance_columns(df, source_name="hotpass_pipeline")

                # Detect PII if enabled
                if enhanced_config.detect_pii:
                    pii_columns = [
                        "contact_primary_email",
                        "contact_primary_phone",
                        "contact_primary_name",
                    ]
                    df = detect_pii_in_dataframe(df, columns=pii_columns, threshold=0.5)

                # Generate compliance report
                policy = POPIAPolicy()
                compliance_report = policy.generate_compliance_report(df)
                logger.info(f"Compliance report generated: {compliance_report}")
            except Exception as e:
                logger.error(f"Compliance checks failed: {e}")

    # Update result with enhanced dataframe
    result.refined = df

    # Record final metrics
    if metrics:
        metrics.record_records_processed(len(df), source="enhanced_pipeline")
        if result.quality_report and result.quality_report.total_records > 0:
            # Calculate quality score from data quality distribution
            quality_score = result.quality_report.data_quality_distribution.get(
                "mean", 0.0
            )
            metrics.update_quality_score(quality_score)

    return result


class _noop:
    """No-op context manager for when observability is disabled."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
