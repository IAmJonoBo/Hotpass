from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest
import requests
from requests import Response
from requests.structures import CaseInsensitiveDict

from hotpass.enrichment import CacheManager, RegistryLookupError, enrich_from_registry

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "enrichment"


class DummySession:
    """Minimal requests-compatible session for fixture responses."""

    def __init__(
        self,
        responses: dict[tuple[str, tuple[tuple[str, str], ...] | None], dict],
        error: Exception | None = None,
    ) -> None:
        self._responses = responses
        self._error = error
        self.calls: list[dict[str, object]] = []

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        timeout: float | tuple[float | None, float | None] | None = None,
        **_: Any,
    ) -> Response:
        if self._error is not None:
            raise self._error
        key = (url, tuple(sorted((params or {}).items())) if params else None)
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        try:
            payload = self._responses[key]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AssertionError(f"Unexpected request: {key}") from exc
        response = Response()
        response.status_code = payload["status"]
        # Direct assignment to _content is necessary here to mock the response body for tests.
        response._content = json.dumps(payload["body"]).encode("utf-8")
        response.headers = CaseInsensitiveDict({"Content-Type": "application/json"})
        response.url = url
        return response


def _load_fixture(name: str) -> dict:
    path = FIXTURE_DIR / name
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_cipc_lookup_success(tmp_path: Path) -> None:
    payload = _load_fixture("cipc_company.json")
    base_url = "https://cipc.example/api"
    dummy_session = DummySession(
        {(base_url, (("search", "Aero Tech"),)): {"status": 200, "body": payload}}
    )
    session = cast(requests.Session, dummy_session)
    cache = CacheManager(db_path=str(tmp_path / "cache.db"), ttl_hours=1)

    result = enrich_from_registry(
        "Aero Tech",
        registry_type="cipc",
        cache=cache,
        session=session,
        config={"base_url": base_url},
    )

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["payload"]["registered_name"] == "Aero Tech (Pty) Ltd"
    assert len(result["payload"]["addresses"]) == 2
    assert result["payload"]["officers"][0]["name"] == "Jane Doe"


def test_cipc_not_found_returns_structured_error(tmp_path: Path) -> None:
    base_url = "https://cipc.example/api"
    dummy_session = DummySession(
        {
            (base_url, (("search", "Unknown"),)): {
                "status": 404,
                "body": {"message": "No match"},
            }
        }
    )
    session = cast(requests.Session, dummy_session)
    cache = CacheManager(db_path=str(tmp_path / "cache.db"), ttl_hours=1)

    result = enrich_from_registry(
        "Unknown",
        registry_type="cipc",
        cache=cache,
        session=session,
        config={"base_url": base_url},
    )

    assert result["success"] is False
    assert result["status_code"] == 404
    assert result["errors"][0]["code"] == "not_found"


def test_sacaa_lookup_success(tmp_path: Path) -> None:
    payload = _load_fixture("sacaa_operator.json")
    base_url = "https://sacaa.example/operators"
    dummy_session = DummySession(
        {(base_url, (("query", "Sky Charter"),)): {"status": 200, "body": payload}}
    )
    session = cast(requests.Session, dummy_session)
    cache = CacheManager(db_path=str(tmp_path / "cache.db"), ttl_hours=1)

    result = enrich_from_registry(
        "Sky Charter",
        registry_type="sacaa",
        cache=cache,
        session=session,
        config={"base_url": base_url},
    )

    assert result["success"] is True
    assert result["payload"]["trading_name"] == "Sky Charter"
    assert result["payload"]["contacts"]["email"] == "ops@skycharter.test"
    assert result["payload"]["officers"][0]["name"] == "Lerato Mokoena"
    assert result["meta"]["provider_meta"]["source"] == "SACAA API"


def test_enrich_from_registry_raises_on_transport_error(tmp_path: Path) -> None:
    base_url = "https://cipc.example/api"
    dummy_session = DummySession({}, error=requests.ConnectionError("boom"))
    session = cast(requests.Session, dummy_session)
    cache = CacheManager(db_path=str(tmp_path / "cache.db"), ttl_hours=1)

    with pytest.raises(RegistryLookupError):
        enrich_from_registry(
            "Failure",
            registry_type="cipc",
            cache=cache,
            session=session,
            config={"base_url": base_url},
        )


def test_enrich_from_registry_uses_cache_before_rate_limit(tmp_path: Path) -> None:
    payload = _load_fixture("cipc_company.json")
    base_url = "https://cipc.example/api"
    dummy_session = DummySession(
        {(base_url, (("search", "Aero Tech"),)): {"status": 200, "body": payload}}
    )
    session = cast(requests.Session, dummy_session)
    cache = CacheManager(db_path=str(tmp_path / "cache.db"), ttl_hours=1)

    # First call populates the cache and advances the rate limiter
    result_first = enrich_from_registry(
        "Aero Tech",
        registry_type="cipc",
        cache=cache,
        session=session,
        config={"base_url": base_url, "throttle_seconds": 10},
    )
    assert result_first["success"] is True

    # Second call should read from cache without invoking the session again
    result_second = enrich_from_registry(
        "Aero Tech",
        registry_type="cipc",
        cache=cache,
        session=session,
        config={"base_url": base_url, "throttle_seconds": 10},
    )

    assert result_second == result_first
    assert len(dummy_session.calls) == 1
