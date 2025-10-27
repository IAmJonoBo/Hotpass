"""Agent-based acquisition framework for Hotpass."""

from .base import AcquisitionAgent, AgentContext, AgentResult, normalise_records
from .config import (
    AcquisitionPlan,
    AgentDefinition,
    AgentTaskDefinition,
    AgentTaskKind,
    ProviderDefinition,
    TargetDefinition,
)
from .runner import AcquisitionManager, run_plan
from .tasks import execute_agent_tasks

__all__ = [
    "AcquisitionAgent",
    "AcquisitionManager",
    "AcquisitionPlan",
    "AgentContext",
    "AgentDefinition",
    "AgentResult",
    "AgentTaskDefinition",
    "AgentTaskKind",
    "ProviderDefinition",
    "TargetDefinition",
    "execute_agent_tasks",
    "normalise_records",
    "run_plan",
]
