"""Tests for enhanced pipeline integration."""

import logging
from unittest.mock import Mock, patch

import pandas as pd
import pytest

pytest.importorskip("frictionless")

import hotpass.pipeline_enhanced as pipeline_enhanced  # noqa: E402
import hotpass.pipeline_enhancements as pipeline_stages  # noqa: E402
from hotpass.compliance import ConsentValidationError  # noqa: E402
from hotpass.pipeline import PipelineResult, QualityReport  # noqa: E402
from hotpass.pipeline_enhanced import (  # noqa: E402
    EnhancedPipelineConfig,
    _build_trace_factory,
    _initialize_observability,
    _noop,
    run_enhanced_pipeline,
)


@pytest.fixture(autouse=True)
def reset_enhanced_pipeline(monkeypatch):
    """Ensure observability state resets between tests."""

    import hotpass.observability as observability

    monkeypatch.setattr(observability, "_instrumentation_initialized", False, raising=False)
    monkeypatch.setattr(observability, "_pipeline_metrics", None, raising=False)
    monkeypatch.setattr(pipeline_enhanced, "get_pipeline_metrics", lambda: Mock(), raising=False)


@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing."""
    data = {
        "organization_name": ["Test Org 1", "Test Org 2", "Test Org 1"],
        "organization_slug": ["test-org-1", "test-org-2", "test-org-1"],
        "province": ["Gauteng", "Western Cape", "Gauteng"],
        "country": ["South Africa", "South Africa", "South Africa"],
        "contact_primary_email": [
            "test1@example.com",
            "test2@example.com",
            "test1@example.com",
        ],
        "website": ["http://test1.com", "http://test2.com", "http://test1.com"],
        "address_primary": ["123 Main St", "456 Oak Ave", "123 Main St"],
        "data_quality_score": [0.8, 0.7, 0.8],
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_pipeline_result(sample_dataframe, monkeypatch):
    """Mock the run_pipeline function to return sample data."""

    def mock_run_pipeline(config):
        return PipelineResult(
            refined=sample_dataframe.copy(),
            quality_report=QualityReport(
                total_records=len(sample_dataframe),
                invalid_records=0,
                schema_validation_errors=[],
                expectations_passed=True,
                expectation_failures=[],
                source_breakdown={},
                data_quality_distribution={"mean": 0.8, "min": 0.7, "max": 0.8},
                performance_metrics={
                    "load_seconds": 0.1,
                    "aggregation_seconds": 0.1,
                    "polars_transform_seconds": 0.05,
                    "polars_materialize_seconds": 0.02,
                    "pandas_sort_seconds": 0.04,
                    "polars_sort_speedup": 1.8,
                    "duckdb_sort_seconds": 0.03,
                    "polars_write_seconds": 0.02,
                    "expectations_seconds": 0.1,
                    "write_seconds": 0.1,
                    "total_seconds": 0.4,
                    "rows_per_second": 7.5,
                    "load_rows_per_second": 30,
                },
                recommendations=[],
                audit_trail=[],
                conflict_resolutions=[],
            ),
            performance_metrics={},
        )

    import hotpass.pipeline_enhanced

    monkeypatch.setattr(hotpass.pipeline_enhanced, "run_pipeline", mock_run_pipeline)


def test_enhanced_pipeline_config_defaults():
    """Test EnhancedPipelineConfig defaults."""
    config = EnhancedPipelineConfig()

    assert config.enable_entity_resolution is False
    assert config.enable_geospatial is False
    assert config.enable_enrichment is False
    assert config.enable_compliance is False
    assert config.enable_observability is False
    assert config.entity_resolution_threshold == 0.75
    assert config.use_splink is False
    assert config.enrichment_concurrency == 8


def test_noop_context_manager():
    """Test the no-op context manager."""
    with _noop() as ctx:
        assert ctx is not None
    # Should not raise any exceptions


def test_initialize_observability_disabled_returns_none(monkeypatch):
    """Observability initialisation should be skipped when disabled."""

    config = EnhancedPipelineConfig(enable_observability=False)
    called = False

    def _guard(*_args, **_kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(pipeline_enhanced, "initialize_observability", _guard)

    assert _initialize_observability(config) is None
    assert called is False


def test_initialize_observability_enabled_invokes_dependencies(monkeypatch):
    """When enabled the helper must call the OpenTelemetry bootstrap and return metrics."""

    config = EnhancedPipelineConfig(enable_observability=True)
    bootstrap_called = False
    metrics_mock = Mock()

    def _fake_initialize(*_args, **_kwargs):
        nonlocal bootstrap_called
        bootstrap_called = True

    monkeypatch.setattr(pipeline_enhanced, "initialize_observability", _fake_initialize)
    monkeypatch.setattr(pipeline_enhanced, "get_pipeline_metrics", lambda: metrics_mock)

    assert _initialize_observability(config) is metrics_mock
    assert bootstrap_called is True


def test_build_trace_factory_disabled(monkeypatch):
    """Disabled tracing should yield the no-op context manager."""

    factory = _build_trace_factory(enabled=False)
    with factory("anything") as ctx:
        assert isinstance(ctx, _noop)


def test_build_trace_factory_enabled_uses_trace_operation(monkeypatch):
    """The trace factory should proxy to trace_operation when enabled."""

    captured = []

    def _fake_trace(name):
        captured.append(name)
        return _noop()

    monkeypatch.setattr(pipeline_enhanced, "trace_operation", _fake_trace)

    factory = _build_trace_factory(enabled=True)
    with factory("entity_resolution"):
        pass

    assert captured == ["entity_resolution"]


def test_enhanced_pipeline_basic(sample_dataframe, mock_pipeline_result, tmp_path):
    """Test basic enhanced pipeline execution."""
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=False,
        enable_geospatial=False,
        enable_enrichment=False,
        enable_compliance=False,
        enable_observability=False,
    )

    result = run_enhanced_pipeline(config, enhanced_config)

    assert result is not None
    assert len(result.refined) == 3
    assert result.quality_report is not None


def test_enhanced_pipeline_with_entity_resolution(sample_dataframe, mock_pipeline_result, tmp_path):
    """Test enhanced pipeline with entity resolution."""
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=True,
        enable_geospatial=False,
        enable_enrichment=False,
        enable_compliance=False,
        enable_observability=False,
        use_splink=False,  # Use fallback
    )

    result = run_enhanced_pipeline(config, enhanced_config)

    assert result is not None
    assert len(result.refined) > 0

    # Check that ML priority scores were added
    assert "completeness_score" in result.refined.columns
    assert "priority_score" in result.refined.columns


def test_enhanced_pipeline_with_compliance(sample_dataframe, mock_pipeline_result, tmp_path):
    """Test enhanced pipeline with compliance features."""
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=False,
        enable_geospatial=False,
        enable_enrichment=False,
        enable_compliance=True,
        enable_observability=False,
        detect_pii=False,  # Disable PII detection to avoid Presidio dependency
        consent_overrides={
            "test-org-1": "granted",
            "test-org-2": "granted",
        },
    )

    result = run_enhanced_pipeline(config, enhanced_config)

    assert result is not None
    assert len(result.refined) > 0

    # Check that provenance columns were added
    assert "data_source" in result.refined.columns
    assert "processed_at" in result.refined.columns
    assert "consent_status" in result.refined.columns
    assert result.compliance_report is not None
    assert result.compliance_report["consent_violations"] == []
    assert result.compliance_report["consent_status_summary"].get("granted", 0) == len(
        result.refined
    )


def test_enhanced_pipeline_missing_consent_raises(sample_dataframe, mock_pipeline_result, tmp_path):
    """Compliance enabled without granted consent should raise an error."""
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_compliance=True,
        enable_observability=False,
        detect_pii=False,
    )

    with pytest.raises(ConsentValidationError):
        run_enhanced_pipeline(config, enhanced_config)


def test_entity_resolution_uses_fallback_when_splink_missing(
    sample_dataframe, mock_pipeline_result, tmp_path, monkeypatch, caplog
):
    """Entity resolution falls back to rule-based matching if Splink import fails."""

    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    fallback_thresholds: list[float] = []

    def fake_fallback(df: pd.DataFrame, threshold: float):
        fallback_thresholds.append(threshold)
        return df.assign(fallback_used=True), []

    def fake_add_scores(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(priority_applied=True)

    def fake_link_entities(df: pd.DataFrame, _config: object):
        raise RuntimeError("splink missing")

    monkeypatch.setattr(pipeline_stages, "link_entities", fake_link_entities)
    monkeypatch.setattr(pipeline_stages, "resolve_entities_fallback", fake_fallback)
    monkeypatch.setattr(pipeline_stages, "add_ml_priority_scores", fake_add_scores)

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=True,
        enable_geospatial=False,
        enable_enrichment=False,
        enable_compliance=False,
        enable_observability=False,
        use_splink=True,
        linkage_output_dir=str(tmp_path / "linkage"),
    )

    with caplog.at_level(logging.WARNING):
        result = run_enhanced_pipeline(config, enhanced_config)

    assert fallback_thresholds, "Fallback resolver should be invoked when Splink is unavailable"
    assert "falling back" in caplog.text.lower()
    assert "priority_applied" in result.refined.columns


def test_enhanced_pipeline_with_observability(sample_dataframe, mock_pipeline_result, tmp_path):
    """Test enhanced pipeline with observability."""
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=False,
        enable_geospatial=False,
        enable_enrichment=False,
        enable_compliance=False,
        enable_observability=True,
    )

    with (
        patch.object(pipeline_enhanced, "initialize_observability", autospec=True) as init_obs,
        patch.object(pipeline_enhanced, "get_pipeline_metrics", autospec=True) as get_metrics,
    ):
        metrics_mock = Mock()
        get_metrics.return_value = metrics_mock

        result = run_enhanced_pipeline(config, enhanced_config)

    init_obs.assert_called_once()
    metrics_mock.record_records_processed.assert_called()

    assert result is not None
    assert len(result.refined) > 0


def test_enhanced_pipeline_all_features(sample_dataframe, mock_pipeline_result, tmp_path):
    """Test enhanced pipeline with all features enabled."""
    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=True,
        enable_geospatial=False,  # Skip geocoding in tests
        enable_enrichment=False,  # Skip web scraping in tests
        enable_compliance=True,
        enable_observability=True,
        use_splink=False,
        geocode_addresses=False,
        enrich_websites=False,
        detect_pii=False,
        consent_overrides={
            "test-org-1": "granted",
            "test-org-2": "granted",
        },
    )

    result = run_enhanced_pipeline(config, enhanced_config)

    assert result is not None
    assert len(result.refined) > 0

    # Check entity resolution features
    assert "completeness_score" in result.refined.columns
    assert "priority_score" in result.refined.columns

    # Check compliance features
    assert "data_source" in result.refined.columns
    assert "processed_at" in result.refined.columns


def test_enhanced_pipeline_with_geospatial_and_enrichment(
    sample_dataframe, mock_pipeline_result, tmp_path, monkeypatch
):
    """Pipeline adds geospatial and enrichment data when enabled."""

    from hotpass.config import get_default_profile
    from hotpass.data_sources import ExcelReadOptions
    from hotpass.pipeline import PipelineConfig

    output_path = tmp_path / "output.xlsx"

    profile = get_default_profile("aviation")
    config = PipelineConfig(
        input_dir=tmp_path,
        output_path=output_path,
        industry_profile=profile,
        excel_options=ExcelReadOptions(),
    )

    geocode_calls: list[pd.DataFrame] = []
    enrich_calls: list[pd.DataFrame] = []

    def fake_geocode_dataframe(df: pd.DataFrame, **_: object) -> pd.DataFrame:
        geocode_calls.append(df)
        enriched = df.copy()
        enriched["latitude"] = 1.0
        enriched["longitude"] = 2.0
        enriched["geocoded"] = True
        return enriched

    def fake_enrich_websites(df: pd.DataFrame, **_: object) -> pd.DataFrame:
        enrich_calls.append(df)
        enriched = df.copy()
        enriched["website_title"] = "Title"
        enriched["website_enriched"] = True
        return enriched

    class FakeCache:
        def __init__(self, *_, **__):
            self.set_calls = []

        def get(self, *_: object, **__: object) -> None:
            return None

        def set(self, *args: object, **__: object) -> None:
            self.set_calls.append(args)

        def stats(self) -> dict[str, int]:
            return {"total_entries": 0, "total_hits": 0}

    monkeypatch.setattr(pipeline_stages, "geocode_dataframe", fake_geocode_dataframe)
    monkeypatch.setattr(pipeline_stages, "enrich_dataframe_with_websites", fake_enrich_websites)
    monkeypatch.setattr(pipeline_stages, "CacheManager", FakeCache)
    monkeypatch.setattr(
        pipeline_stages,
        "enrich_dataframe_with_websites_concurrent",
        fake_enrich_websites,
    )

    enhanced_config = EnhancedPipelineConfig(
        enable_entity_resolution=False,
        enable_geospatial=True,
        geocode_addresses=True,
        enable_enrichment=True,
        enrich_websites=True,
        enable_compliance=False,
        enable_observability=False,
        enrichment_concurrency=1,
    )

    result = run_enhanced_pipeline(config, enhanced_config)

    assert geocode_calls, "Geocoding should be invoked"
    assert enrich_calls, "Website enrichment should be invoked"
    assert "latitude" in result.refined.columns
    assert "website_enriched" in result.refined.columns
