"""Agent orchestrator and task execution endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from jebat.core.agents.factory import AgentFactory, AgentTemplate, AgentType, AgentPersonality
from jebat.core.agents.orchestrator import AgentOrchestrator, AgentTask, TaskPriority

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Shared orchestrator and factory instances
_orchestrator = AgentOrchestrator()
_factory = AgentFactory()

# Wire default agents into both factory and orchestrator
_default_templates = [
    AgentTemplate(agent_type=AgentType.ANALYTICAL, name="analyst", description="Data analysis and insights", personality=AgentPersonality.TECHNICAL, capabilities=["analysis", "data", "patterns"]),
    AgentTemplate(agent_type=AgentType.CREATIVE, name="creative", description="Creative generation and brainstorming", personality=AgentPersonality.CREATIVE, capabilities=["creative", "writing", "brainstorm"]),
    AgentTemplate(agent_type=AgentType.RESEARCHER, name="researcher", description="Research and information gathering", personality=AgentPersonality.TECHNICAL, capabilities=["research", "search", "web"]),
    AgentTemplate(agent_type=AgentType.TASK_EXECUTOR, name="executor", description="Task execution and automation", personality=AgentPersonality.TECHNICAL, capabilities=["execute", "automate", "deploy"]),
    AgentTemplate(agent_type=AgentType.ANALYTICAL, name="memory", description="Memory management and retrieval", personality=AgentPersonality.TECHNICAL, capabilities=["memory", "store", "recall"]),
]
for tpl in _default_templates:
    agent_id = _factory.create(tpl)
    _orchestrator.agents[agent_id] = _factory.get(agent_id)


class TaskRequest(BaseModel):
    description: str = Field(..., min_length=1, description="Task description")
    priority: str = Field(default="MEDIUM", description="Task priority: CRITICAL, HIGH, MEDIUM, LOW, BACKGROUND")
    agent_id: Optional[str] = Field(default=None, description="Specific agent ID to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional task parameters")


class TaskResponse(BaseModel):
    task_id: str
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None


@router.get("")
async def list_agents() -> Dict[str, Any]:
    """List all registered agents."""
    agents = _factory.list_agents()
    registry = _orchestrator.get_agent_registry()
    return {
        "total": len(agents),
        "agents": {
            aid: registry.get(aid, {"type": "unknown"})
            for aid in agents
        },
    }


@router.post("/execute", response_model=TaskResponse)
async def execute_task(req: TaskRequest) -> TaskResponse:
    """Execute a task using the orchestrator's agent selection."""
    priority_map = {p.value: p for p in TaskPriority}
    priority = priority_map.get(req.priority.upper(), TaskPriority.MEDIUM)

    task = AgentTask(
        description=req.description,
        priority=priority,
        agent_id=req.agent_id,
        parameters=req.parameters,
    )
    result = await _orchestrator.execute_task(task)
    return TaskResponse(
        task_id=result.task_id,
        success=result.success,
        result=result.result,
        execution_time=result.execution_time,
        error=result.error,
    )


@router.get("/stats")
async def agent_stats() -> Dict[str, Any]:
    """Orchestrator and agent performance statistics."""
    return _orchestrator.get_stats()
