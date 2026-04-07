"""
JEBAT Ultra-Think Database Repository

Database integration for Ultra-Think thinking trace storage and retrieval.
Provides persistent storage for:
- Thinking sessions
- Thought chains
- Reasoning traces
- Conclusion history
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jebat.database.models import (
    AsyncSessionLocal,
    UltraLoopCycle,
    UltraLoopThinkSession,
    UltraLoopThought,
)

logger = logging.getLogger(__name__)


class UltraThinkRepository:
    """
    Database repository for Ultra-Think thinking session data.

    Provides CRUD operations and analytics for thinking sessions.
    """

    def __init__(self, session_factory=None):
        """
        Initialize the repository.

        Args:
            session_factory: Async session factory (defaults to AsyncSessionLocal)
        """
        self.session_factory = session_factory or AsyncSessionLocal
        logger.info("UltraThinkRepository initialized")

    async def create_session(
        self,
        trace_id: str,
        problem_statement: str,
        thinking_mode: str,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UltraLoopThinkSession:
        """
        Create a new thinking session record.

        Args:
            trace_id: Unique trace identifier
            problem_statement: Problem being thought about
            thinking_mode: Mode of thinking (fast, deliberate, deep, etc.)
            user_id: Optional user identifier
            metadata: Optional metadata

        Returns:
            Created UltraLoopThinkSession instance
        """
        async with self.session_factory() as session:
            think_session = UltraLoopThinkSession(
                id=uuid4(),
                trace_id=trace_id,
                user_id=user_id,
                problem_statement=problem_statement,
                thinking_mode=thinking_mode,
                status="running",
                metadata=metadata or {},
                started_at=datetime.utcnow(),
            )

            session.add(think_session)
            await session.commit()
            await session.refresh(think_session)

            logger.info(f"Created thinking session: {trace_id}")
            return think_session

    async def update_session_status(
        self,
        trace_id: str,
        status: str,
        conclusion: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> Optional[UltraLoopThinkSession]:
        """
        Update thinking session status.

        Args:
            trace_id: Trace identifier
            status: New status (running, completed, failed, timeout)
            conclusion: Optional conclusion
            confidence_score: Optional confidence score

        Returns:
            Updated UltraLoopThinkSession instance or None
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopThinkSession).where(
                    UltraLoopThinkSession.trace_id == trace_id
                )
            )
            think_session = result.scalar_one_or_none()

            if not think_session:
                logger.warning(f"Thinking session not found: {trace_id}")
                return None

            think_session.status = status
            think_session.completed_at = (
                datetime.utcnow()
                if status in ["completed", "failed", "timeout"]
                else None
            )

            if conclusion:
                think_session.conclusion = conclusion
            if confidence_score is not None:
                think_session.confidence_score = confidence_score

            await session.commit()
            await session.refresh(think_session)

            logger.info(f"Updated thinking session {trace_id} status to {status}")
            return think_session

    async def create_thought(
        self,
        trace_id: str,
        thought_id: str,
        content: str,
        phase: str,
        phase_order: int,
        confidence: float = 0.5,
        supporting_evidence: Optional[List[str]] = None,
        counter_arguments: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UltraLoopThought:
        """
        Create a thought record for a thinking session.

        Args:
            trace_id: Parent trace identifier
            thought_id: Unique thought identifier
            content: Thought content
            phase: Thinking phase
            phase_order: Thought order in phase
            confidence: Confidence score
            supporting_evidence: Supporting evidence list
            counter_arguments: Counter arguments list
            metadata: Optional metadata

        Returns:
            Created UltraLoopThought instance or None
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopThinkSession).where(
                    UltraLoopThinkSession.trace_id == trace_id
                )
            )
            think_session = result.scalar_one_or_none()

            if not think_session:
                logger.warning(f"Thinking session not found for thought: {trace_id}")
                return None

            thought = UltraLoopThought(
                id=uuid4(),
                thought_id=thought_id,
                session_id=think_session.id,
                content=content,
                phase=phase,
                phase_order=phase_order,
                confidence=confidence,
                supporting_evidence=supporting_evidence or [],
                counter_arguments=counter_arguments or [],
                metadata=metadata or {},
                created_at=datetime.utcnow(),
            )

            session.add(thought)
            await session.commit()
            await session.refresh(thought)

            logger.debug(f"Created thought {thought_id} for session {trace_id}")
            return thought

    async def get_session(
        self,
        trace_id: str,
        include_thoughts: bool = True,
    ) -> Optional[UltraLoopThinkSession]:
        """
        Get a thinking session by trace ID.

        Args:
            trace_id: Trace identifier
            include_thoughts: Include thought details

        Returns:
            UltraLoopThinkSession instance or None
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopThinkSession).where(
                    UltraLoopThinkSession.trace_id == trace_id
                )
            )
            think_session = result.scalar_one_or_none()

            if think_session and include_thoughts:
                await session.refresh(think_session, attribute_names=["thoughts"])

            return think_session

    async def get_recent_sessions(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        thinking_mode: Optional[str] = None,
    ) -> List[UltraLoopThinkSession]:
        """
        Get recent thinking sessions.

        Args:
            limit: Maximum number of sessions to return
            status: Optional status filter
            thinking_mode: Optional thinking mode filter

        Returns:
            List of UltraLoopThinkSession instances
        """
        async with self.session_factory() as session:
            query = (
                select(UltraLoopThinkSession)
                .order_by(desc(UltraLoopThinkSession.started_at))
                .limit(limit)
            )

            if status:
                query = query.where(UltraLoopThinkSession.status == status)
            if thinking_mode:
                query = query.where(
                    UltraLoopThinkSession.thinking_mode == thinking_mode
                )

            result = await session.execute(query)
            sessions = result.scalars().all()

            return sessions

    async def get_session_statistics(
        self,
        time_window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get thinking session statistics for a time window.

        Args:
            time_window_hours: Time window in hours

        Returns:
            Dictionary with statistics
        """
        async with self.session_factory() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

            # Total sessions
            total_result = await session.execute(
                select(func.count(UltraLoopThinkSession.id)).where(
                    UltraLoopThinkSession.started_at >= cutoff_time
                )
            )
            total_sessions = total_result.scalar() or 0

            # Successful sessions
            success_result = await session.execute(
                select(func.count(UltraLoopThinkSession.id)).where(
                    UltraLoopThinkSession.started_at >= cutoff_time,
                    UltraLoopThinkSession.status == "completed",
                )
            )
            successful_sessions = success_result.scalar() or 0

            # Failed sessions
            failed_result = await session.execute(
                select(func.count(UltraLoopThinkSession.id)).where(
                    UltraLoopThinkSession.started_at >= cutoff_time,
                    UltraLoopThinkSession.status.in_(["failed", "timeout"]),
                )
            )
            failed_sessions = failed_result.scalar() or 0

            # Average confidence score
            avg_conf_result = await session.execute(
                select(func.avg(UltraLoopThinkSession.confidence_score)).where(
                    UltraLoopThinkSession.started_at >= cutoff_time,
                    UltraLoopThinkSession.confidence_score != None,
                )
            )
            avg_confidence = avg_conf_result.scalar() or 0

            # Average thoughts per session
            thoughts_result = await session.execute(
                select(
                    UltraLoopThinkSession.id,
                    func.count(UltraLoopThought.id).label("thought_count"),
                )
                .join(UltraLoopThought, isouter=True)
                .where(UltraLoopThinkSession.started_at >= cutoff_time)
                .group_by(UltraLoopThinkSession.id)
            )
            thought_counts = [row[1] for row in thoughts_result.all()]
            avg_thoughts = (
                sum(thought_counts) / len(thought_counts) if thought_counts else 0
            )

            # Thinking mode distribution
            mode_result = await session.execute(
                select(
                    UltraLoopThinkSession.thinking_mode,
                    func.count(UltraLoopThinkSession.id),
                )
                .where(UltraLoopThinkSession.started_at >= cutoff_time)
                .group_by(UltraLoopThinkSession.thinking_mode)
            )
            mode_distribution = [
                {"mode": row[0], "count": row[1]} for row in mode_result.all()
            ]

            return {
                "time_window_hours": time_window_hours,
                "total_sessions": total_sessions,
                "successful_sessions": successful_sessions,
                "failed_sessions": failed_sessions,
                "success_rate": (successful_sessions / total_sessions * 100)
                if total_sessions > 0
                else 0,
                "avg_confidence_score": avg_confidence,
                "avg_thoughts_per_session": avg_thoughts,
                "thinking_mode_distribution": mode_distribution,
            }

    async def get_thought_chain(
        self,
        trace_id: str,
    ) -> List[UltraLoopThought]:
        """
        Get all thoughts for a thinking session.

        Args:
            trace_id: Trace identifier

        Returns:
            List of UltraLoopThought instances
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopThinkSession).where(
                    UltraLoopThinkSession.trace_id == trace_id
                )
            )
            think_session = result.scalar_one_or_none()

            if not think_session:
                return []

            result = await session.execute(
                select(UltraLoopThought)
                .where(UltraLoopThought.session_id == think_session.id)
                .order_by(UltraLoopThought.phase_order)
            )
            thoughts = result.scalars().all()

            return thoughts

    async def cleanup_old_sessions(
        self,
        retention_days: int = 30,
    ) -> int:
        """
        Clean up old thinking sessions.

        Args:
            retention_days: Number of days to retain sessions

        Returns:
            Number of sessions deleted
        """
        logger.info(f"Cleanup requested for sessions older than {retention_days} days")
        return 0


# Repository instance for easy import
ultra_think_repo = UltraThinkRepository()
