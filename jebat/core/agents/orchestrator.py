"""
JEBAT Agent Orchestrator

Multi-agent task management and coordination.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
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
    ):
        """
        Initialize orchestrator.

        Args:
            config: Configuration
            max_concurrent_tasks: Maximum concurrent tasks
        """
        self.config = config or {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.agents: Dict[str, Any] = {}
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False
        self._processor_task: Optional[asyncio.Task] = None
        
        # Performance tracking for intelligent agent selection
        self.agent_performance: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Tuple[str, str, float, bool]] = []  # (task_id, agent_id, execution_time, success)
        
        logger.info(f"AgentOrchestrator initialized (max={max_concurrent_tasks} tasks)")

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
            task.agent_id = agent  # Store selected agent ID in task

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

            # Update agent performance metrics
            if agent:
                self._update_agent_performance(agent, task_result.execution_time, True)

        except Exception as e:
            task_result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                agent_id=task.agent_id if hasattr(task, 'agent_id') else None,
            )

            # Update agent performance metrics for failed task
            if hasattr(task, 'agent_id') and task.agent_id:
                self._update_agent_performance(task.agent_id, task_result.execution_time, False)

        self.completed_tasks[task.task_id] = task_result
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        
        # Add to task history for tracking
        if hasattr(task, 'agent_id') and task.agent_id:
            self.task_history.append((
                task.task_id,
                task.agent_id,
                task_result.execution_time,
                task_result.success
            ))
            
            # Keep history limited to last 1000 entries
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-1000:]

    def _select_agent(self, task: AgentTask) -> Optional[str]:
        """Select agent for task using intelligent selection based on capabilities and performance."""
        if not self.agents:
            return None
        
        # Get available agents
        available_agents = list(self.agents.keys())
        
        # If only one agent, return it
        if len(available_agents) == 1:
            return available_agents[0]
        
        # Score each agent based on capabilities and performance
        agent_scores = []
        for agent_id in available_agents:
            score = self._calculate_agent_score(agent_id, task)
            agent_scores.append((agent_id, score))
        
        # Sort by score (descending) and return the best agent
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        return agent_scores[0][0] if agent_scores else None
    
    def _calculate_agent_score(self, agent_id: str, task: AgentTask) -> float:
        """Calculate score for agent based on capabilities and performance."""
        agent_info = self.agents.get(agent_id, {})
        if not agent_info:
            return 0.0
        
        score = 0.0
        
        # Capability matching (40% of score)
        task_capabilities_needed = self._extract_task_capabilities(task)
        agent_capabilities = set(agent_info.get("capabilities", []))
        if task_capabilities_needed:
            capability_match = len(task_capabilities_needed.intersection(agent_capabilities)) / len(task_capabilities_needed)
            score += capability_match * 0.4
        else:
            # If no specific capabilities needed, give base score
            score += 0.2
        
        # Performance history (40% of score)
        performance_score = self._get_agent_performance_score(agent_id)
        score += performance_score * 0.4
        
        # Current load (20% of score) - prefer less busy agents
        load_score = 1.0 - min(len([t for t in self.active_tasks.values() if t.agent_id == agent_id]) / 5.0, 1.0)
        score += load_score * 0.2
        
        return score
    
    def _extract_task_capabilities(self, task: AgentTask) -> set:
        """Extract required capabilities from task description or parameters."""
        # Simple implementation - can be enhanced with NLP
        capabilities = set()
        
        # Check task description for keywords
        description_lower = task.description.lower()
        if "analysis" in description_lower or "analyze" in description_lower:
            capabilities.add("analysis")
        if "creative" in description_lower or "create" in description_lower or "brainstorm" in description_lower:
            capabilities.add("creation")
        if "conversation" in description_lower or "chat" in description_lower or "talk" in description_lower:
            capabilities.add("conversation")
        if "research" in description_lower:
            capabilities.add("research")
        
        # Check parameters for capability hints
        params = task.parameters
        if isinstance(params, dict):
            if params.get("type") == "analytical" or params.get("analysis"):
                capabilities.add("analysis")
            if params.get("type") == "creative" or params.get("creative"):
                capabilities.add("creation")
            if params.get("type") == "conversational":
                capabilities.add("conversation")
        
        return capabilities
    
    def _get_agent_performance_score(self, agent_id: str) -> float:
        """Get performance score for agent based on history."""
        if agent_id not in self.agent_performance:
            # New agent - give neutral score
            return 0.5
        
        perf = self.agent_performance[agent_id]
        total_tasks = perf.get("total_tasks", 0)
        if total_tasks == 0:
            return 0.5
        
        success_rate = perf.get("successful_tasks", 0) / total_tasks
        # Normalize execution time (lower is better, but we want to score higher for better performance)
        avg_time = perf.get("avg_execution_time", 1.0)
        time_score = max(0.0, 1.0 - (avg_time / 10.0))  # Assume 10s is slow
        
        # Combine success rate and time score
        return (success_rate * 0.7) + (time_score * 0.3)

    async def _run_task(self, agent_id: Optional[str], task: AgentTask) -> Any:
        """Run task with agent."""
        # Placeholder - actual implementation would call agent
        await asyncio.sleep(0.1)
        return f"Task {task.task_id} completed"

    def get_agent_registry(self) -> Dict[str, Any]:
        """Get agent registry for decision engine."""
        return {
            agent_id: {"type": "agent", "status": "active"}
            for agent_id in self.agents.keys()
        }

    def _update_agent_performance(self, agent_id: str, execution_time: float, success: bool):
        """Update performance metrics for an agent."""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "total_execution_time": 0.0,
                "avg_execution_time": 0.0,
            }
        
        perf = self.agent_performance[agent_id]
        perf["total_tasks"] += 1
        if success:
            perf["successful_tasks"] += 1
        perf["total_execution_time"] += execution_time
        perf["avg_execution_time"] = perf["total_execution_time"] / perf["total_tasks"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        base_stats = {
            "agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "is_running": self._is_running,
        }
        
        # Add performance monitoring stats
        performance_stats = {
            "agent_performance": {
                agent_id: {
                    "total_tasks": perf["total_tasks"],
                    "success_rate": perf["successful_tasks"] / perf["total_tasks"] if perf["total_tasks"] > 0 else 0.0,
                    "avg_execution_time": perf["avg_execution_time"],
                }
                for agent_id, perf in self.agent_performance.items()
            },
            "task_history_size": len(self.task_history),
        }
        
        # Combine stats
        base_stats.update(performance_stats)
        return base_stats
