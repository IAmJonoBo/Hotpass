"""Compliance and data protection module.

This module provides functionality for:
- PII (Personally Identifiable Information) detection
- Data redaction and anonymization
- POPIA (Protection of Personal Information Act) compliance
- Consent and provenance tracking
- Compliance reporting
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd

# Runtime references that degrade gracefully when Presidio is unavailable. The
# explicit annotations avoid mypy "Cannot assign to a type" errors when we
# replace the imported classes with fallback implementations.
AnalyzerEngine: type[Any] | None
AnonymizerEngine: type[Any] | None
OperatorConfig: type[Any]

try:
    from presidio_analyzer import AnalyzerEngine as _AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine as _AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig as _OperatorConfig

    AnalyzerEngine = _AnalyzerEngine
    AnonymizerEngine = _AnonymizerEngine
    OperatorConfig = _OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:

    class _OperatorConfigStub:  # pragma: no cover - only used when Presidio missing
        """Fallback operator config when Presidio is unavailable."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    AnalyzerEngine = None
    AnonymizerEngine = None
    OperatorConfig = _OperatorConfigStub
    PRESIDIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataClassification(Enum):
    """Data classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"
    SENSITIVE_PII = "sensitive_pii"


class LawfulBasis(Enum):
    """Lawful basis for processing under POPIA."""

    CONSENT = "consent"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_INTEREST = "public_interest"


class PIIDetector:
    """PII detection service using Presidio."""

    def __init__(self):
        """Initialize PII detector."""
        if not PRESIDIO_AVAILABLE:
            logger.warning("Presidio not available, PII detection will not work")
            self.analyzer = None
            self.anonymizer = None
        else:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()

    def detect_pii(
        self, text: str, language: str = "en", threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """Detect PII entities in text.

        Args:
            text: Text to analyze
            language: Language code
            threshold: Confidence threshold (0-1)

        Returns:
            List of detected PII entities
        """
        if not self.analyzer:
            logger.warning("PII analyzer not initialized")
            return []

        if not text or pd.isna(text):
            return []

        try:
            results = self.analyzer.analyze(text=text, language=language, score_threshold=threshold)

            return [
                {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start : result.end],
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Error detecting PII: {e}")
            return []

    def anonymize_text(self, text: str, operation: str = "replace", language: str = "en") -> str:
        """Anonymize PII in text.

        Args:
            text: Text to anonymize
            operation: Anonymization operation (replace, redact, hash, mask)
            language: Language code

        Returns:
            Anonymized text
        """
        if not self.analyzer or not self.anonymizer:
            logger.warning("PII anonymizer not initialized")
            return text

        if not text or pd.isna(text):
            return text

        try:
            # Detect PII
            results = self.analyzer.analyze(text=text, language=language)

            if not results:
                return text

            # Anonymize
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={"DEFAULT": OperatorConfig(operation)},
            )

            return anonymized.text

        except Exception as e:
            logger.error(f"Error anonymizing text: {e}")
            return text


def detect_pii_in_dataframe(
    df: pd.DataFrame, columns: list[str] | None = None, threshold: float = 0.5
) -> pd.DataFrame:
    """Detect PII in dataframe columns.

    Args:
        df: Input dataframe
        columns: Columns to check (if None, check all string columns)
        threshold: Detection confidence threshold

    Returns:
        Dataframe with PII detection results
    """
    detector = PIIDetector()

    if not detector.analyzer:
        logger.warning("PII detection not available")
        return df

    # Determine columns to check
    if columns is None:
        columns = df.select_dtypes(include=["object"]).columns.tolist()

    result_df = df.copy()

    # Add PII flag columns
    for col in columns:
        pii_col = f"{col}_has_pii"
        pii_types_col = f"{col}_pii_types"

        result_df[pii_col] = False
        result_df[pii_types_col] = None

        for idx, value in df[col].items():
            if pd.isna(value) or not value:
                continue

            pii_entities = detector.detect_pii(str(value), threshold=threshold)

            if pii_entities:
                result_df.at[idx, pii_col] = True
                result_df.at[idx, pii_types_col] = ",".join(
                    sorted(set(e["entity_type"] for e in pii_entities))
                )

    total_pii = sum(result_df[f"{col}_has_pii"].sum() for col in columns)
    logger.info(f"Detected PII in {total_pii} cells across {len(columns)} columns")

    return result_df


def anonymize_dataframe(
    df: pd.DataFrame, columns: list[str] | None = None, operation: str = "replace"
) -> pd.DataFrame:
    """Anonymize PII in dataframe columns.

    Args:
        df: Input dataframe
        columns: Columns to anonymize (if None, anonymize all string columns)
        operation: Anonymization operation (replace, redact, hash, mask)

    Returns:
        Dataframe with anonymized data
    """
    detector = PIIDetector()

    if not detector.anonymizer:
        logger.warning("PII anonymization not available")
        return df

    # Determine columns to anonymize
    if columns is None:
        columns = df.select_dtypes(include=["object"]).columns.tolist()

    result_df = df.copy()

    # Anonymize each column
    anonymized_count = 0
    for col in columns:
        for idx, value in df[col].items():
            if pd.isna(value) or not value:
                continue

            anonymized = detector.anonymize_text(str(value), operation=operation)

            if anonymized != str(value):
                result_df.at[idx, col] = anonymized
                anonymized_count += 1

    logger.info(f"Anonymized {anonymized_count} cells across {len(columns)} columns")

    return result_df


class POPIAPolicy:
    """POPIA compliance policy manager."""

    def __init__(self, policy_config: dict[str, Any] | None = None):
        """Initialize POPIA policy.

        Args:
            policy_config: Policy configuration dictionary
        """
        self.config = policy_config or {}
        self.field_classifications = self.config.get("field_classifications", {})
        self.retention_policies = self.config.get("retention_policies", {})
        self.consent_requirements = self.config.get("consent_requirements", {})

    def classify_field(self, field_name: str) -> DataClassification:
        """Get classification for a field.

        Args:
            field_name: Field name

        Returns:
            Data classification level
        """
        classification = self.field_classifications.get(
            field_name, DataClassification.INTERNAL.value
        )
        return DataClassification(classification)

    def get_retention_period(self, field_name: str) -> int | None:
        """Get retention period for a field in days.

        Args:
            field_name: Field name

        Returns:
            Retention period in days, or None if not specified
        """
        return self.retention_policies.get(field_name)

    def requires_consent(self, field_name: str) -> bool:
        """Check if field requires explicit consent.

        Args:
            field_name: Field name

        Returns:
            True if consent is required
        """
        return self.consent_requirements.get(field_name, False)

    def get_lawful_basis(self, field_name: str) -> LawfulBasis | None:
        """Get lawful basis for processing a field.

        Args:
            field_name: Field name

        Returns:
            Lawful basis for processing
        """
        basis = self.field_classifications.get(field_name, {}).get("lawful_basis")
        return LawfulBasis(basis) if basis else None

    def generate_compliance_report(self, df: pd.DataFrame) -> dict[str, Any]:
        """Generate POPIA compliance report for a dataframe.

        Args:
            df: Dataframe to analyze

        Returns:
            Compliance report dictionary
        """
        pii_fields: list[str] = []
        consent_required_fields: list[str] = []
        retention_policies: dict[str, int] = {}
        compliance_issues: list[str] = []
        field_classifications: dict[str, str] = {}

        # Analyze each field
        for col in df.columns:
            classification = self.classify_field(str(col))
            field_classifications[str(col)] = classification.value

            if classification in [
                DataClassification.PII,
                DataClassification.SENSITIVE_PII,
            ]:
                pii_fields.append(str(col))

            if self.requires_consent(str(col)):
                consent_required_fields.append(str(col))

            retention = self.get_retention_period(str(col))
            if retention:
                retention_policies[str(col)] = retention

        # Check for compliance issues
        if pii_fields and not consent_required_fields:
            compliance_issues.append("PII fields present but no consent requirements configured")

        if not retention_policies:
            compliance_issues.append("No retention policies configured for any fields")

        return {
            "generated_at": datetime.now().isoformat(),
            "total_fields": len(df.columns),
            "total_records": len(df),
            "field_classifications": field_classifications,
            "pii_fields": pii_fields,
            "consent_required_fields": consent_required_fields,
            "retention_policies": retention_policies,
            "compliance_issues": compliance_issues,
        }


def add_provenance_columns(
    df: pd.DataFrame, source_name: str, processing_timestamp: str | None = None
) -> pd.DataFrame:
    """Add provenance tracking columns to dataframe.

    Args:
        df: Input dataframe
        source_name: Name of the data source
        processing_timestamp: Optional timestamp (ISO format)

    Returns:
        Dataframe with provenance columns
    """
    enriched_df = df.copy()

    # Add provenance columns
    enriched_df["data_source"] = source_name
    enriched_df["processed_at"] = processing_timestamp or datetime.now().isoformat()
    enriched_df["consent_status"] = "pending"  # Default status
    enriched_df["consent_date"] = None
    enriched_df["retention_until"] = None  # To be calculated based on policy

    logger.info(f"Added provenance columns for source: {source_name}")

    return enriched_df
