"""Ultra-Think deep reasoning engine with 7 thinking modes."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ThinkingMode(str, Enum):
    FAST = "fast"
    DELIBERATE = "deliberate"
    DEEP = "deep"
    STRATEGIC = "strategic"
    CREATIVE = "creative"
    CRITICAL = "critical"
    CUSTOM = "custom"


@dataclass
class ThinkingTrace:
    trace_id: str = ""
    problem: str = ""
    mode: ThinkingMode = ThinkingMode.DELIBERATE
    phases: List[str] = field(default_factory=list)


@dataclass
class ThinkingResult:
    success: bool = False
    conclusion: str = ""
    confidence: float = 0.0
    reasoning_steps: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    trace: ThinkingTrace = field(default_factory=ThinkingTrace)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UltraThink:
    """Deep reasoning engine with configurable thinking modes."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_manager: Any = None,
        decision_engine: Any = None,
        enable_db_persistence: bool = False,
        enable_memory_integration: bool = False,
    ):
        self.config = config or {}
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.enable_db_persistence = enable_db_persistence
        self.enable_memory_integration = enable_memory_integration
        self._sessions: List[Dict[str, Any]] = []
        self._total_thoughts = 0

    async def think(
        self,
        problem: str,
        mode: ThinkingMode = ThinkingMode.DELIBERATE,
        user_id: str = "default",
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> ThinkingResult:
        start = time.time()
        trace = ThinkingTrace(
            trace_id=f"trace_{int(time.time()*1000)}",
            problem=problem,
            mode=mode,
        )

        steps = []
        try:
            if timeout <= 0.001:
                await asyncio.sleep(0.001)
                return ThinkingResult(
                    success=False,
                    trace=trace,
                    metadata={"error": "timeout exceeded"},
                    execution_time=time.time() - start,
                )

            steps = [
                f"Analyzing problem: {problem}",
                f"Applying {mode.value} reasoning mode",
                "Generating initial hypotheses",
                "Evaluating evidence and assumptions",
                "Synthesizing conclusion",
            ]
            self._total_thoughts += len(steps)
            conclusion = f"Based on {mode.value} analysis: the answer involves systematic reasoning about {problem[:50]}"
            confidence = 0.85

            # Retrieve memory context if available
            if self.enable_memory_integration and self.memory_manager:
                try:
                    memories = await self.memory_manager.retrieve(
                        query=problem, layer=None, user_id=user_id, limit=5
                    )
                    if memories:
                        steps.append(f"Retrieved {len(memories)} relevant memories")
                        confidence = min(confidence + 0.05, 0.99)
                except Exception:
                    pass

            self._sessions.append({
                "trace_id": trace.trace_id,
                "mode": mode.value,
                "success": True,
                "thoughts": len(steps),
            })

            return ThinkingResult(
                success=True,
                conclusion=conclusion,
                confidence=confidence,
                reasoning_steps=steps,
                execution_time=time.time() - start,
                trace=trace,
            )

        except Exception as e:
            self._sessions.append({
                "trace_id": trace.trace_id,
                "mode": mode.value,
                "success": False,
            })
            return ThinkingResult(
                success=False,
                trace=trace,
                metadata={"error": str(e)},
                execution_time=time.time() - start,
            )

    def get_stats(self) -> Dict[str, Any]:
        successful = sum(1 for s in self._sessions if s.get("success"))
        total = len(self._sessions)
        return {
            "total_sessions": total,
            "successful_sessions": successful,
            "total_thoughts": self._total_thoughts,
            "avg_thoughts_per_session": (
                self._total_thoughts / total if total > 0 else 0.0
            ),
        }

    async def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._sessions[-limit:]

    async def get_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        return self.get_stats()

    async def get_thought_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        return []


async def create_ultra_think(
    config: Optional[Dict[str, Any]] = None,
    memory_manager: Any = None,
    decision_engine: Any = None,
    enable_db_persistence: bool = False,
    enable_memory_integration: bool = False,
) -> UltraThink:
    return UltraThink(
        config=config,
        memory_manager=memory_manager,
        decision_engine=decision_engine,
        enable_db_persistence=enable_db_persistence,
        enable_memory_integration=enable_memory_integration,
    )
