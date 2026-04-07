"""
JEBAT Workflow Engine

DAG-based workflow execution:
- Define workflows as DAGs
- Parallel task execution
- Error handling & retry
- Progress tracking
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """Workflow execution status."""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowTask:
    """Task definition in workflow."""

    id: str
    name: str
    func: Optional[Callable] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowDefinition:
    """Workflow definition."""

    id: str
    name: str
    description: str = ""
    tasks: Dict[str, WorkflowTask] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """
    Workflow Engine for JEBAT.

    Executes DAG-based workflows with parallel task execution.
    """

    def __init__(self):
        """Initialize Workflow Engine."""
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, Dict[str, Any]] = {}

        logger.info("WorkflowEngine initialized")

    def create_workflow(
        self,
        name: str,
        description: str = "",
    ) -> WorkflowDefinition:
        """
        Create a new workflow.

        Args:
            name: Workflow name
            description: Workflow description

        Returns:
            WorkflowDefinition
        """
        workflow_id = f"wf_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        workflow = WorkflowDefinition(
            id=workflow_id,
            name=name,
            description=description,
        )

        self.workflows[workflow_id] = workflow

        logger.info(f"Created workflow: {workflow_id}")

        return workflow

    def add_task(
        self,
        workflow_id: str,
        task_id: str,
        name: str,
        func: Callable,
        dependencies: Optional[List[str]] = None,
        **kwargs,
    ) -> WorkflowTask:
        """
        Add task to workflow.

        Args:
            workflow_id: Target workflow
            task_id: Task ID
            name: Task name
            func: Task function
            dependencies: Task dependencies
            **kwargs: Task arguments

        Returns:
            WorkflowTask
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        task = WorkflowTask(
            id=task_id,
            name=name,
            func=func,
            kwargs=kwargs,
            dependencies=dependencies or [],
        )

        self.workflows[workflow_id].tasks[task_id] = task

        logger.info(f"Added task {task_id} to workflow {workflow_id}")

        return task

    async def execute_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow to execute
            context: Execution context

        Returns:
            Execution result
        """
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING

        execution_id = f"exec_{workflow_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self.executions[execution_id] = {
            "workflow_id": workflow_id,
            "start_time": datetime.now(),
            "context": context or {},
            "task_results": {},
        }

        logger.info(f"Executing workflow {workflow_id} as {execution_id}")

        # Execute tasks in dependency order
        completed_tasks = set()
        failed_tasks = set()

        while len(completed_tasks) + len(failed_tasks) < len(workflow.tasks):
            # Find ready tasks (all dependencies met)
            ready_tasks = self._get_ready_tasks(
                workflow,
                completed_tasks,
                failed_tasks,
            )

            if not ready_tasks:
                if failed_tasks:
                    break
                # Deadlock detection
                pending = set(workflow.tasks.keys()) - completed_tasks - failed_tasks
                if pending:
                    logger.error(f"Deadlock detected: {pending}")
                    break

            # Execute ready tasks in parallel
            tasks_to_run = []
            for task in ready_tasks:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                tasks_to_run.append(self._execute_task(task, context))

            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            for task, result in zip(ready_tasks, results):
                task.completed_at = datetime.now()

                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.error = str(result)
                    failed_tasks.add(task.id)
                    logger.error(f"Task {task.id} failed: {result}")
                else:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    completed_tasks.add(task.id)
                    self.executions[execution_id]["task_results"][task.id] = result
                    logger.info(f"Task {task.id} completed")

        # Determine workflow status
        if failed_tasks:
            workflow.status = WorkflowStatus.FAILED
        else:
            workflow.status = WorkflowStatus.COMPLETED

        return {
            "status": "success" if not failed_tasks else "failed",
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "results": self.executions[execution_id]["task_results"],
            "duration": (
                datetime.now() - self.executions[execution_id]["start_time"]
            ).total_seconds(),
        }

    def _get_ready_tasks(
        self,
        workflow: WorkflowDefinition,
        completed: set,
        failed: set,
    ) -> List[WorkflowTask]:
        """Get tasks ready to execute."""
        ready = []

        for task in workflow.tasks.values():
            if task.id in completed or task.id in failed:
                continue
            if task.status != TaskStatus.PENDING:
                continue

            # Check dependencies
            deps_met = all(dep in completed for dep in task.dependencies)
            deps_failed = any(dep in failed for dep in task.dependencies)

            if deps_failed:
                task.status = TaskStatus.SKIPPED
                continue

            if deps_met:
                ready.append(task)

        return ready

    async def _execute_task(
        self,
        task: WorkflowTask,
        context: Dict[str, Any],
    ) -> Any:
        """Execute single task."""
        if not task.func:
            return None

        # Resolve dependencies from context
        for dep in task.dependencies:
            if dep in context:
                task.kwargs[f"_{dep}_result"] = context[dep]

        # Execute with timeout
        try:
            if asyncio.iscoroutinefunction(task.func):
                result = await asyncio.wait_for(
                    task.func(**task.kwargs),
                    timeout=task.timeout,
                )
            else:
                result = task.func(**task.kwargs)

            # Store in context for dependent tasks
            context[task.id] = result

            return result

        except asyncio.TimeoutError:
            raise Exception(f"Task {task.id} timed out after {task.timeout}s")

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status."""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        workflow = self.workflows[workflow_id]

        task_statuses = {task.id: task.status.value for task in workflow.tasks.values()}

        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "total_tasks": len(workflow.tasks),
            "task_statuses": task_statuses,
        }

    def visualize_workflow(self, workflow_id: str) -> str:
        """Generate workflow visualization (DOT format)."""
        if workflow_id not in self.workflows:
            return ""

        workflow = self.workflows[workflow_id]

        dot = "digraph workflow {\n"
        dot += f'  label="{workflow.name}"\n'

        for task in workflow.tasks.values():
            dot += f'  "{task.id}" [label="{task.name}"]\n'

            for dep in task.dependencies:
                dot += f'  "{dep}" -> "{task.id}"\n'

        dot += "}"

        return dot
