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

    def fake_probe(
        address: str, domain: str, hosts: tuple[str, ...]
    ) -> SMTPProbeResult:
        return SMTPProbeResult(
            status=ValidationStatus.UNDELIVERABLE,
            confidence=0.25,
            reason="smtp_denied",
        )

    return EmailValidator(dns_lookup=fake_dns, smtp_probe=fake_probe)


def test_email_validator_prefers_smtp_probe(smtp_validator: EmailValidator) -> None:
    """SMTP probe results should influence the deliverability status."""

    result = smtp_validator.validate("alice@hotpass.example")

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


def test_contact_validation_service_combines_channels(
    smtp_validator: EmailValidator,
) -> None:
    """Contact service should return cached summary with composite confidence."""

    service = ContactValidationService(email_validator=smtp_validator)
    summary = service.validate_contact(
        email="alice@hotpass.example",
        phone="+27123456789",
        country_code="ZA",
    )

    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    # Second run should reuse cached results
    summary_again = service.validate_contact(
        email="alice@hotpass.example",
        phone="+27123456789",
        country_code="ZA",
    )
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
    from tests.helpers.assertions import expect
expect(\1, "condition failed: \1")
