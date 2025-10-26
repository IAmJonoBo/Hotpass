"""Orchestrates the optional feature set for the enhanced pipeline."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager

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
from .pipeline_enhancements import (
    EnhancedPipelineConfig,
    apply_compliance,
    apply_enrichment,
    apply_entity_resolution,
    apply_geospatial,
)

logger = logging.getLogger(__name__)


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

    metrics = _initialize_observability(enhanced_config)
    trace_factory = _build_trace_factory(enhanced_config.enable_observability)

    # Run base pipeline
    with trace_operation("base_pipeline") if enhanced_config.enable_observability else _noop():
        result = run_pipeline(config)
        if metrics:
            metrics.record_records_processed(len(result.refined), source="base_pipeline")

    df = result.refined
    df = apply_entity_resolution(df, enhanced_config, trace_factory)
    df = apply_geospatial(df, enhanced_config, trace_factory)
    df = apply_enrichment(df, enhanced_config, trace_factory)
    df, compliance_report = apply_compliance(df, enhanced_config, trace_factory)
    if compliance_report is not None:
        result.compliance_report = compliance_report

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
        with trace_operation("geospatial") if enhanced_config.enable_observability else _noop():
            logger.info("Running geospatial enrichment...")
            try:
                # Normalize addresses first
                if "address_primary" in df.columns:
                    df["address_primary"] = df["address_primary"].apply(normalize_address)

                # Geocode addresses
                df = geocode_dataframe(
                    df, address_column="address_primary", country_column="country"
                )
                logger.info("Geospatial enrichment complete")
            except Exception as e:
                logger.error(f"Geospatial enrichment failed: {e}")

    # External Data Enrichment
    if enhanced_config.enable_enrichment and enhanced_config.enrich_websites:
        with trace_operation("enrichment") if enhanced_config.enable_observability else _noop():
            logger.info("Running external data enrichment...")
            try:
                cache = CacheManager(db_path=enhanced_config.cache_path)

                # Enrich from websites
                if "website" in df.columns:
                    df = enrich_dataframe_with_websites(df, website_column="website", cache=cache)
                logger.info("External enrichment complete")

                # Log cache stats
                stats = cache.stats()
                logger.info(f"Cache stats: {stats}")
            except Exception as e:
                logger.error(f"External enrichment failed: {e}")

    # Compliance and PII Detection
    if enhanced_config.enable_compliance:
        with trace_operation("compliance") if enhanced_config.enable_observability else _noop():
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

    if metrics:
        metrics.record_records_processed(len(df), source="enhanced_pipeline")
        if result.quality_report and result.quality_report.total_records > 0:
            # Calculate quality score from data quality distribution
            quality_score = result.quality_report.data_quality_distribution.get("mean", 0.0)
            metrics.update_quality_score(quality_score)

    return result


def _initialize_observability(config: EnhancedPipelineConfig):
    """Initialise observability when requested and return the metrics sink."""

    if not config.enable_observability:
        return None

    initialize_observability(service_name="hotpass", export_to_console=True)
    logger.info("Observability initialized")
    return get_pipeline_metrics()


def _build_trace_factory(
    enabled: bool,
) -> Callable[[str], AbstractContextManager[object]]:
    """Return a helper that wraps operations in observability spans when enabled."""

    if not enabled:
        return lambda _name: _noop()

    def _factory(operation: str) -> AbstractContextManager[object]:
        return trace_operation(operation)

    return _factory


class _noop:
    """No-op context manager for when observability is disabled."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
