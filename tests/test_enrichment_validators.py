"""Tests for email and phone verification services."""

from __future__ import annotations

import pytest

from hotpass.enrichment.validators import (
    ContactValidationService,
    EmailValidator,
    SMTPProbeResult,
    ValidationStatus,
)


@pytest.fixture
def smtp_validator() -> EmailValidator:
    """Email validator wired with deterministic DNS and SMTP probes."""

    def fake_dns(domain: str):
        return (f"mx.{domain}",)

    def fake_probe(address: str, domain: str, hosts: tuple[str, ...]) -> SMTPProbeResult:
        return SMTPProbeResult(
            status=ValidationStatus.UNDELIVERABLE,
            confidence=0.25,
            reason="smtp_denied",
        )

    return EmailValidator(dns_lookup=fake_dns, smtp_probe=fake_probe)


def test_email_validator_prefers_smtp_probe(smtp_validator: EmailValidator) -> None:
    """SMTP probe results should influence the deliverability status."""

    result = smtp_validator.validate("alice@hotpass.example")

    assert result is not None
    assert result.smtp_status == ValidationStatus.UNDELIVERABLE
    assert result.status is ValidationStatus.UNDELIVERABLE
    assert result.reason == "smtp_denied"
    assert pytest.approx(result.confidence, rel=1e-3) == 0.25


def test_contact_validation_service_combines_channels(smtp_validator: EmailValidator) -> None:
    """Contact service should return cached summary with composite confidence."""

    service = ContactValidationService(email_validator=smtp_validator)
    summary = service.validate_contact(
        email="alice@hotpass.example",
        phone="+27123456789",
        country_code="ZA",
    )

    assert summary.email is not None
    assert summary.phone is not None
    assert summary.overall_confidence() > 0
    assert summary.deliverability_score() >= summary.email_confidence() / 2
    # Second run should reuse cached results
    summary_again = service.validate_contact(
        email="alice@hotpass.example",
        phone="+27123456789",
        country_code="ZA",
    )
    assert summary_again.email is summary.email
    assert summary_again.phone is summary.phone
