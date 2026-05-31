"""
JEBAT Agent System

Agent orchestration and factory:
- Multi-agent coordination
- Agent lifecycle management
- Task execution
- Performance tracking
"""

from .factory import AgentFactory, AgentTemplate, AgentType
from .chat_router import (
    LEGENDARY_MODEL_ALIASES,
    SWARM_MODEL_ALIASES,
    HangNadimClassification,
    classify_prompt_with_hang_nadim,
    format_swarm_result_text,
    infer_swarm_task,
    should_route_prompt_to_swarm,
)
from .execution_adapters import BoundedExecutionAdapters
from .orchestrator import AgentOrchestrator, AgentTask, ExecutionMode, TaskPriority, TaskResult
from .search_backend import SwarmSearchBackend

__all__ = [
    "AgentOrchestrator",
    "AgentTask",
    "AgentFactory",
    "AgentType",
    "AgentTemplate",
    "ExecutionMode",
    "BoundedExecutionAdapters",
    "HangNadimClassification",
    "LEGENDARY_MODEL_ALIASES",
    "SWARM_MODEL_ALIASES",
    "SwarmSearchBackend",
    "TaskPriority",
    "TaskResult",
    "classify_prompt_with_hang_nadim",
    "format_swarm_result_text",
    "infer_swarm_task",
    "should_route_prompt_to_swarm",
]
