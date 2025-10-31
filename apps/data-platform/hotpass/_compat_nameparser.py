"""Provide a lightweight :class:`HumanName` fallback when nameparser is absent."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from typing import Any, cast


def _load_human_name_class() -> type[Any]:
    spec = importlib.util.find_spec("nameparser")
    if spec is not None and spec.origin is not None:
        module = importlib.import_module("nameparser")
        human_name = getattr(module, "HumanName", None)
        if isinstance(human_name, type):
            return cast(type[Any], human_name)

    @dataclass
    class _FallbackHumanName:
        """Very small subset of :class:`nameparser.HumanName` for tests."""

        original: str
        full_name: str = ""
        first: str = ""
        middle: str = ""
        last: str = ""
        title: str = ""

        def __post_init__(self) -> None:
            parts = self.original.strip().split()
            self.full_name = self.original.strip()
            self.first = parts[0] if parts else ""
            self.middle = " ".join(parts[1:-1]) if len(parts) > 2 else ""
            self.last = parts[-1] if len(parts) > 1 else ""
            self.title = ""

        def __getattr__(self, item: str) -> str:
            if item == "full_name":
                return self.full_name
            if item == "first":
                return self.first
            if item == "middle":
                return self.middle
            if item == "last":
                return self.last
            if item == "title":
                return self.title
            raise AttributeError(item)

    return _FallbackHumanName


HumanName = _load_human_name_class()

__all__ = ["HumanName"]
