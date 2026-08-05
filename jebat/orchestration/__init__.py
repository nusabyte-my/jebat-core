"""
⚙️ JEBAT Workflow Orchestration

Advanced workflow orchestration for JEBAT:
- DAG-based workflow engine
- Task scheduling
- Dependency resolution
- Conditional branching
- State persistence

Part of Q3 2026 Roadmap
"""

from .workflow_engine import WorkflowEngine

try:
    from .condition_engine import ConditionEngine
except ImportError:
    ConditionEngine = None

try:
    from .dependency_resolver import DependencyResolver
except ImportError:
    DependencyResolver = None

try:
    from .state_manager import StateManager
except ImportError:
    StateManager = None

try:
    from .task_scheduler import TaskScheduler
except ImportError:
    TaskScheduler = None

__all__ = [
    "WorkflowEngine",
    "TaskScheduler",
    "DependencyResolver",
    "ConditionEngine",
    "StateManager",
]
