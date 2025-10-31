"""Typed pytest fixture decorator helpers."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, overload, cast

import pytest

F = TypeVar("F", bound=Callable[..., object])


@overload
def fixture(function: F) -> F:
    ...


@overload
def fixture(
    *,
    scope: str | None = ...,
    params: list[object] | tuple[object, ...] | None = ...,
    autouse: bool = ...,
    ids: list[str] | tuple[str, ...] | Callable[[object], object | None] | None = ...,
    name: str | None = ...,
) -> Callable[[F], F]:
    ...


def fixture(*args: Any, **kwargs: Any) -> Any:
    """Typed wrapper around ``pytest.fixture`` to keep mypy satisfied."""

    return cast(Any, pytest.fixture(*args, **kwargs))


__all__ = ["fixture"]
