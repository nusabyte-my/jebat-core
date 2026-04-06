"""
Expert Automation Skill
Advanced automation skill with comprehensive workflow management, intelligent scheduling,
process orchestration, event-driven automation, and enterprise-grade features.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiofiles
import aiohttp
import requests
import yaml
from croniter import croniter

from .base_skill import BaseSkill, SkillParameter, SkillResult, SkillType


class AutomationTriggerType(Enum):
    """Types of automation triggers"""

    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    WEBHOOK = "webhook"
    FILE_WATCHER = "file_watcher"
    API_POLL = "api_poll"
    QUEUE_BASED = "queue_based"
    MANUAL = "manual"
    CONDITIONAL = "conditional"


class AutomationStatus(Enum):
    """Automation workflow status"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(Enum):
    """Types of automation actions"""

    HTTP_REQUEST = "http_request"
    FILE_OPERATION = "file_operation"
    DATABASE_OPERATION = "database_operation"
    EMAIL_SEND = "email_send"
    SLACK_MESSAGE = "slack_message"
    SCRIPT_EXECUTION = "script_execution"
    CONDITIONAL_LOGIC = "conditional_logic"
    LOOP = "loop"
    PARALLEL_EXECUTION = "parallel_execution"
    DELAY = "delay"
    TRANSFORM_DATA = "transform_data"
    NOTIFICATION = "notification"
    WEBHOOK_CALL = "webhook_call"


@dataclass
class AutomationTrigger:
    """Automation trigger configuration"""

    trigger_id: str
    trigger_type: AutomationTriggerType
    config: Dict[str, Any]
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    last_triggered: Optional[float] = None
    trigger_count: int = 0


@dataclass
class AutomationAction:
    """Automation action configuration"""

    action_id: str
    action_type: ActionType
    config: Dict[str, Any]
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    enabled: bool = True


@dataclass
class WorkflowExecution:
    """Workflow execution tracking"""

    execution_id: str
    workflow_id: str
    status: AutomationStatus
    started_at: float
    completed_at: Optional[float] = None
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutomationWorkflow:
    """Complete automation workflow definition"""

    workflow_id: str
    name: str
    description: str
    triggers: List[AutomationTrigger]
    actions: List[AutomationAction]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    error_handlers: List[Dict[str, Any]] = field(default_factory=list)
    status: AutomationStatus = AutomationStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    execution_history: List[WorkflowExecution] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: int = 5  # 1 = highest, 10 = lowest


class ExpertAutomationSkill(BaseSkill):
    """
    Expert-level automation skill with advanced capabilities.

    Features:
    - Multi-trigger workflow management
    - Advanced scheduling with cron expressions
    - Event-driven automation
    - Parallel and sequential execution
    - Error handling and retry policies
    - Workflow versioning and rollback
    - Real-time monitoring and analytics
    - Template system for reusable workflows
    - Integration with external systems
    - Performance optimization
    - Security and audit logging
    """

    def __init__(
        self,
        skill_id: str = "expert_automation_001",
        name: str = "Expert Automation",
        description: str = "Advanced automation and workflow orchestration capabilities",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            skill_id=skill_id,
            name=name,
            skill_type=SkillType.AUTOMATION,
            description=description,
            version=version,
            config=config or {},
        )

        # Default configuration
        default_config = {
            "execution": {
                "max_concurrent_workflows": 50,
                "max_concurrent_actions": 100,
                "default_timeout": 300,
                "retry_attempts": 3,
                "retry_delay": 5,
                "retry_backoff": 2.0,
            },
            "scheduling": {
                "check_interval": 60,  # seconds
                "max_missed_runs": 3,
                "timezone": "UTC",
                "precision": "minute",  # minute, second
            },
            "monitoring": {
                "enable_metrics": True,
                "metrics_retention_days": 30,
                "enable_alerting": True,
                "alert_thresholds": {
                    "failure_rate": 0.1,  # 10%
                    "execution_time": 600,  # 10 minutes
                },
            },
            "storage": {
                "workflows_directory": "./automation/workflows",
                "templates_directory": "./automation/templates",
                "logs_directory": "./automation/logs",
                "exports_directory": "./automation/exports",
            },
            "security": {
                "enable_audit_log": True,
                "encrypt_sensitive_data": True,
                "require_approval": False,
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "integrations": {
                "n8n": {
                    "enabled": False,
                    "api_url": "http://localhost:5678/api/v1",
                    "webhook_url": "http://localhost:5678/webhook",
                },
                "zapier": {
                    "enabled": False,
                    "api_key": None,
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": None,
                    "bot_token": None,
                },
                "email": {
                    "enabled": False,
                    "smtp_server": None,
                    "smtp_port": 587,
                    "username": None,
                    "password": None,
                },
            },
        }

        # Merge with provided config
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Initialize automation state
        self.workflows: Dict[str, AutomationWorkflow] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_queue = asyncio.Queue()
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        self.file_watchers: Dict[str, asyncio.Task] = {}
        self.webhook_handlers: Dict[str, Dict[str, Any]] = {}

        # Performance metrics
        self.metrics = {
            "workflows_created": 0,
            "workflows_executed": 0,
            "workflows_failed": 0,
            "total_execution_time": 0.0,
            "avg_execution_time": 0.0,
            "actions_executed": 0,
            "triggers_fired": 0,
        }

        # Template library
        self.workflow_templates = {}

        # Create necessary directories
        for directory in self.config["storage"].values():
            os.makedirs(directory, exist_ok=True)

        # Initialize background tasks
        self.scheduler_task = None
        self.queue_processor_task = None
        self.metrics_collector_task = None

        # Load existing workflows and templates
        self._load_existing_workflows()
        self._load_workflow_templates()

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """Execute automation operation"""
        operation = parameters.get("operation", "").lower()

        try:
            # Workflow management
            if operation == "create_workflow":
                return await self._create_workflow(parameters)
            elif operation == "update_workflow":
                return await self._update_workflow(parameters)
            elif operation == "delete_workflow":
                return await self._delete_workflow(parameters)
            elif operation == "execute_workflow":
                return await self._execute_workflow(parameters)
            elif operation == "schedule_workflow":
                return await self._schedule_workflow(parameters)
            elif operation == "pause_workflow":
                return await self._pause_workflow(parameters)
            elif operation == "resume_workflow":
                return await self._resume_workflow(parameters)

            # Trigger management
            elif operation == "add_trigger":
                return await self._add_trigger(parameters)
            elif operation == "remove_trigger":
                return await self._remove_trigger(parameters)
            elif operation == "test_trigger":
                return await self._test_trigger(parameters)

            # Action management
            elif operation == "add_action":
                return await self._add_action(parameters)
            elif operation == "remove_action":
                return await self._remove_action(parameters)
            elif operation == "test_action":
                return await self._test_action(parameters)

            # Template operations
            elif operation == "create_template":
                return await self._create_template(parameters)
            elif operation == "use_template":
                return await self._use_template(parameters)
            elif operation == "list_templates":
                return await self._list_templates(parameters)

            # Monitoring and analytics
            elif operation == "get_workflow_status":
                return await self._get_workflow_status(parameters)
            elif operation == "get_execution_history":
                return await self._get_execution_history(parameters)
            elif operation == "get_metrics":
                return await self._get_metrics(parameters)
            elif operation == "generate_report":
                return await self._generate_report(parameters)

            # System management
            elif operation == "start_automation_engine":
                return await self._start_automation_engine(parameters)
            elif operation == "stop_automation_engine":
                return await self._stop_automation_engine(parameters)
            elif operation == "health_check":
                return await self._health_check(parameters)

            # Import/Export
            elif operation == "export_workflows":
                return await self._export_workflows(parameters)
            elif operation == "import_workflows":
                return await self._import_workflows(parameters)

            # Integration management
            elif operation == "setup_integration":
                return await self._setup_integration(parameters)
            elif operation == "test_integration":
                return await self._test_integration(parameters)

            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            return SkillResult(
                success=False,
                error=f"Automation operation failed: {str(e)}",
                skill_used=self.name,
            )

    async def _create_workflow(self, parameters: Dict[str, Any]) -> SkillResult:
        """Create a new automation workflow"""
        workflow_name = parameters.get("workflow_name")
        description = parameters.get("description", "")
        triggers_config = parameters.get("triggers", [])
        actions_config = parameters.get("actions", [])
        conditions = parameters.get("conditions", [])
        tags = parameters.get("tags", [])
        priority = parameters.get("priority", 5)

        if not workflow_name:
            raise ValueError("workflow_name is required")

        try:
            workflow_id = str(uuid.uuid4())
            current_time = time.time()

            # Process triggers
            triggers = []
            for i, trigger_config in enumerate(triggers_config):
                trigger = AutomationTrigger(
                    trigger_id=f"{workflow_id}_trigger_{i}",
                    trigger_type=AutomationTriggerType(trigger_config.get("type")),
                    config=trigger_config.get("config", {}),
                    enabled=trigger_config.get("enabled", True),
                )
                triggers.append(trigger)

            # Process actions
            actions = []
            for i, action_config in enumerate(actions_config):
                action = AutomationAction(
                    action_id=f"{workflow_id}_action_{i}",
                    action_type=ActionType(action_config.get("type")),
                    config=action_config.get("config", {}),
                    retry_policy=action_config.get("retry_policy", {}),
                    timeout_seconds=action_config.get("timeout", 300),
                    enabled=action_config.get("enabled", True),
                )
                actions.append(action)

            # Create workflow
            workflow = AutomationWorkflow(
                workflow_id=workflow_id,
                name=workflow_name,
                description=description,
                triggers=triggers,
                actions=actions,
                conditions=conditions,
                tags=tags,
                priority=priority,
                created_at=current_time,
                updated_at=current_time,
            )

            # Store workflow
            self.workflows[workflow_id] = workflow

            # Save to disk
            await self._save_workflow(workflow)

            # Setup triggers if workflow is active
            if workflow.status == AutomationStatus.ACTIVE:
                await self._setup_workflow_triggers(workflow)

            self.metrics["workflows_created"] += 1

            return SkillResult(
                success=True,
                data={
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "triggers_count": len(triggers),
                    "actions_count": len(actions),
                    "status": workflow.status.value,
                },
                metadata={
                    "operation": "create_workflow",
                    "priority": priority,
                },
            )

        except Exception as e:
            raise Exception(f"Failed to create workflow: {str(e)}")

    async def _execute_workflow(self, parameters: Dict[str, Any]) -> SkillResult:
        """Execute a workflow manually or from trigger"""
        workflow_id = parameters.get("workflow_id")
        input_data = parameters.get("input_data", {})
        execution_context = parameters.get("context", {})
        wait_for_completion = parameters.get("wait_for_completion", True)

        if not workflow_id or workflow_id not in self.workflows:
            raise ValueError("Valid workflow_id is required")

        try:
            workflow = self.workflows[workflow_id]

            if workflow.status not in [AutomationStatus.ACTIVE, AutomationStatus.DRAFT]:
                raise ValueError(
                    f"Workflow is not in executable state: {workflow.status}"
                )

            execution_id = str(uuid.uuid4())
            start_time = time.time()

            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=AutomationStatus.RUNNING,
                started_at=start_time,
                metadata={
                    "input_data": input_data,
                    "context": execution_context,
                    "manual_execution": True,
                },
            )

            # Store active execution
            self.active_executions[execution_id] = execution

            # Execute workflow
            if wait_for_completion:
                results = await self._execute_workflow_actions(
                    workflow, execution, input_data, execution_context
                )

                execution.status = AutomationStatus.COMPLETED
                execution.completed_at = time.time()
                execution.results = results

                # Update metrics
                execution_time = execution.completed_at - execution.started_at
                self.metrics["workflows_executed"] += 1
                self.metrics["total_execution_time"] += execution_time
                self.metrics["avg_execution_time"] = (
                    self.metrics["total_execution_time"]
                    / self.metrics["workflows_executed"]
                )

                # Store in history
                workflow.execution_history.append(execution)

                # Remove from active executions
                del self.active_executions[execution_id]

                return SkillResult(
                    success=True,
                    data={
                        "execution_id": execution_id,
                        "workflow_id": workflow_id,
                        "status": execution.status.value,
                        "execution_time": execution_time,
                        "results": results,
                        "actions_executed": len(results),
                    },
                    metadata={
                        "operation": "execute_workflow",
                        "execution_mode": "synchronous",
                    },
                )
            else:
                # Queue for asynchronous execution
                await self.execution_queue.put(
                    (workflow, execution, input_data, execution_context)
                )

                return SkillResult(
                    success=True,
                    data={
                        "execution_id": execution_id,
                        "workflow_id": workflow_id,
                        "status": execution.status.value,
                        "queued": True,
                    },
                    metadata={
                        "operation": "execute_workflow",
                        "execution_mode": "asynchronous",
                    },
                )

        except Exception as e:
            if execution_id in self.active_executions:
                self.active_executions[execution_id].status = AutomationStatus.FAILED
                self.active_executions[execution_id].errors.append(str(e))

            self.metrics["workflows_failed"] += 1
            raise Exception(f"Failed to execute workflow: {str(e)}")

    async def _execute_workflow_actions(
        self,
        workflow: AutomationWorkflow,
        execution: WorkflowExecution,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Execute all actions in a workflow"""
        results = []
        current_data = input_data.copy()

        for action in workflow.actions:
            if not action.enabled:
                continue

            try:
                # Check conditions before executing action
                if not await self._evaluate_conditions(
                    workflow.conditions, current_data, context
                ):
                    results.append(
                        {
                            "action_id": action.action_id,
                            "status": "skipped",
                            "reason": "Conditions not met",
                        }
                    )
                    continue

                # Execute action with retry policy
                action_result = await self._execute_action_with_retry(
                    action, current_data, context
                )

                results.append(action_result)

                # Update current data with action output for next action
                if action_result.get("success") and action_result.get("output"):
                    current_data.update(action_result["output"])

                self.metrics["actions_executed"] += 1

            except Exception as e:
                error_result = {
                    "action_id": action.action_id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": time.time(),
                }
                results.append(error_result)
                execution.errors.append(str(e))

                # Handle error based on workflow error handlers
                should_continue = await self._handle_action_error(
                    workflow, action, e, context
                )

                if not should_continue:
                    break

        return results

    async def _execute_action_with_retry(
        self, action: AutomationAction, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action with retry policy"""
        retry_attempts = action.retry_policy.get(
            "attempts", self.config["execution"]["retry_attempts"]
        )
        retry_delay = action.retry_policy.get(
            "delay", self.config["execution"]["retry_delay"]
        )
        retry_backoff = action.retry_policy.get(
            "backoff", self.config["execution"]["retry_backoff"]
        )

        last_error = None

        for attempt in range(retry_attempts):
            try:
                result = await self._execute_single_action(action, data, context)
                return {
                    "action_id": action.action_id,
                    "status": "success",
                    "output": result,
                    "attempt": attempt + 1,
                    "timestamp": time.time(),
                }

            except Exception as e:
                last_error = e

                if attempt < retry_attempts - 1:
                    delay = retry_delay * (retry_backoff**attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    break

        return {
            "action_id": action.action_id,
            "status": "failed",
            "error": str(last_error),
            "attempts": retry_attempts,
            "timestamp": time.time(),
        }

    async def _execute_single_action(
        self, action: AutomationAction, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Execute a single action"""
        action_type = action.action_type
        config = action.config

        if action_type == ActionType.HTTP_REQUEST:
            return await self._execute_http_request(config, data, context)

        elif action_type == ActionType.FILE_OPERATION:
            return await self._execute_file_operation(config, data, context)

        elif action_type == ActionType.DATABASE_OPERATION:
            return await self._execute_database_operation(config, data, context)

        elif action_type == ActionType.EMAIL_SEND:
            return await self._execute_email_send(config, data, context)

        elif action_type == ActionType.SLACK_MESSAGE:
            return await self._execute_slack_message(config, data, context)

        elif action_type == ActionType.SCRIPT_EXECUTION:
            return await self._execute_script(config, data, context)

        elif action_type == ActionType.CONDITIONAL_LOGIC:
            return await self._execute_conditional_logic(config, data, context)

        elif action_type == ActionType.LOOP:
            return await self._execute_loop(config, data, context)

        elif action_type == ActionType.PARALLEL_EXECUTION:
            return await self._execute_parallel_actions(config, data, context)

        elif action_type == ActionType.DELAY:
            return await self._execute_delay(config, data, context)

        elif action_type == ActionType.TRANSFORM_DATA:
            return await self._execute_data_transformation(config, data, context)

        elif action_type == ActionType.NOTIFICATION:
            return await self._execute_notification(config, data, context)

        elif action_type == ActionType.WEBHOOK_CALL:
            return await self._execute_webhook_call(config, data, context)

        else:
            raise ValueError(f"Unsupported action type: {action_type}")

    async def _execute_http_request(
        self, config: Dict[str, Any], data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute HTTP request action"""
        url = self._interpolate_string(config.get("url", ""), data, context)
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        payload = config.get("payload", {})
        timeout = config.get("timeout", 30)

        # Interpolate headers and payload
        headers = {
            k: self._interpolate_string(str(v), data, context)
            for k, v in headers.items()
        }
        payload = self._interpolate_data(payload, data, context)

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            async with session.request(
                method, url, headers=headers, json=payload
            ) as response:
                result = {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                }

                try:
                    result["data"] = await response.json()
                except:
                    result["data"] = await response.text()

                return result

    async def _execute_file_operation(
        self, config: Dict[str, Any], data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute file operation action"""
        operation = config.get("operation", "read")
        file_path = self._interpolate_string(config.get("file_path", ""), data, context)

        if operation == "read":
            async with aiofiles.open(file_path, mode="r") as f:
                content = await f.read()
            return {"content": content, "file_path": file_path}

        elif operation == "write":
            content = self._interpolate_string(config.get("content", ""), data, context)
            async with aiofiles.open(file_path, mode="w") as f:
                await f.write(content)
            return {"bytes_written": len(content), "file_path": file_path}

        elif operation == "append":
            content = self._interpolate_string(config.get("content", ""), data, context)
            async with aiofiles.open(file_path, mode="a") as f:
                await f.write(content)
            return {"bytes_appended": len(content), "file_path": file_path}

        elif operation == "delete":
            os.remove(file_path)
            return {"deleted": True, "file_path": file_path}

        else:
            raise ValueError(f"Unsupported file operation: {operation}")

    async def _execute_delay(
        self, config: Dict[str, Any], data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute delay action"""
        delay_seconds = config.get("seconds", 1)
        delay_type = config.get("type", "fixed")  # fixed, random, exponential

        if delay_type == "random":
            import random

            min_delay = config.get("min_seconds", 1)
            max_delay = config.get("max_seconds", 10)
            delay_seconds = random.uniform(min_delay, max_delay)

        elif delay_type == "exponential":
            base = config.get("base", 2)
            exponent = context.get("retry_attempt", 0)
            delay_seconds = base**exponent

        await asyncio.sleep(delay_seconds)
        return {"delayed_seconds": delay_seconds, "type": delay_type}

    async def _start_automation_engine(self, parameters: Dict[str, Any]) -> SkillResult:
        """Start the automation engine background tasks"""
        try:
            if self.scheduler_task is None or self.scheduler_task.done():
                self.scheduler_task = asyncio.create_task(self._scheduler_loop())

            if self.queue_processor_task is None or self.queue_processor_task.done():
                self.queue_processor_task = asyncio.create_task(
                    self._queue_processor_loop()
                )

            if (
                self.metrics_collector_task is None
                or self.metrics_collector_task.done()
            ):
                self.metrics_collector_task = asyncio.create_task(
                    self._metrics_collector_loop()
                )

            # Setup active workflow triggers
            for workflow in self.workflows.values():
                if workflow.status == AutomationStatus.ACTIVE:
                    await self._setup_workflow_triggers(workflow)

            return SkillResult(
                success=True,
                data={
                    "status": "started",
                    "active_workflows": len(
                        [
                            w
                            for w in self.workflows.values()
                            if w.status == AutomationStatus.ACTIVE
                        ]
                    ),
                    "background_tasks": 3,
                },
                metadata={"operation": "start_automation_engine"},
            )

        except Exception as e:
            raise Exception(f"Failed to start automation engine: {str(e)}")

    async def _scheduler_loop(self):
        """Background scheduler loop"""
        while True:
            try:
                current_time = datetime.now()

                for workflow in self.workflows.values():
                    if workflow.status != AutomationStatus.ACTIVE:
                        continue

                    for trigger in workflow.triggers:
                        if (
                            not trigger.enabled
                            or trigger.trigger_type != AutomationTriggerType.SCHEDULED
                        ):
                            continue

                        # Check if trigger should fire
                        if await self._should_trigger_fire(trigger, current_time):
                            await self._fire_trigger(workflow, trigger)

                await asyncio.sleep(self.config["scheduling"]["check_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _queue_processor_loop(self):
        """Background queue processor loop"""
        while True:
            try:
                (
                    workflow,
                    execution,
                    input_data,
                    context,
                ) = await self.execution_queue.get()

                # Execute workflow asynchronously
                results = await self._execute_workflow_actions(
                    workflow, execution, input_data, context
                )

                execution.status = AutomationStatus.COMPLETED
                execution.completed_at = time.time()
                execution.results = results

                # Store in history and remove from active
                workflow.execution_history.append(execution)
                if execution.execution_id in self.active_executions:
                    del self.active_executions[execution.execution_id]

                # Update metrics
                execution_time = execution.completed_at - execution.started_at
                self.metrics["workflows_executed"] += 1
                self.metrics["total_execution_time"] += execution_time
                self.metrics["avg_execution_time"] = (
                    self.metrics["total_execution_time"]
                    / self.metrics["workflows_executed"]
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Queue processor error: {e}")

    # Utility methods
    def _interpolate_string(
        self, template: str, data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Interpolate variables in string template"""
        all_vars = {**data, **context}

        # Simple variable substitution
        for key, value in all_vars.items():
            template = template.replace(f"{{{key}}}", str(value))
            template = template.replace(f"{{{{{{key}}}}}}", str(value))

        return template

    def _interpolate_data(
        self, data: Any, context_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Recursively interpolate variables in data structure"""
        if isinstance(data, str):
            return self._interpolate_string(data, context_data, context)
        elif isinstance(data, dict):
            return {
                k: self._interpolate_data(v, context_data, context)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [
                self._interpolate_data(item, context_data, context) for item in data
            ]
        else:
            return data

    async def _evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate workflow conditions"""
        if not conditions:
            return True

        for condition in conditions:
            condition_type = condition.get("type", "equals")
