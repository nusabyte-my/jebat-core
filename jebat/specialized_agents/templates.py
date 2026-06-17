"""Specialized agent templates and factory functions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentConfig:
    agent_id: Any = field(default_factory=uuid.uuid4)
    name: str = ""
    type: str = ""
    agent_type: str = ""
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    timeout_seconds: int = 300

    def __post_init__(self):
        if not self.agent_type and self.type:
            self.agent_type = self.type


class BaseAgent:
    """Base specialized agent."""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ):
        if config is None:
            config = AgentConfig(
                name=name or "Agent",
                type=kwargs.get("type", "general"),
            )
        elif name:
            config.name = name
        self.config = config

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "agent": self.config.name}


class ResearcherAgent(BaseAgent):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.config.type:
            self.config.type = "researcher"
            self.config.agent_type = "researcher"


class AnalystAgent(BaseAgent):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.config.type:
            self.config.type = "analyst"
            self.config.agent_type = "analyst"


class ExecutionAgent(BaseAgent):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.config.type:
            self.config.type = "executor"
            self.config.agent_type = "executor"


class MemoryAgent(BaseAgent):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.config.type:
            self.config.type = "memory"
            self.config.agent_type = "memory"


def create_researcher(config: Optional[AgentConfig] = None, **kwargs: Any) -> ResearcherAgent:
    return ResearcherAgent(config=config, **kwargs)


def create_analyst(config: Optional[AgentConfig] = None, **kwargs: Any) -> AnalystAgent:
    return AnalystAgent(config=config, **kwargs)


def create_executor(config: Optional[AgentConfig] = None, **kwargs: Any) -> ExecutionAgent:
    return ExecutionAgent(config=config, **kwargs)
