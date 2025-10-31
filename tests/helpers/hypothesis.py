"""Typed wrappers around Hypothesis decorators for mypy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast, overload

from hypothesis import HealthCheck as HealthCheck  # re-export
from hypothesis import given as _given
from hypothesis import settings as _settings
from hypothesis import strategies as st  # re-export for convenience
from hypothesis.strategies import SearchStrategy
from hypothesis.strategies import composite as _composite

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

# ``draw`` callbacks receive a strategy and return a generated value.
DrawFn = Callable[[SearchStrategy[Any]], Any]


def given(*args: Any, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Typed wrapper around ``hypothesis.given``."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return cast(Callable[P, R], _given(*args, **kwargs)(func))

    return decorator


def settings(*args: Any, **kwargs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Typed wrapper around ``hypothesis.settings``."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return cast(Callable[P, R], _settings(*args, **kwargs)(func))

    return decorator


@overload
def composite(func: Callable[P, T]) -> Callable[P, SearchStrategy[T]]:  # noqa: UP047
    ...


@overload
def composite(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[P, T]], Callable[P, SearchStrategy[T]]]:  # noqa: UP047
    ...


def composite(*args: Any, **kwargs: Any) -> Any:
    """Typed wrapper around ``hypothesis.strategies.composite`` with bare and factory usage."""

    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        func = cast(Callable[P, T], args[0])
        return cast(Callable[P, SearchStrategy[T]], _composite(func))

    def decorator(func: Callable[P, T]) -> Callable[P, SearchStrategy[T]]:
        return cast(Callable[P, SearchStrategy[T]], _composite(*args, **kwargs)(func))

    return decorator


__all__ = ["DrawFn", "HealthCheck", "SearchStrategy", "composite", "given", "settings", "st"]
