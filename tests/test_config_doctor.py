"""Tests for configuration doctor functionality."""

from hotpass.config import get_default_profile
from hotpass.config_doctor import ConfigDoctor, DiagnosticResult


def test_config_doctor_diagnose_default_profile():
    """Test that config doctor can diagnose default profile."""
    profile = get_default_profile("generic")
    doctor = ConfigDoctor(profile=profile)

    results = doctor.diagnose()

    assert len(results) > 0
    assert all(isinstance(r, DiagnosticResult) for r in results)


def test_config_doctor_summary():
    """Test that config doctor generates summary correctly."""
    profile = get_default_profile("aviation")
    doctor = ConfigDoctor(profile=profile)

    summary = doctor.get_summary()

    assert "total_checks" in summary
    assert "passed" in summary
    assert "failed" in summary
    assert "health_score" in summary
    assert 0 <= summary["health_score"] <= 100


def test_config_doctor_identifies_issues():
    """Test that config doctor identifies configuration issues."""
    from hotpass.config import IndustryProfile

    # Create a profile with issues
    profile = IndustryProfile(
        name="test",
        display_name="Test",
        email_validation_threshold=1.5,  # Invalid: > 1.0
        phone_validation_threshold=0.3,  # Warning: too low
    )

    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should find the invalid email threshold
    email_issues = [r for r in results if "email" in r.check_name and not r.passed]
    assert len(email_issues) > 0

    # Should find the low phone threshold
    phone_warnings = [r for r in results if "phone" in r.check_name and r.severity == "warning"]
    assert len(phone_warnings) > 0


def test_config_doctor_autofix():
    """Test that config doctor can auto-fix common issues."""
    from hotpass.config import IndustryProfile

    # Create a profile with fixable issues
    profile = IndustryProfile(
        name="test",
        display_name="Test",
        email_validation_threshold=1.5,  # Will be fixed to 0.85
        required_fields=[],  # Missing organization_name
    )

    doctor = ConfigDoctor(profile=profile)

    # Auto-fix should make changes
    fixed = doctor.autofix()
    assert fixed is True

    # Check that fixes were applied
    assert profile.email_validation_threshold == 0.85
    assert "organization_name" in profile.required_fields


def test_config_doctor_health_score():
    """Test health score calculation."""
    profile = get_default_profile("aviation")
    doctor = ConfigDoctor(profile=profile)

    summary = doctor.get_summary()

    # Aviation profile should be well-configured
    assert summary["health_score"] >= 70
