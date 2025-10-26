"""Tests for configuration and industry profiles."""

import pytest

pytest.importorskip("frictionless")

from hotpass.config import IndustryProfile, get_default_profile, load_industry_profile  # noqa: E402


def test_industry_profile_to_dict_roundtrip():
    """Test that profile can be converted to dict and back."""
    profile = IndustryProfile(
        name="test",
        display_name="Test Profile",
        default_country_code="US",
        source_priorities={"Source A": 2, "Source B": 1},
    )

    data = profile.to_dict()
    restored = IndustryProfile.from_dict(data)

    assert restored.name == profile.name
    assert restored.display_name == profile.display_name
    assert restored.default_country_code == profile.default_country_code
    assert restored.source_priorities == profile.source_priorities


def test_get_default_profile_aviation():
    """Test that aviation profile has expected defaults."""
    profile = get_default_profile("aviation")

    assert profile.name == "aviation"
    assert profile.display_name == "Aviation & Flight Training"
    assert profile.default_country_code == "ZA"
    assert "SACAA Cleaned" in profile.source_priorities
    assert profile.source_priorities["SACAA Cleaned"] == 3


def test_get_default_profile_generic():
    """Test that generic profile works."""
    profile = get_default_profile("generic")

    assert profile.name == "generic"
    assert profile.display_name == "Generic Business"
    assert "organization_name" in profile.column_synonyms


def test_load_industry_profile_aviation(tmp_path):
    """Test loading aviation profile from file."""
    # The aviation profile should exist in the package
    profile = load_industry_profile("aviation")

    assert profile.name == "aviation"
    assert profile.display_name == "Aviation & Flight Training"


def test_profile_column_synonyms():
    """Test that profiles have useful column synonyms."""
    profile = get_default_profile("aviation")

    assert "organization_name" in profile.column_synonyms
    assert "school_name" in profile.column_synonyms["organization_name"]
    assert "email" in profile.column_synonyms["contact_email"]
