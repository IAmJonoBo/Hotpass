"""Automation hooks for delivering pipeline outputs to external systems."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd
import requests


def dispatch_webhooks(
    digest: pd.DataFrame,
    *,
    webhooks: Sequence[str],
    daily_list: pd.DataFrame | None = None,
    logger: Any | None = None,
) -> None:
    """Send intent digest payloads to configured webhook endpoints."""

    if not webhooks or digest.empty:
        return

    payload: dict[str, Any] = {"intent_digest": digest.to_dict(orient="records")}
    if daily_list is not None:
        payload["daily_list"] = daily_list.to_dict(orient="records")

    for url in webhooks:
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - defensive logging
            if logger is not None:
                logger.log_error(f"Webhook delivery failed for {url}: {exc}")
        else:
            if logger is not None:
                logger.log_event(
                    "webhook.delivered",
                    {"url": url, "records": len(payload["intent_digest"])},
                )


def push_crm_updates(
    daily_list: pd.DataFrame,
    endpoint: str,
    *,
    token: str | None = None,
    logger: Any | None = None,
) -> None:
    """Send the daily prospect list to a CRM endpoint."""

    if daily_list.empty:
        return

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"prospects": daily_list.to_dict(orient="records")}
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - defensive logging
        if logger is not None:
            logger.log_error(f"CRM update failed for {endpoint}: {exc}")
    else:
        if logger is not None:
            logger.log_event(
                "crm.updated",
                {"endpoint": endpoint, "records": len(payload["prospects"])},
            )


__all__ = ["dispatch_webhooks", "push_crm_updates"]
