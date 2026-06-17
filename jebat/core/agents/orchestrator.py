"""Agent orchestrator for managing task execution and agent lifecycle."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


@dataclass
class AgentTask:
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: Optional[str] = None


@dataclass
class TaskResult:
    task_id: str = ""
    success: bool = True
    result: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    error: Optional[str] = None


class AgentOrchestrator:
    """Orchestrates agent task execution with intelligent selection and performance tracking."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        max_concurrent_tasks: int = 5,
    ):
        self.config = config or {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.agents: Dict[str, Any] = {}
        self.active_tasks: Dict[str, Any] = {}
        self.completed_tasks: List[Any] = []
        self.task_handlers: Dict[str, Callable] = {}
        self._performance: Dict[str, Dict[str, Any]] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

    def register_handler(self, agent_type: str, handler: Callable) -> None:
        self.task_handlers[agent_type] = handler

    def _select_agent(self, task: AgentTask) -> Optional[str]:
        """Select the best agent for a task based on capabilities."""
        task_type = task.parameters.get("type", "")

        # Type-based matching
        if task_type:
            for agent_id, agent_info in self.agents.items():
                agent_type = ""
                if isinstance(agent_info, dict):
                    agent_type = agent_info.get("type", "")
                elif hasattr(agent_info, "config"):
                    cfg = agent_info.config
                    agent_type = getattr(cfg, "agent_type", getattr(cfg, "type", ""))

                if agent_type == task_type:
                    return agent_id

        # Capability-based matching
        for agent_id, agent_info in self.agents.items():
            capabilities = []
            if isinstance(agent_info, dict):
                capabilities = agent_info.get("capabilities", [])
            elif hasattr(agent_info, "config"):
                cfg = agent_info.config
                capabilities = getattr(cfg, "capabilities", [])

            for cap in capabilities:
                if cap in task.description.lower():
                    return agent_id

        # Fallback: return first available
        if self.agents:
            return next(iter(self.agents))

        return None

    async def execute_task(self, task: AgentTask) -> TaskResult:
        """Execute a task using the best available agent."""
        start_time = time.time()

        agent_id = task.agent_id or self._select_agent(task)

        if not agent_id:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error="No suitable agent found",
            )

        async with self._semaphore:
            self.active_tasks[task.task_id] = task

            try:
                handler = self.task_handlers.get("default")
                if handler:
                    result = await handler(task)
                    execution_time = time.time() - start_time
                    self._update_agent_performance(agent_id, execution_time, result.success)
                    self.completed_tasks.append(task)
                    self.active_tasks.pop(task.task_id, None)
                    return result

                # Default: simulate success
                execution_time = time.time() - start_time
                self._update_agent_performance(agent_id, execution_time, True)
                self.completed_tasks.append(task)
                self.active_tasks.pop(task.task_id, None)
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result={"agent_id": agent_id, "message": "Task executed"},
                    execution_time=execution_time,
                )

            except Exception as e:
                execution_time = time.time() - start_time
                self._update_agent_performance(agent_id, execution_time, False)
                self.active_tasks.pop(task.task_id, None)
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e),
                    execution_time=execution_time,
                )

    def _update_agent_performance(
        self, agent_id: str, execution_time: float, success: bool
    ) -> None:
        if agent_id not in self._performance:
            self._performance[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "total_execution_time": 0.0,
            }
        perf = self._performance[agent_id]
        perf["total_tasks"] += 1
        if success:
            perf["successful_tasks"] += 1
        perf["total_execution_time"] += execution_time

    def get_stats(self) -> Dict[str, Any]:
        agent_performance = {}
        for agent_id, perf in self._performance.items():
            agent_performance[agent_id] = {
                "total_tasks": perf["total_tasks"],
                "success_rate": (
                    perf["successful_tasks"] / perf["total_tasks"]
                    if perf["total_tasks"] > 0
                    else 0.0
                ),
                "avg_execution_time": (
                    perf["total_execution_time"] / perf["total_tasks"]
                    if perf["total_tasks"] > 0
                    else 0.0
                ),
            }
        return {
            "total_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "agent_performance": agent_performance,
        }

    def get_agent_registry(self) -> Dict[str, Any]:
        return self.agents

    async def shutdown(self) -> None:
        self.active_tasks.clear()
