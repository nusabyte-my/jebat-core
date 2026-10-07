"""
JEBAT Workflow Engine

DAG-based workflow execution:
- Define workflows as DAGs
- Parallel task execution
- Error handling & retry
- Progress tracking
"""

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _func_accepts_kwargs(func: Callable) -> bool:
    """Return True if a callable accepts arbitrary keyword arguments (**kwargs)."""
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return False
    return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())


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
        workflow_id = f"wf_{name.lower().replace(' ', '_')}_{uuid4().hex}"

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
        workflow = self.workflows[workflow_id]
        if workflow.status == WorkflowStatus.RUNNING:
            raise ValueError("Cannot edit a running workflow")
        if task_id in workflow.tasks:
            raise ValueError(f"Duplicate task ID: {task_id}")

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
        if workflow.status == WorkflowStatus.RUNNING:
            return {"error": "Workflow is already running"}
        for task in workflow.tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.error = None
            task.started_at = None
            task.completed_at = None
        workflow.status = WorkflowStatus.RUNNING

        context = dict(context) if context is not None else {}

        execution_id = f"exec_{workflow_id}_{uuid4().hex}"

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
        skipped_tasks = set()

        while len(completed_tasks) + len(failed_tasks) + len(skipped_tasks) < len(workflow.tasks):
            # Find ready tasks (all dependencies met)
            ready_tasks = self._get_ready_tasks(
                workflow,
                completed_tasks,
                failed_tasks,
            )
            skipped_tasks = {t.id for t in workflow.tasks.values() if t.status == TaskStatus.SKIPPED}

            if not ready_tasks:
                pending = set(workflow.tasks) - completed_tasks - failed_tasks - skipped_tasks
                if pending:
                    logger.error(f"Deadlock detected: {pending}")
                    for task_id in pending:
                        task = workflow.tasks[task_id]
                        task.status = TaskStatus.FAILED
                        task.error = "Unresolvable or cyclic task dependencies"
                        failed_tasks.add(task_id)
                    break

            # Execute ready tasks in parallel
            tasks_to_run = []
            for task in ready_tasks:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                tasks_to_run.append(self._execute_task(task, context))

            try:
                results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            except asyncio.CancelledError:
                for task in workflow.tasks.values():
                    if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.now()
                workflow.status = WorkflowStatus.FAILED
                raise

            for task, result in zip(ready_tasks, results):
                task.completed_at = datetime.now()

                if isinstance(result, BaseException):
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
            "skipped_tasks": len(skipped_tasks),
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
        blocked = set(failed)
        while True:
            downstream = {
                task.id for task in workflow.tasks.values()
                if task.id not in blocked and any(dep in blocked for dep in task.dependencies)
            }
            if not downstream:
                break
            blocked.update(downstream)

        for task in workflow.tasks.values():
            if task.id in completed or task.id in failed:
                continue
            if task.status != TaskStatus.PENDING:
                continue

            # Check dependencies
            deps_met = all(dep in completed for dep in task.dependencies)
            deps_failed = task.id in blocked

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

        # Resolve dependencies from context, only if the callable accepts kwargs
        kwargs = dict(task.kwargs)
        if _func_accepts_kwargs(task.func):
            for dep in task.dependencies:
                if dep in context:
                    kwargs[f"_{dep}_result"] = context[dep]

        # Execute with timeout
        try:
            if inspect.iscoroutinefunction(task.func):
                result = await asyncio.wait_for(
                    task.func(**kwargs),
                    timeout=task.timeout,
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(task.func, **kwargs),
                    timeout=task.timeout,
                )

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
