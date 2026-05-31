"""
JEBAT Agent Orchestrator

Canonical multi-agent orchestration for JEBAT.

This module keeps the control plane lightweight and deterministic:
- role/capability-based routing
- swarm execution with parallel specialists
- optional search context injection
- consensus-style judgment over agent outputs
- basic performance tracking for future routing
"""

import asyncio
import inspect
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from .execution_adapters import BoundedExecutionAdapters
from jebat.llm.token_usage import estimate_tokens

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionMode(str, Enum):
    """How the orchestrator should execute a task."""

    AUTO = "auto"
    SINGLE = "single"
    SWARM = "swarm"
    CONSENSUS = "consensus"


SearchHandler = Callable[..., Awaitable[Any] | Any]
AgentHandler = Callable[..., Awaitable[Any] | Any]


@dataclass
class AgentTask:
    """Task to be executed by one or more agents."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    agent_id: Optional[str] = None
    user_id: str = "default"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    execution_mode: ExecutionMode = ExecutionMode.AUTO
    required_capabilities: List[str] = field(default_factory=list)
    max_agents: int = 5
    enable_search: bool = False
    search_queries: List[str] = field(default_factory=list)
    require_consensus: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of task execution."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecution:
    """Structured record of a single agent's execution within a task."""

    agent_id: str
    agent_name: str
    role: str
    score: float
    success: bool
    execution_time: float
    result: Any = None
    error: Optional[str] = None
    search_queries: List[str] = field(default_factory=list)
    search_results: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-friendly dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "score": round(self.score, 4),
            "success": self.success,
            "execution_time": round(self.execution_time, 4),
            "result": self.result,
            "error": self.error,
            "search_queries": list(self.search_queries),
            "search_results": self.search_results,
        }


class AgentOrchestrator:
    """
    Central agent orchestration system.

    Responsibilities:
    - Agent registration and lifecycle
    - Capability-aware routing
    - Swarm execution and consensus synthesis
    - Search-aware task enrichment
    - Performance tracking
    """

    BUILTIN_AGENTS: List[Dict[str, Any]] = [
        {
            "id": "panglima-001",
            "name": "Panglima",
            "role": "orchestration",
            "capabilities": ["planning", "routing", "delegation", "consensus", "judgment"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "tukang-001",
            "name": "Tukang",
            "role": "development",
            "capabilities": ["coding", "debugging", "testing", "refactoring", "implementation"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "tukang-web-001",
            "name": "Tukang Web",
            "role": "frontend",
            "capabilities": ["frontend", "ui", "ux", "accessibility", "design"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "pawang-001",
            "name": "Pawang",
            "role": "research",
            "capabilities": ["research", "search", "analysis", "documentation", "synthesis"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "hulubalang-001",
            "name": "Hulubalang",
            "role": "security",
            "capabilities": ["security", "audit", "hardening", "threat_modeling", "pentesting"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "syahbandar-001",
            "name": "Syahbandar",
            "role": "operations",
            "capabilities": ["operations", "deploy", "automation", "observability", "infrastructure"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "bendahara-001",
            "name": "Bendahara",
            "role": "database",
            "capabilities": ["database", "sql", "migration", "optimization", "data_modeling"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "penyemak-001",
            "name": "Penyemak",
            "role": "review",
            "capabilities": ["review", "validation", "qa", "regression", "verification"],
            "automation_enabled": True,
            "search_enabled": False,
            "status": "idle",
        },
        {
            "id": "senibina-antara-muka-001",
            "name": "Senibina Antara Muka",
            "role": "design",
            "capabilities": ["design", "usability", "interaction", "responsive", "product"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "pembina-aplikasi-001",
            "name": "Pembina Aplikasi",
            "role": "application",
            "capabilities": ["architecture", "integration", "fullstack", "delivery", "planning"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "hang-tuah-001",
            "name": "Hang Tuah",
            "role": "strategy",
            "capabilities": ["strategy", "leadership", "planning", "consensus", "diplomacy"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "hang-lekiu-001",
            "name": "Hang Lekiu",
            "role": "reconnaissance",
            "capabilities": ["reconnaissance", "investigation", "search", "discovery", "analysis"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "hang-lekir-001",
            "name": "Hang Lekir",
            "role": "defense",
            "capabilities": ["defense", "hardening", "resilience", "security", "guardrails"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "hang-kasturi-001",
            "name": "Hang Kasturi",
            "role": "stability",
            "capabilities": ["stability", "reliability", "verification", "release", "support"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "hang-nadim-001",
            "name": "Hang Nadim",
            "role": "intelligence",
            "capabilities": ["intelligence", "triage", "intent_classification", "routing", "anomaly_detection"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
        {
            "id": "taming-sari-001",
            "name": "Taming Sari",
            "role": "reduction",
            "capabilities": ["reduction", "synthesis", "conflict_resolution", "confidence_scoring", "judgment"],
            "automation_enabled": True,
            "search_enabled": False,
            "status": "idle",
        },
        {
            "id": "tok-guru-adi-putera-001",
            "name": "Tok Guru Adi Putera",
            "role": "sage",
            "capabilities": ["sage", "doctrine", "memory", "governance", "context_framing"],
            "automation_enabled": True,
            "search_enabled": True,
            "status": "idle",
        },
    ]

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        max_concurrent_tasks: int = 10,
    ):
        """
        Initialize orchestrator.

        Args:
            config: Configuration
            max_concurrent_tasks: Maximum queued tasks processed concurrently
        """
        self.config = {
            "auto_swarm": True,
            "full_orchestration": True,
            "force_swarm_for_all_tasks": True,
            "full_orchestration_enable_search": True,
            "full_orchestration_execution_mode": ExecutionMode.CONSENSUS.value,
            "full_orchestration_max_agents": 8,
            "full_orchestration_support_roles": ["orchestration", "review", "intelligence", "reduction", "sage"],
            "default_swarm_size": 5,
            "history_limit": 1000,
            "default_execution_mode": ExecutionMode.AUTO.value,
            **(config or {}),
        }
        self.max_concurrent_tasks = max(1, max_concurrent_tasks)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, AgentHandler] = {}
        self.search_handler: Optional[SearchHandler] = None
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.task_queue: asyncio.Queue[AgentTask] = asyncio.Queue()
        self._is_running = False
        self._worker_tasks: List[asyncio.Task] = []

        self.agent_performance: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Tuple[str, str, float, bool]] = []
        self.swarm_history: List[Dict[str, Any]] = []
        self.execution_adapters = BoundedExecutionAdapters()

        # Durable policy - separate from rolling task-local prompts
        self.durable_doctrine: List[str] = list(
            (config or {}).get("durable_doctrine", [
                "Preserve bounded execution over uncontrolled expansion",
                "Prefer the smallest safe next step with explicit rollback thinking",
                "Keep the swarm aligned under one governing decision",
            ])
        )
        self.security_policy_rules: List[str] = list(
            (config or {}).get("security_policy_rules", [
                "Elevated-risk tasks require review, security, and defense roles",
                "Critical tasks demand explicit approval or dry-run only",
                "Secret-sensitive operations must not expose credentials in outputs",
            ])
        )

        # Exposure detection patterns (redaction targets)
        self.exposure_patterns: List[re.Pattern[str]] = [
            re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"{,})]+)", re.IGNORECASE),
            re.compile(r"(?:api[_-]?key|apikey|token|secret|private[_-]?key)\s*[:=]\s*['\"]?([^\s'\"{,})]+)", re.IGNORECASE),
            re.compile(r"(?:bearer\s+)([A-Za-z0-9_\-\.]+)", re.IGNORECASE),
            re.compile(r"(?:sk-|pk-)[A-Za-z0-9]{20,}", re.IGNORECASE),
            re.compile(r"(?:https?://[^/]+@)", re.IGNORECASE),  # basic auth in URL
        ]

        logger.info(
            "AgentOrchestrator initialized (max=%s tasks, auto_swarm=%s)",
            self.max_concurrent_tasks,
            self.config["auto_swarm"],
        )

    async def start(self):
        """Start orchestrator workers."""
        if self._is_running:
            return

        self._is_running = True
        self._worker_tasks = [
            asyncio.create_task(self._process_tasks(index))
            for index in range(self.max_concurrent_tasks)
        ]
        logger.info("AgentOrchestrator started with %s workers", len(self._worker_tasks))

    async def stop(self):
        """Stop orchestrator workers."""
        self._is_running = False
        for worker in self._worker_tasks:
            worker.cancel()

        for worker in self._worker_tasks:
            try:
                await worker
            except asyncio.CancelledError:
                pass

        self._worker_tasks = []
        logger.info("AgentOrchestrator stopped")

    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Register or update an agent definition."""
        normalized = {
            "id": agent_id,
            "name": agent_info.get("name", agent_id),
            "role": agent_info.get("role", agent_info.get("type", "general")),
            "type": agent_info.get("type", agent_info.get("role", "general")),
            "capabilities": list(agent_info.get("capabilities", [])),
            "model": agent_info.get("model", ""),
            "provider": agent_info.get("provider", ""),
            "status": agent_info.get("status", "idle"),
            "automation_enabled": agent_info.get("automation_enabled", True),
            "search_enabled": agent_info.get("search_enabled", False),
            "metadata": dict(agent_info.get("metadata", {})),
        }

        if "handler" in agent_info and callable(agent_info["handler"]):
            normalized["handler"] = agent_info["handler"]

        self.agents[agent_id] = normalized
        logger.info("Registered agent: %s (%s)", normalized["name"], normalized["role"])
        return normalized

    def register_builtin_agents(self) -> int:
        """Register JEBAT's canonical built-in specialist agents."""
        registered = 0
        for agent in self.BUILTIN_AGENTS:
            self.register_agent(agent["id"], agent)
            registered += 1
        self.register_builtin_handlers()
        return registered

    def register_builtin_handlers(self):
        """Register default automated handlers for canonical JEBAT roles."""
        for role in {
            "orchestration",
            "development",
            "frontend",
            "research",
            "security",
            "operations",
            "database",
            "review",
            "design",
            "application",
            "strategy",
            "reconnaissance",
            "defense",
            "stability",
            "intelligence",
            "reduction",
            "sage",
        }:
            self.handlers.setdefault(role, self._builtin_role_handler)

    def register_handler(self, key: str, handler: AgentHandler):
        """Register a handler by agent id, role, or the literal key `default`."""
        self.handlers[key] = handler
        logger.info("Registered handler for %s", key)

    def register_search_handler(self, handler: SearchHandler):
        """Register the shared search handler used for search-enabled tasks."""
        self.search_handler = handler
        logger.info("Registered search handler")

    def list_agents(self) -> List[Dict[str, Any]]:
        """List registered agents."""
        return list(self.agents.values())

    async def submit_task(self, task: AgentTask) -> str:
        """Submit task for queued execution."""
        await self.task_queue.put(task)
        self.active_tasks[task.task_id] = task
        logger.info("Task submitted: %s", task.task_id)
        return task.task_id

    async def run_task(self, task: AgentTask) -> TaskResult:
        """Execute a task immediately without queueing."""
        self.active_tasks[task.task_id] = task
        result = await self._execute_task(task)
        return result

    async def execute_task(self, task: AgentTask) -> TaskResult:
        """Compatibility alias used by older integrations such as UltraLoop."""
        return await self.run_task(task)

    def plan_task(self, task: AgentTask) -> Dict[str, Any]:
        """Preview swarm routing, ranking, and lead selection without executing."""
        self._apply_task_defaults(task)
        resolved_mode = self._resolve_execution_mode(task)

        required_capabilities = sorted(self._extract_task_capabilities(task))
        ranked_agents = self._get_ranked_agents(task)
        selected_agents = (
            self._select_swarm_agents(task)
            if resolved_mode in {ExecutionMode.SWARM, ExecutionMode.CONSENSUS}
            else ranked_agents[:1]
        )
        swarm_lead = (
            self._choose_swarm_lead(task, selected_agents)
            if resolved_mode in {ExecutionMode.SWARM, ExecutionMode.CONSENSUS}
            else {}
        )
        preferred_roles = self._get_role_preferences(task)
        security_layer = self._build_security_layer(task)

        return {
            "task_id": task.task_id,
            "description": task.description,
            "execution_mode": resolved_mode.value,
            "required_capabilities": required_capabilities,
            "search_enabled": task.enable_search,
            "require_consensus": task.require_consensus,
            "full_orchestration": self._is_full_orchestration_enabled(task),
            "recommended_delivery_mode": self._recommended_delivery_mode(task),
            "security_layer": security_layer,
            "preferred_roles": preferred_roles,
            "swarm_lead": swarm_lead or None,
            "ranked_agents": [
                self._build_ranked_agent_entry(agent_id, task)
                for agent_id, _score in ranked_agents[: max(task.max_agents * 2, 8)]
            ],
            "selected_agents": [
                self._build_ranked_agent_entry(agent_id, task)
                for agent_id, _score in selected_agents
            ],
        }

    async def _process_tasks(self, worker_index: int):
        """Process queued tasks."""
        while self._is_running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._execute_task(task)
                self.task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                logger.error("Worker %s task processing error: %s", worker_index, exc)

    async def _execute_task(self, task: AgentTask) -> TaskResult:
        """Execute a single task or a swarm task."""
        self._apply_task_defaults(task)
        start_time = datetime.now(timezone.utc)
        mode = self._resolve_execution_mode(task)

        # Enforce critical task policy before any execution
        security_layer = self._build_security_layer(task)
        if security_layer.get("risk_level") == "critical":
            approve = (task.parameters or {}).get("approve_critical") or (task.parameters or {}).get("force_execution") or (task.parameters or {}).get("bypass_safety")
            if not approve:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error="Critical task requires explicit approval (set approve_critical=true) or dry-run mode",
                    execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                    agent_id=task.agent_id,
                    metadata={
                        "execution_mode": mode.value,
                        "full_orchestration": self._is_full_orchestration_enabled(task),
                        "security_layer": {**security_layer, "policy_action": "blocked", "approval_required": True},
                    },
                )

        try:
            if mode in (ExecutionMode.SWARM, ExecutionMode.CONSENSUS):
                task_result = await self._execute_swarm_task(task, mode, start_time)
            else:
                task_result = await self._execute_single_task(task, start_time)
        except Exception as exc:
            task_result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(exc),
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                agent_id=task.agent_id,
                metadata={
                    "execution_mode": mode.value,
                    "full_orchestration": self._is_full_orchestration_enabled(task),
                    "security_layer": self._build_security_layer(task),
                },
            )

        self.completed_tasks[task.task_id] = task_result
        self.active_tasks.pop(task.task_id, None)
        return task_result

    def _resolve_execution_mode(self, task: AgentTask) -> ExecutionMode:
        """Resolve task execution mode."""
        if self._is_full_orchestration_enabled(task):
            if isinstance(task.execution_mode, ExecutionMode) and task.execution_mode in {
                ExecutionMode.SWARM,
                ExecutionMode.CONSENSUS,
            }:
                return task.execution_mode

            params = task.parameters if isinstance(task.parameters, dict) else {}
            requested_mode = str(params.get("execution_mode", "")).strip().lower()
            if requested_mode in {ExecutionMode.SWARM.value, ExecutionMode.CONSENSUS.value}:
                return ExecutionMode(requested_mode)

            return ExecutionMode(
                self.config.get("full_orchestration_execution_mode", ExecutionMode.CONSENSUS.value)
            )

        if isinstance(task.execution_mode, ExecutionMode) and task.execution_mode != ExecutionMode.AUTO:
            return task.execution_mode

        if task.require_consensus:
            return ExecutionMode.CONSENSUS

        if task.agent_id:
            return ExecutionMode.SINGLE

        if task.parameters.get("execution_mode"):
            return ExecutionMode(task.parameters["execution_mode"])

        if task.parameters.get("swarm") or task.parameters.get("parallel"):
            return ExecutionMode.SWARM

        required_capabilities = task.required_capabilities or list(self._extract_task_capabilities(task))
        if self.config.get("auto_swarm", True):
            if task.enable_search:
                return ExecutionMode.SWARM
            if len(required_capabilities) > 1:
                return ExecutionMode.SWARM
            if any(cap in {"research", "planning", "architecture", "review"} for cap in required_capabilities):
                return ExecutionMode.SWARM

        return ExecutionMode(self.config.get("default_execution_mode", ExecutionMode.SINGLE.value))

    async def _execute_single_task(self, task: AgentTask, start_time: datetime) -> TaskResult:
        """Execute task with the best single agent."""
        agent_id = task.agent_id or self._select_agent(task)
        task.agent_id = agent_id

        if agent_id is None and "default" not in self.handlers:
            raise RuntimeError("No agent or default handler available for task execution")

        score = self._calculate_agent_score(agent_id, task) if agent_id else 0.0
        execution = await self._run_task(agent_id, task, score)
        # Build runtime security summary including exposure findings from this execution
        runtime_security = self._build_security_summary(task, [execution], self._extract_next_actions(execution.result))
        task_result = TaskResult(
            task_id=task.task_id,
            success=execution.success,
            result=execution.result,
            error=execution.error,
            execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
            agent_id=agent_id,
            metadata={
                "execution_mode": ExecutionMode.SINGLE.value,
                "full_orchestration": False,
                "security_layer": runtime_security,
                "search_queries": execution.search_queries,
                "search_results": execution.search_results,
            },
        )

        if agent_id:
            self._update_agent_performance(agent_id, execution.execution_time, execution.success)
            self._record_task_history(task.task_id, agent_id, execution.execution_time, execution.success)

        return task_result

    async def _execute_swarm_task(
        self,
        task: AgentTask,
        mode: ExecutionMode,
        start_time: datetime,
    ) -> TaskResult:
        """Execute task across multiple agents and synthesize judgment."""
        selected_agents = self._select_swarm_agents(task)
        swarm_lead = self._choose_swarm_lead(task, selected_agents)
        if not selected_agents and "default" not in self.handlers:
            raise RuntimeError("No agents available for swarm execution")

        executions = await asyncio.gather(
            *[
                self._run_task(agent_id, task, score)
                for agent_id, score in selected_agents
            ],
            return_exceptions=True,
        )

        normalized_executions: List[AgentExecution] = []
        for fallback_index, execution in enumerate(executions):
            if isinstance(execution, Exception):
                agent_id = selected_agents[fallback_index][0]
                agent_info = self.agents.get(agent_id, {})
                normalized_executions.append(
                    AgentExecution(
                        agent_id=agent_id,
                        agent_name=agent_info.get("name", agent_id),
                        role=agent_info.get("role", "general"),
                        score=selected_agents[fallback_index][1],
                        success=False,
                        execution_time=0.0,
                        error=str(execution),
                    )
                )
            else:
                normalized_executions.append(execution)

        for execution in normalized_executions:
            self._update_agent_performance(execution.agent_id, execution.execution_time, execution.success)
            self._record_task_history(
                task.task_id,
                execution.agent_id,
                execution.execution_time,
                execution.success,
            )

        swarm_result = self._judge_swarm_results(task, normalized_executions, mode)
        if swarm_lead:
            swarm_result["swarm_lead"] = swarm_lead
        task_result = TaskResult(
            task_id=task.task_id,
            success=any(execution.success for execution in normalized_executions),
            result=swarm_result,
            error=None if any(execution.success for execution in normalized_executions) else "All swarm agents failed",
            execution_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
            metadata={
                "execution_mode": mode.value,
                "full_orchestration": self._is_full_orchestration_enabled(task),
                "security_layer": self._build_security_layer(task),
                "selected_agents": [agent_id for agent_id, _score in selected_agents],
                "swarm_lead": swarm_lead,
                "agent_count": len(normalized_executions),
            },
        )

        self.swarm_history.append(
            {
                "task_id": task.task_id,
                "mode": mode.value,
                "selected_agents": [agent_id for agent_id, _score in selected_agents],
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        history_limit = int(self.config.get("history_limit", 1000))
        if len(self.swarm_history) > history_limit:
            self.swarm_history = self.swarm_history[-history_limit:]

        return task_result

    def _select_agent(self, task: AgentTask) -> Optional[str]:
        """Select the best single agent for a task."""
        ranked = self._get_ranked_agents(task, limit=1)
        return ranked[0][0] if ranked else None

    def _select_swarm_agents(self, task: AgentTask) -> List[Tuple[str, float]]:
        """Select a role-diverse set of agents for swarm execution."""
        limit = self._resolve_swarm_limit(task)
        ranked = self._get_ranked_agents(task, limit=max(limit * 2, limit))
        if not ranked:
            return []

        selected: List[Tuple[str, float]] = []
        selected_ids = set()
        desired_roles = self._get_role_preferences(task)
        if self._is_full_orchestration_enabled(task):
            for role in self.config.get("full_orchestration_support_roles", []):
                if role not in desired_roles:
                    desired_roles.append(role)

        for role in desired_roles:
            if len(selected) >= limit:
                break
            for agent_id, score in ranked:
                if agent_id in selected_ids:
                    continue
                if self.agents.get(agent_id, {}).get("role", "general") != role:
                    continue
                selected.append((agent_id, score))
                selected_ids.add(agent_id)
                break

        seen_roles = {
            self.agents.get(agent_id, {}).get("role", "general")
            for agent_id, _score in selected
        }
        for agent_id, score in ranked:
            if agent_id in selected_ids:
                continue
            role = self.agents.get(agent_id, {}).get("role", "general")
            if (
                not self._is_full_orchestration_enabled(task)
                and role in seen_roles
                and len(ranked) > limit
            ):
                continue
            selected.append((agent_id, score))
            selected_ids.add(agent_id)
            seen_roles.add(role)
            if len(selected) >= limit:
                break

        selected = selected or ranked[:limit]
        pinned_agent_id = task.agent_id if task.agent_id in self.agents else None
        if self._is_full_orchestration_enabled(task) and pinned_agent_id and pinned_agent_id not in {
            agent_id for agent_id, _score in selected
        }:
            pinned_entry = next(
                ((agent_id, score) for agent_id, score in ranked if agent_id == pinned_agent_id),
                None,
            )
            if pinned_entry:
                if len(selected) >= limit:
                    selected[-1] = pinned_entry
                else:
                    selected.append(pinned_entry)
        lead = self._choose_swarm_lead(task, selected)
        if lead:
            selected.sort(
                key=lambda item: (
                    item[0] != lead.get("agent_id"),
                    -item[1],
                )
            )
        return selected

    def _get_ranked_agents(self, task: AgentTask, limit: Optional[int] = None) -> List[Tuple[str, float]]:
        """Rank agents by task fit."""
        if task.agent_id and not self._is_full_orchestration_enabled(task):
            score = self._calculate_agent_score(task.agent_id, task)
            return [(task.agent_id, score)] if task.agent_id in self.agents else []

        ranked: List[Tuple[str, float]] = []
        for agent_id, agent_info in self.agents.items():
            if not self._is_agent_available(agent_info):
                continue
            ranked.append((agent_id, self._calculate_agent_score(agent_id, task)))

        ranked.sort(key=lambda item: item[1], reverse=True)
        if limit is not None:
            return ranked[:limit]
        return ranked

    def _is_agent_available(self, agent_info: Dict[str, Any]) -> bool:
        """Check whether an agent is eligible for routing."""
        return agent_info.get("status", "idle") not in {"offline", "disabled"}

    def _calculate_agent_score(self, agent_id: Optional[str], task: AgentTask) -> float:
        """Calculate routing score for an agent."""
        return self._score_agent_components(agent_id, task).get("total", 0.0)

    def _score_agent_components(self, agent_id: Optional[str], task: AgentTask) -> Dict[str, float]:
        """Break agent scoring into inspectable components."""
        if not agent_id:
            return {"total": 0.0}

        agent_info = self.agents.get(agent_id, {})
        if not agent_info:
            return {"total": 0.0}

        required_capabilities = task.required_capabilities or list(self._extract_task_capabilities(task))
        agent_capabilities = set(agent_info.get("capabilities", []))
        agent_role = agent_info.get("role", "")
        breakdown: Dict[str, float] = {
            "capability_fit": 0.0,
            "performance": 0.0,
            "load": 0.0,
            "automation": 0.0,
            "search": 0.0,
            "consensus": 0.0,
            "role_preference": 0.0,
        }

        if required_capabilities:
            matches = 0.0
            for capability in required_capabilities:
                capability_lower = capability.lower()
                if capability_lower in agent_capabilities:
                    matches += 1.0
                elif capability_lower == agent_role:
                    matches += 0.85
                elif any(capability_lower in capability for capability in agent_capabilities):
                    matches += 0.6
            breakdown["capability_fit"] = (matches / len(required_capabilities)) * 0.5
        else:
            breakdown["capability_fit"] = 0.2

        breakdown["performance"] = self._get_agent_performance_score(agent_id) * 0.25

        load = len([active for active in self.active_tasks.values() if active.agent_id == agent_id])
        load_score = max(0.0, 1.0 - (load / 5.0))
        breakdown["load"] = load_score * 0.15

        if agent_info.get("automation_enabled", False):
            breakdown["automation"] = 0.05

        if task.enable_search and agent_info.get("search_enabled", False):
            breakdown["search"] = 0.05

        if task.require_consensus and "judgment" in agent_capabilities:
            breakdown["consensus"] = 0.1

        role_preferences = self._get_role_preferences(task)
        if role_preferences and agent_role in role_preferences:
            preference_rank = role_preferences.index(agent_role)
            breakdown["role_preference"] = max(0.0, 0.18 - (preference_rank * 0.04))

        breakdown["total"] = round(sum(breakdown.values()), 4)
        return breakdown

    def _build_ranked_agent_entry(self, agent_id: str, task: AgentTask) -> Dict[str, Any]:
        """Build an inspectable ranked agent entry for planning surfaces."""
        agent = self.agents.get(agent_id, {})
        breakdown = self._score_agent_components(agent_id, task)
        return {
            "agent_id": agent_id,
            "name": agent.get("name", agent_id),
            "role": agent.get("role", "general"),
            "capabilities": list(agent.get("capabilities", [])),
            "score": breakdown.get("total", 0.0),
            "score_breakdown": breakdown,
            "search_enabled": bool(agent.get("search_enabled", False)),
            "automation_enabled": bool(agent.get("automation_enabled", False)),
        }

    def _get_role_preferences(self, task: AgentTask) -> List[str]:
        """Determine preferred lead and support roles for a task."""
        params = task.parameters if isinstance(task.parameters, dict) else {}
        route = str(params.get("hang_nadim_route", "")).strip().lower()
        required_capabilities = [
            str(cap).strip().lower()
            for cap in (task.required_capabilities or self._extract_task_capabilities(task))
            if str(cap).strip()
        ]
        description = task.description.lower()

        ordered_roles: List[str] = []

        def push(role: str):
            if role and role not in ordered_roles:
                ordered_roles.append(role)

        if route == "legendary_swarm":
            if any(
                keyword in description for keyword in ("inventory", "discover", "find every", "map the terrain")
            ):
                push("reconnaissance")
            elif any(
                keyword in description for keyword in ("stability", "rollback", "release confidence", "reliability")
            ):
                push("stability")
            elif any(
                keyword in description for keyword in ("triage", "classify", "route intelligently")
            ):
                push("intelligence")
            elif any(
                keyword in description for keyword in ("protect", "defend", "hardening", "guardrail", "resilience")
            ):
                push("defense")
            else:
                push("strategy")

            for role in ("reconnaissance", "defense", "stability", "intelligence", "strategy"):
                if role in required_capabilities:
                    push(role)
            push("sage")

        capability_role_map = {
            "research": "research",
            "review": "review",
            "database": "database",
            "operations": "operations",
            "security": "security",
            "development": "development",
            "design": "design",
            "application": "application",
            "architecture": "application",
            "planning": "orchestration",
            "strategy": "strategy",
            "reconnaissance": "reconnaissance",
            "defense": "defense",
            "stability": "stability",
            "intelligence": "intelligence",
            "reduction": "reduction",
            "sage": "sage",
        }
        for capability in required_capabilities:
            push(capability_role_map.get(capability, capability))

        if task.require_consensus:
            push("orchestration")

        return ordered_roles

    def _choose_swarm_lead(self, task: AgentTask, selected_agents: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Choose the lead agent for a swarm execution."""
        if not selected_agents:
            return {}

        if task.agent_id and task.agent_id in {agent_id for agent_id, _score in selected_agents}:
            agent = self.agents.get(task.agent_id, {})
            pinned_score = dict(selected_agents).get(task.agent_id, 0.0)
            return {
                "agent_id": task.agent_id,
                "name": agent.get("name", task.agent_id),
                "role": agent.get("role", "general"),
                "score": round(pinned_score, 4),
                "selection_reason": "Pinned agent retained as preferred swarm lead",
            }

        preferred_roles = self._get_role_preferences(task)
        selected_map = {agent_id: score for agent_id, score in selected_agents}

        for role in preferred_roles:
            for agent_id, score in selected_agents:
                agent = self.agents.get(agent_id, {})
                if agent.get("role") == role:
                    return {
                        "agent_id": agent_id,
                        "name": agent.get("name", agent_id),
                        "role": role,
                        "score": round(score, 4),
                        "selection_reason": f"Preferred lead role for this task: {role}",
                    }

        agent_id, score = selected_agents[0]
        agent = self.agents.get(agent_id, {})
        return {
            "agent_id": agent_id,
            "name": agent.get("name", agent_id),
            "role": agent.get("role", "general"),
            "score": round(selected_map[agent_id], 4),
            "selection_reason": "Highest-ranked swarm candidate",
        }

    def _extract_task_capabilities(self, task: AgentTask) -> set[str]:
        """Extract required capabilities from the task description and parameters."""
        if task.required_capabilities:
            return {cap.lower() for cap in task.required_capabilities}

        capabilities = set()
        description = task.description.lower()
        params = task.parameters if isinstance(task.parameters, dict) else {}

        keyword_map = {
            "analysis": ["analysis", "analyze", "insight"],
            "research": ["research", "search", "investigate"],
            "coding": ["code", "coding", "implement"],
            "debugging": ["debug", "bug", "fix"],
            "testing": ["test", "qa", "validation"],
            "security": ["security", "audit", "hardening", "vulnerability"],
            "database": ["database", "sql", "migration", "schema", "query"],
            "operations": ["deploy", "ops", "infrastructure", "observability"],
            "design": ["ui", "ux", "design", "responsive"],
            "planning": ["plan", "orchestrate", "route", "judge"],
            "review": ["review", "verify", "regression"],
            "architecture": ["architecture", "integration", "system design"],
            "strategy": ["strategy", "best approach", "decision", "judge", "tradeoff"],
            "reconnaissance": ["recon", "discovery", "find", "locate", "inventory"],
            "defense": ["defense", "resilience", "guardrail", "protect"],
            "stability": ["stability", "reliability", "release", "support"],
            "intelligence": ["intent", "triage", "classify", "route", "intelligence"],
            "reduction": ["reduce", "synthesize", "merge", "final answer", "confidence"],
            "sage": ["doctrine", "wisdom", "governance", "context framing", "long memory"],
        }

        for capability, keywords in keyword_map.items():
            if any(keyword in description for keyword in keywords):
                capabilities.add(capability)

        if params.get("analysis") or params.get("type") == "analytical":
            capabilities.add("analysis")
        if params.get("creative") or params.get("type") == "creative":
            capabilities.add("design")
        if params.get("database"):
            capabilities.add("database")
        if params.get("security"):
            capabilities.add("security")
        if params.get("research") or task.enable_search:
            capabilities.add("research")
        if params.get("strategy"):
            capabilities.add("strategy")
        if params.get("reconnaissance"):
            capabilities.add("reconnaissance")
        if params.get("defense"):
            capabilities.add("defense")
        if params.get("stability"):
            capabilities.add("stability")
        if params.get("intelligence"):
            capabilities.add("intelligence")
        if params.get("reduction"):
            capabilities.add("reduction")
        if params.get("sage") or params.get("doctrine"):
            capabilities.add("sage")
        if params.get("required_capabilities"):
            capabilities.update(str(cap).lower() for cap in params["required_capabilities"])

        return capabilities

    def _is_full_orchestration_enabled(self, task: AgentTask) -> bool:
        """Return True when every task should execute through the swarm path."""
        params = task.parameters if isinstance(task.parameters, dict) else {}
        if params.get("disable_full_orchestration"):
            return False
        if "full_orchestration" in params:
            return bool(params.get("full_orchestration"))
        return bool(
            self.config.get("full_orchestration", False)
            or self.config.get("force_swarm_for_all_tasks", False)
        )

    def _build_security_layer(self, task: AgentTask) -> Dict[str, Any]:
        """Classify task risk and derive security overlay requirements."""
        text = task.description.lower()
        params = task.parameters if isinstance(task.parameters, dict) else {}

        critical_keywords = {
            "drop database",
            "delete production",
            "rm -rf",
            "reset production",
            "wipe",
            "credential",
            "password",
            "secret",
            "token",
            "public exposure",
        }
        high_keywords = {
            "migration",
            "schema",
            "rollout",
            "production",
            "deploy",
            "rollback",
            "security",
            "hardening",
            "authentication",
            "authorization",
            "database",
        }
        medium_keywords = {
            "review",
            "risk",
            "guardrail",
            "staging",
            "access",
            "compliance",
            "audit",
        }

        triggers: List[str] = []
        risk_level = "low"
        for keyword in sorted(critical_keywords):
            if keyword in text:
                triggers.append(keyword)
        if triggers:
            risk_level = "critical"
        else:
            for keyword in sorted(high_keywords):
                if keyword in text:
                    triggers.append(keyword)
            if triggers:
                risk_level = "high"
            else:
                for keyword in sorted(medium_keywords):
                    if keyword in text:
                        triggers.append(keyword)
                if triggers:
                    risk_level = "medium"

        if params.get("security") or params.get("destructive") or params.get("production"):
            if risk_level == "low":
                risk_level = "high"
            if "explicit-parameter" not in triggers:
                triggers.append("explicit-parameter")

        required_roles: List[str] = []
        if risk_level in {"medium", "high", "critical"}:
            required_roles.append("review")
        if risk_level in {"high", "critical"}:
            required_roles.extend(["security", "defense"])

        deduped_roles: List[str] = []
        for role in required_roles:
            if role not in deduped_roles:
                deduped_roles.append(role)

        layer = {
            "risk_level": risk_level,
            "triggers": triggers,
            "required_roles": deduped_roles,
            "enforced": bool(deduped_roles),
        }

        # Enforce critical policy: dry-run or explicit approval only
        if risk_level == "critical":
            approve = params.get("approve_critical") or params.get("force_execution") or params.get("bypass_safety")
            if not approve:
                layer["policy_action"] = "dry_run_only"
                layer["approval_required"] = True
                layer["dry_run_enforced"] = True
                layer["recommended_controls"] = [
                    "Run in dry-run mode only",
                    "Obtain explicit approval", 
                    "Or set approve_critical=true to override",
                ]
            else:
                layer["policy_action"] = "explicit_override"
                layer["approval_required"] = False
                layer["dry_run_enforced"] = False

        return layer

    def _apply_task_defaults(self, task: AgentTask) -> None:
        """Normalize task defaults before planning or execution."""
        if not isinstance(task.parameters, dict):
            task.parameters = {}

        if not self._is_full_orchestration_enabled(task):
            return

        task.parameters.setdefault("full_orchestration", True)

        required_capabilities = list(task.required_capabilities or self._extract_task_capabilities(task))
        if not required_capabilities:
            required_capabilities = ["research", "review"]

        pinned_role = self.agents.get(task.agent_id or "", {}).get("role")
        support_roles = list(self.config.get("full_orchestration_support_roles", []))
        security_layer = self._build_security_layer(task)
        merged_capabilities = required_capabilities + support_roles + security_layer.get("required_roles", [])
        if pinned_role:
            merged_capabilities.insert(0, pinned_role)

        deduped_capabilities: List[str] = []
        seen = set()
        for capability in merged_capabilities:
            normalized = str(capability).strip().lower()
            if not normalized or normalized in seen:
                continue
            deduped_capabilities.append(normalized)
            seen.add(normalized)

        task.required_capabilities = deduped_capabilities
        task.require_consensus = True
        if self.config.get("full_orchestration_enable_search", True):
            task.enable_search = True
        task.max_agents = self._resolve_swarm_limit(task)

    def _resolve_swarm_limit(self, task: AgentTask) -> int:
        """Resolve how many agents a swarm execution should involve."""
        base_limit = max(1, task.max_agents or int(self.config.get("default_swarm_size", 3)))
        if not self._is_full_orchestration_enabled(task):
            return base_limit

        preferred_roles = self._get_role_preferences(task)
        support_roles = list(self.config.get("full_orchestration_support_roles", []))
        desired_roles: List[str] = []
        for role in [*preferred_roles, *support_roles]:
            if role and role not in desired_roles:
                desired_roles.append(role)

        expanded_limit = max(base_limit, len(desired_roles), len(task.required_capabilities))
        return min(expanded_limit, int(self.config.get("full_orchestration_max_agents", 8)))

    def _build_agent_scope(self, task: AgentTask, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build a bounded role-specific focus block for an agent."""
        role = str(agent_info.get("role", "general")).strip().lower() or "general"
        focus_map = {
            "orchestration": ("coordinate the parallel workset", "routing, sequencing, and consensus"),
            "development": ("implement the minimal code change", "code path, tests, and affected behavior"),
            "frontend": ("refine the user-facing flow", "view hierarchy, layout, and interaction fit"),
            "research": ("collect the strongest evidence", "current facts, comparisons, and supporting signals"),
            "security": ("reduce exposure before change", "attack surface, hardening, and mitigation"),
            "operations": ("protect rollout safety", "deployment sequencing, rollback, and observability"),
            "database": ("validate schema and query impact", "migrations, query cost, and rollback safety"),
            "review": ("challenge assumptions and regressions", "verification, risks, and missing coverage"),
            "design": ("clarify the product surface", "hierarchy, usability, and responsive fit"),
            "application": ("align the cross-layer system", "integration points and delivery shape"),
            "strategy": ("set the governing direction", "tradeoffs, priorities, and execution frame"),
            "reconnaissance": ("map the terrain first", "unknowns, inventory, and discovery signals"),
            "defense": ("strengthen guardrails and resilience", "protections, failure modes, and safeguards"),
            "stability": ("preserve release confidence", "tests, reliability, and support readiness"),
            "intelligence": ("classify and route the work", "intent, decomposition, and specialist fit"),
            "reduction": ("merge the swarm outputs", "conflicts, confidence, and final synthesis"),
            "sage": ("govern with doctrine and memory", "durable context, guardrails, and strategic framing"),
        }
        objective, focus = focus_map.get(role, ("execute the assigned slice", "the role-specific task scope"))
        return {
            "role": role,
            "objective": objective,
            "focus": focus,
            "deliverable": f"{role} findings and next actions for the assigned slice",
            "task_description": task.description,
        }

    def _build_scoped_task(self, task: AgentTask, agent_scope: Dict[str, Any]) -> AgentTask:
        """Clone a task with role-scoped context without mutating the shared task."""
        return AgentTask(
            task_id=task.task_id,
            description=task.description,
            parameters={**(task.parameters or {}), "agent_scope": dict(agent_scope)},
            priority=task.priority,
            agent_id=task.agent_id,
            user_id=task.user_id,
            created_at=task.created_at,
            execution_mode=task.execution_mode,
            required_capabilities=list(task.required_capabilities),
            max_agents=task.max_agents,
            enable_search=task.enable_search,
            search_queries=list(task.search_queries),
            require_consensus=task.require_consensus,
            metadata=dict(task.metadata),
        )

    def _get_agent_performance_score(self, agent_id: str) -> float:
        """Get performance score for agent based on history."""
        if agent_id not in self.agent_performance:
            return 0.5

        perf = self.agent_performance[agent_id]
        total_tasks = perf.get("total_tasks", 0)
        if total_tasks == 0:
            return 0.5

        success_rate = perf.get("successful_tasks", 0) / total_tasks
        avg_time = perf.get("avg_execution_time", 1.0)
        time_score = max(0.0, 1.0 - (avg_time / 10.0))
        return (success_rate * 0.7) + (time_score * 0.3)

    def _trim_to_token_budget(self, text: str, max_tokens: int) -> str:
        """Truncate text to estimated token budget."""
        if not text or max_tokens is None:
            return text
        est = estimate_tokens(text)
        if est <= max_tokens:
            return text
        # Binary search for longest prefix within budget
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi) // 2
            if estimate_tokens(text[:mid]) <= max_tokens:
                lo = mid + 1
            else:
                hi = mid
        return text[: max(0, lo - 1)].rstrip()

    def _apply_output_budget(self, role: str, payload: Any) -> Any:
        """Enforce role-specific token-based output limits to keep swarm responses compact."""
        if not isinstance(payload, dict):
            return payload

        result = dict(payload)
        # Token budget limits per role
        role_budgets = {
            "security": {"summary": 50, "decision": 30, "action": 20, "max_actions": 3},
            "defense": {"summary": 50, "decision": 30, "action": 20, "max_actions": 3},
            "review": {"summary": 50, "decision": 30, "action": 20, "max_actions": 3},
            "reduction": None,  # unlimited
            "sage": None,      # unlimited
        }
        if role in {"reduction", "sage"}:
            limits = None
        elif role in {"security", "defense", "review"}:
            limits = role_budgets[role]
        else:
            limits = {"summary": 100, "decision": 60, "action": 30, "max_actions": 5}

        if limits is None:
            return result

        # Trim summary
        if "summary" in result and isinstance(result["summary"], str):
            result["summary"] = self._trim_to_token_budget(result["summary"], limits["summary"])

        # Trim decision
        if "decision" in result and isinstance(result["decision"], str):
            result["decision"] = self._trim_to_token_budget(result["decision"], limits["decision"])

        # Trim actions
        if "recommended_next_actions" in result and isinstance(result["recommended_next_actions"], list):
            actions = result["recommended_next_actions"]
            max_actions = limits["max_actions"]
            action_budget = limits["action"]
            # Apply length limit first
            if max_actions is not None and len(actions) > max_actions:
                actions = actions[:max_actions]
            if action_budget is not None:
                actions = [self._trim_to_token_budget(a, action_budget) if isinstance(a, str) else a for a in actions]
            result["recommended_next_actions"] = actions

        return result

        # Helper: trim string to token budget
        def trim_to_budget(text: str, max_tokens: int) -> str:
            if not text or max_tokens is None:
                return text
            try:
                from jebat.llm.token_usage import estimate_tokens
            except ImportError:
                # Fallback: rough word-based estimate
                tokens_est = max(len(text) // 4, len(text.split()))
                return text if tokens_est <= max_tokens else text[: max_tokens * 4]
            est = estimate_tokens(text)
            if est <= max_tokens:
                return text
            # Binary search for longest prefix within budget
            lo, hi = 0, len(text)
            while lo < hi:
                mid = (lo + hi) // 2
                if estimate_tokens(text[:mid]) <= max_tokens:
                    lo = mid + 1
                else:
                    hi = mid
            return text[: max(0, lo - 1)].rstrip()

        # Apply summary and decision token trims
        if "summary" in result and isinstance(result["summary"], str):
            result["summary"] = trim_to_budget(result["summary"], limits["summary"])
        if "decision" in result and isinstance(result["decision"], str):
            result["decision"] = trim_to_budget(result["decision"], limits["decision"])

        # Limit and trim actions
        if "recommended_next_actions" in result and isinstance(result["recommended_next_actions"], list):
            actions = result["recommended_next_actions"]
            max_actions = limits["max_actions"]
            if max_actions is not None and len(actions) > max_actions:
                actions = actions[:max_actions]
            # Trim each action string to action token budget
            action_budget = limits.get("action")
            if action_budget is not None:
                trimmed_actions = []
                for act in actions:
                    if isinstance(act, str):
                        trimmed_actions.append(trim_to_budget(act, action_budget))
                    else:
                        trimmed_actions.append(act)
                actions = trimmed_actions
            result["recommended_next_actions"] = actions

        # For doctrine_checks (used by sage) and other list-of-strings fields that may be long
        if "doctrine_checks" in result and isinstance(result["doctrine_checks"], list):
            # No strict token limit but keep only first 2 for compact roles if needed
            # Since doctrine is only for sage (unlimited), no trim needed.
            pass

        return result

    def _scan_for_exposures(self, text: str) -> List[Dict[str, Any]]:
        """Scan text for credential/secret patterns. Returns list of exposure findings."""
        findings: List[Dict[str, Any]] = []
        if not isinstance(text, str):
            return findings

        for pattern in self.exposure_patterns:
            for match in pattern.finditer(text):
                # Redact the actual value in the original text
                findings.append({
                    "type": "credential_exposure",
                    "pattern": pattern.pattern[:80],
                    "context": text[max(0, match.start()-20):match.end()+20].replace("\n", " "),
                    "redacted": True,
                })
        return findings

    def _sanitize_payload(self, payload: Any) -> tuple[Any, List[Dict[str, Any]]]:
        """Recursively scan payload for exposures and redact them. Returns (sanitized, findings)."""
        all_findings: List[Dict[str, Any]] = []

        def scan_and_redact(obj: Any) -> Any:
            nonlocal all_findings
            if isinstance(obj, str):
                findings = self._scan_for_exposures(obj)
                if findings:
                    all_findings.extend(findings)
                    # Redact: replace any matched value with ***
                    redacted = obj
                    for finding in findings:
                        # Re-extract to get exact span (approximate via pattern)
                        pass
                    # Simple redaction: replace any alphanumeric token-like strings matching patterns
                    for pattern in self.exposure_patterns:
                        redacted = pattern.sub("[REDACTED]", redacted)
                    return redacted
                return obj
            elif isinstance(obj, dict):
                return {k: scan_and_redact(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [scan_and_redact(item) for item in obj]
            else:
                return obj

        sanitized = scan_and_redact(payload)
        return sanitized, all_findings

    def _flag_unsafe_output_paths(self, payload: Any) -> List[str]:
        """Detect agent outputs that suggest unsafe public exposure (e.g., 'publish to npm', 'deploy to public')."""
        warnings: List[str] = []
        if not isinstance(payload, dict):
            return warnings

        text_parts = []
        for value in payload.values():
            if isinstance(value, str):
                text_parts.append(value.lower())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item.lower())

        combined = " ".join(text_parts)
        unsafe_indicators = [
            ("public npm", "public npm registry exposure"),
            ("publish to npm", "npm registry exposure"),
            ("deploy to public", "public deployment without access control"),
            ("push to production", "direct production push without gate"),
            ("make it public", "public resource exposure"),
            ("open to internet", "unrestricted internet access"),
            ("no auth required", "missing authentication"),
            ("without auth", "missing authentication"),
            ("no authentication", "missing authentication"),
            ("expose to internet", "unrestricted internet exposure"),
        ]
        for indicator, reason in unsafe_indicators:
            if indicator in combined:
                warnings.append(f"Unsafe output suggestion: {reason} ('{indicator}')")
        return warnings

    async def _run_task(self, agent_id: Optional[str], task: AgentTask, score: float) -> AgentExecution:
        """Run task with an agent handler, agent object, or deterministic fallback."""
        agent_info = self.agents.get(agent_id or "", {})
        agent_name = agent_info.get("name", agent_id or "default")
        agent_role = agent_info.get("role", "general")
        agent_scope = self._build_agent_scope(task, agent_info)
        scoped_task = self._build_scoped_task(task, agent_scope)
        search_queries: List[str] = []
        search_results: Any = None
        start = asyncio.get_running_loop().time()

        try:
            if task.enable_search and self.search_handler and agent_info.get("search_enabled", False):
                search_queries = self._build_search_queries(scoped_task, agent_info, agent_scope)
                search_results = await self._invoke_callable(
                    self.search_handler,
                    scoped_task,
                    agent_info,
                    search_queries,
                )

            handler = (
                agent_info.get("handler")
                or self.handlers.get(agent_id or "")
                or self.handlers.get(agent_role)
                or self.handlers.get("default")
            )

            if handler is not None:
                payload = await self._invoke_callable(
                    handler,
                    scoped_task,
                    agent_info,
                    {
                        "search_queries": search_queries,
                        "search_results": search_results,
                        "agent_scope": agent_scope,
                    },
                )
            else:
                payload = self._default_agent_response(scoped_task, agent_info, search_queries, search_results)

            # Apply secret/data exposure controls: scan and redact sensitive values
            payload, exposure_findings = self._sanitize_payload(payload)
            # Flag unsafe output path suggestions
            unsafe_warnings = self._flag_unsafe_output_paths(payload)

            # Store exposure metadata for security layer
            payload["_exposure_findings"] = exposure_findings
            payload["_unsafe_warnings"] = unsafe_warnings

            # Apply role-specific output budget after sanitization
            payload = self._apply_output_budget(agent_role, payload)

            normalized = self._normalize_result_payload(task.task_id, agent_id, payload)
            execution_time = asyncio.get_running_loop().time() - start
            return AgentExecution(
                agent_id=agent_id or "default",
                agent_name=agent_name,
                role=agent_role,
                score=score,
                success=normalized.success,
                execution_time=execution_time,
                result=normalized.result,
                error=normalized.error,
                search_queries=search_queries,
                search_results=search_results,
            )
        except Exception as exc:
            return AgentExecution(
                agent_id=agent_id or "default",
                agent_name=agent_name,
                role=agent_role,
                score=score,
                success=False,
                execution_time=asyncio.get_running_loop().time() - start,
                error=str(exc),
                search_queries=search_queries,
                search_results=search_results,
            )

    async def _invoke_callable(self, func: Callable[..., Any], *args: Any) -> Any:
        """Invoke a handler while tolerating shorter signatures."""
        signature = inspect.signature(func)
        accepts_varargs = any(
            parameter.kind == inspect.Parameter.VAR_POSITIONAL
            for parameter in signature.parameters.values()
        )

        if accepts_varargs:
            result = func(*args)
        else:
            positional = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            result = func(*args[: len(positional)])

        if inspect.isawaitable(result):
            return await result
        return result

    def _build_search_queries(
        self,
        task: AgentTask,
        agent_info: Dict[str, Any],
        agent_scope: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build search queries for the given task and agent."""
        if task.search_queries:
            base_queries = list(task.search_queries)
        else:
            base_queries = [task.description.strip()]

        required_capabilities = sorted(self._extract_task_capabilities(task))
        if required_capabilities:
            base_queries.append(f"{task.description.strip()} {' '.join(required_capabilities[:2])}".strip())

        role = agent_info.get("role")
        if role:
            base_queries.append(f"{role} perspective {task.description.strip()}")
        focus = str((agent_scope or {}).get("focus", "")).strip()
        if focus:
            base_queries.append(f"{focus} {task.description.strip()}".strip())

        deduped: List[str] = []
        seen = set()
        for query in base_queries:
            normalized = query.strip()
            if not normalized or normalized in seen:
                continue
            deduped.append(normalized)
            seen.add(normalized)
            if len(deduped) >= 3:
                break
        return deduped

    def _normalize_result_payload(
        self,
        task_id: str,
        agent_id: Optional[str],
        payload: Any,
    ) -> TaskResult:
        """Normalize handler output into a TaskResult."""
        if isinstance(payload, TaskResult):
            return payload

        if isinstance(payload, dict) and "success" in payload and ("result" in payload or "error" in payload):
            return TaskResult(
                task_id=task_id,
                success=bool(payload.get("success")),
                result=payload.get("result"),
                error=payload.get("error"),
                agent_id=agent_id,
                metadata=dict(payload.get("metadata", {})),
            )

        return TaskResult(
            task_id=task_id,
            success=True,
            result=payload,
            agent_id=agent_id,
        )

    def _default_agent_response(
        self,
        task: AgentTask,
        agent_info: Dict[str, Any],
        search_queries: List[str],
        search_results: Any,
    ) -> Dict[str, Any]:
        """Deterministic fallback when no real handler is registered."""
        capabilities = sorted(self._extract_task_capabilities(task))
        role = agent_info.get("role", "general")
        name = agent_info.get("name", role)
        scope = task.parameters.get("agent_scope", {}) if isinstance(task.parameters, dict) else {}
        shared_decision = self._build_shared_decision(task, capabilities)

        recommended_action = (
            shared_decision
            or f"{role}: {scope.get('focus', 'review and execute the next step')} for '{task.description}'"
        )
        next_actions = [
            f"{name} focus on {scope.get('focus', 'the assigned task slice')}",
            f"{name} prepare a bounded implementation plan",
        ]
        if capabilities:
            next_actions.append(f"Focus on {', '.join(capabilities[:2])}")
        if search_queries:
            next_actions.append("Validate findings against search results")

        return {
            "decision": recommended_action,
            "summary": f"{name} assessed the task and produced an automated next-step recommendation.",
            "recommended_next_actions": next_actions,
            "capabilities_used": capabilities,
            "scope": scope,
            "search_queries": search_queries,
            "search_results": search_results,
        }

    async def _builtin_role_handler(
        self,
        task: AgentTask,
        agent_info: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Structured automated judgment for built-in specialist roles."""
        role = agent_info.get("role", "general")
        name = agent_info.get("name", role)
        capabilities = sorted(self._extract_task_capabilities(task))
        scope = context.get("agent_scope", {})
        local_results = self._pluck_search_items(context.get("search_results"), "local_results")
        remote_results = self._pluck_search_items(context.get("search_results"), "remote_results")
        evidence = local_results[:2] + remote_results[:2]
        adapter_output = await self.execution_adapters.run(role, task, agent_info)

        decision_templates = {
            "orchestration": f"Dispatch the task through a {self._recommended_delivery_mode(task)} path and converge on a single execution plan.",
            "development": "Implement the smallest change that satisfies the task and verify the affected behavior.",
            "frontend": "Adjust the user-facing flow with responsive, low-noise UI changes and verify layout integrity.",
            "research": "Collect the strongest current evidence, reduce ambiguity, and summarize the best-supported next step.",
            "security": "Assess risk first, identify exposure, and prioritize a mitigation or hardening step before rollout.",
            "operations": "Sequence the rollout, observability, and rollback path before applying operational changes.",
            "database": "Inspect schema and query impact, then stage a dry-run or benchmark before applying changes.",
            "review": "Check for regressions, missing validation, and weak assumptions before approving execution.",
            "design": "Refine the interaction and information hierarchy so the path is clearer and easier to operate.",
            "application": "Coordinate cross-layer changes so backend, frontend, and data changes remain aligned.",
            "strategy": "Set the governing direction, weigh tradeoffs, and choose the strongest execution path.",
            "reconnaissance": "Map the terrain first, discover the strongest signals, and expose hidden constraints early.",
            "defense": "Strengthen guardrails, reduce exposure, and keep the system resilient under change.",
            "stability": "Protect reliability, release confidence, and operational continuity before approving movement.",
            "intelligence": "Classify intent, route the task to the right specialists, and surface the most actionable signals.",
            "reduction": "Reduce the swarm output into one coherent decision, resolve conflicts, and state confidence clearly.",
            "sage": "Provide doctrine, long-memory framing, and governing guidance before the final decision is accepted.",
        }

        next_actions_map = {
            "orchestration": [
                "Rank the specialist agents by fit",
                "Run the best parallel workset",
                "Resolve conflicts into one execution plan",
            ],
            "development": [
                "Locate the governing implementation",
                "Patch the minimal surface area",
                "Run targeted verification",
            ],
            "frontend": [
                "Inspect the active view/component path",
                "Patch the interaction or layout issue",
                "Verify mobile and desktop fit",
            ],
            "research": [
                "Expand the strongest query",
                "Compare the top signals",
                "Summarize the decision with evidence",
            ],
            "security": [
                "Identify attack surface",
                "Check for an exploit or mitigation path",
                "Propose the safest hardening step",
            ],
            "operations": [
                "Confirm deployment prerequisites",
                "Define monitoring and rollback",
                "Apply changes in controlled order",
            ],
            "database": [
                "Inspect schema or migration scope",
                "Run a dry-run or explain plan",
                "Validate rollback safety",
            ],
            "review": [
                "Check the strongest claim in the proposed change",
                "Validate testing coverage",
                "Call out residual risk explicitly",
            ],
            "design": [
                "Inspect hierarchy and density",
                "Tighten copy and controls",
                "Verify usability across viewports",
            ],
            "application": [
                "Map affected layers",
                "Sequence cross-layer edits",
                "Verify the end-to-end path",
            ],
            "strategy": [
                "Frame the decision and its constraints",
                "Compare the strongest candidate paths",
                "Choose the governing execution plan",
            ],
            "reconnaissance": [
                "Locate the highest-signal files and docs",
                "Map open questions and unknowns",
                "Feed discovery back into the swarm",
            ],
            "defense": [
                "Check existing guardrails",
                "Identify reliability or security exposure",
                "Recommend the safest protection step",
            ],
            "stability": [
                "Inspect tests and verification surfaces",
                "Check release and rollback readiness",
                "Preserve confidence before rollout",
            ],
            "intelligence": [
                "Classify the task precisely",
                "Route work to the best specialist mix",
                "Summarize the strongest next action",
            ],
            "reduction": [
                "Compare the strongest specialist conclusions",
                "Resolve conflicts into one final path",
                "State confidence and residual disagreement",
            ],
            "sage": [
                "Recall the durable doctrine and constraints",
                "Check the plan against long-memory context",
                "Advise the governing direction before final merge",
            ],
        }
        shared_decision = self._build_shared_decision(task, capabilities)

        evidence_summary = []
        for item in evidence:
            path = item.get("path") or item.get("url") or item.get("title", "")
            snippet = item.get("snippet", "")
            evidence_summary.append({"source": path, "snippet": snippet[:220]})

        return {
            "decision": (
                shared_decision
                or decision_templates.get(role, f"{name} recommends a structured next step for '{task.description}'.")
            ),
            "summary": f"{name} reviewed the task from the {role} perspective.",
            "recommended_next_actions": next_actions_map.get(role, ["Inspect the task", "Choose the next bounded action"]),
            "capabilities_used": capabilities,
            "scope": scope,
            "search_queries": context.get("search_queries", []),
            "evidence": evidence_summary,
            "search_backend": (context.get("search_results") or {}).get("backend"),
            "actions_executed": adapter_output.get("actions_executed", []),
            "execution_adapter": adapter_output.get("adapter"),
            "tool_findings": {
                key: value
                for key, value in adapter_output.items()
                if key not in {"adapter", "actions_executed"}
            },
            "role": role,
        }

    def _build_shared_decision(self, task: AgentTask, capabilities: List[str]) -> str:
        """Normalize built-in specialist decisions around the governing task archetype."""
        text = task.description.lower()
        capability_set = {str(item).lower() for item in capabilities}

        if (
            {"database", "research", "review"} & capability_set
            and any(keyword in text for keyword in ("migration", "schema", "database", "rollout", "release"))
        ):
            return "run migration dry-run before apply"

        if (
            {"strategy", "defense", "stability", "intelligence"} & capability_set
            and any(keyword in text for keyword in ("protect", "protected", "guardrail", "safest", "resilience", "hardening"))
        ):
            return "Use a protected staged rollout with explicit guardrails and rollback checks."

        if any(keyword in text for keyword in ("compare", "evaluate", "tradeoff", "best option", "decide", "judge")):
            return "Collect evidence, compare the options, and choose one bounded path."

        if any(keyword in text for keyword in ("implement", "fix", "patch", "refactor", "authentication")):
            return "Implement the smallest safe change and verify the affected behavior."

        if {"design", "frontend"} & capability_set or any(keyword in text for keyword in ("ui", "ux", "design", "layout")):
            return "Refine the highest-impact user flow before expanding scope."

        return ""

    def _recommended_delivery_mode(self, task: AgentTask) -> str:
        """Summarize how Panglima should route the task."""
        required_capabilities = sorted(self._extract_task_capabilities(task))
        if task.require_consensus or len(required_capabilities) > 1:
            return "multi-agent consensus"
        if task.enable_search:
            return "search-backed swarm"
        return "single-agent execution"

    def _pluck_search_items(self, search_results: Any, key: str) -> List[Dict[str, Any]]:
        """Safely extract normalized search items."""
        if not isinstance(search_results, dict):
            return []
        items = search_results.get(key, [])
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def _judge_swarm_results(
        self,
        task: AgentTask,
        executions: List[AgentExecution],
        mode: ExecutionMode,
    ) -> Dict[str, Any]:
        """Synthesize a final judgment across multiple agent executions."""
        successful = [execution for execution in executions if execution.success]
        reducer = next((execution for execution in successful if execution.role == "reduction"), None)
        sage = next((execution for execution in successful if execution.role == "sage"), None)
        judged_executions = [
            execution for execution in successful if execution.role not in {"reduction", "sage"}
        ] or successful
        votes = Counter()
        next_actions: List[str] = []

        for execution in judged_executions:
            decision = self._extract_decision(execution.result)
            if decision:
                votes[decision] += 1
            next_actions.extend(self._extract_next_actions(execution.result))

        consensus_decision = ""
        agreement = 0.0
        if votes and judged_executions:
            consensus_decision, vote_count = votes.most_common(1)[0]
            agreement = vote_count / len(judged_executions)
        elif judged_executions:
            consensus_decision = f"Swarm completed '{task.description}' without a structured decision field."
            agreement = 1.0 / len(judged_executions)
        else:
            consensus_decision = f"Swarm failed to execute '{task.description}'."

        unique_actions: List[str] = []
        seen_actions = set()
        for action in next_actions:
            normalized = action.strip()
            if not normalized or normalized in seen_actions:
                continue
            unique_actions.append(normalized)
            seen_actions.add(normalized)

        reducer_payload = (
            self._build_reducer_payload(
                reducer,
                judged_executions,
                consensus_decision,
                agreement,
                dict(votes),
                unique_actions[:8],
            )
            if reducer
            else None
        )
        doctrine_payload = (
            self._build_doctrine_payload(sage, task, consensus_decision)
            if sage
            else None
        )
        security_layer = self._build_security_summary(task, successful, unique_actions[:8])

        return {
            "task_id": task.task_id,
            "execution_mode": mode.value,
            "summary": consensus_decision,
            "consensus": {
                "decision": consensus_decision,
                "agreement": round(agreement, 4),
                "votes": dict(votes),
            },
            "reducer": reducer_payload,
            "doctrine": doctrine_payload,
            "security_layer": security_layer,
            "agent_results": [execution.to_dict() for execution in executions],
            "recommended_next_actions": unique_actions[:8],
            "search_enabled": task.enable_search,
        }

    def _extract_decision(self, payload: Any) -> str:
        """Extract a decision string from a handler payload."""
        if isinstance(payload, str):
            return payload.strip()

        if isinstance(payload, dict):
            for key in ("decision", "recommended_action", "next_action", "next_step", "summary"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return ""

    def _extract_next_actions(self, payload: Any) -> List[str]:
        """Extract follow-up actions from a payload."""
        if not isinstance(payload, dict):
            return []

        for key in ("recommended_next_actions", "next_actions", "actions"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(item) for item in value]
        return []

    def _build_reducer_payload(
        self,
        reducer: AgentExecution,
        judged_executions: List[AgentExecution],
        consensus_decision: str,
        agreement: float,
        votes: Dict[str, int],
        next_actions: List[str],
    ) -> Dict[str, Any]:
        """Build a second-stage reducer summary from specialist outputs."""
        payload = reducer.to_dict()
        conflicts = [
            {"decision": decision, "votes": count}
            for decision, count in votes.items()
            if decision and decision != consensus_decision
        ]
        payload["result"] = {
            "decision": consensus_decision,
            "summary": "Taming Sari merged the swarm outputs into one bounded judgment.",
            "confidence": round(agreement, 4),
            "supporting_roles": [execution.role for execution in judged_executions],
            "votes": votes,
            "conflicts": conflicts,
            "recommended_next_actions": next_actions,
            "synthesized_decision": consensus_decision,
        }
        return payload

    def _build_doctrine_payload(
        self,
        sage: AgentExecution,
        task: AgentTask,
        consensus_decision: str,
    ) -> Dict[str, Any]:
        """Build a doctrine framing payload for the sage role."""
        payload = sage.to_dict()
        payload["result"] = {
            "decision": consensus_decision,
            "summary": "Tok Guru Adi Putera framed the decision against durable doctrine and guardrails.",
            "doctrine_checks": list(self.durable_doctrine),
            "task": task.description,
        }
        return payload

    def _build_security_summary(
        self,
        task: AgentTask,
        executions: List[AgentExecution],
        next_actions: List[str],
    ) -> Dict[str, Any]:
        """Build the runtime security overlay for planning and execution surfaces."""
        security_layer = dict(self._build_security_layer(task))
        active_roles: List[str] = []
        for execution in executions:
            role = str(execution.role or "").strip().lower()
            if role and role not in active_roles:
                active_roles.append(role)

        required_roles = list(security_layer.get("required_roles", []))
        required_roles_present = [role for role in required_roles if role in active_roles]
        security_actions: List[str] = []
        exposure_findings: List[Dict[str, Any]] = []
        unsafe_warnings: List[str] = []

        for execution in executions:
            # Collect security actions only from security-titled roles
            if execution.role in {"security", "defense", "review", "stability", "operations"}:
                for action in self._extract_next_actions(execution.result):
                    normalized = str(action).strip()
                    if normalized and normalized not in security_actions:
                        security_actions.append(normalized)

            # Collect exposure findings from all agents
            result_dict = execution.result if isinstance(execution.result, dict) else {}
            exposure = result_dict.get("_exposure_findings", [])
            if isinstance(exposure, list):
                for finding in exposure:
                    if finding not in exposure_findings:
                        exposure_findings.append(finding)
            warnings = result_dict.get("_unsafe_warnings", [])
            if isinstance(warnings, list):
                for w in warnings:
                    if w not in unsafe_warnings:
                        unsafe_warnings.append(w)

        # Redact policy_rules themselves are not secret; but note any exposure controls active
        exposure_controls = ["credential_redaction_enabled", "unsafe_output_blocking"]
        if exposure_findings:
            exposure_controls.append(f"{len(exposure_findings)} exposure(s) detected and redacted")

        security_layer.update(
            {
                "active_roles": active_roles,
                "required_roles_present": required_roles_present,
                "coverage_ok": all(role in active_roles for role in required_roles),
                "recommended_controls": security_actions[:6] or next_actions[:4],
                "summary": (
                    "Security overlay enforced for elevated-risk execution."
                    if security_layer.get("enforced")
                    else "No elevated security overlay required."
                ),
                "policy_rules": list(self.security_policy_rules),
                "exposure_controls": exposure_controls,
                "exposure_findings": exposure_findings[:10],
                "unsafe_warnings": unsafe_warnings[:5],
            }
        )
        return security_layer

    def _record_task_history(self, task_id: str, agent_id: str, execution_time: float, success: bool):
        """Record bounded task history for reporting."""
        self.task_history.append((task_id, agent_id, execution_time, success))
        history_limit = int(self.config.get("history_limit", 1000))
        if len(self.task_history) > history_limit:
            self.task_history = self.task_history[-history_limit:]

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

    def get_agent_registry(self) -> Dict[str, Any]:
        """Get agent registry snapshot for external decision systems."""
        return {
            agent_id: {
                "name": agent.get("name", agent_id),
                "role": agent.get("role", "general"),
                "capabilities": list(agent.get("capabilities", [])),
                "status": agent.get("status", "idle"),
                "automation_enabled": bool(agent.get("automation_enabled", False)),
                "search_enabled": bool(agent.get("search_enabled", False)),
            }
            for agent_id, agent in self.agents.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        base_stats = {
            "agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "completed_tasks": len(self.completed_tasks),
            "is_running": self._is_running,
            "swarm_executions": len(self.swarm_history),
            "agent_performance": {
                agent_id: {
                    "total_tasks": perf["total_tasks"],
                    "success_rate": (
                        perf["successful_tasks"] / perf["total_tasks"]
                        if perf["total_tasks"] > 0
                        else 0.0
                    ),
                    "total_execution_time": perf["total_execution_time"],
                    "avg_execution_time": perf["avg_execution_time"],
                }
                for agent_id, perf in self.agent_performance.items()
            },
            "task_history_size": len(self.task_history),
        }
        
        # Add monitoring-specific metrics
        monitoring_stats = {
            "monitoring": {
                "total_swarm_executions": len(self.swarm_history),
                "successful_swarm_executions": len([
                    h for h in self.swarm_history 
                    if h.get("success", False)
                ]),
                "failed_swarm_executions": len([
                    h for h in self.swarm_history 
                    if not h.get("success", True)
                ]),
                "avg_swarm_execution_time": (
                    sum(h.get("execution_time", 0) for h in self.swarm_history) /
                    max(len(self.swarm_history), 1)
                ),
                "total_agent_executions": sum(
                    perf["total_tasks"] for perf in self.agent_performance.values()
                ),
                "total_successful_agent_executions": sum(
                    perf["successful_tasks"] for perf in self.agent_performance.values()
                ),
                "overall_agent_success_rate": (
                    sum(perf["successful_tasks"] for perf in self.agent_performance.values()) /
                    max(sum(perf["total_tasks"] for perf in self.agent_performance.values()), 1)
                ),
                "active_agents_count": len([
                    agent_id for agent_id, perf in self.agent_performance.items()
                    if perf["total_tasks"] > 0
                ]),
                "total_agents_ever_used": len(self.agent_performance),
            }
        }
        
        # Merge base stats with monitoring stats
        base_stats.update(monitoring_stats)
        return base_stats
