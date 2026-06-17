"""Database repositories for Ultra-Think session persistence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ThinkSession:
    trace_id: str = ""
    problem_statement: str = ""
    thinking_mode: str = "deliberate"
    status: str = "pending"
    conclusion: str = ""
    confidence_score: float = 0.0


@dataclass
class Thought:
    trace_id: str = ""
    thought_id: str = ""
    content: str = ""
    phase: str = ""
    phase_order: int = 0
    confidence: float = 0.0


class UltraThinkRepository:
    """Repository for Ultra-Think session persistence."""

    def __init__(self, session: Any = None):
        self._sessions: Dict[str, ThinkSession] = {}
        self._thoughts: Dict[str, List[Thought]] = {}

    async def create_session(
        self, trace_id: str, problem_statement: str, thinking_mode: str = "deliberate"
    ) -> ThinkSession:
        s = ThinkSession(
            trace_id=trace_id,
            problem_statement=problem_statement,
            thinking_mode=thinking_mode,
        )
        self._sessions[trace_id] = s
        self._thoughts[trace_id] = []
        return s

    async def update_session_status(
        self,
        trace_id: str,
        status: str,
        conclusion: str = "",
        confidence_score: float = 0.0,
    ) -> None:
        if trace_id in self._sessions:
            s = self._sessions[trace_id]
            s.status = status
            s.conclusion = conclusion
            s.confidence_score = confidence_score

    async def get_session(self, trace_id: str) -> Optional[ThinkSession]:
        return self._sessions.get(trace_id)

    async def create_thought(
        self,
        trace_id: str,
        thought_id: str,
        content: str,
        phase: str,
        phase_order: int = 0,
        confidence: float = 0.0,
    ) -> None:
        t = Thought(
            trace_id=trace_id,
            thought_id=thought_id,
            content=content,
            phase=phase,
            phase_order=phase_order,
            confidence=confidence,
        )
        self._thoughts.setdefault(trace_id, []).append(t)

    async def get_thought_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "thought_id": t.thought_id,
                "content": t.content,
                "phase": t.phase,
                "phase_order": t.phase_order,
                "confidence": t.confidence,
            }
            for t in self._thoughts.get(trace_id, [])
        ]
