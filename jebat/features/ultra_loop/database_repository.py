"""Database repositories for Ultra-Loop cycle persistence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LoopCycle:
    cycle_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"


@dataclass
class LoopPhaseRecord:
    cycle_id: str = ""
    phase_name: str = ""
    phase_order: int = 0
    outputs: Dict[str, Any] = field(default_factory=dict)


class UltraLoopRepository:
    """Repository for Ultra-Loop cycle persistence."""

    def __init__(self, session: Any = None):
        self._cycles: Dict[str, LoopCycle] = {}
        self._phases: Dict[str, List[LoopPhaseRecord]] = {}

    async def create_cycle(
        self, cycle_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> LoopCycle:
        c = LoopCycle(cycle_id=cycle_id, metadata=metadata or {})
        self._cycles[cycle_id] = c
        self._phases[cycle_id] = []
        return c

    async def update_cycle_status(self, cycle_id: str, status: str) -> None:
        if cycle_id in self._cycles:
            self._cycles[cycle_id].status = status

    async def get_cycle(self, cycle_id: str) -> Optional[LoopCycle]:
        return self._cycles.get(cycle_id)

    async def create_phase(
        self,
        cycle_id: str,
        phase_name: str,
        phase_order: int = 0,
        outputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        p = LoopPhaseRecord(
            cycle_id=cycle_id,
            phase_name=phase_name,
            phase_order=phase_order,
            outputs=outputs or {},
        )
        self._phases.setdefault(cycle_id, []).append(p)

    async def get_cycle_phases(self, cycle_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "phase_name": p.phase_name,
                "phase_order": p.phase_order,
                "outputs": p.outputs,
            }
            for p in self._phases.get(cycle_id, [])
        ]
