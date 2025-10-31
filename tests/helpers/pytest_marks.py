"""Typed wrappers around common pytest marks for mypy."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

import pytest

F = TypeVar("F", bound=Callable[..., object])


def parametrize(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Typed wrapper mirroring ``pytest.mark.parametrize``."""

    def decorator(func: F) -> F:
        return cast(F, pytest.mark.parametrize(*args, **kwargs)(func))

    return decorator


def usefixtures(*names: str) -> Callable[[F], F]:
    """Typed wrapper mirroring ``pytest.mark.usefixtures``."""

    def decorator(func: F) -> F:
        return cast(F, pytest.mark.usefixtures(*names)(func))

    return decorator


def asyncio_mark(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Typed wrapper for ``pytest.mark.asyncio``."""

    def decorator(func: F) -> F:
        return cast(F, pytest.mark.asyncio(*args, **kwargs)(func))

    return decorator


def anyio_mark(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Typed wrapper for ``pytest.mark.anyio``."""

    def decorator(func: F) -> F:
        return cast(F, pytest.mark.anyio(*args, **kwargs)(func))

    return decorator


__all__ = ["parametrize", "usefixtures", "asyncio_mark", "anyio_mark"]
