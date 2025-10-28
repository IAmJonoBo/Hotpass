"""Canonical configuration schema for Hotpass runtime components."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hotpass.compliance import DataClassification, LawfulBasis, PIIRedactionConfig


class ProfileConfig(BaseModel):
    """Industry profile describing terminology, validation, and synonyms."""

    model_config = ConfigDict(frozen=True)

    name: str = "generic"
    display_name: str = "Generic Business"
    default_country_code: str = "ZA"
    organization_term: str = "organization"
    organization_type_term: str = "organization_type"
    organization_category_term: str = "category"
    email_validation_threshold: float = 0.85
    phone_validation_threshold: float = 0.85
    website_validation_threshold: float = 0.75
    source_priorities: Mapping[str, int] = Field(default_factory=dict)
    column_synonyms: Mapping[str, Sequence[str]] = Field(default_factory=dict)
    required_fields: Sequence[str] = Field(default_factory=list)
    optional_fields: Sequence[str] = Field(default_factory=list)
    custom_validators: Mapping[str, Mapping[str, Any]] = Field(default_factory=dict)

    @field_validator("source_priorities", mode="after")
    @classmethod
    def _validate_priorities(cls, value: Mapping[str, int]) -> Mapping[str, int]:
        duplicates = len(value.values()) != len(set(value.values()))
        if duplicates:
            msg = "Source priorities must be unique"
            raise ValueError(msg)
        return dict(value)

    def to_dict(self) -> dict[str, Any]:
        """Return the profile as a serialisable dictionary."""

        return self.model_dump(mode="python")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProfileConfig:
        """Instantiate a profile from a dictionary payload."""

        return cls.model_validate(payload)


class DataContractConfig(BaseModel):
    """Link the runtime configuration to published data contracts."""

    dataset: str = "ssot"
    expectation_suite: str = "default"
    schema_descriptor: str = "ssot.schema.json"
    version: str | None = None
    steward: str | None = None


class FeatureSwitches(BaseModel):
    """Feature toggles mirrored across CLI, pipeline, and orchestration."""

    entity_resolution: bool = False
    enrichment: bool = False
    geospatial: bool = False
    compliance: bool = False
    observability: bool = False
    acquisition: bool = False
    dashboards: bool = False


class AcquisitionProviderConfig(BaseModel):
    name: str
    enabled: bool = True
    weight: float = Field(default=1.0, ge=0)
    options: Mapping[str, Any] = Field(default_factory=dict)


class AcquisitionTargetConfig(BaseModel):
    identifier: str
    domain: str | None = None
    location: str | None = None
    metadata: Mapping[str, Any] = Field(default_factory=dict)


class AcquisitionTaskConfig(BaseModel):
    name: str
    kind: Literal["search", "crawl", "api"]
    provider: str | None = None
    options: Mapping[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class AcquisitionAgentConfig(BaseModel):
    name: str
    description: str | None = None
    search_terms: tuple[str, ...] = Field(default_factory=tuple)
    region: str | None = None
    concurrency: int = Field(default=1, ge=1)
    providers: tuple[AcquisitionProviderConfig, ...] = Field(default_factory=tuple)
    targets: tuple[AcquisitionTargetConfig, ...] = Field(default_factory=tuple)
    tasks: tuple[AcquisitionTaskConfig, ...] = Field(default_factory=tuple)
    enabled: bool = True

    @field_validator("search_terms", mode="before")
    @classmethod
    def _clean_terms(cls, values: Iterable[str] | None) -> tuple[str, ...]:
        if values is None:
            return ()
        cleaned: list[str] = []
        for value in values:
            candidate = str(value).strip()
            if candidate and candidate not in cleaned:
                cleaned.append(candidate)
        return tuple(cleaned)


class AcquisitionSettings(BaseModel):
    enabled: bool = False
    deduplicate: bool = True
    provenance_namespace: str = "agent"
    credentials: Mapping[str, str] = Field(default_factory=dict)
    agents: tuple[AcquisitionAgentConfig, ...] = Field(default_factory=tuple)


class IntentCollectorConfig(BaseModel):
    name: str
    enabled: bool = True
    weight: float = Field(default=1.0, ge=0.0)
    options: Mapping[str, Any] = Field(default_factory=dict)


class IntentTargetConfig(BaseModel):
    identifier: str
    slug: str | None = None
    metadata: Mapping[str, Any] = Field(default_factory=dict)


class IntentSettings(BaseModel):
    enabled: bool = False
    deduplicate: bool = True
    collectors: tuple[IntentCollectorConfig, ...] = Field(default_factory=tuple)
    targets: tuple[IntentTargetConfig, ...] = Field(default_factory=tuple)
    credentials: Mapping[str, str] = Field(default_factory=dict)


class PipelineRuntimeConfig(BaseModel):
    """Input/output, reporting, and runtime options for the refinement pipeline."""

    input_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
    output_path: Path = Field(default_factory=lambda: Path.cwd() / "dist" / "refined.xlsx")
    dist_dir: Path = Field(default_factory=lambda: Path.cwd() / "dist")
    archive: bool = False
    expectation_suite: str = "default"
    country_code: str = "ZA"
    qa_mode: str = Field(default="default", pattern=r"^(default|strict|relaxed)$")
    log_format: str = Field(default="rich", pattern=r"^(json|rich)$")
    report_path: Path | None = None
    report_format: str | None = Field(default=None, pattern=r"^(markdown|html)$")
    party_store_path: Path | None = None
    excel_chunk_size: int | None = Field(default=None, ge=1)
    excel_engine: str | None = None
    excel_stage_dir: Path | None = None
    sensitive_fields: tuple[str, ...] = Field(default_factory=tuple)
    observability: bool | None = None
    acquisition: AcquisitionSettings | None = None
    intent_digest_path: Path | None = None
    intent: IntentSettings | None = None
    intent_signal_store_path: Path | None = None
    daily_list_path: Path | None = None
    daily_list_size: int = Field(default=50, ge=1)
    intent_webhooks: tuple[str, ...] = Field(default_factory=tuple)
    crm_endpoint: str | None = None
    crm_token: str | None = None

    @field_validator("sensitive_fields", mode="before")
    @classmethod
    def _normalise_fields(cls, values: Iterable[str] | None) -> tuple[str, ...]:
        if values is None:
            return ()
        normalised: list[str] = []
        for value in values:
            cleaned = str(value).strip().lower()
            if cleaned:
                if cleaned not in normalised:
                    normalised.append(cleaned)
        return tuple(normalised)

    @field_validator("intent_webhooks", mode="before")
    @classmethod
    def _normalise_webhooks(cls, values: Iterable[str] | str | None) -> tuple[str, ...]:
        if values is None:
            return ()
        if isinstance(values, str):
            values = [values]
        cleaned: list[str] = []
        for value in values:
            candidate = str(value).strip()
            if candidate and candidate not in cleaned:
                cleaned.append(candidate)
        return tuple(cleaned)

    @model_validator(mode="after")
    def _infer_report_format(self) -> PipelineRuntimeConfig:
        if self.report_path is not None and self.report_format is None:
            suffix = self.report_path.suffix.lower()
            if suffix in {".md", ".markdown"}:
                object.__setattr__(self, "report_format", "markdown")
            elif suffix in {".html", ".htm"}:
                object.__setattr__(self, "report_format", "html")
        return self


class PIIRedactionSettings(BaseModel):
    """Structured configuration for Presidio-based redaction."""

    enabled: bool = True
    columns: tuple[str, ...] = Field(default_factory=lambda: PIIRedactionConfig().columns)
    language: str = "en"
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    operator: str = "redact"
    operator_params: Mapping[str, Any] = Field(default_factory=dict)
    capture_entity_scores: bool = True

    def to_dataclass(self) -> PIIRedactionConfig:
        return PIIRedactionConfig(
            enabled=self.enabled,
            columns=self.columns,
            language=self.language,
            score_threshold=self.score_threshold,
            operator=self.operator,
            operator_params=dict(self.operator_params) or None,
            capture_entity_scores=self.capture_entity_scores,
        )


class ComplianceControls(BaseModel):
    """Configuration driving compliance features and audit behaviour."""

    detect_pii: bool = False
    audit_log_enabled: bool = True
    consent_required: bool = True
    consent_overrides: Mapping[str, str] = Field(default_factory=dict)
    lawful_basis: LawfulBasis | None = None
    pii_redaction: PIIRedactionSettings = Field(default_factory=PIIRedactionSettings)

    def to_redaction_config(self) -> PIIRedactionConfig:
        return self.pii_redaction.to_dataclass()


class GovernanceMetadata(BaseModel):
    """Governance metadata required for intent-driven configuration."""

    intent: list[str] = Field(default_factory=lambda: ["Baseline refinement"])
    data_owner: str = "Data Governance"
    data_steward: str | None = None
    approver: str | None = None
    classification: DataClassification = DataClassification.INTERNAL
    lawful_basis: LawfulBasis | None = None
    policy_reference: str | None = None
    review_interval_days: int = Field(default=180, ge=30)
    audit_retention_days: int = Field(default=365, ge=30)

    @field_validator("intent", mode="before")
    @classmethod
    def _normalise_intent(cls, values: Iterable[str] | None) -> list[str]:
        if values is None:
            return ["Baseline refinement"]
        cleaned = []
        for value in values:
            candidate = str(value).strip()
            if candidate:
                cleaned.append(candidate)
        return cleaned


class OrchestratorSettings(BaseModel):
    """Prefect orchestration defaults derived from canonical config."""

    deployment: str | None = None
    work_pool: str | None = None
    parameters: Mapping[str, Any] = Field(default_factory=dict)
    run_name_template: str | None = None


class HotpassConfig(BaseModel):
    """Top-level canonical configuration consumed across Hotpass surfaces."""

    model_config = ConfigDict(extra="forbid")

    profile: ProfileConfig = Field(default_factory=ProfileConfig)
    pipeline: PipelineRuntimeConfig = Field(default_factory=PipelineRuntimeConfig)
    features: FeatureSwitches = Field(default_factory=FeatureSwitches)
    compliance: ComplianceControls = Field(default_factory=ComplianceControls)
    data_contract: DataContractConfig = Field(default_factory=DataContractConfig)
    governance: GovernanceMetadata = Field(default_factory=GovernanceMetadata)
    orchestrator: OrchestratorSettings = Field(default_factory=OrchestratorSettings)

    @model_validator(mode="after")
    def _require_intent_for_sensitive_features(self) -> HotpassConfig:
        if (self.features.compliance or self.compliance.detect_pii) and not self.governance.intent:
            msg = "Compliance features require at least one declared governance intent"
            raise ValueError(msg)
        return self

    def to_pipeline_config(self, progress_listener: Any | None = None) -> Any:
        """Materialise a ``PipelineConfig`` dataclass from the canonical schema."""

        from hotpass.config import IndustryProfile
        from hotpass.data_sources import ExcelReadOptions
        from hotpass.pipeline.base import PipelineConfig

        excel_options = None
        if (
            self.pipeline.excel_chunk_size
            or self.pipeline.excel_engine
            or self.pipeline.excel_stage_dir is not None
        ):
            excel_options = ExcelReadOptions(
                chunk_size=self.pipeline.excel_chunk_size,
                engine=self.pipeline.excel_engine,
                stage_to_parquet=self.pipeline.excel_stage_dir is not None,
                stage_dir=self.pipeline.excel_stage_dir,
            )

        industry_profile: IndustryProfile | None = None
        if self.profile is not None:
            industry_profile = IndustryProfile.model_validate(self.profile.model_dump())

        config = PipelineConfig(
            input_dir=self.pipeline.input_dir,
            output_path=self.pipeline.output_path,
            expectation_suite_name=self.pipeline.expectation_suite,
            country_code=self.pipeline.country_code,
            excel_options=excel_options,
            industry_profile=industry_profile,
            progress_listener=progress_listener,
            pii_redaction=self.compliance.to_redaction_config(),
        )

        if self.pipeline.acquisition and self.pipeline.acquisition.enabled:
            from hotpass.data_sources.agents import (
                AcquisitionPlan,
                AgentDefinition,
                AgentTaskDefinition,
                AgentTaskKind,
                ProviderDefinition,
                TargetDefinition,
            )

            plan = AcquisitionPlan(
                enabled=True,
                deduplicate=self.pipeline.acquisition.deduplicate,
                provenance_namespace=self.pipeline.acquisition.provenance_namespace,
                agents=tuple(
                    AgentDefinition(
                        name=agent.name,
                        description=agent.description,
                        search_terms=agent.search_terms,
                        region=agent.region,
                        concurrency=agent.concurrency,
                        providers=tuple(
                            ProviderDefinition(
                                name=provider.name,
                                options=dict(provider.options),
                                enabled=provider.enabled,
                                weight=provider.weight,
                            )
                            for provider in agent.providers
                        ),
                        targets=tuple(
                            TargetDefinition(
                                identifier=target.identifier,
                                domain=target.domain,
                                location=target.location,
                                metadata=dict(target.metadata),
                            )
                            for target in agent.targets
                        ),
                        tasks=tuple(
                            AgentTaskDefinition(
                                name=task.name,
                                kind=AgentTaskKind(task.kind),
                                provider=task.provider,
                                options=dict(task.options),
                                enabled=task.enabled,
                            )
                            for task in agent.tasks
                        ),
                    )
                    for agent in self.pipeline.acquisition.agents
                ),
            )
            config.acquisition_plan = plan
            config.agent_credentials = dict(self.pipeline.acquisition.credentials)

        if self.pipeline.intent and self.pipeline.intent.enabled:
            from hotpass.enrichment.intent import (
                IntentCollectorDefinition,
                IntentPlan,
                IntentTargetDefinition,
            )

            intent_plan = IntentPlan(
                enabled=True,
                deduplicate=self.pipeline.intent.deduplicate,
                collectors=tuple(
                    IntentCollectorDefinition(
                        name=collector.name,
                        options=dict(collector.options),
                        enabled=collector.enabled,
                        weight=collector.weight,
                    )
                    for collector in self.pipeline.intent.collectors
                ),
                targets=tuple(
                    IntentTargetDefinition(
                        identifier=target.identifier,
                        slug=target.slug,
                        metadata=dict(target.metadata),
                    )
                    for target in self.pipeline.intent.targets
                ),
                storage_path=self.pipeline.intent_signal_store_path,
            )
            config.intent_plan = intent_plan
            config.intent_credentials = dict(self.pipeline.intent.credentials)

        if self.pipeline.intent_digest_path is not None:
            config.intent_digest_path = self.pipeline.intent_digest_path
        if self.pipeline.intent_signal_store_path is not None:
            config.intent_signal_store_path = self.pipeline.intent_signal_store_path
        if self.pipeline.daily_list_path is not None:
            config.daily_list_path = self.pipeline.daily_list_path
        if self.pipeline.daily_list_size:
            config.daily_list_size = int(self.pipeline.daily_list_size)
        if self.pipeline.intent_webhooks:
            config.automation_webhooks = tuple(self.pipeline.intent_webhooks)
        if self.pipeline.crm_endpoint is not None:
            config.crm_endpoint = self.pipeline.crm_endpoint
        if self.pipeline.crm_token is not None:
            config.crm_token = self.pipeline.crm_token

        if self.pipeline.qa_mode == "relaxed":
            config.enable_audit_trail = False
            config.enable_recommendations = False
        elif self.pipeline.qa_mode == "strict":
            config.enable_audit_trail = True
            config.enable_recommendations = True

        return config

    def to_enhanced_config(self) -> Any:
        """Materialise ``EnhancedPipelineConfig`` with canonical governance context."""

        from hotpass.pipeline.features.config import EnhancedPipelineConfig

        enhanced = EnhancedPipelineConfig(
            enable_entity_resolution=self.features.entity_resolution,
            enable_geospatial=self.features.geospatial,
            enable_enrichment=self.features.enrichment,
            enable_compliance=self.features.compliance,
            enable_observability=self.features.observability,
            enable_acquisition=self.features.acquisition,
            detect_pii=self.compliance.detect_pii,
            consent_overrides=dict(self.compliance.consent_overrides) or None,
        )

        enhanced.audit_log_enabled = self.compliance.audit_log_enabled
        enhanced.consent_required = self.compliance.consent_required
        enhanced.governance_intent = tuple(self.governance.intent)
        enhanced.governance_classification = self.governance.classification
        enhanced.lawful_basis = self.compliance.lawful_basis or self.governance.lawful_basis
        enhanced.telemetry_attributes = {
            "governance_classification": self.governance.classification.value,
            "data_owner": self.governance.data_owner,
        }

        return enhanced

    def merge(self, updates: Mapping[str, Any]) -> HotpassConfig:
        """Return a copy of the configuration with deep updates applied."""

        current = self.model_dump(mode="python")
        merged = _deep_update(current, updates)
        return HotpassConfig.model_validate(merged)


def _deep_update(original: Mapping[str, Any], updates: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge dictionaries while preserving original values."""

    result: dict[str, Any] = dict(original)
    for key, value in updates.items():
        if key not in result:
            result[key] = value
            continue
        existing = result[key]
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            result[key] = _deep_update(existing, value)
        else:
            result[key] = value
    return result


__all__ = [
    "ComplianceControls",
    "DataContractConfig",
    "FeatureSwitches",
    "GovernanceMetadata",
    "HotpassConfig",
    "OrchestratorSettings",
    "PIIRedactionSettings",
    "PipelineRuntimeConfig",
    "ProfileConfig",
]
