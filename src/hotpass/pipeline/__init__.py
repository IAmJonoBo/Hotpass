"""Public pipeline API backed by the intent-driven orchestrator."""

from __future__ import annotations

from ..compliance import PIIRedactionConfig
from ..quality import build_ssot_schema as _default_build_ssot_schema
from .base import (
    PIPELINE_EVENT_AGGREGATE_COMPLETED,
    PIPELINE_EVENT_AGGREGATE_PROGRESS,
    PIPELINE_EVENT_AGGREGATE_STARTED,
    PIPELINE_EVENT_COMPLETED,
    PIPELINE_EVENT_EXPECTATIONS_COMPLETED,
    PIPELINE_EVENT_EXPECTATIONS_STARTED,
    PIPELINE_EVENT_LOAD_COMPLETED,
    PIPELINE_EVENT_LOAD_STARTED,
    PIPELINE_EVENT_SCHEMA_COMPLETED,
    PIPELINE_EVENT_SCHEMA_STARTED,
    PIPELINE_EVENT_START,
    PIPELINE_EVENT_WRITE_COMPLETED,
    PIPELINE_EVENT_WRITE_STARTED,
    SSOT_COLUMNS,
    PipelineConfig,
    PipelineResult,
    QualityReport,
    _aggregate_group,
)
from .features import EnhancedPipelineConfig
from .orchestrator import (
    PipelineExecutionConfig,
    PipelineOrchestrator,
    default_feature_bundle,
)


def build_ssot_schema():
    """Return the default SSOT schema descriptor."""

    return _default_build_ssot_schema()


__all__ = [
    "PIIRedactionConfig",
    "PipelineConfig",
    "QualityReport",
    "PipelineResult",
    "PipelineExecutionConfig",
    "PipelineOrchestrator",
    "EnhancedPipelineConfig",
    "default_feature_bundle",
    "PIPELINE_EVENT_START",
    "PIPELINE_EVENT_LOAD_STARTED",
    "PIPELINE_EVENT_LOAD_COMPLETED",
    "PIPELINE_EVENT_AGGREGATE_STARTED",
    "PIPELINE_EVENT_AGGREGATE_PROGRESS",
    "PIPELINE_EVENT_AGGREGATE_COMPLETED",
    "PIPELINE_EVENT_SCHEMA_STARTED",
    "PIPELINE_EVENT_SCHEMA_COMPLETED",
    "PIPELINE_EVENT_EXPECTATIONS_STARTED",
    "PIPELINE_EVENT_EXPECTATIONS_COMPLETED",
    "PIPELINE_EVENT_WRITE_STARTED",
    "PIPELINE_EVENT_WRITE_COMPLETED",
    "PIPELINE_EVENT_COMPLETED",
    "SSOT_COLUMNS",
    "_aggregate_group",
    "build_ssot_schema",
    "run_pipeline",
]


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Execute the base pipeline using the shared orchestrator."""

    orchestrator = PipelineOrchestrator()
    execution = PipelineExecutionConfig(base_config=config)
    return orchestrator.run(execution)
