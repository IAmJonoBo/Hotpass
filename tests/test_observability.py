"""Tests for OpenTelemetry observability module."""

import pytest

pytest.importorskip(
    "opentelemetry",
    reason="OpenTelemetry dependencies are required for observability instrumentation.",
)

from hotpass.observability import (
    PipelineMetrics,
    get_meter,
    get_pipeline_metrics,
    get_tracer,
    initialize_observability,
    trace_operation,
)


def test_initialize_observability():
    """Test observability initialization."""
    tracer, meter = initialize_observability(
        service_name="test-service",
        environment="test",
        export_to_console=False,
    )

    assert tracer is not None
    assert meter is not None


def test_get_tracer():
    """Test getting a tracer instance."""
    tracer = get_tracer("test-tracer")
    assert tracer is not None


def test_get_meter():
    """Test getting a meter instance."""
    meter = get_meter("test-meter")
    assert meter is not None


def test_trace_operation_success():
    """Test tracing a successful operation."""
    with trace_operation("test-operation", {"key": "value"}) as span:
        assert span is not None
        # Operation succeeds
        result = 42

    assert result == 42


def test_trace_operation_with_exception():
    """Test tracing an operation that raises an exception."""
    with pytest.raises(ValueError):
        with trace_operation("failing-operation"):
            raise ValueError("Test error")


def test_pipeline_metrics_creation():
    """Test creating pipeline metrics."""
    metrics = PipelineMetrics()

    assert metrics.records_processed is not None
    assert metrics.validation_failures is not None
    assert metrics.load_duration is not None
    assert metrics.aggregation_duration is not None
    assert metrics.validation_duration is not None
    assert metrics.write_duration is not None


def test_pipeline_metrics_record_operations():
    """Test recording various metrics."""
    metrics = PipelineMetrics()

    # These should not raise exceptions
    metrics.record_records_processed(100, "test-source")
    metrics.record_validation_failure("test-rule")
    metrics.record_load_duration(1.5, "test-source")
    metrics.record_aggregation_duration(2.3)
    metrics.record_validation_duration(0.8)
    metrics.record_write_duration(1.2)
    metrics.update_quality_score(0.95)

    assert metrics._latest_quality_score == 0.95


def test_get_pipeline_metrics_singleton():
    """Test that pipeline metrics is a singleton."""
    metrics1 = get_pipeline_metrics()
    metrics2 = get_pipeline_metrics()

    assert metrics1 is metrics2


def test_pipeline_metrics_quality_score_callback():
    """Test quality score gauge callback."""
    metrics = PipelineMetrics()
    metrics.update_quality_score(0.85)

    observations = metrics._get_quality_score(None)
    assert len(observations) == 1
    assert observations[0].value == 0.85
