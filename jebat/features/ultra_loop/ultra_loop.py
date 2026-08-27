"""
JEBAT Ultra-Loop - Continuous Processing and Learning System

The Ultra-Loop is the heartbeat of JEBAT, running continuous cycles of:
1. Perception - Gather inputs from all channels and sessions
2. Cognition - Process and reason about inputs via decision engine
3. Memory - Store and consolidate experiences via enhanced memory
4. Action - Execute responses and tasks via agent orchestrator
5. Learning - Update models and improve performance via self-learning

This creates a perpetual learning loop that makes JEBAT smarter over time.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .database_repository import UltraLoopRepository

logger = logging.getLogger(__name__)


class LoopPhase(Enum):
    """Phases of the ultra-loop cycle"""

    PERCEPTION = "perception"
    COGNITION = "cognition"
    MEMORY = "memory"
    ACTION = "action"
    LEARNING = "learning"


@dataclass
class LoopMetrics:
    """Metrics for ultra-loop performance"""

    cycle_count: int = 0
    total_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    avg_cycle_time: float = 0.0
    last_cycle_time: float = 0.0
    total_execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    last_error: Optional[str] = None
    last_cycle_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_cycle_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cycle_count": self.cycle_count,
            "total_cycles": self.total_cycles,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "avg_cycle_time": self.avg_cycle_time,
            "last_cycle_time": self.last_cycle_time,
            "total_execution_time": self.total_execution_time,
            "errors_count": len(self.errors),
            "last_error": self.last_error,
            "uptime_seconds": (
                datetime.now(timezone.utc) - self.last_cycle_start
            ).total_seconds(),
        }


@dataclass
class LoopContext:
    """Context for a single loop cycle"""

    cycle_id: str
    phase: LoopPhase
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "state": self.state,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
        }


class UltraLoop:
    """
    JEBAT Ultra-Loop - Continuous Processing and Learning System

    Runs perpetual cycles of perception, cognition, memory, action, and learning
    to create a self-improving AI assistant.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_manager=None,
        decision_engine=None,
        agent_orchestrator=None,
        cache_manager=None,
        enable_db_persistence: bool = True,
    ):
        """
        Initialize the Ultra-Loop system

        Args:
            config: Loop configuration
            memory_manager: Memory system integration
            decision_engine: Decision engine integration
            agent_orchestrator: Agent orchestration integration
            cache_manager: Cache management integration
            enable_db_persistence: Enable database persistence for cycles
        """
        self.config = config or {}
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.agent_orchestrator = agent_orchestrator
        self.cache_manager = cache_manager
        self.enable_db_persistence = enable_db_persistence

        # Database repository
        self.db_repo = UltraLoopRepository() if enable_db_persistence else None

        # Loop control
        self._is_running = False
        self._current_cycle = 0
        self._loop_task: Optional[asyncio.Task] = None
        self._current_db_cycle = None

        # Timing
        self.cycle_interval = self.config.get("cycle_interval", 1.0)
        self.max_cycles = self.config.get("max_cycles", 0)

        # Metrics
        self.metrics = LoopMetrics()

        # Phase handlers
        self.phase_handlers: Dict[LoopPhase, List[Callable]] = {
            phase: [] for phase in LoopPhase
        }

        # Event handlers
        self.cycle_start_handlers: List[Callable] = []
        self.cycle_end_handlers: List[Callable] = []
        self.error_handlers: List[Callable] = []

        # Lazy-initialized subsystems
        self._enhanced_memory = None
        self._meta_learner = None
        self._session_manager = None

        # Cycle performance tracking
        self._cycle_history: List[Dict[str, Any]] = []

        logger.info(
            "Ultra-Loop initialized with database persistence: %s",
            enable_db_persistence,
        )

    # ── Lazy Subsystem Init ────────────────────────────────────────────

    def _get_enhanced_memory(self):
        """Lazily initialize EnhancedMemorySystem."""
        if self._enhanced_memory is None:
            try:
                from jebat.features.memory import EnhancedMemorySystem
                self._enhanced_memory = EnhancedMemorySystem()
            except Exception:
                pass
        return self._enhanced_memory

    def _get_meta_learner(self):
        """Lazily initialize MetaLearner for learning phase."""
        if self._meta_learner is None:
            try:
                from jebat.features.self_learning import MetaLearner
                self._meta_learner = MetaLearner()
            except Exception:
                pass
        return self._meta_learner

    def _get_session_manager(self):
        """Lazily initialize SessionManager for perception phase."""
        if self._session_manager is None:
            try:
                from jebat.features.session import SessionManager
                self._session_manager = SessionManager()
            except Exception:
                pass
        return self._session_manager

    # ── Handler Registration ────────────────────────────────────────────

    def on_phase(self, phase: LoopPhase, handler: Callable):
        """Register handler for a specific phase"""
        self.phase_handlers[phase].append(handler)

    def on_cycle_start(self, handler: Callable):
        """Register handler for cycle start"""
        self.cycle_start_handlers.append(handler)

    def on_cycle_end(self, handler: Callable):
        """Register handler for cycle end"""
        self.cycle_end_handlers.append(handler)

    def on_error(self, handler: Callable):
        """Register handler for errors"""
        self.error_handlers.append(handler)

    async def _trigger_phase_handlers(self, phase: LoopPhase, context: LoopContext):
        """Trigger all handlers for a phase"""
        for handler in self.phase_handlers[phase]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
            except Exception as e:
                logger.error(f"Phase handler error ({phase.value}): {e}")

    async def _trigger_cycle_start_handlers(self, context: LoopContext):
        """Trigger cycle start handlers"""
        for handler in self.cycle_start_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
            except Exception as e:
                logger.error(f"Cycle start handler error: {e}")

    async def _trigger_cycle_end_handlers(self, context: LoopContext):
        """Trigger cycle end handlers"""
        for handler in self.cycle_end_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
            except Exception as e:
                logger.error(f"Cycle end handler error: {e}")

    async def _trigger_error_handlers(self, error: Exception, context: LoopContext):
        """Trigger error handlers"""
        for handler in self.error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error, context)
                else:
                    handler(error, context)
            except Exception as e:
                logger.error(f"Error handler error: {e}")

    # ══════════════════════════════════════════════════════════════════
    # PHASE 1 — PERCEPTION
    # ══════════════════════════════════════════════════════════════════

    async def perception_phase(self, context: LoopContext):
        """
        Perception Phase - Gather inputs from all sources

        - Read recent session messages
        - Check for pending events
        - Gather environmental context
        - Update sensory buffer (M0)
        """
        logger.debug(f"Cycle {context.cycle_id}: Perception phase")
        await self._trigger_phase_handlers(LoopPhase.PERCEPTION, context)

        inputs = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sessions_checked": 0,
            "messages_gathered": 0,
            "events": [],
            "pending_tasks": [],
        }

        # Gather from session manager
        sm = self._get_session_manager()
        if sm:
            try:
                recent_sessions = sm.list_sessions(limit=5)
                inputs["sessions_checked"] = len(recent_sessions)

                # Gather recent messages from active sessions
                for session in recent_sessions:
                    messages = sm.load_history(session.id, limit=3)
                    for msg in messages:
                        if msg.role == "user":
                            inputs["messages_gathered"] += 1
                            inputs["events"].append({
                                "type": "user_message",
                                "session_id": session.id,
                                "content": msg.content[:500],
                                "timestamp": msg.created_at,
                            })
            except Exception as e:
                logger.warning(f"Perception session gather failed: {e}")

        # Check for pending delegate tasks
        try:
            from jebat.tools import TOOL_REGISTRY
            if "delegate_task" in TOOL_REGISTRY:
                inputs["pending_tasks"].append({
                    "type": "capability_available",
                    "tool": "delegate_task",
                })
        except Exception:
            pass

        context.outputs["perception"] = inputs
        context.state["inputs_available"] = bool(inputs["events"])

    # ══════════════════════════════════════════════════════════════════
    # PHASE 2 — COGNITION
    # ══════════════════════════════════════════════════════════════════

    async def cognition_phase(self, context: LoopContext):
        """
        Cognition Phase - Process and reason about inputs

        - Analyze incoming data via decision engine
        - Select appropriate agents
        - Plan responses
        - Classify task priority
        """
        logger.debug(f"Cycle {context.cycle_id}: Cognition phase")
        await self._trigger_phase_handlers(LoopPhase.COGNITION, context)

        perception = context.outputs.get("perception", {})
        events = perception.get("events", [])

        cognition_result = {
            "decisions_made": 0,
            "agents_selected": [],
            "plans_created": [],
            "event_classifications": [],
        }

        if not events:
            context.outputs["cognition"] = cognition_result
            return

        # Classify each event
        for event in events:
            classification = self._classify_event(event)
            cognition_result["event_classifications"].append(classification)

            # Route to decision engine if applicable
            if self.decision_engine and classification.get("needs_action"):
                try:
                    decision = await self.decision_engine.decide(
                        task={
                            "description": event.get("content", ""),
                            "type": classification.get("event_type", "unknown"),
                            "priority": classification.get("priority", "medium"),
                        },
                        context={"event": event},
                    )
                    cognition_result["decisions_made"] += 1
                    if decision.selected_option:
                        cognition_result["agents_selected"].append(
                            decision.selected_option
                        )
                    cognition_result["plans_created"].append({
                        "action": classification.get("suggested_action", "respond"),
                        "agent": decision.selected_option,
                        "priority": classification.get("priority", "medium"),
                        "event": event,
                    })
                except Exception as e:
                    logger.error(f"Cognition decision error: {e}")

        context.outputs["cognition"] = cognition_result

    def _classify_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Classify an event by type, priority, and suggested action."""
        content = event.get("content", "").lower()
        event_type = event.get("type", "unknown")

        # Priority classification
        priority = "low"
        needs_action = True
        suggested_action = "respond"

        # High-priority patterns
        urgent_keywords = ["urgent", "critical", "error", "failed", "broken", "help"]
        if any(kw in content for kw in urgent_keywords):
            priority = "high"
            suggested_action = "investigate"

        # Security-related
        security_keywords = ["scan", "vulnerability", "pentest", "security", "CVE"]
        if any(kw in content for kw in security_keywords):
            priority = "high"
            suggested_action = "delegate_to_sentinel"

        # Code-related
        code_keywords = ["code", "implement", "fix", "bug", "feature", "refactor"]
        if any(kw in content for kw in code_keywords):
            suggested_action = "delegate_to_dev"

        # Question patterns
        if "?" in content or content.startswith(("how", "what", "why", "when", "where")):
            suggested_action = "answer"

        return {
            "event_type": event_type,
            "priority": priority,
            "needs_action": needs_action,
            "suggested_action": suggested_action,
            "content_preview": content[:100],
        }

    # ══════════════════════════════════════════════════════════════════
    # PHASE 3 — MEMORY
    # ══════════════════════════════════════════════════════════════════

    async def memory_phase(self, context: LoopContext):
        """
        Memory Phase - Store and consolidate experiences

        - Store new memories from this cycle
        - Update heat scores
        - Trigger consolidation if needed
        - Extract patterns from accumulated data
        """
        logger.debug(f"Cycle {context.cycle_id}: Memory phase")
        await self._trigger_phase_handlers(LoopPhase.MEMORY, context)

        memory_result = {
            "memories_stored": 0,
            "memories_consolidated": 0,
            "patterns_extracted": 0,
        }

        # Store cycle summary as episodic memory
        enhanced = self._get_enhanced_memory()
        if enhanced:
            try:
                perception = context.outputs.get("perception", {})
                cognition = context.outputs.get("cognition", {})
                action = context.outputs.get("action", {})

                cycle_summary = (
                    f"Cycle {context.cycle_id}: "
                    f"Gathered {perception.get('messages_gathered', 0)} messages, "
                    f"Made {cognition.get('decisions_made', 0)} decisions, "
                    f"Executed {action.get('tasks_executed', 0)} tasks"
                )

                tags = {"ultra_loop", f"cycle:{context.cycle_id}"}
                # Add agent tags
                for agent in cognition.get("agents_selected", []):
                    if agent:
                        tags.add(f"agent:{agent}")

                await enhanced.encode(
                    content=cycle_summary,
                    memory_type=enhanced.MemoryType.EPISODIC
                    if hasattr(enhanced, "MemoryType")
                    else __import__("jebat.features.memory", fromlist=["MemoryType"]).MemoryType.EPISODIC,
                    tags=tags,
                    importance=0.4,
                    context={
                        "cycle_id": context.cycle_id,
                        "messages": perception.get("messages_gathered", 0),
                        "decisions": cognition.get("decisions_made", 0),
                        "tasks": action.get("tasks_executed", 0),
                    },
                )
                memory_result["memories_stored"] += 1
            except Exception as e:
                logger.warning(f"Memory encoding failed: {e}")

        # Store in legacy memory manager if available
        if self.memory_manager:
            try:
                cycle_data = json.dumps(context.outputs, default=str)[:2000]
                await self.memory_manager.store(
                    content=cycle_data,
                    user_id="ultra_loop",
                )
                memory_result["memories_stored"] += 1
            except Exception as e:
                logger.warning(f"Legacy memory store failed: {e}")

        # Run consolidation every 10 cycles
        if enhanced and self._current_cycle % 10 == 0 and self._current_cycle > 0:
            try:
                result = await enhanced.consolidate()
                memory_result["memories_consolidated"] = result.consolidated_count
                memory_result["patterns_extracted"] = result.patterns_extracted
            except Exception as e:
                logger.warning(f"Memory consolidation failed: {e}")

        context.outputs["memory"] = memory_result

    # ══════════════════════════════════════════════════════════════════
    # PHASE 4 — ACTION
    # ══════════════════════════════════════════════════════════════════

    async def action_phase(self, context: LoopContext):
        """
        Action Phase - Execute responses and tasks

        - Send responses to channels
        - Execute agent tasks
        - Update system state
        - Trigger external actions
        """
        logger.debug(f"Cycle {context.cycle_id}: Action phase")
        await self._trigger_phase_handlers(LoopPhase.ACTION, context)

        action_result = {
            "responses_sent": 0,
            "tasks_executed": 0,
            "actions_completed": [],
            "agent_results": [],
        }

        # Execute planned actions through agent orchestrator
        if self.agent_orchestrator:
            cognition = context.outputs.get("cognition", {})
            plans = cognition.get("plans_created", [])

            for plan in plans:
                try:
                    from jebat.core.agents.orchestrator import (
                        AgentTask,
                        TaskPriority,
                    )

                    priority_map = {
                        "high": TaskPriority.HIGH,
                        "medium": TaskPriority.MEDIUM,
                        "low": TaskPriority.LOW,
                    }

                    task = AgentTask(
                        description=plan.get("event", {}).get("content", "Execute action")[:500],
                        parameters=plan.get("event", {}),
                        priority=priority_map.get(plan.get("priority", "medium"), TaskPriority.MEDIUM),
                    )

                    if hasattr(self.agent_orchestrator, "execute_task"):
                        result = await self.agent_orchestrator.execute_task(task)
                        action_result["tasks_executed"] += 1
                        action_result["agent_results"].append({
                            "task_id": task.task_id,
                            "success": result.success if hasattr(result, "success") else True,
                            "result": result.result if hasattr(result, "result") else None,
                        })
                except Exception as e:
                    logger.error(f"Action execution error: {e}")
                    action_result["actions_completed"].append({
                        "action": plan.get("action", "unknown"),
                        "status": "failed",
                        "error": str(e),
                    })
        else:
            # No orchestrator — record that action was skipped
            action_result["actions_completed"].append({
                "action": "no_orchestrator",
                "status": "skipped",
            })

        context.outputs["action"] = action_result

    # ══════════════════════════════════════════════════════════════════
    # PHASE 5 — LEARNING
    # ══════════════════════════════════════════════════════════════════

    async def learning_phase(self, context: LoopContext):
        """
        Learning Phase - Update models and improve performance

        - Analyze cycle performance
        - Record outcomes for self-learning
        - Adjust strategy selection
        - Extract reusable patterns
        """
        logger.debug(f"Cycle {context.cycle_id}: Learning phase")
        await self._trigger_phase_handlers(LoopPhase.LEARNING, context)

        learning_result = {
            "outcomes_recorded": 0,
            "strategies_updated": 0,
            "insights_generated": [],
        }

        # Analyze cycle performance
        perception = context.outputs.get("perception", {})
        cognition = context.outputs.get("cognition", {})
        action = context.outputs.get("action", {})
        memory = context.outputs.get("memory", {})

        cycle_performance = {
            "cycle_id": context.cycle_id,
            "messages_processed": perception.get("messages_gathered", 0),
            "decisions_made": cognition.get("decisions_made", 0),
            "tasks_executed": action.get("tasks_executed", 0),
            "memories_stored": memory.get("memories_stored", 0),
            "success": context.error is None,
        }

        # Track in history
        self._cycle_history.append(cycle_performance)
        if len(self._cycle_history) > 100:
            self._cycle_history = self._cycle_history[-100:]

        # Feed to MetaLearner
        meta = self._get_meta_learner()
        if meta:
            try:
                # Determine which strategy was effective
                strategy_name = "default"
                if cognition.get("agents_selected"):
                    strategy_name = cognition["agents_selected"][0] or "default"

                # Record outcome
                success = (
                    action.get("tasks_executed", 0) > 0
                    and context.error is None
                )

                # Record outcome (reward: 1.0 for success, 0.0 for failure)
                reward = 1.0 if success else 0.0

                meta.record_outcome(
                    strategy_id=strategy_name,
                    reward=reward,
                    context={
                        "decisions": cognition.get("decisions_made", 0),
                        "tasks": action.get("tasks_executed", 0),
                        "memories": memory.get("memories_stored", 0),
                        "cycle_id": context.cycle_id,
                    },
                )
                learning_result["outcomes_recorded"] += 1
            except Exception as e:
                logger.warning(f"MetaLearner recording failed: {e}")

        # Extract insights from cycle patterns (every 5 cycles)
        if len(self._cycle_history) >= 5 and self._current_cycle % 5 == 0:
            recent = self._cycle_history[-5:]
            avg_tasks = sum(c.get("tasks_executed", 0) for c in recent) / len(recent)
            success_rate = sum(1 for c in recent if c.get("success")) / len(recent)

            if success_rate < 0.5:
                learning_result["insights_generated"].append(
                    f"Low success rate ({success_rate:.0%}) in last 5 cycles — consider strategy change"
                )
            if avg_tasks == 0:
                learning_result["insights_generated"].append(
                    "No tasks executed in last 5 cycles — check orchestrator connectivity"
                )

        context.outputs["learning"] = learning_result

    # ══════════════════════════════════════════════════════════════════
    # CYCLE RUNNER
    # ══════════════════════════════════════════════════════════════════

    async def _run_cycle(self):
        """Run a single complete ultra-loop cycle"""
        cycle_id = f"cycle_{self._current_cycle:06d}"
        context = LoopContext(cycle_id=cycle_id, phase=LoopPhase.PERCEPTION)

        cycle_start = time.time()
        self.metrics.last_cycle_start = datetime.now(timezone.utc)

        # Create database record if persistence is enabled
        if self.db_repo:
            try:
                self._current_db_cycle = await self.db_repo.create_cycle(
                    cycle_id=cycle_id,
                    metadata={"cycle_number": self._current_cycle},
                )
            except Exception as e:
                logger.warning(f"Failed to create DB cycle record: {e}")
                self._current_db_cycle = None

        try:
            await self._trigger_cycle_start_handlers(context)

            # Execute each phase in sequence
            phases = [
                (LoopPhase.PERCEPTION, self.perception_phase),
                (LoopPhase.COGNITION, self.cognition_phase),
                (LoopPhase.MEMORY, self.memory_phase),
                (LoopPhase.ACTION, self.action_phase),
                (LoopPhase.LEARNING, self.learning_phase),
            ]

            for idx, (phase, phase_method) in enumerate(phases):
                context.phase = phase
                phase_start = time.time()

                try:
                    await phase_method(context)

                    # Store phase record if persistence is enabled
                    if self.db_repo and self._current_db_cycle:
                        phase_outputs = context.outputs.get(phase.value, {})
                        await self.db_repo.create_phase(
                            cycle_id=cycle_id,
                            phase_name=phase.value,
                            phase_order=idx,
                            inputs=dict(context.inputs),
                            outputs=phase_outputs,
                        )
                except Exception as e:
                    logger.error(f"Phase {phase.value} failed: {e}")
                    if self.db_repo and self._current_db_cycle:
                        await self.db_repo.create_phase(
                            cycle_id=cycle_id,
                            phase_name=phase.value,
                            phase_order=idx,
                            inputs=dict(context.inputs),
                            outputs={"error": str(e)},
                        )
                    raise

            # Update metrics
            self.metrics.successful_cycles += 1
            context.end_time = datetime.now(timezone.utc)

            # Update database record
            if self.db_repo and self._current_db_cycle:
                await self.db_repo.update_cycle_status(
                    cycle_id=cycle_id,
                    status="completed",
                )

        except Exception as e:
            self.metrics.failed_cycles += 1
            self.metrics.last_error = str(e)
            context.error = str(e)
            logger.error(f"Cycle {cycle_id} failed: {e}")

            if self.db_repo and self._current_db_cycle:
                await self.db_repo.update_cycle_status(
                    cycle_id=cycle_id,
                    status="failed",
                    error_message=str(e),
                )

            await self._trigger_error_handlers(e, context)

        finally:
            cycle_time = time.time() - cycle_start
            self.metrics.last_cycle_time = cycle_time
            self.metrics.total_execution_time += cycle_time
            self.metrics.avg_cycle_time = (
                self.metrics.total_execution_time / self.metrics.total_cycles
                if self.metrics.total_cycles > 0
                else 0
            )

            await self._trigger_cycle_end_handlers(context)

            self._current_cycle += 1
            self.metrics.total_cycles = self._current_cycle
            self._current_db_cycle = None

    async def _loop_runner(self):
        """Background loop runner"""
        logger.info("Ultra-Loop started")

        while self._is_running:
            await self._run_cycle()

            if self.max_cycles > 0 and self._current_cycle >= self.max_cycles:
                logger.info(f"Reached max cycles ({self.max_cycles}), stopping")
                break

            await asyncio.sleep(self.cycle_interval)

        self._is_running = False
        logger.info("Ultra-Loop stopped")

    async def start(self):
        """Start the ultra-loop"""
        if self._is_running:
            logger.warning("Ultra-Loop already running")
            return

        self._is_running = True
        self._loop_task = asyncio.create_task(self._loop_runner())

    async def stop(self):
        """Stop the ultra-loop"""
        self._is_running = False

        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

        logger.info("Ultra-Loop shutdown complete")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current loop metrics"""
        return self.metrics.to_dict()

    def get_status(self) -> Dict[str, Any]:
        """Get loop status"""
        return {
            "is_running": self._is_running,
            "current_cycle": self._current_cycle,
            "cycle_interval": self.cycle_interval,
            "max_cycles": self.max_cycles,
            "metrics": self.get_metrics(),
        }

    async def get_cycle_history(
        self,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get cycle history from database."""
        if not self.db_repo:
            return self._cycle_history[-limit:]

        cycles = await self.db_repo.get_recent_cycles(limit=limit, status=status)
        return [
            cycle.to_dict()
            if hasattr(cycle, "to_dict")
            else {
                "cycle_id": cycle.cycle_id,
                "status": cycle.status,
                "started_at": cycle.started_at.isoformat(),
                "completed_at": cycle.completed_at.isoformat()
                if cycle.completed_at
                else None,
            }
            for cycle in cycles
        ]

    async def get_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get loop statistics from database."""
        if not self.db_repo:
            return self.get_metrics()

        db_stats = await self.db_repo.get_cycle_statistics(
            time_window_hours=time_window_hours
        )

        return {
            **self.get_metrics(),
            **db_stats,
        }


async def create_ultra_loop(
    config: Optional[Dict[str, Any]] = None,
    **components,
) -> UltraLoop:
    """Factory function to create and initialize Ultra-Loop"""
    loop = UltraLoop(config=config, **components)
    return loop
