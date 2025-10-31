"""Typed wrappers around common Hypothesis decorators to appease mypy."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast, overload

from hypothesis import HealthCheck as HealthCheck  # re-export
from hypothesis import given as _given
from hypothesis import settings as _settings
from hypothesis.strategies import composite as _composite
from hypothesis import strategies as st  # re-export for convenience

F = TypeVar("F", bound=Callable[..., object])


@overload
def given(function: F) -> F: ...


@overload
def given(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...


def given(*args: Any, **kwargs: Any):
    """Typed wrapper around ``hypothesis.given``."""

    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        func = cast(F, args[0])
        return cast(F, _given()(func))

    def decorator(func: F) -> F:
        return cast(F, _given(*args, **kwargs)(func))

    return decorator


@overload
def settings(function: F) -> F: ...


@overload
def settings(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...


def settings(*args: Any, **kwargs: Any):
    """Typed wrapper around ``hypothesis.settings``."""

    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        func = cast(F, args[0])
        return cast(F, _settings()(func))

    def decorator(func: F) -> F:
        return cast(F, _settings(*args, **kwargs)(func))

    return decorator


@overload
def composite(function: F) -> F: ...


@overload
def composite(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...


def composite(*args: Any, **kwargs: Any):
    """Typed wrapper around ``hypothesis.strategies.composite``."""

    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        func = cast(F, args[0])
        return cast(F, _composite()(func))

    def decorator(func: F) -> F:
        return cast(F, _composite(*args, **kwargs)(func))

    return decorator


__all__ = ["given", "settings", "composite", "HealthCheck", "st"]
