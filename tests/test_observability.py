# ruff: noqa: I001

from __future__ import annotations

from collections.abc import Iterator

import pytest

pytest.importorskip("frictionless")

import hotpass.observability as observability  # noqa: E402
from hotpass.telemetry import pipeline_stage
from hotpass.telemetry.registry import (
    TelemetryModules,
    TelemetryPolicy,
    TelemetryRegistry,
)

from ._telemetry_stubs import (
    DummyConsoleMetricExporter,
    DummyConsoleSpanExporter,
    DummyMeter,
    DummyMeterProvider,
    DummyMetricReader,
    DummyMetrics,
    DummyResource,
    DummySpanProcessor,
    DummyTracer,
    DummyTracerProvider,
    build_modules,
)


def _modules(available: bool = True) -> TelemetryModules:
    DummyMetricReader.instances = []
    meter, trace_module, metrics_module = build_modules()
    return TelemetryModules(
        available=available,
        metrics=metrics_module,
        trace=trace_module,
        meter_provider_cls=DummyMeterProvider,
        metric_reader_cls=DummyMetricReader,
        tracer_provider_cls=DummyTracerProvider,
        span_processor_cls=DummySpanProcessor,
        console_span_exporter_cls=DummyConsoleSpanExporter,
        console_metric_exporter_cls=DummyConsoleMetricExporter,
        resource_cls=DummyResource,
    )


@pytest.fixture(autouse=True)
def reset_registry() -> Iterator[None]:
    """Ensure each test starts with an isolated telemetry registry."""

    modules = _modules()
    policy = TelemetryPolicy(allowed_exporters={"console"})
    registry = TelemetryRegistry(
        modules=modules,
        policy=policy,
        metrics_factory=DummyMetrics,
        register_shutdown=lambda fn: fn(),
    )
    observability.use_registry(registry)
    yield
    observability.shutdown_observability()


def test_initialize_observability_configures_registry() -> None:
    tracer, meter = observability.initialize_observability(
        service_name="svc",
        environment="prod",
        exporters=("console",),
    )

    assert isinstance(tracer, DummyTracer)
    assert isinstance(meter, DummyMeter)
    metrics = observability.get_pipeline_metrics()
    assert isinstance(metrics, DummyMetrics)
    assert DummyResource.last_attributes == {
        "service.name": "svc",
        "service.version": "0.1.0",
        "deployment.environment": "prod",
    }


def test_initialize_observability_idempotent() -> None:
    first = observability.initialize_observability(service_name="svc")
    second = observability.initialize_observability(service_name="svc")
    assert first == second
    assert len(DummyMetricReader.instances) == 1


def test_trace_operation_records_error_status() -> None:
    observability.initialize_observability(service_name="svc")

    with pytest.raises(RuntimeError):
        with observability.trace_operation("failing"):
            raise RuntimeError("boom")

    span = observability.trace.get_tracer("hotpass").spans[-1]
    assert span.status == {"code": "ERROR", "description": "boom"}


def test_pipeline_stage_records_metrics_and_attributes() -> None:
    observability.initialize_observability(service_name="svc")
    metrics = observability.get_pipeline_metrics()

    with pipeline_stage("ingest", {"input_dir": "./data", "tags": ["a", "b"]}):
        pass

    tracer = observability.trace.get_tracer("hotpass.pipeline")
    span = tracer.spans[-1]
    assert span.name == "pipeline.ingest"
    assert span.attributes["hotpass.pipeline.stage"] == "ingest"
    assert span.attributes["hotpass.pipeline.input_dir"] == "./data"
    assert span.attributes["hotpass.pipeline.tags"] == "a, b"
    histogram = metrics.meter.histograms["hotpass.load.duration"]
    assert histogram.calls, "expected load duration histogram to record"


def test_get_pipeline_metrics_lazy_when_uninitialised() -> None:
    metrics = observability.get_pipeline_metrics()
    assert isinstance(metrics, DummyMetrics)


def test_record_automation_delivery_tracks_requests() -> None:
    observability.initialize_observability(service_name="svc")
    metrics = observability.get_pipeline_metrics()
    metrics.record_automation_delivery(
        target="crm",
        status="delivered",
        endpoint=None,
        attempts=1,
        latency=1.5,
        idempotency="id-123",
    )
    metrics.record_automation_delivery(
        target="crm",
        status="circuit_open",
        endpoint="https://api.example",
        attempts=3,
        latency=None,
        idempotency="id-123",
    )
    request_calls = metrics.meter.counters["hotpass.automation.requests"].calls
    failure_calls = metrics.meter.counters["hotpass.automation.failures"].calls
    latency_calls = metrics.meter.histograms["hotpass.automation.duration"].calls
    assert request_calls[0][1]["status"] == "delivered"
    assert request_calls[1][1]["status"] == "circuit_open"
    assert failure_calls[0][1]["status"] == "circuit_open"
    assert latency_calls[0][0] == 1.5
    assert latency_calls[0][1]["target"] == "crm"


def test_shutdown_observability_invokes_lifecycle() -> None:
    observability.initialize_observability(service_name="svc")
    reader = DummyMetricReader.instances[0]

    observability.shutdown_observability()

    assert reader.shutdown_called is True


def test_noop_registry_when_modules_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modules = _modules(available=False)
    policy = TelemetryPolicy(allowed_exporters={"console"})
    registry = TelemetryRegistry(
        modules=modules,
        policy=policy,
        metrics_factory=DummyMetrics,
        register_shutdown=lambda fn: fn(),
    )
    observability.use_registry(registry)

    tracer, meter = observability.initialize_observability(service_name="svc")

    assert isinstance(tracer, DummyTracer)
    assert isinstance(meter, DummyMeter)
    assert registry.meter_provider is None
    assert registry.tracer_provider is None


def test_trace_operation_injects_additional_attributes() -> None:
    observability.initialize_observability(service_name="svc")

    with observability.trace_operation("annotated", {"key": "value"}):
        pass

    span = observability.trace.get_tracer("hotpass").spans[-1]
    assert span.attributes["key"] == "value"
