"""Agent factory for creating specialized agent instances from templates."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(str, Enum):
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CONVERSATIONAL = "conversational"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    EXECUTOR = "executor"
    MEMORY = "memory"


class AgentPersonality(str, Enum):
    TECHNICAL = "technical"
    CREATIVE = "creative"
    FRIENDLY = "friendly"
    ANALYTICAL = "analytical"


@dataclass
class AgentTemplate:
    agent_type: AgentType = AgentType.ANALYTICAL
    name: str = ""
    description: str = ""
    personality: AgentPersonality = AgentPersonality.TECHNICAL
    capabilities: List[str] = field(default_factory=list)


class AgentFactory:
    """Creates and manages agent instances from templates."""

    def __init__(self):
        self._agents: Dict[str, Any] = {}

    def create(self, template: AgentTemplate, agent_id: Optional[str] = None) -> str:
        agent_id = agent_id or str(uuid.uuid4())
        self._agents[agent_id] = {
            "id": agent_id,
            "template": template,
            "name": template.name,
            "type": template.agent_type.value,
            "personality": template.personality.value,
            "capabilities": template.capabilities,
            "description": template.description,
        }
        return agent_id

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())
