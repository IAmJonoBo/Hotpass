"""Tests for the ARC runner lifecycle verification helpers."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from scripts.arc.verify_runner_lifecycle import RunnerLifecycleVerifier


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


@dataclass
class _Response:
    json_payload: dict[str, Any]

    def json(self) -> dict[str, Any]:
        return self.json_payload

    def raise_for_status(self) -> None:  # noqa: D401 - behaviour is mocked
        """Mimic `requests.Response.raise_for_status`."""
        return None


class _Session:
    def __init__(self, payloads: Iterator[dict[str, Any]]) -> None:
        self._payloads = payloads
        self.request_count = 0

    def get(self, url: str, headers: dict[str, str], timeout: float) -> _Response:  # noqa: ARG002
        self.request_count += 1
        try:
            payload = next(self._payloads)
        except StopIteration as exc:  # pragma: no cover - guard for unexpected calls
            raise AssertionError("No more payloads configured for test") from exc
        return _Response(json_payload=payload)


class _Command:
    def __init__(self, results: Iterator[str]) -> None:
        self._results = results
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        try:
            return next(self._results)
        except StopIteration as exc:  # pragma: no cover - guard for unexpected calls
            raise AssertionError("No more command results configured for test") from exc


class _Clock:
    def __init__(self, values: Iterator[float]) -> None:
        self._values = values

    def __call__(self) -> float:
        try:
            return next(self._values)
        except StopIteration as exc:  # pragma: no cover - guard for unexpected calls
            raise AssertionError("Clock exhausted during test") from exc


class _Sleeper:
    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, duration: float) -> None:
        self.calls.append(duration)


class _VerifierFactory:
    def __init__(
        self,
        github_payloads: Iterator[dict[str, Any]],
        command_results: Iterator[str],
        clock_values: Iterator[float],
        poll_interval: float,
        timeout: float,
    ) -> None:
        self.session = _Session(payloads=github_payloads)
        self.command = _Command(results=command_results)
        self.clock = _Clock(values=clock_values)
        self.sleeper = _Sleeper()
        self.verifier = RunnerLifecycleVerifier(
            owner="Hotpass",
            repository="pipeline",
            scale_set="hotpass-arc",
            namespace="arc-runners",
            session=self.session,
            run_command=self.command,
            now=self.clock,
            sleep=self.sleeper,
            timeout_seconds=timeout,
            poll_interval=poll_interval,
        )


def _build_verifier(
    github_payloads: Iterator[dict[str, Any]],
    command_results: Iterator[str],
    clock_values: Iterator[float],
    poll_interval: float = 1.0,
    timeout: float = 5.0,
) -> tuple[RunnerLifecycleVerifier, _Sleeper]:
    factory = _VerifierFactory(
        github_payloads=github_payloads,
        command_results=command_results,
        clock_values=clock_values,
        poll_interval=poll_interval,
        timeout=timeout,
    )
    return factory.verifier, factory.sleeper


def test_verifier_succeeds_when_runners_idle() -> None:
    payloads = iter([
        {"total_count": 1, "runners": [{"busy": True, "name": "hotpass-arc-1"}]},
        {"total_count": 1, "runners": [{"busy": False, "name": "hotpass-arc-1"}]},
    ])
    command_results = iter(["runner-pod", ""])  # kubectl output shows pod until drained
    clock_values = iter([0.0, 1.0, 2.1])

    verifier, sleeper = _build_verifier(payloads, command_results, clock_values)
    verifier.verify()

    expect(len(sleeper.calls) == 1, "Verifier should sleep while waiting for drain")


def test_verifier_raises_when_timeout_expires() -> None:
    payloads = iter([{"total_count": 1, "runners": [{"busy": True, "name": "hotpass-arc-1"}]}] * 4)
    command_results = iter(["runner-pod", "runner-pod"])  # pods never drain
    clock_values = iter([0.0, 1.0, 2.0, 3.1])

    verifier, _ = _build_verifier(
        payloads,
        command_results,
        clock_values,
        poll_interval=0.5,
        timeout=3.0,
    )

    error: Exception | None = None
    try:
        verifier.verify()
    except Exception as exc:  # noqa: BLE001 - capturing for expect pattern
        error = exc

    expect(error is not None, "Verifier should raise when runners remain busy")
    expect("Timed out" in str(error), "Error should mention timeout for diagnostics")
