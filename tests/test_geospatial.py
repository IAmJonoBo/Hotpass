"""Tests for geospatial module."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from hotpass.geospatial import (
    Geocoder,
    calculate_distance_matrix,
    cluster_by_proximity,
    create_geodataframe,
    geocode_dataframe,
    infer_province_from_coordinates,
    normalize_address,
)


def test_normalize_address_basic():
    """Test basic address normalization."""
    address = "123  Main   Street"
    normalized = normalize_address(address)
    assert normalized == "123 Main Street"


def test_normalize_address_abbreviations():
    """Test address abbreviation expansion."""
    address = "123 Main St"
    normalized = normalize_address(address)
    assert "Street" in normalized


def test_normalize_address_empty():
    """Test normalizing empty address."""
    assert normalize_address("") == ""
    assert normalize_address(None) == ""


@patch("hotpass.geospatial.GEOPY_AVAILABLE", True)
@patch("hotpass.geospatial.Nominatim")
def test_geocoder_init(mock_nominatim):
    """Test geocoder initialization."""
    geocoder = Geocoder(user_agent="Test/1.0")
    mock_nominatim.assert_called_once()
    assert geocoder.geolocator is not None


@patch("hotpass.geospatial.GEOPY_AVAILABLE", False)
def test_geocoder_init_no_geopy():
    """Test geocoder initialization without geopy."""
    geocoder = Geocoder()
    assert geocoder.geolocator is None


@patch("hotpass.geospatial.GEOPY_AVAILABLE", True)
def test_geocode_address_success():
    """Test successful address geocoding."""
    with patch("hotpass.geospatial.Nominatim") as mock_nominatim:
        # Mock location result
        mock_location = Mock()
        mock_location.latitude = -26.2041
        mock_location.longitude = 28.0473
        mock_location.address = "Johannesburg, South Africa"
        mock_location.raw = {"place_id": 123}

        mock_geolocator = Mock()
        mock_geolocator.geocode.return_value = mock_location
        mock_nominatim.return_value = mock_geolocator

        geocoder = Geocoder()
        result = geocoder.geocode_address("Johannesburg")

        assert result is not None
        assert result["latitude"] == -26.2041
        assert result["longitude"] == 28.0473
        assert "Johannesburg" in result["formatted_address"]


@patch("hotpass.geospatial.GEOPY_AVAILABLE", True)
def test_geocode_address_not_found():
    """Test geocoding with no results."""
    with patch("hotpass.geospatial.Nominatim") as mock_nominatim:
        mock_geolocator = Mock()
        mock_geolocator.geocode.return_value = None
        mock_nominatim.return_value = mock_geolocator

        geocoder = Geocoder()
        result = geocoder.geocode_address("NonexistentPlace12345")

        assert result is None


@patch("hotpass.geospatial.GEOPY_AVAILABLE", True)
def test_geocode_address_empty():
    """Test geocoding empty address."""
    with patch("hotpass.geospatial.Nominatim"):
        geocoder = Geocoder()
        assert geocoder.geocode_address("") is None
        assert geocoder.geocode_address(None) is None


@patch("hotpass.geospatial.GEOPY_AVAILABLE", True)
def test_reverse_geocode_success():
    """Test successful reverse geocoding."""
    with patch("hotpass.geospatial.Nominatim") as mock_nominatim:
        mock_location = Mock()
        mock_location.address = "123 Main Street, City"
        mock_location.raw = {"place_id": 456}

        mock_geolocator = Mock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim.return_value = mock_geolocator

        geocoder = Geocoder()
        result = geocoder.reverse_geocode(-26.2041, 28.0473)

        assert result is not None
        assert "Main Street" in result["formatted_address"]


@patch("hotpass.geospatial.GEOPY_AVAILABLE", True)
def test_reverse_geocode_not_found():
    """Test reverse geocoding with no results."""
    with patch("hotpass.geospatial.Nominatim") as mock_nominatim:
        mock_geolocator = Mock()
        mock_geolocator.reverse.return_value = None
        mock_nominatim.return_value = mock_geolocator

        geocoder = Geocoder()
        result = geocoder.reverse_geocode(0.0, 0.0)

        assert result is None


@patch("hotpass.geospatial.Geocoder.geocode_address")
def test_geocode_dataframe_success(mock_geocode):
    """Test geocoding dataframe."""
    df = pd.DataFrame(
        {
            "organization_name": ["Company A", "Company B"],
            "organization_address": ["123 Main St", "456 Oak Ave"],
        }
    )

    # Mock geocoding results
    mock_geocode.side_effect = [
        {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "formatted_address": "123 Main Street, New York",
        },
        {
            "latitude": 34.0522,
            "longitude": -118.2437,
            "formatted_address": "456 Oak Avenue, Los Angeles",
        },
    ]

    result_df = geocode_dataframe(df)

    assert "latitude" in result_df.columns
    assert "longitude" in result_df.columns
    assert "geocoded" in result_df.columns
    assert result_df["geocoded"].sum() == 2
    assert result_df.loc[0, "latitude"] == 40.7128


def test_geocode_dataframe_missing_column():
    """Test geocoding with missing column."""
    df = pd.DataFrame(
        {
            "organization_name": ["Company A"],
        }
    )

    result_df = geocode_dataframe(df, address_column="nonexistent")

    # Should return original dataframe
    assert "latitude" not in result_df.columns


@patch("hotpass.geospatial.Geocoder.geocode_address")
def test_geocode_dataframe_null_addresses(mock_geocode):
    """Test geocoding with null addresses."""
    df = pd.DataFrame(
        {
            "organization_address": ["123 Main St", None, ""],
        }
    )

    mock_geocode.return_value = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "formatted_address": "123 Main Street",
    }

    result_df = geocode_dataframe(df)

    # Only one should be geocoded
    assert result_df["geocoded"].sum() == 1
    assert mock_geocode.call_count == 1


@patch("hotpass.geospatial.Geocoder.reverse_geocode")
def test_infer_province_from_coordinates(mock_reverse):
    """Test province inference from coordinates."""
    mock_reverse.return_value = {
        "formatted_address": "Johannesburg, Gauteng, South Africa",
        "raw": {
            "address": {
                "state": "Gauteng",
                "country": "South Africa",
            }
        },
    }

    province = infer_province_from_coordinates(-26.2041, 28.0473)

    assert province == "Gauteng"


@patch("hotpass.geospatial.Geocoder.reverse_geocode")
def test_infer_province_no_result(mock_reverse):
    """Test province inference with no result."""
    mock_reverse.return_value = None

    province = infer_province_from_coordinates(0.0, 0.0)

    assert province is None


@patch("hotpass.geospatial.GEOPANDAS_AVAILABLE", True)
@patch("hotpass.geospatial.gpd")
@patch("hotpass.geospatial.Point")
def test_create_geodataframe(mock_point, mock_gpd):
    """Test creating GeoDataFrame."""
    df = pd.DataFrame(
        {
            "name": ["A", "B"],
            "latitude": [40.7128, 34.0522],
            "longitude": [-74.0060, -118.2437],
        }
    )

    # Mock Point objects
    mock_point.side_effect = [Mock(), Mock()]

    # Mock GeoDataFrame with __len__ support
    mock_gdf = Mock()
    mock_gdf.__len__ = Mock(return_value=2)
    mock_gpd.GeoDataFrame.return_value = mock_gdf

    create_geodataframe(df)

    assert mock_gpd.GeoDataFrame.called
    assert mock_point.call_count == 2


@patch("hotpass.geospatial.GEOPANDAS_AVAILABLE", False)
def test_create_geodataframe_no_geopandas():
    """Test creating GeoDataFrame without geopandas."""
    df = pd.DataFrame(
        {
            "latitude": [40.7128],
            "longitude": [-74.0060],
        }
    )

    with pytest.raises(ImportError):
        create_geodataframe(df)


def test_create_geodataframe_missing_columns():
    """Test creating GeoDataFrame with missing columns."""
    df = pd.DataFrame(
        {
            "name": ["A"],
        }
    )

    with pytest.raises(ValueError):
        create_geodataframe(df)


@patch("hotpass.geospatial.GEOPANDAS_AVAILABLE", False)
def test_calculate_distance_matrix_no_geopandas():
    """Test distance calculation without geopandas."""
    df = pd.DataFrame(
        {
            "latitude": [40.7128, 34.0522],
            "longitude": [-74.0060, -118.2437],
        }
    )

    result = calculate_distance_matrix(df)

    assert result.empty


@patch("hotpass.geospatial.GEOPANDAS_AVAILABLE", False)
def test_cluster_by_proximity_no_geopandas():
    """Test clustering without geopandas."""
    df = pd.DataFrame(
        {
            "latitude": [40.7128, 34.0522],
            "longitude": [-74.0060, -118.2437],
        }
    )

    result = cluster_by_proximity(df)

    assert "geo_cluster_id" in result.columns
    assert (result["geo_cluster_id"] == -1).all()
