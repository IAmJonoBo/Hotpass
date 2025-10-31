"""Typed helpers for creating optional dependency stubs in tests."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any, Callable, Mapping, Protocol, TypeVar, cast


def fake_module(name: str, attrs: Mapping[str, Any] | None = None) -> ModuleType:
    """Create a ``ModuleType`` with provided attributes and register it in ``sys.modules``."""

    module = ModuleType(name)
    if attrs:
        for key, value in attrs.items():
            setattr(module, key, value)
    sys.modules.setdefault(name, module)
    return module


class RapidFuzzScorer(Protocol):
    """Protocol for RapidFuzz scoring callables."""

    def __call__(self, *args: Any, **kwargs: Any) -> float:
        ...


def make_rapidfuzz_stub() -> ModuleType:
    """Return a stub ``rapidfuzz`` module with deterministic scorers."""

    def _scorer(*_args: Any, **_kwargs: Any) -> float:
        return 100.0

    fuzz_module = fake_module(
        "rapidfuzz.fuzz",
        {
            "token_sort_ratio": _scorer,
            "partial_ratio": _scorer,
            "token_set_ratio": _scorer,
        },
    )
    return fake_module("rapidfuzz", {"fuzz": fuzz_module})


class PanderaDataFrameSchema:
    """Simple placeholder for ``pandera.pandas.DataFrameSchema``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class PanderaColumn:
    """Simple placeholder for ``pandera.pandas.Column``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


def make_pandera_stub() -> ModuleType:
    """Return a stub ``pandera`` module with minimal surface area."""

    pandas_module = fake_module(
        "pandera.pandas",
        {
            "DataFrameSchema": PanderaDataFrameSchema,
            "Column": PanderaColumn,
        },
    )
    errors_module = fake_module(
        "pandera.errors",
        {"SchemaErrors": type("SchemaErrors", (Exception,), {})},
    )
    return fake_module("pandera", {"pandas": pandas_module, "errors": errors_module})


class DuckDBPyConnection:
    """Stub for ``duckdb.DuckDBPyConnection``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


def make_duckdb_stub() -> ModuleType:
    """Return a stub ``duckdb`` module."""

    return fake_module("duckdb", {"DuckDBPyConnection": DuckDBPyConnection})


T = TypeVar("T")


class _PolarsFrame:
    """Very small stand-in for Polars frame/series objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:  # pragma: no cover - simple debugging helper
        return f"_PolarsFrame(args={self.args!r}, kwargs={self.kwargs!r})"


def make_polars_stub() -> ModuleType:
    """Return a stub ``polars`` module covering the surfaces used in tests."""

    def _factory(*args: Any, **kwargs: Any) -> _PolarsFrame:
        return _PolarsFrame(*args, **kwargs)

    return fake_module(
        "polars",
        {
            "DataFrame": _PolarsFrame,
            "LazyFrame": _PolarsFrame,
            "Series": _PolarsFrame,
            "Expr": _PolarsFrame,
            "col": _factory,
            "concat": _factory,
        },
    )


__all__ = [
    "DuckDBPyConnection",
    "PanderaColumn",
    "PanderaDataFrameSchema",
    "RapidFuzzScorer",
    "_PolarsFrame",
    "fake_module",
    "make_duckdb_stub",
    "make_pandera_stub",
    "make_polars_stub",
    "make_rapidfuzz_stub",
]
