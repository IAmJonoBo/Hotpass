"""Centralised warning configuration for Hotpass runtime."""

from __future__ import annotations

import warnings

from marshmallow.warnings import ChangedInMarshmallow4Warning

warnings.filterwarnings(
    "ignore",
    category=ChangedInMarshmallow4Warning,
    message=(
        "`Number` field should not be instantiated. Use `Integer`, `Float`, or `Decimal` instead."
    ),
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="module 'sre_constants' is deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="module 'sre_parse' is deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="Importing pandas-specific classes and functions from the",
)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="pandera._pandas_deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="`result_format` configured at the Validator-level will not be persisted",
)
warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message="Implicitly cleaning up <TemporaryDirectory",
)
warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message="unclosed database",
)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=("Could not infer format, so each element will be parsed individually"),
)
