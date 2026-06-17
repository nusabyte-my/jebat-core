"""Decision engine for agent selection and task routing."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Routes tasks to appropriate agents based on rules and capabilities."""

    def __init__(
        self,
        agent_registry: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.agent_registry = agent_registry or {}
        self.config = config or {}
        self._decisions: List[Dict[str, Any]] = []
        self._stats = {"total_decisions": 0, "successful": 0}

    async def decide(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Make a routing decision for a task."""
        self._stats["total_decisions"] += 1

        task_type = task.get("type", "general")
        best_agent = None

        for agent_id, agent_info in self.agent_registry.items():
            if isinstance(agent_info, dict):
                caps = agent_info.get("capabilities", [])
                if any(task_type.lower() in cap.lower() for cap in caps):
                    best_agent = agent_id
                    break

        if not best_agent and self.agent_registry:
            best_agent = next(iter(self.agent_registry))

        decision = {
            "task_type": task_type,
            "selected_agent": best_agent,
            "confidence": 0.8 if best_agent else 0.2,
        }

        self._decisions.append(decision)
        if best_agent:
            self._stats["successful"] += 1

        return decision

    def get_stats(self) -> Dict[str, Any]:
        return {**self._stats, "total_agents": len(self.agent_registry)}
