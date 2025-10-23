"""Utility helpers for normalising and standardising strings."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from urllib.parse import urlparse, urlunparse

import phonenumbers

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


def clean_string(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value).strip() or None


def normalize_email(value: str | None) -> str | None:
    value = clean_string(value)
    if not value:
        return None
    normalized = value.lower()
    if "@" not in normalized:
        return None
    return normalized


def normalize_phone(value: str | None, country_code: str = "ZA") -> str | None:
    value = clean_string(value)
    if not value:
        return None
    digits = re.sub(r"[^0-9+]+", "", value)
    if not digits:
        return None
    try:
        parsed = phonenumbers.parse(digits, country_code)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def normalize_website(value: str | None) -> str | None:
    value = clean_string(value)
    if not value:
        return None
    if not re.match(r"https?://", value, flags=re.I):
        value = f"https://{value}"
    parsed = urlparse(value)
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    netloc = netloc.lower().lstrip()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    normalised_path = path.rstrip("/")
    rebuilt = urlunparse(("https", netloc, normalised_path, "", "", ""))
    return rebuilt.rstrip("/")


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
