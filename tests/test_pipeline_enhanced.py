"""Tests for enhanced pipeline integration."""

import pandas as pd
import pytest

from hotpass.pipeline import PipelineResult, QualityReport
from hotpass.pipeline_enhanced import (
    EnhancedPipelineConfig,
    _noop,
    run_enhanced_pipeline,
)


@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing."""
    data = {
        "organization_name": ["Test Org 1", "Test Org 2", "Test Org 1"],
        "organization_slug": ["test-org-1", "test-org-2", "test-org-1"],
        "province": ["Gauteng", "Western Cape", "Gauteng"],
        "country": ["South Africa", "South Africa", "South Africa"],
        "contact_primary_email": ["test1@example.com", "test2@example.com", "test1@example.com"],
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


def test_noop_context_manager():
    """Test the no-op context manager."""
    with _noop() as ctx:
        assert ctx is not None
    # Should not raise any exceptions


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
    )

    result = run_enhanced_pipeline(config, enhanced_config)

    assert result is not None
    assert len(result.refined) > 0

    # Check that provenance columns were added
    assert "data_source" in result.refined.columns
    assert "processed_at" in result.refined.columns
    assert "consent_status" in result.refined.columns


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

    result = run_enhanced_pipeline(config, enhanced_config)

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
