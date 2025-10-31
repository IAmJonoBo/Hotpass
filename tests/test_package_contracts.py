"""Package-level contract verification tests."""

import importlib

import pytest

pytest.importorskip("frictionless")

import hotpass  # noqa: E402

from tests.helpers.assertions import expect


def test_enhanced_pipeline_exports_available() -> None:
    """The top-level package should expose enhanced pipeline contracts."""
    module = importlib.import_module("hotpass.pipeline_enhanced")

    exported_names = set(getattr(hotpass, "__all__", ()))

    expect(
        "EnhancedPipelineConfig" in exported_names,
        "EnhancedPipelineConfig should be exported",
    )
    expect(
        "run_enhanced_pipeline" in exported_names,
        "run_enhanced_pipeline should be exported",
    )

    expect(
        hotpass.EnhancedPipelineConfig is module.EnhancedPipelineConfig,
        "EnhancedPipelineConfig should be re-exported from module",
    )
    expect(
        hotpass.run_enhanced_pipeline is module.run_enhanced_pipeline,
        "run_enhanced_pipeline should be re-exported from module",
    )


__all__ = ["test_enhanced_pipeline_exports_available"]
