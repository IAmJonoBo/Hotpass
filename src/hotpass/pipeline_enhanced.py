"""Orchestrates the optional feature set for the enhanced pipeline."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager

from .observability import get_pipeline_metrics, initialize_observability, trace_operation
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

    with trace_factory("base_pipeline"):
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

    result.refined = df

    if metrics:
        metrics.record_records_processed(len(df), source="enhanced_pipeline")
        if result.quality_report and result.quality_report.total_records > 0:
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
