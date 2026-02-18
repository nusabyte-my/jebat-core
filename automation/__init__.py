"""
Automation Package
Contains orchestration and management components for the Multi-Agent Automation System.

This package provides:
- AgentManager: Central coordinator for multiple agents
- TaskQueue: Task management and distribution system
- Orchestration utilities and workflow management
- Coordination between agents and skills

Usage:
    from automation import AgentManager, TaskQueue
    from automation.agent_manager import AgentManager

    # Create and configure agent manager
    manager = AgentManager("manager_001")

    # Register agents and start coordination
    manager.register_agent(my_agent)
    await manager.start()
"""

__version__ = "1.0.0"

# Import main components
from .agent_manager import AgentManager, TaskQueue

# Define what gets imported with "from automation import *"
__all__ = [
    "AgentManager",
    "TaskQueue",
]

# Manager registry for different orchestration strategies
MANAGER_REGISTRY = {
    "standard": AgentManager,
    # Future: Add specialized managers
    # "distributed": DistributedAgentManager,
    # "priority": PriorityAgentManager,
}


def create_manager(manager_type: str = "standard", manager_id: str = None, **kwargs):
    """
    Factory function to create agent managers by type.

    Args:
        manager_type: Type of manager to create ("standard", etc.)
        manager_id: Unique identifier for the manager (optional)
        **kwargs: Additional configuration parameters

    Returns:
        AgentManager instance of the specified type

    Raises:
        ValueError: If manager_type is not registered

    Example:
        manager = create_manager("standard", "manager_001", max_concurrent_tasks=10)
    """
    if manager_type not in MANAGER_REGISTRY:
        available_types = list(MANAGER_REGISTRY.keys())
        raise ValueError(
            f"Unknown manager type '{manager_type}'. Available types: {available_types}"
        )

    manager_class = MANAGER_REGISTRY[manager_type]

    # Generate default manager ID if not provided
    if manager_id is None:
        import time

        manager_id = f"{manager_type}_manager_{int(time.time())}"

    return manager_class(manager_id=manager_id, **kwargs)


def list_manager_types():
    """
    List all available manager types.

    Returns:
        List of available manager type names
    """
    return list(MANAGER_REGISTRY.keys())


def get_manager_info():
    """
    Get information about all available manager types.

    Returns:
        Dictionary mapping manager types to their class information
    """
    info = {}
    for manager_type, manager_class in MANAGER_REGISTRY.items():
        info[manager_type] = {
            "class_name": manager_class.__name__,
            "module": manager_class.__module__,
            "description": manager_class.__doc__.split("\n")[1].strip()
            if manager_class.__doc__
            else "No description available",
        }
    return info


# Utility functions for common orchestration patterns
async def run_sequential_workflow(manager: AgentManager, workflow_tasks: list):
    """
    Execute a list of tasks sequentially across agents.

    Args:
        manager: AgentManager instance
        workflow_tasks: List of task dictionaries with 'agent_id' and 'task' keys

    Returns:
        List of results in execution order
    """
    results = []

    for task_config in workflow_tasks:
        agent_id = task_config.get("agent_id")
        task = task_config.get("task")

        if not agent_id or not task:
            continue

        task_id = await manager.submit_task(agent_id, task)
        result = await manager.get_task_result(task_id)
        results.append(result)

    return results


async def run_parallel_workflow(manager: AgentManager, workflow_tasks: list):
    """
    Execute a list of tasks in parallel across agents.

    Args:
        manager: AgentManager instance
        workflow_tasks: List of task dictionaries with 'agent_id' and 'task' keys

    Returns:
        List of results (order may not match submission order)
    """
    import asyncio

    # Submit all tasks
    task_ids = []
    for task_config in workflow_tasks:
        agent_id = task_config.get("agent_id")
        task = task_config.get("task")

        if agent_id and task:
            task_id = await manager.submit_task(agent_id, task)
            task_ids.append(task_id)

    # Wait for all results
    result_tasks = [manager.get_task_result(task_id) for task_id in task_ids]

    results = await asyncio.gather(*result_tasks, return_exceptions=True)
    return results


def register_manager(manager_type: str, manager_class: type):
    """
    Register a new manager type with the registry.

    Args:
        manager_type: String identifier for the manager type
        manager_class: Class that implements manager functionality

    Raises:
        ValueError: If manager_class doesn't have required methods
    """
    required_methods = ["register_agent", "submit_task", "start", "stop"]

    for method in required_methods:
        if not hasattr(manager_class, method):
            raise ValueError(f"Manager class must implement '{method}' method")

    MANAGER_REGISTRY[manager_type] = manager_class


def unregister_manager(manager_type: str):
    """
    Remove a manager type from the registry.

    Args:
        manager_type: String identifier for the manager type to remove

    Returns:
        bool: True if manager was removed, False if not found
    """
    if manager_type in MANAGER_REGISTRY and manager_type != "standard":
        del MANAGER_REGISTRY[manager_type]
        return True
    return False
