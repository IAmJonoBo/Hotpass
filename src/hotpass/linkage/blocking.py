"""Deterministic blocking strategies for probabilistic linkage."""

from __future__ import annotations

from collections.abc import Iterable


def default_blocking_rules() -> list[str]:
    """Return deterministic Splink blocking rules that suit Hotpass data."""

    return [
        "l.linkage_slug = r.linkage_slug",
        "l.contact_primary_email IS NOT NULL AND l.contact_primary_email = r.contact_primary_email",
        "rapidfuzz_token_sort_ratio(l.linkage_name, r.linkage_name) >= 0.96",
        "rapidfuzz_partial_ratio(l.linkage_phone, r.linkage_phone) >= 0.92",
    ]


def review_payload_fields(default_fields: Iterable[str] | None = None) -> tuple[str, ...]:
    """Return fields that should accompany review tasks."""

    baseline = (
        "organization_name",
        "organization_slug",
        "province",
        "address_primary",
        "contact_primary_email",
        "contact_primary_phone",
    )
    if default_fields is None:
        return baseline
    merged = tuple(dict.fromkeys([*baseline, *default_fields]))
    return merged
