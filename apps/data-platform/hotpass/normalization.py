"""Utility helpers for normalising and standardising strings."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from .transform import clean_text as _clean_text
from .transform import normalise_identifier
from .transform import normalize_email as _normalize_email
from .transform import normalize_phone as _normalize_phone
from .transform import normalize_website as _normalize_website

_PROVINCE_ALIASES = {
    "gauteng": "Gauteng",
    "gpretoria": "Gauteng",
    "western cape": "Western Cape",
    "wcape": "Western Cape",
    "kwazulu-natal": "KwaZulu-Natal",
    "kwa zulu natal": "KwaZulu-Natal",
    "kzn": "KwaZulu-Natal",
    "eastern cape": "Eastern Cape",
    "north west": "North West",
    "limpopo": "Limpopo",
    "mpumalanga": "Mpumalanga",
    "free state": "Free State",
    "northern cape": "Northern Cape",
}


def coalesce(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def clean_string(value: object | None, max_length: int = 10000) -> str | None:
    """Clean and validate string input with optional length limit for security."""
    return _clean_text(value, max_length=max_length)


def normalize_email(value: str | None) -> str | None:
    return _normalize_email(value)


def normalize_phone(value: str | None, country_code: str = "ZA") -> str | None:
    return _normalize_phone(value, country_code=country_code)


def normalize_website(value: str | None) -> str | None:
    return _normalize_website(value)


def normalize_province(value: str | None) -> str | None:
    value = clean_string(value)
    if not value:
        return None
    key = value.lower().replace("-", " ").replace("  ", " ")
    key = re.sub(r"[^a-z ]+", "", key)
    key = key.replace("province", "").strip()
    return _PROVINCE_ALIASES.get(key, value.title())


def slugify(value: str | None) -> str | None:
    value = clean_string(value)
    if not value:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or None


def join_non_empty(parts: Iterable[str | None], separator: str = " ") -> str | None:
    cleaned: list[str] = []
    for part in parts:
        normalised = clean_string(part)
        if normalised:
            cleaned.append(normalised)
    if not cleaned:
        return None
    return separator.join(cleaned)


def normalize_identifier(value: str | None) -> str | None:
    """Expose identifier normalisation based on python-stdnum helpers."""
    return normalise_identifier(value)
