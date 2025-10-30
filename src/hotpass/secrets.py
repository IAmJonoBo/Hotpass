"""Vault-backed secret loading utilities."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

import requests


class VaultError(RuntimeError):
    """Raised when Vault interactions fail."""


@dataclass
class VaultResponse(Protocol):
    """Subset of response methods required for Vault interactions."""

    def json(self) -> Mapping[str, Any]: ...

    def raise_for_status(self) -> None: ...


class VaultSession(Protocol):
    """Protocol capturing the session behaviour required by the manager."""

    def get(self, url: str, **kwargs: Any) -> VaultResponse: ...

    def post(self, url: str, **kwargs: Any) -> VaultResponse: ...


@dataclass
class VaultSecretManager:
    """Lightweight Vault client focused on KVv2 secrets."""

    addr: str
    session: VaultSession
    namespace: str | None = None
    auth_mount: str = "github"
    role: str | None = None
    audience: str = "hotpass"
    kv_mount: str = "kv"
    token: str | None = None

    def _headers(self, include_token: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {}
        if include_token:
            token = self._ensure_token()
            headers["X-Vault-Token"] = token
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace
        return headers

    def _ensure_token(self) -> str:
        if self.token:
            return self.token

        env_token = os.getenv("HOTPASS_VAULT_TOKEN")
        if env_token:
            self.token = env_token
            return env_token

        if self.role:
            self.token = self._login_with_oidc()
            return self.token

        msg = "Vault token unavailable and no role configured for OIDC login"
        raise VaultError(msg)

    def _login_with_oidc(self) -> str:
        request_url = os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL")
        request_token = os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
        if not request_url or not request_token:
            msg = "GitHub OIDC environment variables not present"
            raise VaultError(msg)

        delimiter = "&" if "?" in request_url else "?"
        audience = os.getenv("HOTPASS_VAULT_OIDC_AUDIENCE", self.audience)
        oidc_url = f"{request_url}{delimiter}audience={audience}"

        oidc_resp = self.session.get(
            oidc_url,
            headers={"Authorization": f"Bearer {request_token}"},
            timeout=30,
        )
        oidc_resp.raise_for_status()
        oidc_token = oidc_resp.json().get("value")
        if not oidc_token:
            msg = "OIDC provider did not return a token"
            raise VaultError(msg)

        login_url = f"{self.addr.rstrip('/')}/v1/auth/{self.auth_mount}/login"
        login_resp = self.session.post(
            login_url,
            json={"role": self.role, "jwt": oidc_token},
            headers=self._headers(include_token=False),
            timeout=30,
        )
        login_resp.raise_for_status()
        client_token = login_resp.json().get("auth", {}).get("client_token")
        if not client_token:
            msg = "Vault login response missing client token"
            raise VaultError(msg)
        return cast(str, client_token)

    @classmethod
    def from_env(
        cls,
        *,
        session: VaultSession | None = None,
    ) -> VaultSecretManager | None:
        addr = os.getenv("HOTPASS_VAULT_ADDR")
        if not addr:
            return None

        namespace = os.getenv("HOTPASS_VAULT_NAMESPACE")
        auth_mount = os.getenv("HOTPASS_VAULT_AUTH_MOUNT", "github")
        role = os.getenv("HOTPASS_VAULT_ROLE")
        audience = os.getenv("HOTPASS_VAULT_OIDC_AUDIENCE", "hotpass")
        kv_mount = os.getenv("HOTPASS_VAULT_KV_MOUNT", "kv")

        return cls(
            addr=addr,
            session=session or cast(VaultSession, requests.Session()),
            namespace=namespace,
            auth_mount=auth_mount,
            role=role,
            audience=audience,
            kv_mount=kv_mount,
        )

    def read_kv_secret(self, path: str) -> dict[str, Any]:
        normalized = path.lstrip("/")
        secret_url = f"{self.addr.rstrip('/')}/v1/{self.kv_mount}/data/{normalized}"
        response = self.session.get(secret_url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        payload = response.json()
        return dict(payload.get("data", {}).get("data", {}))


def load_prefect_environment_secrets(
    *,
    session: VaultSession | None = None,
    manager: VaultSecretManager | None = None,
) -> Mapping[str, str]:
    """Fetch Prefect credentials from Vault and expose them as environment variables."""

    manager = manager or VaultSecretManager.from_env(session=session)
    if manager is None:
        return {}

    path = os.getenv("HOTPASS_VAULT_PREFECT_PATH", "hotpass/prefect")
    secret_payload = manager.read_kv_secret(path)

    env_mapping = {
        "prefect_api_key": "PREFECT_API_KEY",  # pragma: allowlist secret - env var name only
        "prefect_api_url": "PREFECT_API_URL",  # pragma: allowlist secret - env var name only
    }

    exported: dict[str, str] = {}
    for key, value in secret_payload.items():
        env_key = env_mapping.get(key, key.upper())
        if value is None:
            continue
        os.environ[env_key] = str(value)
        exported[env_key] = str(value)

    return exported


__all__ = [
    "VaultResponse",
    "VaultSession",
    "VaultSecretManager",
    "VaultError",
    "load_prefect_environment_secrets",
]
