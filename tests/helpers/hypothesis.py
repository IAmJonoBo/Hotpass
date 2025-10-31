
"""Typed wrappers around Hypothesis decorators for mypy."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, overload, cast

from hypothesis import HealthCheck as HealthCheck  # re-export
from hypothesis import given as _given
from hypothesis import settings as _settings
from hypothesis.strategies import SearchStrategy
from hypothesis.strategies import composite as _composite
from hypothesis import strategies as st  # re-export for convenience

F = TypeVar("F", bound=Callable[..., object])
T = TypeVar("T")


@overload
def given(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...


def given(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Typed wrapper around ``hypothesis.given``."""

    def decorator(func: F) -> F:
        return cast(F, _given(*args, **kwargs)(func))

    return decorator


@overload
def settings(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...


def settings(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Typed wrapper around ``hypothesis.settings``."""

    def decorator(func: F) -> F:
        return cast(F, _settings(*args, **kwargs)(func))

    return decorator


def composite(*args: Any, **kwargs: Any) -> Callable[[Callable[..., T]], Callable[..., SearchStrategy[T]]]:
    """Typed wrapper around ``hypothesis.strategies.composite``."""

    def decorator(func: Callable[..., T]) -> Callable[..., SearchStrategy[T]]:
        return cast(Callable[..., SearchStrategy[T]], _composite(*args, **kwargs)(func))

    return decorator


__all__ = ["given", "settings", "composite", "HealthCheck", "st", "SearchStrategy"]
