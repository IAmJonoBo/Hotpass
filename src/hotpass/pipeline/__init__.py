"""Public pipeline API backed by the intent-driven orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..config_schema import HotpassConfig


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


def run_pipeline(config: PipelineConfig | HotpassConfig) -> PipelineResult:
    """Execute the pipeline from either a legacy dataclass or canonical config."""

    orchestrator = PipelineOrchestrator()

    if not isinstance(config, PipelineConfig):
        from ..config_schema import HotpassConfig  # Local import to avoid circular dependency

        if isinstance(config, HotpassConfig):
            execution = PipelineExecutionConfig(
                base_config=config.to_pipeline_config(),
                enhanced_config=config.to_enhanced_config(),
                features=default_feature_bundle(),
            )
            return orchestrator.run(execution)
        msg = f"Unsupported configuration type: {type(config)!r}"
        raise TypeError(msg)

    execution = PipelineExecutionConfig(base_config=config)
    return orchestrator.run(execution)
