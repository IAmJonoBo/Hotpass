from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from hotpass.cli.main import main as cli_main


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class DummyLogger:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.events: list[tuple[str, dict[str, object]]] = []
        self.console = None

    def log_error(self, message: str) -> None:
        self.errors.append(message)

    def log_event(self, name: str, payload: dict[str, object]) -> None:
        self.events.append((name, payload))


@pytest.mark.usefixtures("monkeypatch")
def test_resolve_profile_defaults(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "duplicates.csv"
    output_path = tmp_path / "deduped.csv"
    dataset = pd.DataFrame(
        {
            "organization_name": ["Acme Flight", "Acme Flight"],
            "contact_email": ["ops@acme.test", "ops@acme.test"],
            "contact_phone": ["+2711000000", "+2711000000"],
        }
    )
    dataset.to_csv(input_path, index=False)

    profile_path = tmp_path / "advanced-resolve.toml"
    profile_path.write_text(
        """
name = "advanced-resolve"
summary = "Advanced resolve coverage"
log_format = "json"
industry_profile = "test"

[features]
entity_resolution = true

[options]
sensitive_fields = ["contact_email"]
"""
    )

    captured: dict[str, object] = {}

    def fake_structured_logger(log_format: str, sensitive_fields: tuple[str, ...]) -> DummyLogger:
        captured["log_format"] = log_format
        captured["sensitive_fields"] = tuple(sensitive_fields)
        return DummyLogger()

    class DummyResult:
        def __init__(self, deduped: pd.DataFrame) -> None:
            self.deduplicated = deduped
            self.matches = pd.DataFrame({"classification": []})
            self.review_queue = pd.DataFrame({"classification": []})
            from hotpass.linkage import LinkageThresholds

            self.thresholds = LinkageThresholds(high=0.9, review=0.7)

    def fake_link_entities(df: pd.DataFrame, config: Any) -> DummyResult:
        captured["use_splink"] = config.use_splink
        captured["threshold_high"] = config.thresholds.high
        captured["threshold_review"] = config.thresholds.review
        return DummyResult(df.iloc[[0]].copy())

    monkeypatch.setattr("hotpass.cli.commands.resolve.StructuredLogger", fake_structured_logger)
    monkeypatch.setattr("hotpass.cli.commands.resolve.link_entities", fake_link_entities)

    exit_code = cli_main(
        [
            "resolve",
            "--input-file",
            str(input_path),
            "--output-file",
            str(output_path),
            "--profile",
            str(profile_path),
        ]
    )

    expect(exit_code == 0, "Resolve command should succeed with advanced profile")
    expect(output_path.exists(), "Deduplicated output should be written")
    expect(captured.get("log_format") == "json", "Profile should enforce JSON log format")
    sensitive_fields = captured.get("sensitive_fields", ())
    expect(
        isinstance(sensitive_fields, tuple) and "contact_email" in sensitive_fields,
        "Sensitive fields from profile should propagate",
    )
    expect(
        captured.get("threshold_high") == 0.9,
        "Match threshold should honour CLI defaults when not overridden",
    )
    expect(
        captured.get("threshold_review") == 0.7,
        "Review threshold should honour CLI defaults when not overridden",
    )
    expect(captured.get("use_splink") is True, "Entity resolution feature flag should enable Splink")
    expect(output_path.read_text().strip() != "", "Output CSV should contain data")
