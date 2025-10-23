"""Adapters that ingest and harmonise the legacy Excel inputs."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .normalization import (
    clean_string,
    join_non_empty,
    normalize_email,
    normalize_phone,
    normalize_province,
    normalize_website,
)


@dataclass
class RawRecord:
    organization_name: str
    source_dataset: str
    source_record_id: str
    province: str | None = None
    area: str | None = None
    address: str | None = None
    category: str | None = None
    organization_type: str | None = None
    status: str | None = None
    website: str | None = None
    planes: str | None = None
    description: str | None = None
    notes: str | None = None
    last_interaction_date: str | None = None
    priority: str | None = None
    contact_names: list[str] | None = None
    contact_roles: list[str] | None = None
    contact_emails: list[str] | None = None
    contact_phones: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "organization_name": self.organization_name,
            "source_dataset": self.source_dataset,
            "source_record_id": self.source_record_id,
            "province": self.province,
            "area": self.area,
            "address": self.address,
            "category": self.category,
            "organization_type": self.organization_type,
            "status": self.status,
            "website": self.website,
            "planes": self.planes,
            "description": self.description,
            "notes": self.notes,
            "last_interaction_date": self.last_interaction_date,
            "priority": self.priority,
            "contact_names": self.contact_names or [],
            "contact_roles": self.contact_roles or [],
            "contact_emails": self.contact_emails or [],
            "contact_phones": self.contact_phones or [],
        }


def _extract_normalized_emails(value: object | None) -> list[str]:
    if isinstance(value, str):
        parts = [p.strip() for p in re.split(r"[;,/|]+", value) if p.strip()]
    else:
        parts = []
    emails: list[str] = []
    for part in parts:
        normalised = normalize_email(part)
        if normalised and normalised not in emails:
            emails.append(normalised)
    return emails


def _normalise_contacts(
    df: pd.DataFrame,
    country_code: str,
    name_fields: Iterable[str],
    email_field: str,
    phone_fields: Iterable[str],
    role_field: str | None = None,
) -> list[dict[str, Any]]:
    contacts: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        name_parts = [clean_string(row.get(field)) for field in name_fields]
        name = join_non_empty(name_parts)
        raw_email = row.get(email_field)
        email_candidates = _extract_normalized_emails(raw_email)
        if not email_candidates:
            email_value: str | list[str] | None = None
        elif len(email_candidates) == 1:
            email_value = email_candidates[0]
        else:
            email_value = email_candidates
        phones: list[str] = []
        for field in phone_fields:
            normalised_phone = normalize_phone(row.get(field), country_code=country_code)
            if normalised_phone:
                phones.append(normalised_phone)
        role = clean_string(row.get(role_field)) if role_field else None
        contacts.append(
            {
                "name": name,
                "email": email_value,
                "phones": [phone for phone in phones if phone],
                "role": role,
            }
        )
    return contacts


def _split_contact_fields(
    contacts: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    names: list[str] = []
    roles: list[str] = []
    emails: list[str] = []
    phones: list[str] = []
    for contact in contacts:
        name = contact.get("name")
        if isinstance(name, str) and name:
            names.append(name)
        role = contact.get("role")
        if isinstance(role, str) and role:
            roles.append(role)
        email = contact.get("email")
        if isinstance(email, str) and email:
            emails.append(email)
        elif isinstance(email, list):
            for value in email:
                if isinstance(value, str) and value:
                    emails.append(value)
        contact_phones = contact.get("phones", [])
        if isinstance(contact_phones, list):
            for phone in contact_phones:
                if isinstance(phone, str) and phone:
                    phones.append(phone)
    return names, roles, emails, phones


def load_reachout_database(input_dir: Path, country_code: str) -> pd.DataFrame:
    org_path = input_dir / "Reachout Database.xlsx"
    organisation_df = pd.read_excel(org_path, sheet_name="Organisation")
    contacts_df = pd.read_excel(org_path, sheet_name="Contact Info")

    contact_groups = contacts_df.groupby("ID")
    records: list[RawRecord] = []
    for _, org in organisation_df.iterrows():
        org_id = org.get("ID")
        org_name = clean_string(org.get("Organisation Name"))
        if not org_name:
            continue
        group = (
            contact_groups.get_group(org_id) if org_id in contact_groups.groups else pd.DataFrame()
        )
        contacts = _normalise_contacts(
            group,
            country_code=country_code,
            name_fields=("Firstname", "Surname"),
            email_field="Email",
            phone_fields=("Phone", "WhatsApp"),
            role_field="Position",
        )
        names, roles, emails, phones = _split_contact_fields(contacts)
        primary_description = clean_string(org.get("Description Type"))
        notes = [clean_string(org.get("Notes")), clean_string(org.get("Open Questions"))]
        record = RawRecord(
            organization_name=org_name,
            source_dataset="Reachout Database",
            source_record_id=f"reachout:{org_id}",
            province=normalize_province(org.get("Area")),
            area=clean_string(org.get("Area")),
            address=clean_string(org.get("Address")),
            category=clean_string(org.get("Type")),
            organization_type=clean_string(org.get("Type")),
            website=normalize_website(org.get("Website")),
            planes=clean_string(org.get("Planes")),
            description=join_non_empty(
                [primary_description, clean_string(org.get("Notes"))],
                separator=" | ",
            ),
            notes=join_non_empty(notes, separator=" | "),
            last_interaction_date=clean_string(org.get("Reachout Date")),
            contact_names=names,
            contact_roles=roles,
            contact_emails=emails,
            contact_phones=phones,
        )
        records.append(record)
    return pd.DataFrame([record.as_dict() for record in records])


def load_contact_database(input_dir: Path, country_code: str) -> pd.DataFrame:
    path = input_dir / "Contact Database.xlsx"
    company_df = pd.read_excel(path, sheet_name="Company_Cat")
    contacts_df = pd.read_excel(path, sheet_name="Company_Contacts")
    addresses_df = pd.read_excel(path, sheet_name="Company_Addresses")
    capture_df = pd.read_excel(path, sheet_name="10-10-25 Capture")

    contacts_grouped = contacts_df.groupby("C_ID")
    address_map: dict[str, str] = {}
    for _, addr in addresses_df.iterrows():
        cid = addr.get("C_ID")
        address = join_non_empty([addr.get("Airport"), addr.get("Unnamed: 4")], separator=", ")
        if cid not in address_map and address:
            address_map[cid] = address

    capture_notes: dict[str, str] = {}
    for _, row in capture_df.iterrows():
        school_name = clean_string(row.get("School"))
        description = join_non_empty(
            [clean_string(row.get("Description")), clean_string(row.get("Type"))],
            separator=" | ",
        )
        if school_name and description:
            capture_notes[school_name] = description

    records: list[RawRecord] = []
    for _, company in company_df.iterrows():
        company_name = clean_string(company.get("Company"))
        if not company_name:
            continue
        cid = company.get("C_ID")
        contacts_subset = (
            contacts_grouped.get_group(cid) if cid in contacts_grouped.groups else pd.DataFrame()
        )
        contacts = _normalise_contacts(
            contacts_subset,
            country_code=country_code,
            name_fields=("FirstName", "Surname"),
            email_field="Email",
            phone_fields=("Cellnumber", "Landline"),
            role_field="Position",
        )
        names, roles, emails, phones = _split_contact_fields(contacts)
        records.append(
            RawRecord(
                organization_name=company_name,
                source_dataset="Contact Database",
                source_record_id=f"contact:{cid}",
                province=None,
                area=None,
                address=address_map.get(cid),
                category=clean_string(company.get("Category")),
                organization_type=clean_string(company.get("Category")),
                status=clean_string(company.get("Status")),
                website=normalize_website(company.get("Website")),
                planes=None,
                description=capture_notes.get(company_name),
                notes=None,
                last_interaction_date=clean_string(company.get("LoadDate")),
                priority=clean_string(company.get("Priority")),
                contact_names=names,
                contact_roles=roles,
                contact_emails=emails,
                contact_phones=phones,
            )
        )
    return pd.DataFrame([record.as_dict() for record in records])


def load_sacaa_cleaned(input_dir: Path, country_code: str) -> pd.DataFrame:
    path = input_dir / "SACAA Flight Schools - Refined copy__CLEANED.xlsx"
    df = pd.read_excel(path, sheet_name="Cleaned")
    records: list[RawRecord] = []
    for _, row in df.iterrows():
        org_name = clean_string(row.get("Name of Organisation"))
        if not org_name:
            continue
        email_candidates = _extract_normalized_emails(row.get("Contact Email Address"))
        if not email_candidates:
            contact_email: str | list[str] | None = None
        elif len(email_candidates) == 1:
            contact_email = email_candidates[0]
        else:
            contact_email = email_candidates
        contact_row = {
            "name": clean_string(row.get("Contact Person")),
            "email": contact_email,
            "phones": [normalize_phone(row.get("Contact Number"), country_code=country_code)],
            "role": None,
        }
        names, roles, emails, phones = _split_contact_fields([contact_row])
        website = normalize_website(row.get("Website URL"))
        records.append(
            RawRecord(
                organization_name=org_name,
                source_dataset="SACAA Cleaned",
                source_record_id=f"sacaa:{org_name}",
                province=normalize_province(row.get("Province")),
                area=normalize_province(row.get("Province")),
                address=None,
                category="Flight School",
                organization_type=clean_string(row.get("Status")),
                status=clean_string(row.get("Status")),
                website=website,
                planes=None,
                description=None,
                notes=None,
                last_interaction_date=None,
                contact_names=names,
                contact_roles=roles,
                contact_emails=emails,
                contact_phones=phones,
            )
        )
    return pd.DataFrame([record.as_dict() for record in records])
