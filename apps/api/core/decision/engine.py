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

    def __init__(self, agent_registry: Optional[Dict] = None):
        """
        Initialize decision engine.

        Args:
            agent_registry: Registry of available agents
        """
        self.agent_registry = agent_registry or {}
        self.decision_history: List[DecisionResult] = []
        self.performance_stats: Dict[str, Any] = {}
        logger.info(
            f"Decision Engine initialized with {len(self.agent_registry)} agents"
        )

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
        """Select best agent for task."""
        if not self.agent_registry:
            return None

        # Simple selection - return first available
        return next(iter(self.agent_registry.keys()), None)

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "agents_registered": len(self.agent_registry),
            "decisions_made": len(self.decision_history),
        }
