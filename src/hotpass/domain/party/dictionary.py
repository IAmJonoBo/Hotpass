"""Generate Markdown documentation for the canonical party schemas."""

from __future__ import annotations

import types
from collections.abc import Iterable
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

from .models import ContactMethod, Party, PartyAlias, PartyRole


def _type_name(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        if getattr(annotation, "__name__", None):
            return annotation.__name__
        return str(annotation)
    args = get_args(annotation)
    if origin is list or origin is tuple:
        inner = ", ".join(_type_name(arg) for arg in args) or "Any"
        bracket = "[" if origin is list else "("
        closing = "]" if origin is list else ")"
        return f"{origin.__name__}{bracket}{inner}{closing}"
    if origin is dict:
        if len(args) == 2:
            return f"dict[{_type_name(args[0])}, {_type_name(args[1])}]"
        return "dict"
    if origin in {Union, getattr(types, "UnionType", Union)}:  # pragma: no cover - Py<3.10
        return " | ".join(_type_name(arg) for arg in args)
    return str(annotation)


def _document_model(model: type[BaseModel]) -> str:
    lines = [
        f"### `{model.__name__}`",
        "",
        "| Field | Type | Required | Description |",
        "| --- | --- | --- | --- |",
    ]
    for name, field in model.model_fields.items():
        annotation = field.annotation or Any
        field_type = _type_name(annotation)
        required = "Yes" if field.is_required() else "No"
        description = field.description or ""
        lines.append(f"| `{name}` | `{field_type}` | {required} | {description} |")
    lines.append("")
    return "\n".join(lines)


def render_dictionary(models: Iterable[type[BaseModel]] | None = None) -> str:
    """Render the Hotpass data dictionary for the canonical party schemas."""

    models = tuple(models or (Party, PartyAlias, PartyRole, ContactMethod))
    sections = ["# Hotpass Data Dictionary", ""]
    for model in models:
        sections.append(_document_model(model))
    return "\n".join(sections)
