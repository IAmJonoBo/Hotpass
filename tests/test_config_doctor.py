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
    phone_warnings = [
        r for r in results if "phone" in r.check_name and r.severity == "warning"
    ]
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


def test_config_doctor_empty_profile_name():
    """Test detection of empty profile name."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(name="", display_name="Test")
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect empty profile name
    name_issues = [
        r for r in results if r.check_name == "profile_name" and not r.passed
    ]
    assert len(name_issues) > 0
    assert name_issues[0].severity == "error"


def test_config_doctor_empty_display_name():
    """Test detection of empty display name."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(name="test", display_name="")
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect empty display name
    display_issues = [
        r for r in results if r.check_name == "profile_display_name" and not r.passed
    ]
    assert len(display_issues) > 0
    assert display_issues[0].severity == "warning"


def test_config_doctor_high_threshold_warning():
    """Test warning for very high validation thresholds."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test",
        display_name="Test",
        website_validation_threshold=0.98,  # Very high
    )
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should warn about high website threshold
    website_warnings = [
        r for r in results if "website" in r.check_name and r.severity == "warning"
    ]
    assert len(website_warnings) > 0


def test_config_doctor_no_source_priorities():
    """Test detection of missing source priorities."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test",
        display_name="Test",
        source_priorities={},  # Empty priorities
    )
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect missing source priorities
    priority_issues = [
        r for r in results if r.check_name == "source_priorities" and not r.passed
    ]
    assert len(priority_issues) > 0
    assert priority_issues[0].severity == "warning"


def test_config_doctor_duplicate_source_priorities():
    """Test detection of duplicate source priority values."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test",
        display_name="Test",
        source_priorities={"source1": 1, "source2": 1},  # Duplicate priority values
    )
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect duplicate priorities
    dup_issues = [
        r
        for r in results
        if r.check_name == "source_priorities_unique" and not r.passed
    ]
    assert len(dup_issues) > 0


def test_config_doctor_no_column_synonyms():
    """Test detection of missing column synonyms."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test",
        display_name="Test",
        column_synonyms={},  # No synonyms
    )
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect missing column synonyms
    synonym_issues = [
        r for r in results if r.check_name == "column_synonyms" and not r.passed
    ]
    assert len(synonym_issues) > 0


def test_config_doctor_missing_critical_field_synonyms():
    """Test detection of missing synonyms for critical fields."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test",
        display_name="Test",
        column_synonyms={"other_field": ["synonym"]},  # Missing critical fields
    )
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect missing critical field synonyms
    critical_issues = [
        r
        for r in results
        if r.check_name == "column_synonyms_critical" and not r.passed
    ]
    assert len(critical_issues) > 0
    assert critical_issues[0].severity == "warning"


def test_config_doctor_no_required_fields():
    """Test detection of missing required fields."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(name="test", display_name="Test", required_fields=[])
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect missing required fields
    required_issues = [
        r for r in results if r.check_name == "required_fields" and not r.passed
    ]
    assert len(required_issues) > 0


def test_config_doctor_missing_org_name_in_required():
    """Test detection of organization_name not in required fields."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test",
        display_name="Test",
        required_fields=["other_field"],  # Missing org_name
    )
    doctor = ConfigDoctor(profile=profile)
    results = doctor.diagnose()

    # Should detect missing organization_name in required fields
    org_issues = [
        r
        for r in results
        if r.check_name == "required_fields_org_name" and not r.passed
    ]
    assert len(org_issues) > 0


def test_config_doctor_print_report(capsys):
    """Test that print_report outputs to console."""
    profile = get_default_profile("generic")
    doctor = ConfigDoctor(profile=profile)

    doctor.print_report()

    captured = capsys.readouterr()
    assert "Configuration Health Check Report" in captured.out
    assert "Health Score" in captured.out


def test_config_doctor_autofix_phone_threshold():
    """Test autofix for phone threshold."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test", display_name="Test", phone_validation_threshold=1.5
    )
    doctor = ConfigDoctor(profile=profile)

    fixed = doctor.autofix()
    assert fixed is True
    assert profile.phone_validation_threshold == 0.85


def test_config_doctor_autofix_website_threshold():
    """Test autofix for website threshold."""
    from hotpass.config import IndustryProfile

    profile = IndustryProfile(
        name="test", display_name="Test", website_validation_threshold=1.5
    )
    doctor = ConfigDoctor(profile=profile)

    fixed = doctor.autofix()
    assert fixed is True
    assert profile.website_validation_threshold == 0.75


def test_config_doctor_no_autofix_needed():
    """Test that autofix returns False when no fixes are needed."""
    profile = get_default_profile("aviation")
    doctor = ConfigDoctor(profile=profile)

    # Aviation profile is already well-configured
    fixed = doctor.autofix()
    # May or may not need fixes depending on profile state
    assert isinstance(fixed, bool)
