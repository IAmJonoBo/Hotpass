"""Utilities that assert GitHub ARC runner scale sets recycle pods cleanly."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import requests


class CommandRunner(Protocol):
    def __call__(self, args: list[str]) -> str:  # pragma: no cover - protocol
        """Execute ``args`` and return the command's stdout."""


@dataclass(frozen=True)
class RunnerStatus:
    name: str
    busy: bool

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> RunnerStatus:
        return cls(name=payload.get("name", "unknown"), busy=bool(payload.get("busy", False)))


class RunnerLifecycleVerifier:
    """Checks a RunnerScaleSet for leftover pods or busy runners."""

    def __init__(
        self,
        *,
        owner: str,
        repository: str,
        scale_set: str,
        namespace: str,
        session: requests.Session | None = None,
        run_command: CommandRunner | None = None,
        now: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        timeout_seconds: float = 600.0,
        poll_interval: float = 10.0,
    ) -> None:
        self.owner = owner
        self.repository = repository
        self.scale_set = scale_set
        self.namespace = namespace
        self.session = session or requests.Session()
        self._run_command = run_command or self._default_run_command
        self._now = now or time.monotonic
        self._sleep = sleep or time.sleep
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval

    @staticmethod
    def _default_run_command(args: list[str]) -> str:
        result = subprocess.run(args, capture_output=True, check=True, text=True)
        return result.stdout.strip()

    def _list_runner_pods(self) -> list[str]:
        command = [
            "kubectl",
            "get",
            "pods",
            "-n",
            self.namespace,
            "-l",
            f"actions.github.com/scale-set-name={self.scale_set}",
            "--no-headers",
        ]
        output = self._run_command(command)
        return [line for line in output.splitlines() if line.strip()]

    def _fetch_runner_status(self) -> list[RunnerStatus]:
        url = f"https://api.github.com/repos/{self.owner}/{self.repository}/actions/runners"
        response = self.session.get(
            url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        runners = payload.get("runners", [])
        return [RunnerStatus.from_payload(item) for item in runners]

    def verify(self) -> None:
        deadline = self._now() + self.timeout_seconds
        while self._now() < deadline:
            pods = self._list_runner_pods()
            runners = self._fetch_runner_status()
            busy = [runner for runner in runners if runner.busy]
            if not pods and not busy:
                return
            self._sleep(self.poll_interval)
        raise RuntimeError(
            "Timed out waiting for ARC runner scale set to become idle",
        )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ARC runner scale set lifecycle",
    )
    parser.add_argument(
        "--owner",
        required=True,
        help="GitHub organisation or user that owns the repository",
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="Repository containing the workflows that use the runners",
    )
    parser.add_argument(
        "--scale-set",
        required=True,
        help="RunnerScaleSet name configured in the cluster",
    )
    parser.add_argument(
        "--namespace",
        default="arc-runners",
        help="Kubernetes namespace hosting the runner pods",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Seconds to wait for the runner to drain",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=10.0,
        help="Seconds between status checks",
    )
    parser.add_argument(
        "--output",
        choices={"text", "json"},
        default="text",
        help="Render mode for verification results",
    )
    return parser.parse_args(argv)


def _emit_result(success: bool, mode: str) -> None:
    if mode == "json":
        print(json.dumps({"success": success}))
    else:
        state = "healthy" if success else "unhealthy"
        print(f"Runner scale set is {state}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    verifier = RunnerLifecycleVerifier(
        owner=args.owner,
        repository=args.repository,
        scale_set=args.scale_set,
        namespace=args.namespace,
        timeout_seconds=args.timeout,
        poll_interval=args.poll_interval,
    )
    try:
        verifier.verify()
    except Exception as exc:  # noqa: BLE001 - surfaced to the CLI
        _emit_result(False, args.output)
        print(str(exc), file=sys.stderr)
        return 1
    _emit_result(True, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
