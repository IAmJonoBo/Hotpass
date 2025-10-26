"""Intent-driven pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..observability import PipelineMetrics
from .base import BasePipelineExecutor, PipelineConfig, PipelineResult
from .features import (
    ComplianceFeature,
    EnhancedPipelineConfig,
    EnrichmentFeature,
    EntityResolutionFeature,
    FeatureContext,
    GeospatialFeature,
    PipelineFeatureStrategy,
    TraceFactory,
    default_trace_factory,
    ensure_feature_sequence,
)


@dataclass(slots=True)
class PipelineExecutionConfig:
    """Configuration describing how the orchestrator should execute the pipeline."""

    base_config: PipelineConfig
    enhanced_config: EnhancedPipelineConfig = field(default_factory=EnhancedPipelineConfig)
    features: tuple[PipelineFeatureStrategy, ...] = field(default_factory=tuple)
    trace_factory: TraceFactory | None = None
    metrics: PipelineMetrics | None = None

    def with_default_trace_factory(self) -> PipelineExecutionConfig:
        if self.trace_factory is None:
            self.trace_factory = default_trace_factory(self.enhanced_config.enable_observability)
        return self


class PipelineOrchestrator:
    """Coordinate the base pipeline and optional feature strategies."""

    def __init__(self, base_executor: BasePipelineExecutor | None = None):
        self._base_executor = base_executor or BasePipelineExecutor()

    def run(self, execution: PipelineExecutionConfig) -> PipelineResult:
        execution = execution.with_default_trace_factory()
        execution.features = ensure_feature_sequence(execution.features)

        result = self._base_executor.run(execution.base_config)

        if execution.metrics:
            execution.metrics.record_records_processed(len(result.refined), source="base_pipeline")

        if execution.trace_factory is None:
            raise RuntimeError(
                "PipelineExecutionConfig.trace_factory must be set before running the orchestrator."
            )

        context = FeatureContext(
            base_config=execution.base_config,
            enhanced_config=execution.enhanced_config,
            trace_factory=execution.trace_factory,
            metrics=execution.metrics,
        )

        for feature in execution.features:
            if feature.is_enabled(context):
                result = feature.apply(result, context)

        if execution.metrics:
            execution.metrics.record_records_processed(
                len(result.refined), source="enhanced_pipeline"
            )
            if (
                result.quality_report
                and result.quality_report.total_records > 0
                and "mean" in result.quality_report.data_quality_distribution
            ):
                execution.metrics.update_quality_score(
                    result.quality_report.data_quality_distribution.get("mean", 0.0)
                )

        return result


def default_feature_bundle() -> tuple[PipelineFeatureStrategy, ...]:
    """Return the default ordering of enhanced pipeline features."""

    return (
        EntityResolutionFeature(),
        GeospatialFeature(),
        EnrichmentFeature(),
        ComplianceFeature(),
    )
