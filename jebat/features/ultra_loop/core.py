"""Ultra-Loop continuous processing engine."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class LoopPhase(str, Enum):
    PERCEPTION = "perception"
    PROCESSING = "processing"
    ACTION = "action"
    REFLECTION = "reflection"


@dataclass
class PhaseContext:
    phase: LoopPhase = LoopPhase.PERCEPTION
    cycle_id: int = 0
    data: Dict[str, Any] = field(default_factory=dict)


class UltraLoop:
    """Continuous processing loop with configurable phase callbacks."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_manager: Any = None,
        decision_engine: Any = None,
        cache_manager: Any = None,
        agent_orchestrator: Any = None,
        enable_db_persistence: bool = False,
    ):
        self.config = config or {}
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.cache_manager = cache_manager
        self.agent_orchestrator = agent_orchestrator
        self.enable_db_persistence = enable_db_persistence
        self._running = False
        self._cycle_count = 0
        self._successful_cycles = 0
        self._failed_cycles = 0
        self._phase_callbacks: Dict[LoopPhase, List[Callable]] = {}
        self._task: Optional[asyncio.Task] = None
        self._cycle_history: List[Dict[str, Any]] = []

    def on_phase(self, phase: LoopPhase, callback: Callable) -> None:
        self._phase_callbacks.setdefault(phase, []).append(callback)

    async def start(self) -> None:
        self._running = True
        interval = self.config.get("cycle_interval", 1.0)
        max_cycles = self.config.get("max_cycles", 0)

        async def _run():
            while self._running:
                if max_cycles > 0 and self._cycle_count >= max_cycles:
                    break
                try:
                    await self._run_cycle()
                except Exception as e:
                    self._failed_cycles += 1
                    logger.error(f"Cycle {self._cycle_count} failed: {e}")
                await asyncio.sleep(interval)

        self._task = asyncio.create_task(_run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_cycle(self) -> None:
        cycle_id = self._cycle_count
        self._cycle_count += 1

        try:
            for phase in LoopPhase:
                ctx = PhaseContext(phase=phase, cycle_id=cycle_id)
                for cb in self._phase_callbacks.get(phase, []):
                    cb(ctx)

            self._successful_cycles += 1
            self._cycle_history.append({"cycle_id": cycle_id, "status": "completed"})

        except Exception as e:
            self._failed_cycles += 1
            self._cycle_history.append({"cycle_id": cycle_id, "status": "failed"})
            raise

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_cycles": self._cycle_count,
            "successful_cycles": self._successful_cycles,
            "failed_cycles": self._failed_cycles,
            "running": self._running,
        }

    async def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._cycle_history[-limit:]

    async def get_statistics(self, time_window_hours: int = 1) -> Dict[str, Any]:
        return self.get_metrics()


async def create_ultra_loop(
    config: Optional[Dict[str, Any]] = None,
    memory_manager: Any = None,
    decision_engine: Any = None,
    cache_manager: Any = None,
    agent_orchestrator: Any = None,
    enable_db_persistence: bool = False,
) -> UltraLoop:
    return UltraLoop(
        config=config,
        memory_manager=memory_manager,
        decision_engine=decision_engine,
        cache_manager=cache_manager,
        agent_orchestrator=agent_orchestrator,
        enable_db_persistence=enable_db_persistence,
    )
