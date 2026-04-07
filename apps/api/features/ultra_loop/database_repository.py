"""
JEBAT Ultra-Loop Database Repository

Database integration for Ultra-Loop cycle storage and retrieval.
Provides persistent storage for:
- Cycle execution history
- Phase-level metrics
- Performance tracking
- Error tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jebat.database.models import (
    AsyncSessionLocal,
    Base,
    UltraLoopCycle,
    UltraLoopPhase,
)

logger = logging.getLogger(__name__)


class UltraLoopRepository:
    """
    Database repository for Ultra-Loop cycle data.

    Provides CRUD operations and analytics for ultra-loop execution history.
    """

    def __init__(self, session_factory=None):
        """
        Initialize the repository.

        Args:
            session_factory: Async session factory (defaults to AsyncSessionLocal)
        """
        self.session_factory = session_factory or AsyncSessionLocal
        logger.info("UltraLoopRepository initialized")

    async def create_cycle(
        self,
        cycle_id: str,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UltraLoopCycle:
        """
        Create a new cycle record.

        Args:
            cycle_id: Unique cycle identifier
            user_id: Optional user identifier
            metadata: Optional metadata

        Returns:
            Created UltraLoopCycle instance
        """
        async with self.session_factory() as session:
            cycle = UltraLoopCycle(
                id=uuid4(),
                cycle_id=cycle_id,
                user_id=user_id,
                status="running",
                metadata=metadata or {},
                started_at=datetime.utcnow(),
            )

            session.add(cycle)
            await session.commit()
            await session.refresh(cycle)

            logger.info(f"Created cycle record: {cycle_id}")
            return cycle

    async def update_cycle_status(
        self,
        cycle_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[UltraLoopCycle]:
        """
        Update cycle status.

        Args:
            cycle_id: Cycle identifier
            status: New status (running, completed, failed)
            error_message: Optional error message

        Returns:
            Updated UltraLoopCycle instance or None
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopCycle).where(UltraLoopCycle.cycle_id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if not cycle:
                logger.warning(f"Cycle not found: {cycle_id}")
                return None

            cycle.status = status
            cycle.completed_at = (
                datetime.utcnow() if status in ["completed", "failed"] else None
            )
            if error_message:
                cycle.error_message = error_message

            await session.commit()
            await session.refresh(cycle)

            logger.info(f"Updated cycle {cycle_id} status to {status}")
            return cycle

    async def create_phase(
        self,
        cycle_id: str,
        phase_name: str,
        phase_order: int,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
    ) -> UltraLoopPhase:
        """
        Create a phase record for a cycle.

        Args:
            cycle_id: Parent cycle identifier
            phase_name: Phase name (perception, cognition, memory, action, learning)
            phase_order: Phase execution order
            inputs: Phase inputs
            outputs: Phase outputs

        Returns:
            Created UltraLoopPhase instance
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopCycle).where(UltraLoopCycle.cycle_id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if not cycle:
                logger.warning(f"Cycle not found for phase: {cycle_id}")
                return None

            phase = UltraLoopPhase(
                id=uuid4(),
                cycle_id=cycle.id,
                phase_name=phase_name,
                phase_order=phase_order,
                status="completed",
                inputs=inputs or {},
                outputs=outputs or {},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

            session.add(phase)
            await session.commit()
            await session.refresh(phase)

            logger.debug(f"Created phase {phase_name} for cycle {cycle_id}")
            return phase

    async def get_cycle(
        self,
        cycle_id: str,
        include_phases: bool = True,
    ) -> Optional[UltraLoopCycle]:
        """
        Get a cycle by ID.

        Args:
            cycle_id: Cycle identifier
            include_phases: Include phase details

        Returns:
            UltraLoopCycle instance or None
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopCycle).where(UltraLoopCycle.cycle_id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if cycle and include_phases:
                await session.refresh(cycle, attribute_names=["phases"])

            return cycle

    async def get_recent_cycles(
        self,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[UltraLoopCycle]:
        """
        Get recent cycles.

        Args:
            limit: Maximum number of cycles to return
            status: Optional status filter

        Returns:
            List of UltraLoopCycle instances
        """
        async with self.session_factory() as session:
            query = (
                select(UltraLoopCycle)
                .order_by(desc(UltraLoopCycle.started_at))
                .limit(limit)
            )

            if status:
                query = query.where(UltraLoopCycle.status == status)

            result = await session.execute(query)
            cycles = result.scalars().all()

            return cycles

    async def get_cycle_statistics(
        self,
        time_window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get cycle statistics for a time window.

        Args:
            time_window_hours: Time window in hours

        Returns:
            Dictionary with statistics
        """
        async with self.session_factory() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

            # Total cycles
            total_result = await session.execute(
                select(func.count(UltraLoopCycle.id)).where(
                    UltraLoopCycle.started_at >= cutoff_time
                )
            )
            total_cycles = total_result.scalar() or 0

            # Successful cycles
            success_result = await session.execute(
                select(func.count(UltraLoopCycle.id)).where(
                    UltraLoopCycle.started_at >= cutoff_time,
                    UltraLoopCycle.status == "completed",
                )
            )
            successful_cycles = success_result.scalar() or 0

            # Failed cycles
            failed_result = await session.execute(
                select(func.count(UltraLoopCycle.id)).where(
                    UltraLoopCycle.started_at >= cutoff_time,
                    UltraLoopCycle.status == "failed",
                )
            )
            failed_cycles = failed_result.scalar() or 0

            # Average cycle time
            avg_time_result = await session.execute(
                select(
                    func.avg(UltraLoopCycle.completed_at - UltraLoopCycle.started_at)
                ).where(
                    UltraLoopCycle.started_at >= cutoff_time,
                    UltraLoopCycle.status == "completed",
                    UltraLoopCycle.completed_at != None,
                )
            )
            avg_cycle_time = avg_time_result.scalar() or 0

            # Phase statistics
            phase_result = await session.execute(
                select(
                    UltraLoopPhase.phase_name,
                    func.count(UltraLoopPhase.id),
                    func.avg(UltraLoopPhase.completed_at - UltraLoopPhase.started_at),
                )
                .where(UltraLoopPhase.started_at >= cutoff_time)
                .group_by(UltraLoopPhase.phase_name)
            )
            phase_stats = phase_result.all()

            return {
                "time_window_hours": time_window_hours,
                "total_cycles": total_cycles,
                "successful_cycles": successful_cycles,
                "failed_cycles": failed_cycles,
                "success_rate": (successful_cycles / total_cycles * 100)
                if total_cycles > 0
                else 0,
                "avg_cycle_time_seconds": avg_cycle_time.total_seconds()
                if avg_cycle_time
                else 0,
                "phase_statistics": [
                    {
                        "phase_name": row[0],
                        "count": row[1],
                        "avg_duration_seconds": (
                            row[2].total_seconds() if row[2] else 0
                        ),
                    }
                    for row in (phase_stats or [])
                ],
            }

    async def get_phase_history(
        self,
        cycle_id: str,
    ) -> List[UltraLoopPhase]:
        """
        Get all phases for a cycle.

        Args:
            cycle_id: Cycle identifier

        Returns:
            List of UltraLoopPhase instances
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(UltraLoopCycle).where(UltraLoopCycle.cycle_id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if not cycle:
                return []

            result = await session.execute(
                select(UltraLoopPhase)
                .where(UltraLoopPhase.cycle_id == cycle.id)
                .order_by(UltraLoopPhase.phase_order)
            )
            phases = result.scalars().all()

            return phases

    async def cleanup_old_cycles(
        self,
        retention_days: int = 30,
    ) -> int:
        """
        Clean up old cycles.

        Args:
            retention_days: Number of days to retain cycles

        Returns:
            Number of cycles deleted
        """
        # This would require actual SQLAlchemy delete operations
        # For now, just log the intention
        logger.info(f"Cleanup requested for cycles older than {retention_days} days")
        return 0


# Repository instance for easy import
ultra_loop_repo = UltraLoopRepository()
