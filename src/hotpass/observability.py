"""OpenTelemetry observability integration for Hotpass.

This module provides metrics, logging, and tracing instrumentation using OpenTelemetry.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Module logger
logger = logging.getLogger(__name__)

# Global instrumentation state
_instrumentation_initialized = False


def initialize_observability(
    service_name: str = "hotpass",
    environment: str | None = None,
    export_to_console: bool = True,
) -> tuple[trace.Tracer, metrics.Meter]:
    """Initialize OpenTelemetry instrumentation for the application.

    Args:
        service_name: Name of the service for resource identification
        environment: Deployment environment (e.g., "production", "staging")
        export_to_console: Whether to export telemetry to console

    Returns:
        Tuple of (tracer, meter) for instrumentation
    """
    global _instrumentation_initialized

    if _instrumentation_initialized:
        logger.warning("Observability already initialized, skipping")
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
        trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(trace_provider)

    # Initialize metrics
    if export_to_console:
        metric_reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(), export_interval_millis=60000
        )
    else:
        # Would configure OTLP exporter or other backend here
        metric_reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(), export_interval_millis=60000
        )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)

    _instrumentation_initialized = True
    logger.info(
        f"Observability initialized for service '{service_name}' in environment '{environment}'"
    )

    return get_tracer(), get_meter()


def get_tracer(name: str = "hotpass") -> trace.Tracer:
    """Get the application tracer.

    Args:
        name: Tracer name

    Returns:
        OpenTelemetry tracer instance
    """
    return trace.get_tracer(name)


def get_meter(name: str = "hotpass") -> metrics.Meter:
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
