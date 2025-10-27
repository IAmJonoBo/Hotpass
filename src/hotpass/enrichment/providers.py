"""Provider adapters powering acquisition agents."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar

from ..data_sources import RawRecord
from ..normalization import (
    clean_string,
    join_non_empty,
    normalize_email,
    normalize_phone,
    normalize_website,
)


@dataclass(slots=True)
class ProviderContext:
    """Contextual information available to providers."""

    country_code: str
    credentials: Mapping[str, str]
    issued_at: datetime


@dataclass(slots=True)
class ProviderPayload:
    """Payload returned by providers for a single entity."""

    record: RawRecord
    provenance: Mapping[str, Any]
    confidence: float = 0.5


class ProviderError(RuntimeError):
    """Raised when a provider fails to produce a payload."""


class BaseProvider:
    """Base class for provider implementations."""

    name: ClassVar[str]

    def __init__(self, options: Mapping[str, Any] | None = None) -> None:
        self.options = dict(options or {})

    def lookup(
        self,
        target_identifier: str,
        target_domain: str | None,
        context: ProviderContext,
    ) -> Iterable[ProviderPayload]:  # pragma: no cover - virtual
        raise NotImplementedError


class ProviderRegistry:
    """Instantiate providers by name."""

    def __init__(self) -> None:
        self._providers: MutableMapping[str, type[BaseProvider]] = {}

    def register(self, name: str, provider_cls: type[BaseProvider]) -> None:
        self._providers[name.lower()] = provider_cls

    def create(self, name: str, options: Mapping[str, Any] | None = None) -> BaseProvider:
        try:
            provider_cls = self._providers[name.lower()]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ProviderError(f"Unknown provider: {name}") from exc
        return provider_cls(options)


REGISTRY = ProviderRegistry()


class LinkedInProvider(BaseProvider):
    """Produce contacts sourced from LinkedIn style profile datasets."""

    name = "linkedin"

    def lookup(
        self,
        target_identifier: str,
        target_domain: str | None,
        context: ProviderContext,
    ) -> Iterable[ProviderPayload]:
        dataset = self.options.get("profiles", {})
        entry = dataset.get(target_identifier) or dataset.get(target_domain or "")
        if not entry:
            return []
        contacts = entry.get("contacts", [])
        records: list[ProviderPayload] = []
        organisation = clean_string(entry.get("organization")) or target_identifier
        for idx, contact in enumerate(contacts, start=1):
            name = clean_string(contact.get("name"))
            if not name:
                continue
            email_value = normalize_email(contact.get("email")) if contact.get("email") else None
            phone_value = (
                normalize_phone(contact.get("phone"), country_code=context.country_code)
                if contact.get("phone")
                else None
            )
            role_value = clean_string(contact.get("title"))
            role_list = [role_value] if role_value else []
            provenance = {
                "provider": self.name,
                "url": entry.get("profile_url"),
                "retrieved_at": context.issued_at.isoformat(),
                "source": "linkedin",
            }
            record = RawRecord(
                organization_name=organisation,
                source_dataset="LinkedIn",
                source_record_id=f"linkedin:{target_identifier}:{idx}",
                province=clean_string(entry.get("province")),
                area=clean_string(entry.get("area")),
                organization_type=clean_string(entry.get("type")),
                status="active",
                website=normalize_website(entry.get("website") or target_domain),
                description=clean_string(entry.get("description")),
                contact_names=[name],
                contact_roles=role_list,
                contact_emails=[email_value] if email_value else [],
                contact_phones=[phone_value] if phone_value else [],
                provenance=[provenance],
            )
            records.append(
                ProviderPayload(
                    record=record,
                    provenance=provenance,
                    confidence=float(contact.get("confidence", 0.6)),
                )
            )
        return records


class ClearbitProvider(BaseProvider):
    """Provide company-level enrichment from Clearbit style datasets."""

    name = "clearbit"

    def lookup(
        self,
        target_identifier: str,
        target_domain: str | None,
        context: ProviderContext,
    ) -> Iterable[ProviderPayload]:
        dataset = self.options.get("companies", {})
        entry = dataset.get(target_domain or target_identifier)
        if not entry:
            return []
        tags = entry.get("tags", [])
        provenance = {
            "provider": self.name,
            "endpoint": "companies/find",
            "retrieved_at": context.issued_at.isoformat(),
            "source": "clearbit",
        }
        record = RawRecord(
            organization_name=clean_string(entry.get("name")) or target_identifier,
            source_dataset="Clearbit",
            source_record_id=f"clearbit:{target_identifier}",
            website=normalize_website(entry.get("domain") or target_domain),
            address=clean_string(entry.get("address")),
            description=clean_string(entry.get("description")),
            category=clean_string(entry.get("category")),
            organization_type=clean_string(entry.get("type")),
            notes=join_non_empty(tags, separator=" | "),
            provenance=[provenance],
        )
        return [
            ProviderPayload(
                record=record,
                provenance=provenance,
                confidence=float(entry.get("confidence", 0.7)),
            )
        ]


class AviationRegistryProvider(BaseProvider):
    """Return fleet details for aviation operators."""

    name = "aviation_registry"

    def lookup(
        self,
        target_identifier: str,
        target_domain: str | None,
        context: ProviderContext,
    ) -> Iterable[ProviderPayload]:
        dataset = self.options.get("fleets", {})
        entry = dataset.get(target_identifier)
        if not entry:
            return []
        planes = entry.get("fleet", [])
        provenance = {
            "provider": self.name,
            "registry": entry.get("registry", "unknown"),
            "retrieved_at": context.issued_at.isoformat(),
            "source": "aviation",
        }
        record = RawRecord(
            organization_name=clean_string(entry.get("name")) or target_identifier,
            source_dataset="Aviation Registry",
            source_record_id=f"aviation:{target_identifier}",
            planes=join_non_empty(planes, separator=", "),
            notes=clean_string(entry.get("notes")),
            provenance=[provenance],
        )
        return [
            ProviderPayload(
                record=record,
                provenance=provenance,
                confidence=float(entry.get("confidence", 0.5)),
            )
        ]


REGISTRY.register(LinkedInProvider.name, LinkedInProvider)
REGISTRY.register(ClearbitProvider.name, ClearbitProvider)
REGISTRY.register(AviationRegistryProvider.name, AviationRegistryProvider)
