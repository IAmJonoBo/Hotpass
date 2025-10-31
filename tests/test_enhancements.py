"""Compatibility re-export tests for pipeline enhancements."""

from __future__ import annotations

import importlib

from hotpass import pipeline_enhancements
from hotpass.pipeline.features import ComplianceFeature, EnhancedPipelineConfig

from tests.helpers.assertions import expect


def test_reexported_symbols_match_pipeline_features() -> None:
    expect(
        pipeline_enhancements.ComplianceFeature is ComplianceFeature,
        "ComplianceFeature should be re-exported",
    )
    expect(
        pipeline_enhancements.EnhancedPipelineConfig is EnhancedPipelineConfig,
        "EnhancedPipelineConfig should match pipeline.features module",
    )


def test___all___declares_public_surface() -> None:
    public = set(pipeline_enhancements.__all__)
    expected = {
        "ComplianceFeature",
        "EnhancedPipelineConfig",
        "EnrichmentFeature",
        "EntityResolutionFeature",
        "FeatureContext",
        "GeospatialFeature",
        "PipelineFeatureStrategy",
        "TraceFactory",
        "default_trace_factory",
    }
    expect(public == expected, "__all__ should list the compatibility exports")


def test_module_import_is_idempotent() -> None:
    # Re-import to ensure no side effects or missing dependencies
    module = importlib.reload(pipeline_enhancements)
    expect(
        hasattr(module, "ComplianceFeature"),
        "Reloaded module should expose ComplianceFeature",
    )
