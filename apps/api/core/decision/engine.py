"""
JEBAT Decision Engine

Intelligent routing and decision-making:
- Agent selection
- Task routing
- Priority assignment
- Performance learning
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """Decision types."""

    AGENT_SELECTION = "agent_selection"
    ROUTING = "routing"
    PRIORITY = "priority"


@dataclass
class DecisionResult:
    """Decision result."""

    decision_type: DecisionType
    selected_option: Any
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """
    Decision making engine.

    Makes intelligent routing decisions based on:
    - Agent capabilities
    - Task requirements
    - Historical performance
    - User preferences
    """

    def __init__(self, agent_registry=None):
        """
        Initialize decision engine.

        Args:
            agent_registry: AgentRegistry instance or dict of available agents
        """
        self.agent_registry = agent_registry
        self.decision_history: List[DecisionResult] = []
        self.performance_stats: Dict[str, Any] = {}

        agent_count = 0
        if self.agent_registry is not None:
            # Support both AgentRegistry instance and legacy dict
            if hasattr(self.agent_registry, "get_all_agents"):
                agent_count = len(self.agent_registry.get_all_agents())
            elif isinstance(self.agent_registry, dict):
                agent_count = len(self.agent_registry)

        logger.info(f"Decision Engine initialized with {agent_count} agents")

    async def decide(
        self,
        task: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> DecisionResult:
        """
        Make a decision.

        Args:
            task: Task description
            context: Optional context

        Returns:
            Decision result
        """
        # Select best agent
        selected = self._select_agent(task)

        result = DecisionResult(
            decision_type=DecisionType.AGENT_SELECTION,
            selected_option=selected,
            confidence=0.8,
            reasoning=f"Selected agent based on task requirements",
        )

        self.decision_history.append(result)
        return result

    def _select_agent(self, task: Dict[str, Any]) -> Optional[str]:
        """Select best agent for task using AgentRegistry."""
        if self.agent_registry is None:
            return None

        # Use AgentRegistry's find_best_agent if available
        if hasattr(self.agent_registry, "find_best_agent"):
            description = task.get("description", "") or str(task)
            best = self.agent_registry.find_best_agent(description)
            if best is not None:
                return best.agent_id
            # Fall back to any available agent
            available = self.agent_registry.find_available()
            if available:
                return available[0].agent_id
            return None

        # Legacy dict fallback
        if not self.agent_registry:
            return None
        return next(iter(self.agent_registry.keys()), None)

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        agent_count = 0
        if self.agent_registry is not None:
            if hasattr(self.agent_registry, "get_all_agents"):
                agent_count = len(self.agent_registry.get_all_agents())
            elif isinstance(self.agent_registry, dict):
                agent_count = len(self.agent_registry)
        return {
            "agents_registered": agent_count,
            "decisions_made": len(self.decision_history),
        }
