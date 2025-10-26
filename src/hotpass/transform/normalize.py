"""Rich text and identifier normalisation helpers."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import phonenumbers

try:
    from stdnum import numdb
    from stdnum.exceptions import InvalidFormat
    from stdnum.util import clean as stdnum_clean
except ImportError:  # pragma: no cover - optional dependency fallback
    numdb = None

    class _InvalidFormatFallback(Exception):
        """Fallback exception mirroring python-stdnum's InvalidFormat."""

    InvalidFormat = _InvalidFormatFallback

    def stdnum_clean(value: str, delete_chars: str) -> str:
        """Basic character stripping fallback when python-stdnum is unavailable."""

        result = value
        for character in delete_chars:
            result = result.replace(character, "")
        return result


from .._compat_nameparser import HumanName

try:  # pragma: no cover - optional modules for locale-specific numbers
    from stdnum.za import postcode as za_postcode  # type: ignore[attr-defined]
    from stdnum.za import vat as za_vat  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback if optional modules missing
    za_postcode = None
    za_vat = None


@dataclass(frozen=True)
class NormalizedName:
    """Structured view of a human name parsed via :mod:`nameparser`."""

    full: str
    given: str | None = None
    middle: str | None = None
    family: str | None = None
    title: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        """Serialise the name into a mapping for downstream consumers."""
        return {
            "full": self.full,
            "given": self.given,
            "middle": self.middle,
            "family": self.family,
            "title": self.title,
        }


def clean_text(value: object | None, *, max_length: int = 10000) -> str | None:
    """Normalise arbitrary values into trimmed unicode strings."""
    if value is None:
        return None
    if isinstance(value, float) and value != value:  # NaN guard
        return None
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    if not text:
        return None
    if len(text) > max_length:
        text = text[:max_length]
    text = unicodedata.normalize("NFKC", text)
    return text or None


def parse_person_name(value: object | None) -> NormalizedName | None:
    """Return a parsed representation of a person's name."""
    text = clean_text(value)
    if not text:
        return None
    name = HumanName(text)
    return NormalizedName(
        full=name.full_name,
        given=name.first or None,
        middle=name.middle or None,
        family=name.last or None,
        title=name.title or None,
    )


def normalize_email(value: object | None) -> str | None:
    """Lower-case and validate email addresses."""
    text = clean_text(value)
    if not text:
        return None
    if "@" not in text:
        return None
    local, _, domain = text.partition("@")
    if not local or not domain:
        return None
    return f"{local.lower()}@{domain.lower()}"


def normalize_phone(value: object | None, *, country_code: str = "ZA") -> str | None:
    """Return an E.164 formatted phone number when valid."""
    text = clean_text(value)
    if not text:
        return None
    digits = re.sub(r"[^0-9+]+", "", text)
    if not digits:
        return None
    try:
        parsed = phonenumbers.parse(digits, country_code)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def normalize_website(value: object | None) -> str | None:
    """Ensure website URLs are https-prefixed and normalised."""
    text = clean_text(value)
    if not text:
        return None
    if not re.match(r"https?://", text, flags=re.I):
        text = f"https://{text}"
    parsed = urlparse(text)
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    netloc = netloc.lower().lstrip()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    clean_path = path.rstrip("/")
    rebuilt = urlunparse(("https", netloc, clean_path, "", "", ""))
    return rebuilt.rstrip("/")


def normalize_vat_number(value: object | None) -> str | None:
    """Validate and canonicalise a South African VAT number when available."""
    text = clean_text(value)
    if not text:
        return None
    cleaned = stdnum_clean(text, " -")
    if za_vat is None:
        return cleaned
    try:
        validated = za_vat.compact(za_vat.validate(cleaned))
    except InvalidFormat:
        return None
    return validated


def normalize_postal_code(value: object | None) -> str | None:
    """Return a canonical postal code for supported regions."""
    text = clean_text(value)
    if not text:
        return None
    cleaned = stdnum_clean(text, " -")
    if za_postcode is not None:
        try:
            return za_postcode.validate(cleaned)
        except InvalidFormat:
            return None
    if cleaned.isdigit() and 3 <= len(cleaned) <= 6:
        return cleaned
    return None


def normalise_identifier(value: object | None) -> str | None:
    """Canonicalise generic identifiers by stripping punctuation and upper-casing."""
    text = clean_text(value)
    if not text:
        return None
    cleaned = stdnum_clean(text, " -/").upper()
    # fall back to python-stdnum database for known patterns when available
    if numdb is not None and numdb.get(cleaned):  # pragma: no cover - optional datasets
        return cleaned
    return cleaned or None
