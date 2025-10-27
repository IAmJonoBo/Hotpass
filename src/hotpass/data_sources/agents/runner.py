"""Utilities to orchestrate acquisition agents."""

from __future__ import annotations

import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

from ...enrichment.providers import REGISTRY as provider_registry
from ...enrichment.providers import BaseProvider, ProviderContext, ProviderPayload
from ...normalization import clean_string
from .. import RawRecord
from .base import AgentContext, AgentResult, normalise_records
from .config import AcquisitionPlan, AgentDefinition, ProviderDefinition, TargetDefinition


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
        result = AgentResult(agent_name=agent.name)
        targets = agent.active_targets()
        if not targets:
            fallback_targets = [
                TargetDefinition(identifier=term)
                for term in agent.search_terms
                if clean_string(term)
            ]
            targets = tuple(fallback_targets)
        for provider_definition in agent.active_providers():
            provider = self._create_provider(provider_definition)
            payloads = self._execute_provider(provider, provider_definition, targets, context)
            for payload in payloads:
                self._apply_provenance(payload, agent, result)
        return result

    def _execute_provider(
        self,
        provider: BaseProvider,
        definition: ProviderDefinition,
        targets: Sequence[object],
        context: AgentContext,
    ) -> Iterable[ProviderPayload]:
        provider_context = ProviderContext(
            country_code=context.country_code,
            credentials=context.credentials,
            issued_at=context.issued_at,
        )
        payloads: list[ProviderPayload] = []
        for target in targets:
            identifier = clean_string(getattr(target, "identifier", ""))
            domain = clean_string(getattr(target, "domain", None)) or None
            if not identifier and not domain:
                continue
            for payload in provider.lookup(identifier or domain or "", domain, provider_context):
                payloads.append(payload)
        return payloads

    def _apply_provenance(
        self,
        payload: ProviderPayload,
        agent: AgentDefinition,
        result: AgentResult,
    ) -> None:
        record = payload.record
        provenance = dict(payload.provenance)
        provenance.update(
            {
                "agent": agent.name,
                "confidence": payload.confidence,
            }
        )
        record.provenance = [provenance]
        result.records.append(record)
        result.provenance.append(provenance)

    def _create_provider(self, definition: ProviderDefinition) -> BaseProvider:
        return provider_registry.create(definition.name, definition.options)


def run_plan(
    plan: AcquisitionPlan,
    *,
    country_code: str,
    credentials: Mapping[str, str] | None = None,
) -> tuple[pd.DataFrame, list[AgentTiming], list[str]]:
    """Execute the acquisition plan and return a dataframe with collected records."""

    manager = AcquisitionManager(plan, credentials=credentials)
    return manager.run(country_code=country_code)
