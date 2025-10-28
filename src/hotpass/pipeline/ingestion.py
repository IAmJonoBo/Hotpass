from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from ..compliance import redact_dataframe
from ..data_sources import (
    ExcelReadOptions,
    load_contact_database,
    load_reachout_database,
    load_sacaa_cleaned,
)
from ..data_sources.agents import run_plan as run_acquisition_plan
from ..normalization import normalize_province, slugify
from .config import PipelineConfig


def _load_agent_frame(config: PipelineConfig) -> tuple[pd.DataFrame, dict[str, float]]:
    if config.preloaded_agent_frame is not None:
        frame = config.preloaded_agent_frame.copy(deep=True)
        timings = {
            f"agent:{timing.agent_name}": timing.seconds
            for timing in config.preloaded_agent_timings
        }
        return frame, timings

    if not (config.acquisition_plan and config.acquisition_plan.enabled):
        return pd.DataFrame(), {}

    frame, agent_timings, warnings = run_acquisition_plan(
        config.acquisition_plan,
        country_code=config.country_code,
        credentials=config.agent_credentials,
    )
    config.preloaded_agent_frame = frame.copy(deep=True)
    config.preloaded_agent_timings = list(agent_timings)
    config.preloaded_agent_warnings.extend(warnings)
    timings = {f"agent:{timing.agent_name}": timing.seconds for timing in agent_timings}
    return frame, timings


def load_sources(
    input_dir: Path,
    country_code: str,
    excel_options: ExcelReadOptions | None,
) -> Mapping[str, pd.DataFrame]:
    loaders = {
        "Reachout Database": load_reachout_database,
        "Contact Database": load_contact_database,
        "SACAA Cleaned": load_sacaa_cleaned,
    }
    frames: dict[str, pd.DataFrame] = {}
    for label, loader in loaders.items():
        try:
            frame = loader(input_dir, country_code, excel_options)
        except FileNotFoundError:
            continue
        if not frame.empty:
            frames[label] = frame
    return frames


def ingest_sources(
    config: PipelineConfig,
) -> tuple[pd.DataFrame, dict[str, float], list[dict[str, Any]]]:
    agent_frame, agent_timings = _load_agent_frame(config)

    source_timings: dict[str, float] = dict(agent_timings)
    frames: list[pd.DataFrame] = []
    if not agent_frame.empty:
        frames.append(agent_frame)

    for label, frame in load_sources(
        config.input_dir, config.country_code, config.excel_options
    ).items():
        frames.append(frame)
        source_timings[label] = frame.attrs.get("load_seconds", 0.0)

    if not frames:
        return _empty_sources_frame(), source_timings, []

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined["organization_slug"] = combined["organization_name"].apply(slugify)
    combined["province"] = combined["province"].apply(normalize_province)
    return combined, source_timings, []


def apply_redaction(
    config: PipelineConfig, frame: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    if not config.pii_redaction.enabled:
        return frame, []
    return redact_dataframe(frame, config.pii_redaction)


def _empty_sources_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "organization_name",
            "source_dataset",
            "source_record_id",
            "province",
            "area",
            "address",
            "category",
            "organization_type",
            "status",
            "website",
            "planes",
            "description",
            "notes",
            "last_interaction_date",
            "priority",
            "contact_names",
            "contact_roles",
            "contact_emails",
            "contact_phones",
        ]
    )
