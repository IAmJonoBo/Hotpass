"""Contact models and helpers with validation-aware scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from hotpass.enrichment.validators import (
    ContactValidationService,
    EmailValidationResult,
    PhoneValidationResult,
    ValidationStatus,
)
from hotpass.transform.scoring import LeadScorer

_VALIDATION_SERVICE = ContactValidationService()
_LEAD_SCORER = LeadScorer()


@dataclass
class Contact:
    """Represents a single contact with role and preference information."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    department: str | None = None
    is_primary: bool = False
    preference_score: float = 0.0
    source_dataset: str | None = None
    source_record_id: str | None = None
    last_interaction: str | None = None
    email_validation: EmailValidationResult | None = None
    phone_validation: PhoneValidationResult | None = None
    lead_score: float = 0.0
    validation_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert contact to dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "department": self.department,
            "is_primary": self.is_primary,
            "preference_score": self.preference_score,
            "source_dataset": self.source_dataset,
            "source_record_id": self.source_record_id,
            "last_interaction": self.last_interaction,
            "email_validation": self.email_validation.as_dict() if self.email_validation else None,
            "phone_validation": self.phone_validation.as_dict() if self.phone_validation else None,
            "lead_score": self.lead_score,
            "validation_flags": list(self.validation_flags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Contact:
        """Create contact from dictionary."""
        contact = cls(
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            role=data.get("role"),
            department=data.get("department"),
            is_primary=data.get("is_primary", False),
            preference_score=data.get("preference_score", 0.0),
            source_dataset=data.get("source_dataset"),
            source_record_id=data.get("source_record_id"),
            last_interaction=data.get("last_interaction"),
            lead_score=data.get("lead_score", 0.0),
            validation_flags=list(data.get("validation_flags", [])),
        )
        email_validation = data.get("email_validation")
        if isinstance(email_validation, dict) and email_validation.get("address"):
            status_raw = email_validation.get("status", ValidationStatus.UNKNOWN)
            if not isinstance(status_raw, ValidationStatus):
                try:
                    status = ValidationStatus(str(status_raw))
                except ValueError:
                    status = ValidationStatus.UNKNOWN
            else:
                status = status_raw
            contact.email_validation = EmailValidationResult(
                address=email_validation.get("address", ""),
                status=status,
                confidence=float(email_validation.get("confidence", 0.0)),
                reason=email_validation.get("reason"),
                mx_hosts=tuple(email_validation.get("mx_hosts", [])),
            )
        phone_validation = data.get("phone_validation")
        if isinstance(phone_validation, dict) and phone_validation.get("number"):
            status_raw = phone_validation.get("status", ValidationStatus.UNKNOWN)
            if not isinstance(status_raw, ValidationStatus):
                try:
                    status = ValidationStatus(str(status_raw))
                except ValueError:
                    status = ValidationStatus.UNKNOWN
            else:
                status = status_raw
            contact.phone_validation = PhoneValidationResult(
                number=phone_validation.get("number", ""),
                status=status,
                confidence=float(phone_validation.get("confidence", 0.0)),
                reason=phone_validation.get("reason"),
                carrier_name=phone_validation.get("carrier"),
                region_code=phone_validation.get("region_code"),
                number_type=phone_validation.get("number_type"),
            )
        return contact

    def calculate_completeness(self) -> float:
        """Calculate how complete this contact record is (0.0 to 1.0)."""
        fields = [self.name, self.email, self.phone, self.role, self.department]
        filled = sum(1 for field in fields if field)
        base_score = filled / len(fields)
        adjustment = 0.0
        if self.email_validation:
            if self.email_validation.status == ValidationStatus.DELIVERABLE:
                adjustment += 0.1 * self.email_validation.confidence
            elif self.email_validation.status == ValidationStatus.UNDELIVERABLE:
                adjustment -= 0.2 * max(0.1, self.email_validation.confidence)
        if self.phone_validation:
            if self.phone_validation.status == ValidationStatus.DELIVERABLE:
                adjustment += 0.08 * self.phone_validation.confidence
            elif self.phone_validation.status == ValidationStatus.UNDELIVERABLE:
                adjustment -= 0.15 * max(0.1, self.phone_validation.confidence)
        score = max(0.0, min(1.0, base_score + adjustment))
        return score


@dataclass
class OrganizationContacts:
    """Manages multiple contacts for an organization."""

    organization_name: str
    contacts: list[Contact] = field(default_factory=list)

    def add_contact(self, contact: Contact) -> None:
        """Add a contact to the organization."""
        self.contacts.append(contact)

    def get_primary_contact(self) -> Contact | None:
        """Get the primary contact, or the best available contact."""
        primary = [c for c in self.contacts if c.is_primary]
        if primary:
            return primary[0]
        if not self.contacts:
            return None
        return max(self.contacts, key=lambda c: c.preference_score)

    def get_contacts_by_role(self, role: str) -> list[Contact]:
        """Get all contacts with a specific role."""
        return [c for c in self.contacts if c.role and c.role.lower() == role.lower()]

    def get_all_emails(self) -> list[str]:
        """Get all unique email addresses."""
        emails = [c.email for c in self.contacts if c.email]
        return list(dict.fromkeys(emails))

    def get_all_phones(self) -> list[str]:
        """Get all unique phone numbers."""
        phones = [c.phone for c in self.contacts if c.phone]
        return list(dict.fromkeys(phones))

    def calculate_preference_scores(
        self,
        source_priority: dict[str, int] | None = None,
        recency_weight: float = 0.2,
        completeness_weight: float = 0.25,
        role_weight: float = 0.2,
        validation_weight: float = 0.2,
        lead_weight: float = 0.15,
        lead_scorer: LeadScorer | None = None,
    ) -> None:
        """Calculate preference scores for all contacts."""
        if source_priority is None:
            source_priority = {}
        lead_model = lead_scorer or _LEAD_SCORER
        role_importance = {
            "ceo": 1.0,
            "director": 0.9,
            "manager": 0.8,
            "owner": 1.0,
            "chief": 0.95,
            "head": 0.85,
            "coordinator": 0.7,
            "admin": 0.6,
            "assistant": 0.5,
        }
        max_priority = max(source_priority.values()) if source_priority else 1.0
        for contact in self.contacts:
            contact.validation_flags = []
            source_score = 0.0
            if contact.source_dataset and max_priority:
                source_score = source_priority.get(contact.source_dataset, 0) / max_priority
            completeness = contact.calculate_completeness()
            role_score = 0.5
            if contact.role:
                role_lower = contact.role.lower()
                for key, value in role_importance.items():
                    if key in role_lower:
                        role_score = value
                        break
            email_confidence = (
                contact.email_validation.confidence if contact.email_validation else 0.0
            )
            phone_confidence = (
                contact.phone_validation.confidence if contact.phone_validation else 0.0
            )
            if contact.email_validation and contact.email_validation.status in {
                ValidationStatus.RISKY,
                ValidationStatus.UNDELIVERABLE,
            }:
                contact.validation_flags.append(f"email:{contact.email_validation.status.value}")
            if contact.phone_validation and contact.phone_validation.status in {
                ValidationStatus.RISKY,
                ValidationStatus.UNDELIVERABLE,
            }:
                contact.validation_flags.append(f"phone:{contact.phone_validation.status.value}")
            validation_score = (
                (email_confidence + phone_confidence) / 2
                if (email_confidence or phone_confidence)
                else 0.0
            )
            lead_score = lead_model.score(
                completeness=completeness,
                email_confidence=email_confidence,
                phone_confidence=phone_confidence,
                source_priority=source_score,
                intent_score=0.0,
            ).value
            contact.lead_score = lead_score
            numerator = (
                source_score * recency_weight
                + completeness * completeness_weight
                + role_score * role_weight
                + validation_score * validation_weight
                + lead_score * lead_weight
            )
            denominator = (
                recency_weight + completeness_weight + role_weight + validation_weight + lead_weight
            )
            contact.preference_score = numerator / denominator if denominator else 0.0

    def to_flat_dict(self) -> dict[str, Any]:
        """Convert to flat dictionary format for SSOT output."""
        primary = self.get_primary_contact()
        result: dict[str, Any] = {
            "organization_name": self.organization_name,
            "contact_primary_name": primary.name if primary else None,
            "contact_primary_email": primary.email if primary else None,
            "contact_primary_phone": primary.phone if primary else None,
            "contact_primary_role": primary.role if primary else None,
            "contact_primary_email_confidence": (
                primary.email_validation.confidence
                if primary and primary.email_validation
                else None
            ),
            "contact_primary_email_status": (
                primary.email_validation.status.value
                if primary and primary.email_validation
                else None
            ),
            "contact_primary_phone_confidence": (
                primary.phone_validation.confidence
                if primary and primary.phone_validation
                else None
            ),
            "contact_primary_phone_status": (
                primary.phone_validation.status.value
                if primary and primary.phone_validation
                else None
            ),
            "contact_primary_lead_score": primary.lead_score if primary else None,
        }
        secondary = [c for c in self.contacts if c != primary]
        if secondary:
            result["contact_secondary_emails"] = ";".join([c.email for c in secondary if c.email])
            result["contact_secondary_phones"] = ";".join([c.phone for c in secondary if c.phone])
            result["contact_secondary_names"] = ";".join([c.name for c in secondary if c.name])
            result["contact_secondary_roles"] = ";".join([c.role for c in secondary if c.role])
        else:
            result["contact_secondary_emails"] = None
            result["contact_secondary_phones"] = None
            result["contact_secondary_names"] = None
            result["contact_secondary_roles"] = None
        result["total_contacts"] = len(self.contacts)
        result["contacts_with_email"] = sum(1 for c in self.contacts if c.email)
        result["contacts_with_phone"] = sum(1 for c in self.contacts if c.phone)
        aggregated_flags = sorted({flag for c in self.contacts for flag in c.validation_flags})
        result["contact_validation_flags"] = (
            ";".join(aggregated_flags) if aggregated_flags else None
        )
        return result


def consolidate_contacts_from_rows(
    organization_name: str,
    rows: pd.DataFrame,
    source_priority: dict[str, int] | None = None,
    *,
    country_code: str = "ZA",
    validator: ContactValidationService | None = None,
    lead_scorer: LeadScorer | None = None,
) -> OrganizationContacts:
    """Consolidate contact information from DataFrame rows."""

    org_contacts = OrganizationContacts(organization_name=organization_name)
    validator = validator or _VALIDATION_SERVICE
    lead_model = lead_scorer or _LEAD_SCORER

    for _, row in rows.iterrows():
        names = row.get("contact_names", [])
        emails = row.get("contact_emails", [])
        phones = row.get("contact_phones", [])
        roles = row.get("contact_roles", [])
        if not isinstance(names, list):
            names = [names] if names else []
        if not isinstance(emails, list):
            emails = [emails] if emails else []
        if not isinstance(phones, list):
            phones = [phones] if phones else []
        if not isinstance(roles, list):
            roles = [roles] if roles else []
        max_len = max(len(names), len(emails), len(phones), len(roles), 1)
        for index in range(max_len):
            name = names[index] if index < len(names) else None
            email = emails[index] if index < len(emails) else None
            phone = phones[index] if index < len(phones) else None
            role = roles[index] if index < len(roles) else None
            if not any([name, email, phone]):
                continue
            contact = Contact(
                name=name,
                email=email,
                phone=phone,
                role=role,
                source_dataset=row.get("source_dataset"),
                source_record_id=row.get("source_record_id"),
                last_interaction=row.get("last_interaction_date"),
            )
            summary = validator.validate_contact(
                email=email,
                phone=phone,
                country_code=country_code,
            )
            contact.email_validation = summary.email
            contact.phone_validation = summary.phone
            contact.validation_flags = summary.flags()
            if summary.email:
                contact.email = summary.email.address
            if summary.phone:
                contact.phone = summary.phone.number
            org_contacts.add_contact(contact)

    org_contacts.calculate_preference_scores(
        source_priority=source_priority,
        lead_scorer=lead_model,
    )
    return org_contacts
