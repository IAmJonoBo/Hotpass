"""Utilities to orchestrate acquisition agents."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from ...enrichment.providers import REGISTRY as provider_registry
from ...enrichment.providers import CredentialStore
from .. import RawRecord
from .base import AgentContext, AgentResult, normalise_records
from .config import AcquisitionPlan, AgentDefinition
from .tasks import execute_agent_tasks


@dataclass(slots=True)
class AgentTiming:
    """Capture timing metadata for agent execution."""

    agent_name: str
    seconds: float
    record_count: int


class AcquisitionManager:
    """Instantiate providers and execute configured agents."""

    def __init__(
        self,
        plan: AcquisitionPlan,
        *,
        credentials: Mapping[str, str] | None = None,
    ) -> None:
        self.plan = plan
        self.credentials = dict(credentials or {})

    def run(self, *, country_code: str) -> tuple[pd.DataFrame, list[AgentTiming], list[str]]:
        all_records: list[RawRecord] = []
        timings: list[AgentTiming] = []
        warnings: list[str] = []

        for agent in self.plan.active_agents():
            start = time.perf_counter()
            result = self._run_agent(agent, country_code=country_code)
            duration = time.perf_counter() - start
            timings.append(
                AgentTiming(
                    agent_name=agent.name,
                    seconds=duration,
                    record_count=len(result.records),
                )
            )
            all_records.extend(result.records)
            warnings.extend(result.warnings)

        if not all_records:
            return pd.DataFrame(), timings, warnings

        records = normalise_records(all_records) if self.plan.deduplicate else list(all_records)
        frame = pd.DataFrame([record.as_dict() for record in records])
        return frame, timings, warnings

    def _run_agent(self, agent: AgentDefinition, *, country_code: str) -> AgentResult:
        context = AgentContext(
            plan=self.plan,
            agent=agent,
            credentials=self.credentials,
            country_code=country_code,
        )
        credential_store = CredentialStore(context.credentials)
        result = execute_agent_tasks(agent, context, provider_registry, credential_store)
        for provenance in result.provenance:
            provenance.setdefault("agent", agent.name)
        for record in result.records:
            if record.provenance:
                for entry in record.provenance:
                    entry.setdefault("agent", agent.name)
        return result


def run_plan(
    plan: AcquisitionPlan,
    *,
    country_code: str,
    credentials: Mapping[str, str] | None = None,
) -> tuple[pd.DataFrame, list[AgentTiming], list[str]]:
    """Execute the acquisition plan and return a dataframe with collected records."""

    manager = AcquisitionManager(plan, credentials=credentials)
    return manager.run(country_code=country_code)
