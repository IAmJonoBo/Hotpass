from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import pandas as pd

from hotpass.pipeline import (
    PIIRedactionConfig,
    PipelineConfig,
    PipelineExecutionConfig,
    PipelineOrchestrator,
    PipelineResult,
    QualityReport,
)
from hotpass.pipeline.features import (
    EnhancedPipelineConfig,
    FeatureContext,
    PipelineFeatureStrategy,
)


class RecordingMetrics:
    def __init__(self) -> None:
        self.records: list[tuple[str, int]] = []
        self.quality_scores: list[float] = []

    def record_records_processed(self, count: int, source: str = "unknown") -> None:
        self.records.append((source, count))

    def update_quality_score(self, score: float) -> None:
        self.quality_scores.append(score)


@dataclass
class StubFeature(PipelineFeatureStrategy):
    name: str
    enabled: bool = True
    marker: str = "marker"

    def is_enabled(self, context: FeatureContext) -> bool:
        return self.enabled

    def apply(self, result: PipelineResult, context: FeatureContext) -> PipelineResult:
        result.performance_metrics.setdefault("feature_order", []).append(self.name)
        result.refined[self.marker] = self.name
        return result


class StubExecutor:
    def __init__(self, template: PipelineResult, events: tuple[str, ...] = ()) -> None:
        self.template = template
        self.events = events
        self.calls = 0

    def run(self, config: PipelineConfig) -> PipelineResult:  # pragma: no cover - simple helper
        self.calls += 1
        if config.progress_listener:
            for event in self.events:
                config.progress_listener(event, {"event": event})
        return PipelineResult(
            refined=self.template.refined.copy(),
            quality_report=replace(self.template.quality_report),
            performance_metrics=dict(self.template.performance_metrics),
        )


def _base_result() -> PipelineResult:
    frame = pd.DataFrame({"organization_name": ["alpha", "beta"]})
    report = QualityReport(
        total_records=2,
        invalid_records=0,
        schema_validation_errors=[],
        expectations_passed=True,
        expectation_failures=[],
        source_breakdown={},
        data_quality_distribution={"mean": 0.8},
        performance_metrics={},
    )
    return PipelineResult(refined=frame, quality_report=report, performance_metrics={})


def test_orchestrator_base_only_records_metrics(tmp_path):
    metrics = RecordingMetrics()
    events: list[tuple[str, dict[str, Any]]] = []

    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=tmp_path / "refined.xlsx",
        pii_redaction=PIIRedactionConfig(enabled=False),
        progress_listener=lambda name, payload: events.append((name, payload)),
    )
    executor = StubExecutor(_base_result(), events=("pipeline.start", "pipeline.completed"))
    orchestrator = PipelineOrchestrator(base_executor=executor)

    execution = PipelineExecutionConfig(base_config=config, metrics=metrics)
    result = orchestrator.run(execution)

    assert executor.calls == 1
    assert result.quality_report.total_records == 2
    assert metrics.records == [("base_pipeline", 2), ("enhanced_pipeline", 2)]
    assert metrics.quality_scores == [0.8]
    assert [event for event, _ in events] == ["pipeline.start", "pipeline.completed"]


def test_orchestrator_applies_feature_bundle(tmp_path):
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=tmp_path / "refined.xlsx",
        pii_redaction=PIIRedactionConfig(enabled=False),
    )
    executor = StubExecutor(_base_result())
    orchestrator = PipelineOrchestrator(base_executor=executor)

    features = (
        StubFeature(name="entity"),
        StubFeature(name="geospatial", marker="geo"),
    )
    execution = PipelineExecutionConfig(
        base_config=config,
        enhanced_config=EnhancedPipelineConfig(enable_entity_resolution=True),
        features=features,
    )

    result = orchestrator.run(execution)

    assert list(result.performance_metrics["feature_order"]) == ["entity", "geospatial"]
    assert set(result.refined.columns) >= {"marker", "geo"}


def test_orchestrator_skips_disabled_features(tmp_path):
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=tmp_path / "refined.xlsx",
        pii_redaction=PIIRedactionConfig(enabled=False),
    )
    executor = StubExecutor(_base_result())
    orchestrator = PipelineOrchestrator(base_executor=executor)

    features = (
        StubFeature(name="entity", enabled=False, marker="entity"),
        StubFeature(name="enrichment", enabled=True, marker="enriched"),
    )
    execution = PipelineExecutionConfig(
        base_config=config,
        enhanced_config=EnhancedPipelineConfig(enable_enrichment=True),
        features=features,
    )

    result = orchestrator.run(execution)

    assert "feature_order" in result.performance_metrics
    assert result.performance_metrics["feature_order"] == ["enrichment"]
    assert "enriched" in result.refined.columns
    assert "entity" not in result.refined.columns
