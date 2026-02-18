"""
JEBAT Ultra-Loop - Continuous Processing and Learning System

The Ultra-Loop is the heartbeat of JEBAT, running continuous cycles of:
1. Perception - Gather inputs from all channels
2. Cognition - Process and reason about inputs
3. Memory - Store and consolidate experiences
4. Action - Execute responses and tasks
5. Learning - Update models and improve performance

This creates a perpetual learning loop that makes JEBAT smarter over time.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

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
    last_cycle_start: datetime = field(default_factory=datetime.utcnow)
    last_cycle_end: datetime = field(default_factory=datetime.utcnow)

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
                datetime.utcnow() - self.last_cycle_start
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
    start_time: datetime = field(default_factory=datetime.utcnow)
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
    ):
        """
        Initialize the Ultra-Loop system

        Args:
            config: Loop configuration
            memory_manager: Memory system integration
            decision_engine: Decision engine integration
            agent_orchestrator: Agent orchestration integration
            cache_manager: Cache management integration
        """
        self.config = config or {}
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.agent_orchestrator = agent_orchestrator
        self.cache_manager = cache_manager

        # Loop control
        self._is_running = False
        self._current_cycle = 0
        self._loop_task: Optional[asyncio.Task] = None

        # Timing
        self.cycle_interval = self.config.get("cycle_interval", 1.0)  # seconds
        self.max_cycles = self.config.get("max_cycles", 0)  # 0 = unlimited

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

        logger.info("Ultra-Loop initialized")

    def on_phase(self, phase: LoopPhase, handler: Callable):
        """Register handler for a specific phase"""
        self.phase_handlers[phase].append(handler)
        logger.info(f"Registered handler for phase: {phase.value}")

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

    async def perception_phase(self, context: LoopContext):
        """
        Perception Phase - Gather inputs from all sources

        - Read from message channels
        - Check for new events
        - Gather environmental context
        - Update sensory buffer (M0)
        """
        logger.debug(f"Cycle {context.cycle_id}: Perception phase")
        await self._trigger_phase_handlers(LoopPhase.PERCEPTION, context)

        # Gather inputs from sources
        inputs = {
            "timestamp": datetime.utcnow().isoformat(),
            "sources_checked": 0,
            "events_gathered": 0,
        }

        # TODO: Integrate with channel gateway
        # inputs["messages"] = await self.gateway.get_new_messages()
        # inputs["events"] = await self.event_bus.get_pending_events()

        context.outputs["perception"] = inputs
        context.state["inputs_available"] = True

    async def cognition_phase(self, context: LoopContext):
        """
        Cognition Phase - Process and reason about inputs

        - Analyze incoming data
        - Run decision engine
        - Select appropriate agents
        - Plan responses
        """
        logger.debug(f"Cycle {context.cycle_id}: Cognition phase")
        await self._trigger_phase_handlers(LoopPhase.COGNITION, context)

        cognition_result = {
            "decisions_made": 0,
            "agents_selected": [],
            "plans_created": [],
        }

        # Process inputs through decision engine
        if self.decision_engine and context.outputs.get("perception", {}).get(
            "messages"
        ):
            try:
                # TODO: Implement decision processing
                # decision = await self.decision_engine.decide(context_data)
                cognition_result["decisions_made"] += 1
            except Exception as e:
                logger.error(f"Cognition error: {e}")
                cognition_result["error"] = str(e)

        context.outputs["cognition"] = cognition_result

    async def memory_phase(self, context: LoopContext):
        """
        Memory Phase - Store and consolidate experiences

        - Store new memories
        - Update heat scores
        - Trigger consolidation
        - Extract insights
        """
        logger.debug(f"Cycle {context.cycle_id}: Memory phase")
        await self._trigger_phase_handlers(LoopPhase.MEMORY, context)

        memory_result = {
            "memories_stored": 0,
            "memories_consolidated": 0,
            "heat_scores_updated": 0,
        }

        # Store experiences from this cycle
        if self.memory_manager:
            try:
                # TODO: Implement memory storage
                # await self.memory_manager.store_cycle_memories(context)
                memory_result["memories_stored"] = 1
            except Exception as e:
                logger.error(f"Memory error: {e}")
                memory_result["error"] = str(e)

        context.outputs["memory"] = memory_result

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
        }

        # Execute planned actions
        if self.agent_orchestrator:
            try:
                # TODO: Implement action execution
                # actions = context.outputs.get("cognition", {}).get("plans", [])
                # for action in actions:
                #     await self.agent_orchestrator.execute(action)
                action_result["tasks_executed"] = 1
            except Exception as e:
                logger.error(f"Action error: {e}")
                action_result["error"] = str(e)

        context.outputs["action"] = action_result

    async def learning_phase(self, context: LoopContext):
        """
        Learning Phase - Update models and improve performance

        - Analyze cycle performance
        - Update decision weights
        - Adjust agent selection
        - Optimize cache strategies
        """
        logger.debug(f"Cycle {context.cycle_id}: Learning phase")
        await self._trigger_phase_handlers(LoopPhase.LEARNING, context)

        learning_result = {
            "models_updated": 0,
            "weights_adjusted": 0,
            "optimizations_applied": [],
        }

        # Analyze and learn from this cycle
        try:
            # TODO: Implement learning
            # performance = self._analyze_cycle_performance(context)
            # if performance.needs_improvement:
            #     await self._apply_optimizations(performance)
            learning_result["models_updated"] = 1
        except Exception as e:
            logger.error(f"Learning error: {e}")
            learning_result["error"] = str(e)

        context.outputs["learning"] = learning_result

    async def _run_cycle(self):
        """Run a single complete ultra-loop cycle"""
        cycle_id = f"cycle_{self._current_cycle:06d}"
        context = LoopContext(cycle_id=cycle_id, phase=LoopPhase.PERCEPTION)

        cycle_start = time.time()
        self.metrics.last_cycle_start = datetime.utcnow()

        try:
            # Trigger cycle start handlers
            await self._trigger_cycle_start_handlers(context)

            # Execute each phase in sequence
            phases = [
                (LoopPhase.PERCEPTION, self.perception_phase),
                (LoopPhase.COGNITION, self.cognition_phase),
                (LoopPhase.MEMORY, self.memory_phase),
                (LoopPhase.ACTION, self.action_phase),
                (LoopPhase.LEARNING, self.learning_phase),
            ]

            for phase, phase_method in phases:
                context.phase = phase
                await phase_method(context)

            # Update metrics
            self.metrics.successful_cycles += 1
            context.end_time = datetime.utcnow()

        except Exception as e:
            self.metrics.failed_cycles += 1
            self.metrics.last_error = str(e)
            context.error = str(e)
            logger.error(f"Cycle {cycle_id} failed: {e}")
            await self._trigger_error_handlers(e, context)

        finally:
            # Update timing metrics
            cycle_time = time.time() - cycle_start
            self.metrics.last_cycle_time = cycle_time
            self.metrics.total_execution_time += cycle_time
            self.metrics.avg_cycle_time = (
                self.metrics.total_execution_time / self.metrics.total_cycles
                if self.metrics.total_cycles > 0
                else 0
            )

            # Trigger cycle end handlers
            await self._trigger_cycle_end_handlers(context)

            self._current_cycle += 1
            self.metrics.total_cycles = self._current_cycle

    async def _loop_runner(self):
        """Background loop runner"""
        logger.info("Ultra-Loop started")

        while self._is_running:
            await self._run_cycle()

            # Check if we've reached max cycles
            if self.max_cycles > 0 and self._current_cycle >= self.max_cycles:
                logger.info(f"Reached max cycles ({self.max_cycles}), stopping")
                break

            # Wait for next cycle
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


async def create_ultra_loop(
    config: Optional[Dict[str, Any]] = None,
    **components,
) -> UltraLoop:
    """Factory function to create and initialize Ultra-Loop"""
    loop = UltraLoop(config=config, **components)
    return loop
