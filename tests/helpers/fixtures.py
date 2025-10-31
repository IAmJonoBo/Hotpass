"""Typed pytest fixture decorator helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast, overload

import pytest

P = ParamSpec("P")
R = TypeVar("R")


@overload
def fixture(function: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    ...


@overload
def fixture(
    *,
    scope: str | None = ...,
    params: list[object] | tuple[object, ...] | None = ...,
    autouse: bool = ...,
    ids: list[str] | tuple[str, ...] | Callable[[object], object | None] | None = ...,
    name: str | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]:  # noqa: UP047
    ...


def fixture(*args: Any, **kwargs: Any) -> Any:  # noqa: UP047
    """Typed wrapper around ``pytest.fixture`` to keep mypy satisfied."""

    return cast(Any, pytest.fixture(*args, **kwargs))


__all__ = ["fixture"]
