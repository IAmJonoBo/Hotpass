"""Tests for configuration and industry profiles."""

import pytest

pytest.importorskip("frictionless")

from hotpass.config import (  # noqa: E402
    IndustryProfile,
    get_default_profile,
    load_industry_profile,
)


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

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_get_default_profile_aviation():
    """Test that aviation profile has expected defaults."""
    profile = get_default_profile("aviation")

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_get_default_profile_generic():
    """Test that generic profile works."""
    profile = get_default_profile("generic")

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_load_industry_profile_aviation(tmp_path):
    """Test loading aviation profile from file."""
    # The aviation profile should exist in the package
    profile = load_industry_profile("aviation")

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")


def test_profile_column_synonyms():
    """Test that profiles have useful column synonyms."""
    profile = get_default_profile("aviation")

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
