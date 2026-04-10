"""
JEBAT Agent Orchestrator

Multi-agent task management and coordination.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentTask:
    """Task to be executed by an agent."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    agent_id: Optional[str] = None
    user_id: str = "default"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskResult:
    """Result of task execution."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_id: Optional[str] = None


class AgentOrchestrator:
    """
    Central agent orchestration system.

    Responsibilities:
    - Agent creation and lifecycle
    - Task routing and execution
    - Performance monitoring
    - Error recovery
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        max_concurrent_tasks: int = 10,
        agent_registry=None,
    ):
        """
        Initialize orchestrator.

        Args:
            config: Configuration
            max_concurrent_tasks: Maximum concurrent tasks
            agent_registry: AgentRegistry instance for agent discovery
        """
        self.config = config or {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.agent_registry = agent_registry
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False
        self._processor_task: Optional[asyncio.Task] = None

        agent_count = 0
        if self.agent_registry:
            agent_count = len(self.agent_registry.get_all_agents())

        logger.info(f"AgentOrchestrator initialized (max={max_concurrent_tasks} tasks, agents={agent_count})")

    async def start(self):
        """Start orchestrator."""
        if self._is_running:
            return

        self._is_running = True
        self._processor_task = asyncio.create_task(self._process_tasks())
        logger.info("AgentOrchestrator started")

    async def stop(self):
        """Stop orchestrator."""
        self._is_running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("AgentOrchestrator stopped")

    async def submit_task(self, task: AgentTask) -> str:
        """Submit task for execution."""
        await self.task_queue.put(task)
        self.active_tasks[task.task_id] = task
        logger.info(f"Task submitted: {task.task_id}")
        return task.task_id

    async def _process_tasks(self):
        """Process task queue."""
        while self._is_running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task processing error: {e}")

    async def _execute_task(self, task: AgentTask):
        """Execute a single task."""
        start_time = datetime.utcnow()

        try:
            # Find appropriate agent
            agent = self._select_agent(task)

            # Execute task
            result = await self._run_task(agent, task)

            # Record result
            task_result = TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                agent_id=agent if agent else None,
            )

        except Exception as e:
            task_result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

        self.completed_tasks[task.task_id] = task_result
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]

    def _select_agent(self, task: AgentTask) -> Optional[str]:
        """Select agent for task using the AgentRegistry."""
        # Use registry's capability-based selection if available
        if self.agent_registry is not None:
            best = self.agent_registry.find_best_agent(task.description)
            if best is not None:
                return best.agent_id
            # Fall back to any available agent
            available = self.agent_registry.find_available()
            if available:
                return available[0].agent_id
            logger.warning("No available agents in registry")
            return None
        # Legacy fallback — empty
        return None

    async def _run_task(self, agent_id: Optional[str], task: AgentTask) -> Any:
        """Run task with agent."""
        # Placeholder - actual implementation would call agent
        await asyncio.sleep(0.1)
        return f"Task {task.task_id} completed"

    def get_agent_registry(self) -> Dict[str, Any]:
        """Get agent registry for decision engine."""
        if self.agent_registry is not None:
            return {
                agent.agent_id: {
                    "name": agent.agent_name,
                    "role": agent.agent_role,
                    "provider": agent.provider,
                    "model": agent.model,
                    "capabilities": agent.capabilities,
                    "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                }
                for agent in self.agent_registry.get_all_agents()
            }
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        agent_count = 0
        if self.agent_registry is not None:
            agent_count = len(self.agent_registry.get_all_agents())
        return {
            "agents": agent_count,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "is_running": self._is_running,
        }
