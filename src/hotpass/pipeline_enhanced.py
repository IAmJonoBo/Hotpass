"""Orchestrates the optional feature set for the enhanced pipeline."""

from __future__ import annotations

import logging

from .observability import get_pipeline_metrics, initialize_observability
from .pipeline.base import PipelineConfig, PipelineResult
from .pipeline.features import EnhancedPipelineConfig
from .pipeline.orchestrator import (
    PipelineExecutionConfig,
    PipelineOrchestrator,
    default_feature_bundle,
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

    if enhanced_config.linkage_output_dir is None:
        enhanced_config.linkage_output_dir = str(config.output_path.parent / "linkage")

    metrics = _initialize_observability(enhanced_config)

    orchestrator = PipelineOrchestrator()
    execution = PipelineExecutionConfig(
        base_config=config,
        enhanced_config=enhanced_config,
        features=default_feature_bundle(),
        metrics=metrics,
    )

    return orchestrator.run(execution)


def _initialize_observability(config: EnhancedPipelineConfig):
    """Initialise observability when requested and return the metrics sink."""

    if not config.enable_observability:
        return None

    attributes = dict(config.telemetry_attributes)
    environment = attributes.get("deployment.environment")
    initialize_observability(
        service_name="hotpass",
        environment=environment,
        exporters=("console",),
        resource_attributes=attributes,
    )
    logger.info("Observability initialized")
    return get_pipeline_metrics()
