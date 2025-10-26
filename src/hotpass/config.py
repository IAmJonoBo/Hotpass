"""Configuration management for industry profiles and pipeline settings."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - fallback when PyYAML missing at runtime
    yaml = cast("Any", None)


@dataclass
class IndustryProfile:
    """Configuration profile for industry-specific terminology and rules."""

    name: str
    display_name: str
    default_country_code: str = "ZA"

    # Field terminology mappings
    organization_term: str = "organization"
    organization_type_term: str = "organization_type"
    organization_category_term: str = "category"

    # Validation thresholds
    email_validation_threshold: float = 0.85
    phone_validation_threshold: float = 0.85
    website_validation_threshold: float = 0.75

    # Source priority mapping (higher is better)
    source_priorities: dict[str, int] = field(default_factory=dict)

    # Column synonyms for intelligent mapping
    column_synonyms: dict[str, list[str]] = field(default_factory=dict)

    # Required vs optional fields
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)

    # Custom validation rules
    custom_validators: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndustryProfile:
        """Create profile from dictionary."""
        return cls(
            name=data.get("name", "generic"),
            display_name=data.get("display_name", "Generic"),
            default_country_code=data.get("default_country_code", "ZA"),
            organization_term=data.get("organization_term", "organization"),
            organization_type_term=data.get(
                "organization_type_term", "organization_type"
            ),
            organization_category_term=data.get(
                "organization_category_term", "category"
            ),
            email_validation_threshold=data.get("email_validation_threshold", 0.85),
            phone_validation_threshold=data.get("phone_validation_threshold", 0.85),
            website_validation_threshold=data.get("website_validation_threshold", 0.75),
            source_priorities=data.get("source_priorities", {}),
            column_synonyms=data.get("column_synonyms", {}),
            required_fields=data.get("required_fields", []),
            optional_fields=data.get("optional_fields", []),
            custom_validators=data.get("custom_validators", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "default_country_code": self.default_country_code,
            "organization_term": self.organization_term,
            "organization_type_term": self.organization_type_term,
            "organization_category_term": self.organization_category_term,
            "email_validation_threshold": self.email_validation_threshold,
            "phone_validation_threshold": self.phone_validation_threshold,
            "website_validation_threshold": self.website_validation_threshold,
            "source_priorities": self.source_priorities,
            "column_synonyms": self.column_synonyms,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "custom_validators": self.custom_validators,
        }


def load_industry_profile(
    profile_name: str, config_dir: Path | None = None
) -> IndustryProfile:
    """Load an industry profile from configuration directory."""
    if config_dir is None:
        config_dir = Path(__file__).parent / "profiles"

    profile_path = config_dir / f"{profile_name}.yaml"

    # Try YAML first
    if profile_path.exists():
        with open(profile_path) as f:
            data = yaml.safe_load(f)
            return IndustryProfile.from_dict(data)

    # Try JSON
    json_path = config_dir / f"{profile_name}.json"
    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
            return IndustryProfile.from_dict(data)

    # Return default profile
    return get_default_profile(profile_name)


def get_default_profile(profile_name: str = "generic") -> IndustryProfile:
    """Get a built-in default profile."""
    if profile_name == "aviation":
        return IndustryProfile(
            name="aviation",
            display_name="Aviation & Flight Training",
            default_country_code="ZA",
            organization_term="flight_school",
            organization_type_term="school_type",
            organization_category_term="training_category",
            source_priorities={
                "SACAA Cleaned": 3,
                "Reachout Database": 2,
                "Contact Database": 1,
            },
            column_synonyms={
                "organization_name": [
                    "school_name",
                    "institution_name",
                    "provider_name",
                    "company_name",
                    "account_name",
                    "organisation_name",
                ],
                "contact_email": [
                    "email",
                    "email_address",
                    "primary_email",
                    "contact_email_address",
                    "e-mail",
                    "e_mail",
                    "mail",
                ],
                "contact_phone": [
                    "phone",
                    "telephone",
                    "phone_number",
                    "contact_number",
                    "tel",
                    "mobile",
                    "cell",
                    "cellphone",
                ],
                "website": [
                    "url",
                    "website_url",
                    "web_address",
                    "homepage",
                    "site",
                    "web",
                ],
                "province": ["state", "region", "area", "territory"],
            },
            required_fields=["organization_name"],
            optional_fields=[
                "contact_primary_email",
                "contact_primary_phone",
                "website",
                "province",
                "address_primary",
            ],
        )

    # Generic profile for any industry
    return IndustryProfile(
        name="generic",
        display_name="Generic Business",
        default_country_code="ZA",
        column_synonyms={
            "organization_name": [
                "name",
                "company",
                "business",
                "entity",
                "organization",
                "company_name",
                "business_name",
                "organisation",
            ],
            "contact_email": [
                "email",
                "email_address",
                "e-mail",
                "e_mail",
                "mail",
                "contact_email",
                "primary_email",
            ],
            "contact_phone": [
                "phone",
                "telephone",
                "phone_number",
                "tel",
                "mobile",
                "cell",
                "cellphone",
                "contact_number",
            ],
            "website": ["url", "website", "web", "homepage", "site", "web_address"],
            "address": [
                "address",
                "location",
                "street_address",
                "mailing_address",
                "physical_address",
            ],
        },
        required_fields=["organization_name"],
        optional_fields=[
            "contact_primary_email",
            "contact_primary_phone",
            "website",
            "province",
            "address_primary",
        ],
    )


def save_industry_profile(profile: IndustryProfile, config_dir: Path) -> None:
    """Save an industry profile to YAML."""
    config_dir.mkdir(parents=True, exist_ok=True)
    profile_path = config_dir / f"{profile.name}.yaml"

    with open(profile_path, "w") as f:
        yaml.dump(profile.to_dict(), f, default_flow_style=False, sort_keys=False)
