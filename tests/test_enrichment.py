"""Tests for enrichment module."""

import tempfile
from unittest.mock import Mock, patch

import pandas as pd
import pytest

import hotpass.enrichment as enrichment
from hotpass.enrichment import (
    CacheManager,
    enrich_dataframe_with_registries,
    enrich_dataframe_with_websites,
    enrich_from_registry,
    extract_website_content,
)


@pytest.fixture(autouse=True)
def reset_enrichment_flags(monkeypatch):
    """Ensure optional dependency flags start from a clean slate."""

    monkeypatch.setattr(enrichment, "REQUESTS_AVAILABLE", True, raising=False)
    monkeypatch.setattr(enrichment, "TRAFILATURA_AVAILABLE", True, raising=False)


@pytest.fixture
def temp_cache():
    """Create temporary cache for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(db_path=f"{tmpdir}/test_cache.db", ttl_hours=1)
        yield cache


def test_cache_manager_init(temp_cache):
    """Test cache manager initialization."""
    assert temp_cache.db_path.exists()
    stats = temp_cache.stats()
    assert stats["total_entries"] == 0
    assert stats["total_hits"] == 0


def test_cache_set_and_get(temp_cache):
    """Test setting and getting cache values."""
    temp_cache.set("test_key", "test_value")
    value = temp_cache.get("test_key")
    assert value == "test_value"


def test_cache_get_nonexistent(temp_cache):
    """Test getting nonexistent key returns None."""
    value = temp_cache.get("nonexistent")
    assert value is None


def test_cache_delete(temp_cache):
    """Test deleting cache entries."""
    temp_cache.set("test_key", "test_value")
    temp_cache.delete("test_key")
    value = temp_cache.get("test_key")
    assert value is None


def test_cache_hit_count(temp_cache):
    """Test cache hit counting."""
    temp_cache.set("test_key", "test_value")

    # Access the key multiple times
    for _ in range(5):
        temp_cache.get("test_key")

    stats = temp_cache.stats()
    assert stats["total_hits"] == 5


def test_cache_stats(temp_cache):
    """Test cache statistics."""
    temp_cache.set("key1", "value1")
    temp_cache.set("key2", "value2")
    temp_cache.get("key1")
    temp_cache.get("key1")

    stats = temp_cache.stats()
    assert stats["total_entries"] == 2
    assert stats["total_hits"] == 2
    assert stats["avg_hits_per_entry"] == 1.0


def test_cache_clear_expired(temp_cache):
    """Test clearing expired entries."""
    # Set TTL to 0 hours for testing
    temp_cache.ttl = temp_cache.ttl.__class__(hours=0)
    temp_cache.set("test_key", "test_value")

    # Clear expired entries
    count = temp_cache.clear_expired()
    assert count == 1

    # Verify key is gone
    value = temp_cache.get("test_key")
    assert value is None


@patch("hotpass.enrichment.TRAFILATURA_AVAILABLE", True)
@patch("hotpass.enrichment.REQUESTS_AVAILABLE", True)
@patch("hotpass.enrichment.requests", create=True)
@patch("hotpass.enrichment.trafilatura", create=True)
def test_extract_website_content_success(mock_trafilatura, mock_requests, temp_cache):
    """Test successful website content extraction."""
    # Mock response
    mock_response = Mock()
    mock_response.text = "<html><body>Test content</body></html>"
    mock_response.raise_for_status = Mock()
    mock_requests.get.return_value = mock_response

    # Mock trafilatura
    mock_trafilatura.extract.return_value = "Extracted text content"
    mock_metadata = Mock()
    mock_metadata.title = "Test Title"
    mock_metadata.author = "Test Author"
    mock_metadata.date = "2025-01-01"
    mock_metadata.description = "Test Description"
    mock_trafilatura.extract_metadata.return_value = mock_metadata

    result = extract_website_content("https://example.com", cache=temp_cache)

    assert result["success"] is True
    assert result["title"] == "Test Title"
    assert result["text"] == "Extracted text content"
    assert result["url"] == "https://example.com"


@patch("hotpass.enrichment.TRAFILATURA_AVAILABLE", True)
@patch("hotpass.enrichment.REQUESTS_AVAILABLE", True)
@patch("hotpass.enrichment.requests", create=True)
def test_extract_website_content_error(mock_requests, temp_cache):
    """Test website content extraction with error."""
    mock_requests.get.side_effect = Exception("Connection timeout")

    result = extract_website_content("https://example.com", cache=temp_cache)

    assert result["success"] is False
    assert "error" in result
    assert "Connection timeout" in result["error"]


@patch("hotpass.enrichment.TRAFILATURA_AVAILABLE", False)
def test_extract_website_content_no_trafilatura():
    """Test website extraction when trafilatura is not available."""
    result = extract_website_content("https://example.com")

    assert "error" in result
    assert "Trafilatura not installed" in result["error"]


def test_extract_website_content_caching(temp_cache):
    """Test that website content is cached."""
    with (
        patch("hotpass.enrichment.TRAFILATURA_AVAILABLE", True),
        patch("hotpass.enrichment.REQUESTS_AVAILABLE", True),
        patch("hotpass.enrichment.requests", create=True) as mock_requests,
        patch("hotpass.enrichment.trafilatura", create=True) as mock_trafilatura,
    ):
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        mock_trafilatura.extract.return_value = "Test text"
        mock_trafilatura.extract_metadata.return_value = None

        # First call should hit the API
        result1 = extract_website_content("https://example.com", cache=temp_cache)
        assert result1["success"] is True

        # Second call should use cache
        result2 = extract_website_content("https://example.com", cache=temp_cache)
        assert result2["success"] is True

        # Verify only one API call was made
        assert mock_requests.get.call_count == 1


def test_enrich_from_registry_stub(temp_cache):
    """Test registry enrichment stub."""
    result = enrich_from_registry("Test Company", registry_type="cipc", cache=temp_cache)

    assert result["org_name"] == "Test Company"
    assert result["registry_type"] == "cipc"
    assert result["status"] == "not_implemented"
    assert "registration_number" in result


def test_enrich_from_registry_caching(temp_cache):
    """Test that registry lookups are cached."""
    # First call
    result1 = enrich_from_registry("Test Company", registry_type="cipc", cache=temp_cache)

    # Second call should use cache
    result2 = enrich_from_registry("Test Company", registry_type="cipc", cache=temp_cache)

    # Both should return same data
    assert result1 == result2

    # Check cache stats
    stats = temp_cache.stats()
    assert stats["total_entries"] == 1
    assert stats["total_hits"] == 1


@patch("hotpass.enrichment.extract_website_content")
def test_enrich_dataframe_with_websites(mock_extract, temp_cache):
    """Test enriching dataframe with website content."""
    # Create test dataframe
    df = pd.DataFrame(
        {
            "organization_name": ["Company A", "Company B"],
            "organization_website": ["https://companya.com", "https://companyb.com"],
        }
    )

    # Mock successful extraction
    mock_extract.side_effect = [
        {
            "success": True,
            "title": "Company A Website",
            "description": "Company A description",
            "text": "Lorem ipsum dolor sit amet",
        },
        {
            "success": True,
            "title": "Company B Website",
            "description": "Company B description",
            "text": "Consectetur adipiscing elit",
        },
    ]

    result_df = enrich_dataframe_with_websites(df, cache=temp_cache)

    assert "website_title" in result_df.columns
    assert "website_description" in result_df.columns
    assert "website_enriched" in result_df.columns
    assert result_df["website_enriched"].sum() == 2
    assert result_df.loc[0, "website_title"] == "Company A Website"


@patch("hotpass.enrichment.extract_website_content")
def test_enrich_dataframe_with_websites_missing_column(mock_extract):
    """Test website enrichment with missing column."""
    df = pd.DataFrame(
        {
            "organization_name": ["Company A"],
        }
    )

    result_df = enrich_dataframe_with_websites(df, website_column="nonexistent")

    # Should return original dataframe
    assert "website_title" not in result_df.columns


@patch("hotpass.enrichment.extract_website_content")
def test_enrich_dataframe_with_websites_null_urls(mock_extract, temp_cache):
    """Test website enrichment with null URLs."""
    df = pd.DataFrame(
        {
            "organization_name": ["Company A", "Company B"],
            "organization_website": ["https://companya.com", None],
        }
    )

    mock_extract.return_value = {
        "success": True,
        "title": "Company A Website",
        "description": "Test",
        "text": "Test text",
    }

    result_df = enrich_dataframe_with_websites(df, cache=temp_cache)

    # Only one should be enriched
    assert result_df["website_enriched"].sum() == 1
    assert mock_extract.call_count == 1


@patch("hotpass.enrichment.enrich_from_registry")
def test_enrich_dataframe_with_registries(mock_enrich_registry, temp_cache):
    """Test enriching dataframe with registry data."""
    df = pd.DataFrame(
        {
            "organization_name": ["Company A", "Company B"],
            "location": ["City A", "City B"],
        }
    )

    # Mock registry responses
    mock_enrich_registry.side_effect = [
        {
            "status": "found",
            "registration_number": "REG123",
        },
        {
            "status": "not_found",
            "registration_number": None,
        },
    ]

    result_df = enrich_dataframe_with_registries(df, registry_type="cipc", cache=temp_cache)

    assert "registry_type" in result_df.columns
    assert "registry_status" in result_df.columns
    assert "registry_number" in result_df.columns
    assert result_df.loc[0, "registry_number"] == "REG123"


@patch("hotpass.enrichment.enrich_from_registry")
def test_enrich_dataframe_with_registries_missing_column(mock_enrich_registry):
    """Test registry enrichment with missing column."""
    df = pd.DataFrame(
        {
            "company": ["Company A"],
        }
    )

    result_df = enrich_dataframe_with_registries(df, org_name_column="nonexistent")

    # Should return original dataframe
    assert "registry_type" not in result_df.columns


def test_enrich_dataframe_with_registries_null_names(temp_cache):
    """Test registry enrichment with null organization names."""
    df = pd.DataFrame(
        {
            "organization_name": ["Company A", None, ""],
        }
    )

    result_df = enrich_dataframe_with_registries(df, cache=temp_cache)

    # Only one should be queried
    assert result_df["registry_enriched"].sum() == 0  # Stub returns not_implemented
