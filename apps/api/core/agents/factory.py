"""
JEBAT Agent Factory

Agent creation and template management.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent types."""

    CONVERSATIONAL = "conversational"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    TASK_EXECUTOR = "task_executor"
    RESEARCHER = "researcher"


class AgentPersonality(str, Enum):
    """Agent personalities."""

    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"


@dataclass
class AgentTemplate:
    """Agent creation template."""

    agent_type: AgentType
    name: str
    description: str
    personality: AgentPersonality = AgentPersonality.PROFESSIONAL
    capabilities: List[str] = field(default_factory=list)
    model: str = "gpt-4"
    temperature: float = 0.7
    config: Dict[str, Any] = field(default_factory=dict)


class AgentFactory:
    """
    Factory for creating agents.

    Provides templates and dynamic agent creation.
    """

    def __init__(self):
        """Initialize agent factory."""
        self.agents: Dict[str, Any] = {}
        self.templates: Dict[str, AgentTemplate] = {}
        self._register_default_templates()
        logger.info("AgentFactory initialized")

    def _register_default_templates(self):
        """Register default agent templates."""
        templates = [
            AgentTemplate(
                agent_type=AgentType.CONVERSATIONAL,
                name="ChatAgent",
                description="Friendly conversational agent",
                personality=AgentPersonality.FRIENDLY,
                capabilities=["conversation", "context"],
            ),
            AgentTemplate(
                agent_type=AgentType.ANALYTICAL,
                name="AnalystAgent",
                description="Data analysis agent",
                personality=AgentPersonality.TECHNICAL,
                capabilities=["analysis", "insights"],
            ),
            AgentTemplate(
                agent_type=AgentType.CREATIVE,
                name="CreativeAgent",
                description="Creative content agent",
                personality=AgentPersonality.CREATIVE,
                capabilities=["creation", "brainstorming"],
            ),
        ]

        for template in templates:
            self.templates[template.agent_type.value] = template
            logger.info(f"Registered template: {template.name}")

    def create(
        self,
        template: AgentTemplate,
        agent_id: Optional[str] = None,
    ) -> str:
        """
        Create agent from template.

        Args:
            template: Agent template
            agent_id: Optional custom ID

        Returns:
            Agent ID
        """
        agent_id = agent_id or f"agent_{uuid4().hex[:8]}"

        self.agents[agent_id] = {
            "id": agent_id,
            "name": template.name,
            "type": template.agent_type.value,
            "personality": template.personality.value,
            "capabilities": template.capabilities,
            "model": template.model,
            "created_at": datetime.utcnow(),
        }

        logger.info(f"Created agent: {agent_id} ({template.name})")
        return agent_id

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents."""
        return list(self.agents.values())

    def get_template(self, agent_type: AgentType) -> Optional[AgentTemplate]:
        """Get template by type."""
        return self.templates.get(agent_type.value)
