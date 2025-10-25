"""Metrics, logging, and tracing instrumentation utilities.

The module wraps OpenTelemetry initialisation so the broader codebase can rely
on observability primitives without importing heavy dependencies at import
time. When OpenTelemetry is unavailable the helpers transparently fall back to
no-op implementations. A custom console exporter guards against shutdown
errors that previously surfaced when QA tooling closed stdout before
background exporter threads flushed their buffers.
"""

from __future__ import annotations

import atexit
import logging
import os
from collections.abc import Callable, Iterable
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from opentelemetry.metrics import Meter
    from opentelemetry.trace import Tracer
else:  # pragma: no cover - runtime fallback
    Meter = Any
    Tracer = Any

metrics: Any
trace: Any

try:  # pragma: no cover - exercised in availability tests
    from opentelemetry import metrics as otel_metrics
    from opentelemetry import trace as otel_trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SpanExportResult,
    )

    metrics = otel_metrics
    trace = otel_trace
    OBSERVABILITY_AVAILABLE = True
except ImportError:  # pragma: no cover - validated via unit tests
    OBSERVABILITY_AVAILABLE = False

    @dataclass
    class _NoopObservation:
        value: float

    class _NoopInstrument:
        def add(self, *_: Any, **__: Any) -> None:  # type: ignore[no-untyped-def]
            return None

        def record(self, *_: Any, **__: Any) -> None:  # type: ignore[no-untyped-def]
            return None

    class _NoopObservable:
        def __init__(self, callbacks: Iterable[Callable[..., Any]] | None = None):
            self.callbacks = list(callbacks or [])

    class _NoopMeter:
        def create_counter(self, *args: Any, **kwargs: Any) -> _NoopInstrument:
            return _NoopInstrument()

        def create_histogram(self, *args: Any, **kwargs: Any) -> _NoopInstrument:
            return _NoopInstrument()

        def create_observable_gauge(
            self, *args: Any, callbacks: Iterable[Callable[..., Any]] | None = None, **kwargs: Any
        ) -> _NoopObservable:
            return _NoopObservable(callbacks=callbacks)

    class _NoopSpan:
        def set_attribute(self, *_: Any, **__: Any) -> None:
            return None

        def record_exception(self, *_: Any, **__: Any) -> None:
            return None

        def set_status(self, *_: Any, **__: Any) -> None:
            return None

    class _NoopTracer:
        def start_as_current_span(self, *_: Any, **__: Any):  # type: ignore[no-untyped-def]
            return nullcontext(_NoopSpan())

    class _NoopTraceModule(SimpleNamespace):
        def get_tracer(self, *_: Any, **__: Any) -> _NoopTracer:  # type: ignore[no-untyped-def]
            return _NoopTracer()

        def set_tracer_provider(self, *_: Any, **__: Any) -> None:  # type: ignore[no-untyped-def]
            return None

        StatusCode = SimpleNamespace(ERROR="ERROR")

        def Status(self, code: Any, description: str):  # type: ignore[no-untyped-def]
            return {"code": code, "description": description}

    class _NoopMetricsModule(SimpleNamespace):
        _meter = _NoopMeter()

        def get_meter(self, *_: Any, **__: Any) -> _NoopMeter:  # type: ignore[no-untyped-def]
            return self._meter

        def set_meter_provider(self, *_: Any, **__: Any) -> None:  # type: ignore[no-untyped-def]
            return None

        Observation = _NoopObservation

    class MeterProvider:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
            return None

    class PeriodicExportingMetricReader:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
            return None

    class ConsoleMetricExporter:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
            return None

    class Resource:  # type: ignore[no-redef]
        @staticmethod
        def create(attributes: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover - noop
            return attributes

    class TracerProvider:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
            self._processors: list[Any] = []

        def add_span_processor(self, processor: Any) -> None:  # pragma: no cover - noop
            self._processors.append(processor)

    class BatchSpanProcessor:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
            return None

    class ConsoleSpanExporter:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
            return None

    class SpanExportResult:  # type: ignore[no-redef]
        SUCCESS = "success"

    metrics = _NoopMetricsModule()
    trace = _NoopTraceModule()


class _SafeConsoleMetricExporter(ConsoleMetricExporter):
    """Console exporter that tolerates closed output streams."""

    def export(
        self, metrics_data: Any, timeout_millis: float = 1000.0, **kwargs: Any
    ) -> Any:  # pragma: no cover - exercised indirectly
        try:
            return super().export(metrics_data, timeout_millis=timeout_millis, **kwargs)
        except ValueError as exc:  # pragma: no cover - depends on runtime
            logger.debug(
                "Suppressed ValueError while exporting console metrics: %s",
                exc,
                exc_info=exc,
            )
            return None


class _SafeConsoleSpanExporter(ConsoleSpanExporter):
    """Span exporter that tolerates closed streams during shutdown."""

    def export(self, spans: Any) -> Any:  # pragma: no cover - exercised indirectly
        try:
            return super().export(spans)
        except ValueError:  # pragma: no cover - depends on runtime
            return getattr(SpanExportResult, "SUCCESS", None)


# Module logger
logger = logging.getLogger(__name__)

# Global instrumentation state
_instrumentation_initialized = False
_shutdown_registered = False
_meter_provider: MeterProvider | None = None
_metric_reader: PeriodicExportingMetricReader | None = None
_trace_provider: TracerProvider | None = None


def initialize_observability(
    service_name: str = "hotpass",
    environment: str | None = None,
    export_to_console: bool = True,
) -> tuple[Tracer, Meter]:
    """Initialize OpenTelemetry instrumentation for the application.

    Args:
        service_name: Name of the service for resource identification
        environment: Deployment environment (e.g., "production", "staging")
        export_to_console: Whether to export telemetry to console

    Returns:
        Tuple of (tracer, meter) for instrumentation
    """
    global \
        _instrumentation_initialized, \
        _meter_provider, \
        _metric_reader, \
        _trace_provider, \
        _shutdown_registered

    if _instrumentation_initialized:
        logger.warning("Observability already initialized, skipping")
        return get_tracer(), get_meter()

    if not OBSERVABILITY_AVAILABLE:
        logger.warning("OpenTelemetry not available; using no-op observability implementation")
        _instrumentation_initialized = True
        if not _shutdown_registered:
            atexit.register(shutdown_observability)
            _shutdown_registered = True
        return get_tracer(), get_meter()

    environment = environment or os.getenv("HOTPASS_ENVIRONMENT", "development")

    # Create resource with service metadata
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": environment or "unknown",  # type: ignore[dict-item]
        }
    )

    # Initialize tracing
    trace_provider = TracerProvider(resource=resource)
    if export_to_console:
        trace_provider.add_span_processor(BatchSpanProcessor(_SafeConsoleSpanExporter()))
    trace.set_tracer_provider(trace_provider)
    _trace_provider = trace_provider

    # Initialize metrics
    if export_to_console:
        exporter: ConsoleMetricExporter | None = _SafeConsoleMetricExporter()
    else:
        exporter = None

    if exporter is not None:
        metric_reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
    else:
        metric_reader = PeriodicExportingMetricReader(
            _SafeConsoleMetricExporter(), export_interval_millis=60000
        )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)
    _meter_provider = meter_provider
    _metric_reader = metric_reader

    _instrumentation_initialized = True
    if not _shutdown_registered:
        atexit.register(shutdown_observability)
        _shutdown_registered = True
    logger.info(
        f"Observability initialized for service '{service_name}' in environment '{environment}'"
    )

    return get_tracer(), get_meter()


def shutdown_observability() -> None:
    """Tear down configured exporters and providers gracefully."""

    global _instrumentation_initialized, _meter_provider, _metric_reader, _trace_provider

    if not _instrumentation_initialized:
        return

    for component in (_metric_reader, _meter_provider, _trace_provider):
        if component is None:
            continue
        shutdown = getattr(component, "shutdown", None)
        if callable(shutdown):  # pragma: no branch - simple guard
            try:
                shutdown()  # type: ignore[misc]
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.debug(
                    "Suppressed exception while shutting down observability component %s: %s",
                    component,
                    exc,
                    exc_info=exc,
                )

    _meter_provider = None
    _metric_reader = None
    _trace_provider = None
    _instrumentation_initialized = False


def get_tracer(name: str = "hotpass") -> Tracer:
    """Get the application tracer.

    Args:
        name: Tracer name

    Returns:
        OpenTelemetry tracer instance
    """
    return trace.get_tracer(name)


def get_meter(name: str = "hotpass") -> Meter:
    """Get the application meter for metrics.

    Args:
        name: Meter name

    Returns:
        OpenTelemetry meter instance
    """
    return metrics.get_meter(name)


@contextmanager
def trace_operation(operation_name: str, attributes: dict[str, Any] | None = None):
    """Context manager for tracing an operation.

    Args:
        operation_name: Name of the operation being traced
        attributes: Optional attributes to attach to the span

    Yields:
        Span for the operation
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


class PipelineMetrics:
    """Metrics collector for pipeline operations."""

    def __init__(self):
        """Initialize pipeline metrics."""
        meter = get_meter()

        # Counters
        self.records_processed = meter.create_counter(
            name="hotpass.records.processed",
            description="Total number of records processed",
            unit="records",
        )

        self.validation_failures = meter.create_counter(
            name="hotpass.validation.failures",
            description="Number of validation failures",
            unit="failures",
        )

        # Histograms
        self.load_duration = meter.create_histogram(
            name="hotpass.load.duration",
            description="Duration of data loading operations",
            unit="seconds",
        )

        self.aggregation_duration = meter.create_histogram(
            name="hotpass.aggregation.duration",
            description="Duration of aggregation operations",
            unit="seconds",
        )

        self.validation_duration = meter.create_histogram(
            name="hotpass.validation.duration",
            description="Duration of validation operations",
            unit="seconds",
        )

        self.write_duration = meter.create_histogram(
            name="hotpass.write.duration",
            description="Duration of write operations",
            unit="seconds",
        )

        # Gauges (via observable gauges)
        self.data_quality_score = meter.create_observable_gauge(
            name="hotpass.data.quality_score",
            description="Overall data quality score",
            callbacks=[self._get_quality_score],
        )

        self._latest_quality_score = 0.0

    def _get_quality_score(self, options):
        """Callback for quality score gauge."""
        return [metrics.Observation(self._latest_quality_score)]

    def record_records_processed(self, count: int, source: str = "unknown"):
        """Record number of records processed.

        Args:
            count: Number of records
            source: Source dataset name
        """
        self.records_processed.add(count, {"source": source})

    def record_validation_failure(self, rule_name: str):
        """Record a validation failure.

        Args:
            rule_name: Name of the validation rule that failed
        """
        self.validation_failures.add(1, {"rule": rule_name})

    def record_load_duration(self, seconds: float, source: str = "unknown"):
        """Record data loading duration.

        Args:
            seconds: Duration in seconds
            source: Source dataset name
        """
        self.load_duration.record(seconds, {"source": source})

    def record_aggregation_duration(self, seconds: float):
        """Record aggregation duration.

        Args:
            seconds: Duration in seconds
        """
        self.aggregation_duration.record(seconds)

    def record_validation_duration(self, seconds: float):
        """Record validation duration.

        Args:
            seconds: Duration in seconds
        """
        self.validation_duration.record(seconds)

    def record_write_duration(self, seconds: float):
        """Record write operation duration.

        Args:
            seconds: Duration in seconds
        """
        self.write_duration.record(seconds)

    def update_quality_score(self, score: float):
        """Update the latest quality score.

        Args:
            score: Quality score (0.0 to 1.0)
        """
        self._latest_quality_score = score


# Global metrics instance
_pipeline_metrics: PipelineMetrics | None = None


def get_pipeline_metrics() -> PipelineMetrics:
    """Get the global pipeline metrics instance.

    Returns:
        PipelineMetrics instance
    """
    global _pipeline_metrics
    if _pipeline_metrics is None:
        _pipeline_metrics = PipelineMetrics()
    return _pipeline_metrics
