"""Tests for compliance module."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from hotpass.compliance import (
    ConsentValidationError,
    DataClassification,
    LawfulBasis,
    PIIDetector,
    POPIAPolicy,
    add_provenance_columns,
    anonymize_dataframe,
    detect_pii_in_dataframe,
)


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", False)
def test_pii_detector_init_no_presidio():
    """Test PII detector initialization without Presidio."""
    detector = PIIDetector()
    assert detector.analyzer is None
    assert detector.anonymizer is None


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
@patch("hotpass.compliance.AnalyzerEngine")
@patch("hotpass.compliance.AnonymizerEngine")
def test_pii_detector_init_with_presidio(mock_anonymizer, mock_analyzer):
    """Test PII detector initialization with Presidio."""
    PIIDetector()
    mock_analyzer.assert_called_once()
    mock_anonymizer.assert_called_once()


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
def test_detect_pii_success():
    """Test successful PII detection."""
    with (
        patch("hotpass.compliance.AnalyzerEngine") as mock_analyzer_class,
        patch("hotpass.compliance.AnonymizerEngine"),
    ):
        # Mock analyzer results
        mock_result = Mock()
        mock_result.entity_type = "EMAIL_ADDRESS"
        mock_result.start = 0
        mock_result.end = 20
        mock_result.score = 0.95

        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = [mock_result]
        mock_analyzer_class.return_value = mock_analyzer

        detector = PIIDetector()
        results = detector.detect_pii("test@example.com")

        assert len(results) == 1
        assert results[0]["entity_type"] == "EMAIL_ADDRESS"
        assert results[0]["score"] == 0.95


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
def test_detect_pii_empty_text():
    """Test PII detection with empty text."""
    with (
        patch("hotpass.compliance.AnalyzerEngine"),
        patch("hotpass.compliance.AnonymizerEngine"),
    ):
        detector = PIIDetector()
        assert detector.detect_pii("") == []
        assert detector.detect_pii(None) == []


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
def test_anonymize_text_success():
    """Test successful text anonymization."""
    with (
        patch("hotpass.compliance.AnalyzerEngine") as mock_analyzer_class,
        patch("hotpass.compliance.AnonymizerEngine") as mock_anonymizer_class,
    ):
        # Mock analyzer result
        mock_result = Mock()
        mock_result.entity_type = "EMAIL_ADDRESS"
        mock_result.start = 0
        mock_result.end = 20

        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = [mock_result]
        mock_analyzer_class.return_value = mock_analyzer

        # Mock anonymizer result
        mock_anonymized = Mock()
        mock_anonymized.text = "<EMAIL_ADDRESS>"

        mock_anonymizer = Mock()
        mock_anonymizer.anonymize.return_value = mock_anonymized
        mock_anonymizer_class.return_value = mock_anonymizer

        detector = PIIDetector()
        result = detector.anonymize_text("test@example.com")

        assert result == "<EMAIL_ADDRESS>"


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
def test_anonymize_text_no_pii():
    """Test anonymization with no PII detected."""
    with (
        patch("hotpass.compliance.AnalyzerEngine") as mock_analyzer_class,
        patch("hotpass.compliance.AnonymizerEngine"),
    ):
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = []
        mock_analyzer_class.return_value = mock_analyzer

        detector = PIIDetector()
        result = detector.anonymize_text("Hello world")

        assert result == "Hello world"


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
@patch("hotpass.compliance.PIIDetector")
def test_detect_pii_in_dataframe(mock_detector_class):
    """Test PII detection in dataframe."""
    df = pd.DataFrame(
        {
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@example.com", "jane@example.com"],
        }
    )

    # Mock detector
    mock_detector = Mock()

    # Mock PII detection results
    mock_detector.detect_pii.side_effect = [
        [{"entity_type": "PERSON", "score": 0.9}],
        [{"entity_type": "EMAIL_ADDRESS", "score": 0.95}],
        [{"entity_type": "PERSON", "score": 0.85}],
        [{"entity_type": "EMAIL_ADDRESS", "score": 0.98}],
    ]
    mock_detector.analyzer = Mock()  # Not None so it passes the check
    mock_detector_class.return_value = mock_detector

    result_df = detect_pii_in_dataframe(df, columns=["name", "email"])

    assert "name_has_pii" in result_df.columns
    assert "email_has_pii" in result_df.columns
    assert result_df["name_has_pii"].sum() == 2
    assert result_df["email_has_pii"].sum() == 2


@patch("hotpass.compliance.PIIDetector")
def test_detect_pii_in_dataframe_no_presidio(mock_detector_class):
    """Test PII detection when Presidio is not available."""
    mock_detector = Mock()
    mock_detector.analyzer = None
    mock_detector_class.return_value = mock_detector

    df = pd.DataFrame(
        {
            "name": ["John Doe"],
        }
    )

    result_df = detect_pii_in_dataframe(df)

    # Should return original dataframe
    assert len(result_df.columns) == len(df.columns)


@patch("hotpass.compliance.PRESIDIO_AVAILABLE", True)
@patch("hotpass.compliance.PIIDetector")
def test_anonymize_dataframe(mock_detector_class):
    """Test dataframe anonymization."""
    df = pd.DataFrame(
        {
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@example.com", "jane@example.com"],
        }
    )

    # Mock detector
    mock_detector = Mock()
    mock_detector.anonymizer = Mock()  # Not None so it passes the check
    # Order: name[0], name[1], email[0], email[1]
    mock_detector.anonymize_text.side_effect = [
        "<PERSON>",  # John Doe
        "<PERSON>",  # Jane Smith
        "<EMAIL_ADDRESS>",  # john@example.com
        "<EMAIL_ADDRESS>",  # jane@example.com
    ]
    mock_detector_class.return_value = mock_detector

    result_df = anonymize_dataframe(df, columns=["name", "email"])

    assert result_df.loc[0, "name"] == "<PERSON>"
    assert result_df.loc[0, "email"] == "<EMAIL_ADDRESS>"


def test_data_classification_enum():
    """Test DataClassification enum."""
    assert DataClassification.PUBLIC.value == "public"
    assert DataClassification.PII.value == "pii"
    assert DataClassification.SENSITIVE_PII.value == "sensitive_pii"


def test_lawful_basis_enum():
    """Test LawfulBasis enum."""
    assert LawfulBasis.CONSENT.value == "consent"
    assert LawfulBasis.LEGITIMATE_INTEREST.value == "legitimate_interest"


def test_popia_policy_init():
    """Test POPIA policy initialization."""
    config = {
        "field_classifications": {
            "email": "pii",
        },
        "retention_policies": {
            "email": 730,
        },
    }

    policy = POPIAPolicy(config)

    assert policy.config == config
    assert policy.field_classifications["email"] == "pii"


def test_popia_policy_classify_field():
    """Test field classification."""
    config = {
        "field_classifications": {
            "email": "pii",
        },
    }

    policy = POPIAPolicy(config)

    assert policy.classify_field("email") == DataClassification.PII
    assert policy.classify_field("unknown") == DataClassification.INTERNAL


def test_popia_policy_retention_period():
    """Test retention period retrieval."""
    config = {
        "retention_policies": {
            "email": 730,
        },
    }

    policy = POPIAPolicy(config)

    assert policy.get_retention_period("email") == 730
    assert policy.get_retention_period("unknown") is None


def test_popia_policy_consent_requirements():
    """Test consent requirements."""
    config = {
        "consent_requirements": {
            "email": True,
        },
    }

    policy = POPIAPolicy(config)

    assert policy.requires_consent("email") is True
    assert policy.requires_consent("unknown") is False


def test_popia_policy_generate_report():
    """Test compliance report generation."""
    config = {
        "field_classifications": {
            "email": "pii",
            "name": "pii",
        },
        "retention_policies": {
            "email": 730,
        },
        "consent_requirements": {
            "email": True,
        },
    }

    df = pd.DataFrame(
        {
            "email": ["test@example.com"],
            "name": ["John Doe"],
            "city": ["New York"],
            "consent_status": ["granted"],
        }
    )

    policy = POPIAPolicy(config)
    report = policy.generate_compliance_report(df)

    assert report["total_fields"] == 4
    assert report["total_records"] == 1
    assert "email" in report["pii_fields"]
    assert "email" in report["consent_required_fields"]
    assert report["retention_policies"]["email"] == 730
    assert report["consent_status_summary"]["granted"] == 1
    assert report["consent_violations"] == []

    policy.enforce_consent(report)


def test_popia_policy_report_compliance_issues():
    """Test compliance issue detection in report."""
    config = {
        "field_classifications": {
            "email": "pii",
        },
    }

    df = pd.DataFrame(
        {
            "email": ["test@example.com"],
        }
    )

    policy = POPIAPolicy(config)
    report = policy.generate_compliance_report(df)

    # Should have issues because no consent requirements or retention policies
    assert len(report["compliance_issues"]) > 0


def test_popia_policy_reports_consent_violation():
    """Consent enforcement should flag rows without granted status."""
    config = {
        "consent_requirements": {"email": True},
    }

    df = pd.DataFrame({"email": ["test@example.com"], "consent_status": ["pending"]})

    policy = POPIAPolicy(config)
    report = policy.generate_compliance_report(df)

    assert report["consent_violations"]
    with pytest.raises(ConsentValidationError):
        policy.enforce_consent(report)


def test_popia_policy_enforce_consent_allows_granted_status():
    """Consent enforcement should allow granted statuses."""
    config = {
        "consent_requirements": {"email": True},
    }

    df = pd.DataFrame({"email": ["test@example.com"], "consent_status": ["granted"]})

    policy = POPIAPolicy(config)
    report = policy.generate_compliance_report(df)

    assert report["consent_violations"] == []
    policy.enforce_consent(report)


def test_add_provenance_columns():
    """Test adding provenance columns."""
    df = pd.DataFrame(
        {
            "name": ["John Doe"],
            "email": ["john@example.com"],
        }
    )

    result_df = add_provenance_columns(df, source_name="Test Source")

    assert "data_source" in result_df.columns
    assert "processed_at" in result_df.columns
    assert "consent_status" in result_df.columns
    assert result_df.loc[0, "data_source"] == "Test Source"


def test_add_provenance_columns_preserves_existing_consent():
    """Existing consent fields remain intact when provenance is added."""
    df = pd.DataFrame(
        {
            "name": ["Jane"],
            "consent_status": ["granted"],
            "consent_date": ["2025-10-01"],
        }
    )

    result_df = add_provenance_columns(df, source_name="Test Source")

    assert result_df.loc[0, "consent_status"] == "granted"
    assert result_df.loc[0, "consent_date"] == "2025-10-01"


def test_add_provenance_columns_with_timestamp():
    """Test adding provenance columns with custom timestamp."""
    df = pd.DataFrame(
        {
            "name": ["John Doe"],
        }
    )

    timestamp = "2025-01-01T00:00:00"
    result_df = add_provenance_columns(df, source_name="Test", processing_timestamp=timestamp)

    assert result_df.loc[0, "processed_at"] == timestamp
