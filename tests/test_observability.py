"""Tests for OpenTelemetry observability module."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Literal

import pytest

import hotpass.observability as observability
from hotpass.observability import (
    PipelineMetrics,
    get_meter,
    get_pipeline_metrics,
    get_tracer,
    initialize_observability,
    shutdown_observability,
    trace_operation,
)


@pytest.fixture(autouse=True)
def reset_observability_globals(monkeypatch):
    """Reset module-level state between tests."""

    monkeypatch.setattr(observability, "_instrumentation_initialized", False, raising=False)
    monkeypatch.setattr(observability, "_pipeline_metrics", None, raising=False)
    monkeypatch.setattr(observability, "_meter_provider", None, raising=False)
    monkeypatch.setattr(observability, "_metric_reader", None, raising=False)
    monkeypatch.setattr(observability, "_trace_provider", None, raising=False)
    monkeypatch.setattr(observability, "_shutdown_registered", False, raising=False)
    monkeypatch.setattr(
        observability,
        "atexit",
        SimpleNamespace(register=lambda fn: fn),
        raising=False,
    )


@pytest.fixture
def instrumentation_stubs(monkeypatch):
    """Patch observability dependencies with lightweight stubs."""

    class DummyObservation:
        def __init__(self, value: float):
            self.value = value

    class DummyInstrument:
        def __init__(self) -> None:
            self.calls: list[tuple[str, float, dict[str, object]]] = []

        def add(self, value: float, attributes: dict[str, object] | None = None) -> None:
            self.calls.append(("add", value, attributes or {}))

        def record(self, value: float, attributes: dict[str, object] | None = None) -> None:
            self.calls.append(("record", value, attributes or {}))

    class DummyObservableGauge:
        def __init__(self, callbacks: list | None = None) -> None:
            self.callbacks = list(callbacks or [])

    class DummyMeter:
        def __init__(self) -> None:
            self.created: dict[str, object] = {}

        def create_counter(self, name: str, **_: object) -> DummyInstrument:
            instrument = DummyInstrument()
            self.created[name] = instrument
            return instrument

        def create_histogram(self, name: str, **_: object) -> DummyInstrument:
            instrument = DummyInstrument()
            self.created[name] = instrument
            return instrument

        def create_observable_gauge(
            self,
            name: str,
            callbacks: list | None = None,
            **_: object,
        ) -> DummyObservableGauge:
            gauge = DummyObservableGauge(callbacks=list(callbacks or []))
            self.created[name] = gauge
            return gauge

    class DummyMetricsModule:
        Observation = DummyObservation

        def __init__(self) -> None:
            self.provider: object | None = None
            self.meter = DummyMeter()

        def get_meter(self, *_: object, **__: object) -> DummyMeter:
            return self.meter

        def set_meter_provider(self, provider: object) -> None:
            self.provider = provider

    class DummySpan:
        def __init__(self, name: str) -> None:
            self.name = name
            self.attributes: dict[str, object] = {}
            self.exceptions: list[Exception] = []
            self.status: object | None = None

        def set_attribute(self, key: str, value: object) -> None:
            self.attributes[key] = value

        def record_exception(self, exc: Exception) -> None:
            self.exceptions.append(exc)

        def set_status(self, status: object) -> None:
            self.status = status

    class DummySpanContext:
        def __init__(self, span: DummySpan) -> None:
            self._span = span

        def __enter__(self) -> DummySpan:
            return self._span

        def __exit__(
            self,
            exc_type: object,
            exc: object,
            tb: object,
        ) -> Literal[False]:
            return False

    class DummyTracer:
        def __init__(self) -> None:
            self.spans: list[DummySpan] = []

        def start_as_current_span(self, name: str) -> DummySpanContext:
            span = DummySpan(name)
            self.spans.append(span)
            return DummySpanContext(span)

    class DummyTraceModule:
        StatusCode = SimpleNamespace(ERROR="ERROR")

        def __init__(self) -> None:
            self.provider: object | None = None
            self.tracer = DummyTracer()

        def get_tracer(self, *_: object, **__: object) -> DummyTracer:
            return self.tracer

        def set_tracer_provider(self, provider: object) -> None:
            self.provider = provider

        def Status(self, code: object, description: str) -> dict[str, object]:
            return {"code": code, "description": description}

    class DummyMetricReader:
        instances: list[DummyMetricReader] = []

        def __init__(self, exporter: object, export_interval_millis: int = 60000) -> None:
            self.exporter = exporter
            self.export_interval_millis = export_interval_millis
            self.shutdown_called = False
            self.instances.append(self)

        def shutdown(self) -> None:
            self.shutdown_called = True

    class DummyMeterProvider:
        instances: list[DummyMeterProvider] = []

        def __init__(
            self,
            *_: object,
            metric_readers: list[object] | None = None,
            resource: object | None = None,
        ) -> None:
            self.metric_readers = list(metric_readers or [])
            self.resource = resource
            self.shutdown_called = False
            self.instances.append(self)

        def shutdown(self) -> None:
            self.shutdown_called = True

    class DummyTracerProvider:
        instances: list[DummyTracerProvider] = []

        def __init__(self, *_: object, resource: object | None = None) -> None:
            self.resource = resource
            self.processors: list[object] = []
            self.shutdown_called = False
            self.instances.append(self)

        def add_span_processor(self, processor: object) -> None:
            self.processors.append(processor)

        def shutdown(self) -> None:
            self.shutdown_called = True

    class DummyBatchSpanProcessor:
        instances: list[DummyBatchSpanProcessor] = []

        def __init__(self, exporter: object) -> None:
            self.exporter = exporter
            self.shutdown_called = False
            self.instances.append(self)

        def shutdown(self) -> None:
            self.shutdown_called = True

    class DummyConsoleSpanExporter:
        instances: list[DummyConsoleSpanExporter] = []

        def __init__(self) -> None:
            self.instances.append(self)

    class DummySafeConsoleSpanExporter:
        instances: list[DummySafeConsoleSpanExporter] = []

        def __init__(self) -> None:
            self.instances.append(self)

        def export(self, spans: object) -> object:
            return spans

    class DummyResource:
        last_attributes: dict[str, object] | None = None

        @staticmethod
        def create(attributes: dict[str, object]) -> dict[str, object]:
            DummyResource.last_attributes = attributes
            return attributes

    metrics_module = DummyMetricsModule()
    trace_module = DummyTraceModule()

    DummyMetricReader.instances = []
    DummyMeterProvider.instances = []
    DummyTracerProvider.instances = []
    DummyBatchSpanProcessor.instances = []
    DummyConsoleSpanExporter.instances = []
    DummySafeConsoleSpanExporter.instances = []
    DummyResource.last_attributes = None

    monkeypatch.setattr(observability, "metrics", metrics_module, raising=False)
    monkeypatch.setattr(observability, "trace", trace_module, raising=False)
    monkeypatch.setattr(observability, "MeterProvider", DummyMeterProvider, raising=False)
    monkeypatch.setattr(
        observability,
        "PeriodicExportingMetricReader",
        DummyMetricReader,
        raising=False,
    )
    monkeypatch.setattr(observability, "TracerProvider", DummyTracerProvider, raising=False)
    monkeypatch.setattr(observability, "BatchSpanProcessor", DummyBatchSpanProcessor, raising=False)
    monkeypatch.setattr(
        observability,
        "ConsoleSpanExporter",
        DummyConsoleSpanExporter,
        raising=False,
    )
    monkeypatch.setattr(
        observability,
        "_SafeConsoleSpanExporter",
        DummySafeConsoleSpanExporter,
        raising=False,
    )
    monkeypatch.setattr(observability, "Resource", DummyResource, raising=False)
    monkeypatch.setattr(observability, "OBSERVABILITY_AVAILABLE", True, raising=False)

    return SimpleNamespace(
        metrics_module=metrics_module,
        trace_module=trace_module,
        metric_reader_cls=DummyMetricReader,
        meter_provider_cls=DummyMeterProvider,
        tracer_provider_cls=DummyTracerProvider,
        batch_processor_cls=DummyBatchSpanProcessor,
        console_span_exporter_cls=DummyConsoleSpanExporter,
        safe_console_span_exporter_cls=DummySafeConsoleSpanExporter,
        resource_cls=DummyResource,
    )


def test_initialize_observability(instrumentation_stubs):
    """Instrumentation should be configured with console exporters when requested."""

    tracer, meter = initialize_observability(
        service_name="test-service",
        environment="test",
        export_to_console=True,
    )

    assert tracer is instrumentation_stubs.trace_module.tracer
    assert meter is instrumentation_stubs.metrics_module.meter
    assert (
        instrumentation_stubs.metrics_module.provider
        is instrumentation_stubs.meter_provider_cls.instances[0]
    )
    assert (
        instrumentation_stubs.trace_module.provider
        is instrumentation_stubs.tracer_provider_cls.instances[0]
    )
    assert instrumentation_stubs.metric_reader_cls.instances[0].exporter is not None
    assert instrumentation_stubs.batch_processor_cls.instances[0].exporter is not None
    assert instrumentation_stubs.safe_console_span_exporter_cls.instances
    assert instrumentation_stubs.resource_cls.last_attributes == {
        "service.name": "test-service",
        "service.version": "0.1.0",
        "deployment.environment": "test",
    }


def test_initialize_observability_idempotent(instrumentation_stubs):
    """Calling initialize more than once should reuse existing instrumentation."""

    first_tracer, first_meter = initialize_observability(export_to_console=True)
    initial_reader_count = len(instrumentation_stubs.metric_reader_cls.instances)

    tracer, meter = initialize_observability(export_to_console=True)

    assert tracer is first_tracer
    assert meter is first_meter
    assert len(instrumentation_stubs.metric_reader_cls.instances) == initial_reader_count


def test_shutdown_observability(instrumentation_stubs):
    """Shutdown should invoke component-specific teardown hooks."""

    initialize_observability(export_to_console=True)
    reader = instrumentation_stubs.metric_reader_cls.instances[0]
    meter_provider = instrumentation_stubs.meter_provider_cls.instances[0]
    tracer_provider = instrumentation_stubs.tracer_provider_cls.instances[0]

    shutdown_observability()

    assert reader.shutdown_called is True
    assert meter_provider.shutdown_called is True
    assert tracer_provider.shutdown_called is True
    assert observability._instrumentation_initialized is False


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


def test_safe_console_exporter_swallows_value_error(monkeypatch):
    """Console exporter should ignore ValueError emitted during shutdown."""

    calls: list[tuple[object, float]] = []

    def failing_export(self, metrics_data, timeout_millis: float = 1000.0, **_: object) -> None:  # noqa: ANN001
        calls.append((metrics_data, timeout_millis))
        raise ValueError("closed file")

    monkeypatch.setattr(
        observability.ConsoleMetricExporter,
        "export",
        failing_export,
        raising=False,
    )

    exporter = observability._SafeConsoleMetricExporter()
    assert exporter.export(object()) is None
    assert calls


def test_safe_console_span_exporter_swallows_value_error(monkeypatch):
    """Span exporter should suppress ValueError when stdout is unavailable."""

    def failing_export(self, spans: object) -> object:  # noqa: ANN001
        raise ValueError("closed stream")

    monkeypatch.setattr(
        observability.ConsoleSpanExporter,
        "export",
        failing_export,
        raising=False,
    )

    exporter = observability._SafeConsoleSpanExporter()
    result = exporter.export([object()])
    expected_success = getattr(observability.SpanExportResult, "SUCCESS", None)
    assert result == expected_success


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
