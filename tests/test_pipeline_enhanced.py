from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

pytest.importorskip("frictionless")

import hotpass.pipeline_enhanced as pipeline_enhanced
from hotpass.pipeline import (
    PIIRedactionConfig,
    PipelineConfig,
    PipelineExecutionConfig,
    PipelineOrchestrator,
    PipelineResult,
    QualityReport,
    default_feature_bundle,
)
from hotpass.pipeline.features import EnhancedPipelineConfig
from hotpass.pipeline_enhanced import _initialize_observability, run_enhanced_pipeline


@pytest.fixture(autouse=True)
def reset_observability(monkeypatch):
    """Ensure observability state resets between tests."""

    import hotpass.observability as observability

    monkeypatch.setattr(observability, "_instrumentation_initialized", False, raising=False)
    monkeypatch.setattr(observability, "_pipeline_metrics", None, raising=False)


@pytest.fixture
def base_pipeline_config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        input_dir=tmp_path,
        output_path=tmp_path / "refined.xlsx",
        pii_redaction=PIIRedactionConfig(enabled=False),
    )


@pytest.fixture
def sample_result() -> PipelineResult:
    frame = pd.DataFrame({"organization_name": ["Alpha"]})
    report = QualityReport(
        total_records=1,
        invalid_records=0,
        schema_validation_errors=[],
        expectations_passed=True,
        expectation_failures=[],
        source_breakdown={},
        data_quality_distribution={"mean": 1.0},
        performance_metrics={},
    )
    return PipelineResult(refined=frame, quality_report=report, performance_metrics={})


def test_enhanced_pipeline_config_defaults():
    config = EnhancedPipelineConfig()

    assert not config.enable_entity_resolution
    assert not config.enable_geospatial
    assert not config.enable_enrichment
    assert not config.enable_compliance
    assert not config.enable_observability
    assert config.entity_resolution_threshold == 0.75
    assert config.enrichment_concurrency == 8


def test_initialize_observability_disabled_returns_none(monkeypatch):
    config = EnhancedPipelineConfig(enable_observability=False)
    called = False

    def _guard(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(pipeline_enhanced, "initialize_observability", _guard)

    assert _initialize_observability(config) is None
    assert called is False


def test_initialize_observability_enabled_invokes_dependencies(monkeypatch):
    config = EnhancedPipelineConfig(
        enable_observability=True,
        telemetry_attributes={"deployment.environment": "qa", "hotpass.profile": "aviation"},
    )
    metrics_mock = Mock()
    captured_kwargs: dict[str, object] | None = None

    def _fake_initialize(*_args, **kwargs):
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    monkeypatch.setattr(pipeline_enhanced, "initialize_observability", _fake_initialize)
    monkeypatch.setattr(pipeline_enhanced, "get_pipeline_metrics", lambda: metrics_mock)

    assert _initialize_observability(config) is metrics_mock
    assert captured_kwargs == {
        "service_name": "hotpass",
        "environment": "qa",
        "exporters": ("console",),
        "resource_attributes": {"deployment.environment": "qa", "hotpass.profile": "aviation"},
    }


def test_run_enhanced_pipeline_uses_orchestrator(monkeypatch, base_pipeline_config, sample_result):
    orchestrator_mock = Mock(spec=PipelineOrchestrator)
    orchestrator_mock.run.return_value = sample_result
    monkeypatch.setattr(pipeline_enhanced, "PipelineOrchestrator", lambda: orchestrator_mock)
    monkeypatch.setattr(pipeline_enhanced, "_initialize_observability", lambda *_: None)

    enhanced_config = EnhancedPipelineConfig(enable_entity_resolution=True)
    result = run_enhanced_pipeline(base_pipeline_config, enhanced_config)

    assert result is sample_result
    orchestrator_mock.run.assert_called_once()
    (execution_config,) = orchestrator_mock.run.call_args.args
    assert isinstance(execution_config, PipelineExecutionConfig)
    assert execution_config.base_config is base_pipeline_config
    assert execution_config.enhanced_config is enhanced_config
    assert execution_config.features == default_feature_bundle()


def test_run_enhanced_pipeline_sets_default_linkage_dir(monkeypatch, tmp_path, sample_result):
    orchestrator_mock = Mock(spec=PipelineOrchestrator)
    orchestrator_mock.run.return_value = sample_result
    monkeypatch.setattr(pipeline_enhanced, "PipelineOrchestrator", lambda: orchestrator_mock)
    monkeypatch.setattr(pipeline_enhanced, "_initialize_observability", lambda *_: None)

    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=tmp_path / "refined.xlsx",
        pii_redaction=PIIRedactionConfig(enabled=False),
    )
    enhanced_config = EnhancedPipelineConfig(linkage_output_dir=None)

    run_enhanced_pipeline(config, enhanced_config)

    (execution_config,) = orchestrator_mock.run.call_args.args
    assert execution_config.enhanced_config.linkage_output_dir == str(
        config.output_path.parent / "linkage"
    )


def test_run_enhanced_pipeline_initializes_observability(monkeypatch, base_pipeline_config):
    metrics_mock = Mock()
    orchestrator_mock = Mock(spec=PipelineOrchestrator)
    orchestrator_mock.run.return_value = Mock(spec=PipelineResult)
    monkeypatch.setattr(pipeline_enhanced, "PipelineOrchestrator", lambda: orchestrator_mock)
    monkeypatch.setattr(
        pipeline_enhanced,
        "_initialize_observability",
        lambda config: metrics_mock if config.enable_observability else None,
    )

    enhanced_config = EnhancedPipelineConfig(enable_observability=True)
    run_enhanced_pipeline(base_pipeline_config, enhanced_config)

    (execution_config,) = orchestrator_mock.run.call_args.args
    assert execution_config.metrics is metrics_mock
