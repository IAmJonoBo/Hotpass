"""Enhanced contact management for organizations with multiple contacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


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
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Contact:
        """Create contact from dictionary."""
        return cls(
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
        )

    def calculate_completeness(self) -> float:
        """Calculate how complete this contact record is (0.0 to 1.0)."""
        fields = [self.name, self.email, self.phone, self.role, self.department]
        filled = sum(1 for field in fields if field)
        return filled / len(fields)


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
        # First, check for explicitly marked primary
        primary = [c for c in self.contacts if c.is_primary]
        if primary:
            return primary[0]

        # If no primary, return contact with highest preference score
        if not self.contacts:
            return None

        return max(self.contacts, key=lambda c: c.preference_score)

    def get_contacts_by_role(self, role: str) -> list[Contact]:
        """Get all contacts with a specific role."""
        return [c for c in self.contacts if c.role and c.role.lower() == role.lower()]

    def get_all_emails(self) -> list[str]:
        """Get all unique email addresses."""
        emails = [c.email for c in self.contacts if c.email]
        return list(dict.fromkeys(emails))  # Preserve order, remove duplicates

    def get_all_phones(self) -> list[str]:
        """Get all unique phone numbers."""
        phones = [c.phone for c in self.contacts if c.phone]
        return list(dict.fromkeys(phones))  # Preserve order, remove duplicates

    def calculate_preference_scores(
        self,
        source_priority: dict[str, int] | None = None,
        recency_weight: float = 0.3,
        completeness_weight: float = 0.3,
        role_weight: float = 0.4,
    ) -> None:
        """
        Calculate preference scores for all contacts.

        Args:
            source_priority: Mapping of source dataset names to priority scores
            recency_weight: Weight for recency in score calculation
            completeness_weight: Weight for completeness in score calculation
            role_weight: Weight for role importance in score calculation
        """
        if source_priority is None:
            source_priority = {}

        # Define role importance
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

        for contact in self.contacts:
            # Source priority score (normalized)
            source_score = 0.0
            if contact.source_dataset:
                max_priority = max(source_priority.values()) if source_priority else 1
                source_score = (
                    source_priority.get(contact.source_dataset, 0) / max_priority
                )

            # Completeness score
            completeness = contact.calculate_completeness()

            # Role importance score
            role_score = 0.5  # Default for unknown roles
            if contact.role:
                role_lower = contact.role.lower()
                for key, value in role_importance.items():
                    if key in role_lower:
                        role_score = value
                        break

            # Combined preference score
            contact.preference_score = (
                source_score * recency_weight
                + completeness * completeness_weight
                + role_score * role_weight
            )

    def to_flat_dict(self) -> dict[str, Any]:
        """
        Convert to flat dictionary format for SSOT output.

        Returns primary contact info plus secondary contacts as delimited strings.
        """
        primary = self.get_primary_contact()

        result: dict[str, Any] = {
            "organization_name": self.organization_name,
            "contact_primary_name": primary.name if primary else None,
            "contact_primary_email": primary.email if primary else None,
            "contact_primary_phone": primary.phone if primary else None,
            "contact_primary_role": primary.role if primary else None,
        }

        # Get secondary contacts (all except primary)
        secondary = [c for c in self.contacts if c != primary]

        if secondary:
            result["contact_secondary_emails"] = ";".join(
                [c.email for c in secondary if c.email]
            )
            result["contact_secondary_phones"] = ";".join(
                [c.phone for c in secondary if c.phone]
            )
            result["contact_secondary_names"] = ";".join(
                [c.name for c in secondary if c.name]
            )
            result["contact_secondary_roles"] = ";".join(
                [c.role for c in secondary if c.role]
            )
        else:
            result["contact_secondary_emails"] = None
            result["contact_secondary_phones"] = None
            result["contact_secondary_names"] = None
            result["contact_secondary_roles"] = None

        # Add count metrics
        result["total_contacts"] = len(self.contacts)
        result["contacts_with_email"] = sum(1 for c in self.contacts if c.email)
        result["contacts_with_phone"] = sum(1 for c in self.contacts if c.phone)

        return result


def consolidate_contacts_from_rows(
    organization_name: str,
    rows: pd.DataFrame,
    source_priority: dict[str, int] | None = None,
) -> OrganizationContacts:
    """
    Consolidate contact information from multiple rows into an OrganizationContacts object.

    Args:
        organization_name: Name of the organization
        rows: DataFrame rows for this organization
        source_priority: Mapping of source dataset names to priority scores

    Returns:
        OrganizationContacts with all contacts and calculated preference scores
    """
    org_contacts = OrganizationContacts(organization_name=organization_name)

    for _, row in rows.iterrows():
        # Extract contact information from row
        names = row.get("contact_names", [])
        emails = row.get("contact_emails", [])
        phones = row.get("contact_phones", [])
        roles = row.get("contact_roles", [])

        # Ensure all are lists
        if not isinstance(names, list):
            names = [names] if names else []
        if not isinstance(emails, list):
            emails = [emails] if emails else []
        if not isinstance(phones, list):
            phones = [phones] if phones else []
        if not isinstance(roles, list):
            roles = [roles] if roles else []

        # Create contacts from available information
        max_len = max(len(names), len(emails), len(phones), len(roles), 1)

        for i in range(max_len):
            name = names[i] if i < len(names) else None
            email = emails[i] if i < len(emails) else None
            phone = phones[i] if i < len(phones) else None
            role = roles[i] if i < len(roles) else None

            # Only create contact if at least one field is present
            if name or email or phone:
                contact = Contact(
                    name=name,
                    email=email,
                    phone=phone,
                    role=role,
                    source_dataset=row.get("source_dataset"),
                    source_record_id=row.get("source_record_id"),
                    last_interaction=row.get("last_interaction_date"),
                )
                org_contacts.add_contact(contact)

    # Calculate preference scores
    org_contacts.calculate_preference_scores(source_priority=source_priority)

    return org_contacts
