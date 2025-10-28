"""Agent-based acquisition framework for Hotpass."""

from .base import AcquisitionAgent, AgentContext, AgentResult, normalise_records
from .config import AcquisitionPlan, AgentDefinition, ProviderDefinition, TargetDefinition
from .runner import AcquisitionManager, run_plan

__all__ = [
    "AcquisitionAgent",
    "AcquisitionManager",
    "AcquisitionPlan",
    "AgentContext",
    "AgentDefinition",
    "AgentResult",
    "ProviderDefinition",
    "TargetDefinition",
    "normalise_records",
    "run_plan",
]
