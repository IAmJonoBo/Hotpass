"""Package-level contract verification tests."""

import importlib

import hotpass


def test_enhanced_pipeline_exports_available() -> None:
    """The top-level package should expose enhanced pipeline contracts."""
    module = importlib.import_module("hotpass.pipeline_enhanced")

    exported_names = set(getattr(hotpass, "__all__", ()))

    assert "EnhancedPipelineConfig" in exported_names
    assert "run_enhanced_pipeline" in exported_names

    assert hotpass.EnhancedPipelineConfig is module.EnhancedPipelineConfig
    assert hotpass.run_enhanced_pipeline is module.run_enhanced_pipeline


__all__ = ["test_enhanced_pipeline_exports_available"]
