# ==================== JEBAT AI System - Database Repository Layer ====================
# Version: 1.0.0
# Repository pattern for database operations with caching, error recovery, and performance optimization
#
# This module provides repository classes for:
# - User management
# - Memory System (5-layer architecture: M0-M4)
# - Agent System (configurations, performance, tasks)
# - Decision Engine (routing, priorities)
# - Error Recovery System (circuit breakers, DLQ)
# - Smart Cache (HOT/WARM/COLD tiers)
# - MCP Protocol Server (JSON-RPC operations)
# - WebSocket Gateway (real-time notifications)
# - Model Forge (query optimization, model management)
# - Sentinel Security (threat detection, policies)
# - Skills System (agent capabilities)

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy import (
    and_,
    delete,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Agent,
    AgentPerformance,
    AgentSkill,
    AgentState,
    AuditLog,
    CacheEntry,
    CacheMetrics,
    CacheTier,
    CircuitBreaker,
    CircuitState,
    ConnectionState,
    DeadLetterQueue,
    DecisionLog,
    DecisionRule,
    ErrorSeverity,
    ErrorTracking,
    MCPOperation,
    MemoryLayer,
    MemoryM0,
    MemoryM1,
    MemoryM2,
    MemoryM3,
    MemoryM4,
    Model,
    ModelUsage,
    SecurityEvent,
    SecurityPolicy,
    Skill,
    SkillExecution,
    Task,
    TaskPriority,
    TaskStatus,
    User,
    WebSocketConnection,
    WebSocketMessage,
)

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for model classes
T = TypeVar("T")


class BaseRepository:
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Initialize repository.

        Args:
            session: Database session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> T:
        """
        Create a new record.

        Args:
            **kwargs: Model fields and values

        Returns:
            T: Created model instance
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            logger.debug(f"Created {self.model.__name__} instance: {instance.id}")
            return instance
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            await self.session.rollback()
            raise

    async def create_bulk(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in bulk.

        Args:
            items: List of dictionaries with model fields

        Returns:
            List[T]: Created model instances
        """
        try:
            instances = [self.model(**item) for item in items]
            self.session.add_all(instances)
            await self.session.flush()
            for instance in instances:
                await self.session.refresh(instance)
            logger.debug(f"Created {len(instances)} {self.model.__name__} instances")
            return instances
        except Exception as e:
            logger.error(f"Error creating bulk {self.model.__name__}: {e}")
            await self.session.rollback()
            raise

    async def get_by_id(self, id: Union[str, int]) -> Optional[T]:
        """
        Get record by ID.

        Args:
            id: Record ID

        Returns:
            Optional[T]: Model instance or None
        """
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """
        Get all records with optional pagination and ordering.

        Args:
            limit: Maximum number of records
            offset: Number of records to skip
            order_by: Field to order by (prefix with '-' for descending)

        Returns:
            List[T]: List of model instances
        """
        try:
            query = select(self.model)

            # Apply ordering
            if order_by:
                if order_by.startswith("-"):
                    field = getattr(self.model, order_by[1:])
                    query = query.order_by(field.desc())
                else:
                    field = getattr(self.model, order_by)
                    query = query.order_by(field)

            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []

    async def update(self, id: Union[str, int], **kwargs) -> Optional[T]:
        """
        Update a record by ID.

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Optional[T]: Updated model instance or None
        """
        try:
            instance = await self.get_by_id(id)
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                await self.session.flush()
                await self.session.refresh(instance)
                logger.debug(f"Updated {self.model.__name__} instance: {instance.id}")
                return instance
            return None
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} id {id}: {e}")
            await self.session.rollback()
            return None

    async def update_bulk(self, ids: List[Union[str, int]], **kwargs) -> int:
        """
        Update multiple records by IDs.

        Args:
            ids: List of record IDs
            **kwargs: Fields to update

        Returns:
            int: Number of updated records
        """
        try:
            stmt = update(self.model).where(self.model.id.in_(ids)).values(**kwargs)
            result = await self.session.execute(stmt)
            await self.session.flush()
            logger.debug(f"Updated {result.rowcount} {self.model.__name__} instances")
            return result.rowcount
        except Exception as e:
            logger.error(f"Error updating bulk {self.model.__name__}: {e}")
            await self.session.rollback()
            return 0

    async def delete(self, id: Union[str, int]) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            instance = await self.get_by_id(id)
            if instance:
                await self.session.delete(instance)
                await self.session.flush()
                logger.debug(f"Deleted {self.model.__name__} instance: {instance.id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} id {id}: {e}")
            await self.session.rollback()
            return False

    async def delete_bulk(self, ids: List[Union[str, int]]) -> int:
        """
        Delete multiple records by IDs.

        Args:
            ids: List of record IDs

        Returns:
            int: Number of deleted records
        """
        try:
            stmt = delete(self.model).where(self.model.id.in_(ids))
            result = await self.session.execute(stmt)
            await self.session.flush()
            logger.debug(f"Deleted {result.rowcount} {self.model.__name__} instances")
            return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting bulk {self.model.__name__}: {e}")
            await self.session.rollback()
            return 0

    async def count(self, **filters) -> int:
        """
        Count records matching filters.

        Args:
            **filters: Field filters

        Returns:
            int: Count of matching records
        """
        try:
            query = select(func.count(self.model.id))
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0

    async def exists(self, **filters) -> bool:
        """
        Check if any record matches filters.

        Args:
            **filters: Field filters

        Returns:
            bool: True if exists, False otherwise
        """
        return await self.count(**filters) > 0

    async def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """
        Query records with filters, ordering, and pagination.

        Args:
            filters: Dictionary of field filters
            order_by: Field to order by
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List[T]: List of matching model instances
        """
        try:
            query = select(self.model)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, key).in_(value))
                    else:
                        query = query.where(getattr(self.model, key) == value)

            # Apply ordering
            if order_by:
                if order_by.startswith("-"):
                    field = getattr(self.model, order_by[1:])
                    query = query.order_by(field.desc())
                else:
                    field = getattr(self.model, order_by)
                    query = query.order_by(field)

            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error querying {self.model.__name__}: {e}")
            return []


# ==================== User Repository ====================


class UserRepository(BaseRepository):
    """Repository for user management."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await self.session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        return await self.query(filters={"is_active": True})

    async def get_admin_users(self) -> List[User]:
        """Get all admin users."""
        return await self.query(filters={"is_admin": True})

    async def update_last_login(self, user_id: str) -> Optional[User]:
        """Update user's last login time."""
        return await self.update(user_id, last_login_at=datetime.now(timezone.utc))


# ==================== Memory System Repositories ====================


class MemoryRepository(BaseRepository):
    """Base repository for memory operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        super().__init__(session, model)

    async def get_by_user(self, user_id: str, limit: Optional[int] = None) -> List[T]:
        """Get memory entries for a user."""
        return await self.query(filters={"user_id": user_id}, limit=limit)

    async def get_by_session(
        self, user_id: str, session_id: str, limit: Optional[int] = None
    ) -> List[T]:
        """Get memory entries for a user session."""
        return await self.query(
            filters={"user_id": user_id, "session_id": session_id}, limit=limit
        )

    async def get_expired(self) -> List[T]:
        """Get expired memory entries."""
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(self.model).where(self.model.expires_at < now)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting expired {self.model.__name__}: {e}")
            return []

    async def delete_expired(self) -> int:
        """Delete expired memory entries."""
        try:
            expired = await self.get_expired()
            ids = [item.id for item in expired]
            return await self.delete_bulk(ids)
        except Exception as e:
            logger.error(f"Error deleting expired {self.model.__name__}: {e}")
            return 0

    async def search_by_content(
        self,
        user_id: str,
        query_text: str,
        limit: Optional[int] = 10,
    ) -> List[T]:
        """Search memory entries by content."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.content.ilike(f"%{query_text}%"),
                    )
                )
                .order_by(self.model.heat_score.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching {self.model.__name__} by content: {e}")
            return []


class MemoryM0Repository(MemoryRepository):
    """Repository for M0 (Working Memory)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MemoryM0)


class MemoryM1Repository(MemoryRepository):
    """Repository for M1 (Short-term Memory)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MemoryM1)

    async def get_recent(
        self, user_id: str, hours: int = 24, limit: Optional[int] = 50
    ) -> List[MemoryM1]:
        """Get recent memory entries."""
        try:
            cutoff = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            result = await self.session.execute(
                select(MemoryM1)
                .where(
                    and_(
                        MemoryM1.user_id == user_id,
                        MemoryM1.created_at >= cutoff,
                    )
                )
                .order_by(MemoryM1.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting recent M1 entries: {e}")
            return []


class MemoryM2Repository(MemoryRepository):
    """Repository for M2 (Medium-term Memory)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MemoryM2)


class MemoryM3Repository(MemoryRepository):
    """Repository for M3 (Long-term Memory)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MemoryM3)

    async def search_by_tags(
        self, user_id: str, tags: List[str], limit: Optional[int] = 10
    ) -> List[MemoryM3]:
        """Search memory entries by tags."""
        try:
            result = await self.session.execute(
                select(MemoryM3)
                .where(
                    and_(
                        MemoryM3.user_id == user_id,
                        MemoryM3.tags.overlap(tags),
                    )
                )
                .order_by(MemoryM3.heat_score.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching M3 entries by tags: {e}")
            return []


class MemoryM4Repository(MemoryRepository):
    """Repository for M4 (Permanent Memory)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MemoryM4)


# ==================== Agent System Repositories ====================


class AgentRepository(BaseRepository):
    """Repository for agent management."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Agent)

    async def get_by_type(self, agent_type: str) -> List[Agent]:
        """Get agents by type."""
        return await self.query(filters={"type": agent_type})

    async def get_by_state(self, state: AgentState) -> List[Agent]:
        """Get agents by state."""
        return await self.query(filters={"state": state})

    async def get_active_agents(self) -> List[Agent]:
        """Get all active agents."""
        return await self.query(filters={"is_active": True})

    async def get_idle_agents(self) -> List[Agent]:
        """Get all idle agents."""
        return await self.query(filters={"state": AgentState.IDLE, "is_active": True})

    async def update_state(self, agent_id: str, state: AgentState) -> Optional[Agent]:
        """Update agent state."""
        return await self.update(agent_id, state=state)

    async def update_heartbeat(self, agent_id: str) -> Optional[Agent]:
        """Update agent heartbeat."""
        return await self.update(agent_id, last_heartbeat_at=datetime.now(timezone.utc))


class TaskRepository(BaseRepository):
    """Repository for task management."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)

    async def get_by_user(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Task]:
        """Get tasks for a user."""
        return await self.query(
            filters={"user_id": user_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_agent(
        self, agent_id: str, limit: Optional[int] = None
    ) -> List[Task]:
        """Get tasks for an agent."""
        return await self.query(
            filters={"agent_id": agent_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status."""
        return await self.query(filters={"status": status}, order_by="-created_at")

    async def get_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get tasks by priority."""
        return await self.query(filters={"priority": priority}, order_by="-created_at")

    async def get_pending_tasks(self, limit: Optional[int] = 10) -> List[Task]:
        """Get pending tasks sorted by priority."""
        try:
            priority_order = {
                TaskPriority.CRITICAL: 0,
                TaskPriority.HIGH: 1,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 3,
                TaskPriority.BACKGROUND: 4,
            }

            result = await self.session.execute(
                select(Task)
                .where(Task.status == TaskStatus.PENDING)
                .order_by(Task.priority.asc(), Task.created_at.asc())
                .limit(limit)
            )
            tasks = list(result.scalars().all())
            # Sort by custom priority order
            tasks.sort(key=lambda t: priority_order.get(t.priority, 99))
            return tasks
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []

    async def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        """Update task status."""
        return await self.update(task_id, status=status)

    async def assign_agent(self, task_id: str, agent_id: str) -> Optional[Task]:
        """Assign task to an agent."""
        return await self.update(task_id, agent_id=agent_id)

    async def add_error(self, task_id: str, error_message: str) -> Optional[Task]:
        """Add error message to task."""
        task = await self.get_by_id(task_id)
        if task:
            return await self.update(
                task_id,
                error_message=error_message,
                retry_count=task.retry_count + 1,
            )
        return None

    async def complete_task(
        self, task_id: str, output_data: Dict[str, Any]
    ) -> Optional[Task]:
        """Mark task as completed."""
        return await self.update(
            task_id,
            status=TaskStatus.COMPLETED,
            output_data=output_data,
            completed_at=datetime.now(timezone.utc),
        )

    async def fail_task(self, task_id: str, error_message: str) -> Optional[Task]:
        """Mark task as failed."""
        return await self.update(
            task_id,
            status=TaskStatus.FAILED,
            error_message=error_message,
            completed_at=datetime.now(timezone.utc),
        )


class AgentPerformanceRepository(BaseRepository):
    """Repository for agent performance metrics."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AgentPerformance)

    async def get_by_agent(
        self, agent_id: str, limit: Optional[int] = 100
    ) -> List[AgentPerformance]:
        """Get performance metrics for an agent."""
        return await self.query(
            filters={"agent_id": agent_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_metric_type(
        self, agent_id: str, metric_type: str, limit: Optional[int] = 100
    ) -> List[AgentPerformance]:
        """Get performance metrics by type."""
        return await self.query(
            filters={"agent_id": agent_id, "metric_type": metric_type},
            limit=limit,
            order_by="-created_at",
        )

    async def get_recent(
        self, hours: int = 24, limit: Optional[int] = 100
    ) -> List[AgentPerformance]:
        """Get recent performance metrics."""
        try:
            cutoff = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            result = await self.session.execute(
                select(AgentPerformance)
                .where(AgentPerformance.created_at >= cutoff)
                .order_by(AgentPerformance.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting recent performance metrics: {e}")
            return []


# ==================== Decision Engine Repositories ====================


class DecisionRuleRepository(BaseRepository):
    """Repository for decision rules."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DecisionRule)

    async def get_by_type(self, rule_type: str) -> List[DecisionRule]:
        """Get rules by type."""
        return await self.query(
            filters={"rule_type": rule_type, "is_active": True}, order_by="-priority"
        )

    async def get_active_rules(self) -> List[DecisionRule]:
        """Get all active rules."""
        return await self.query(filters={"is_active": True}, order_by="-priority")


class DecisionLogRepository(BaseRepository):
    """Repository for decision logs."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DecisionLog)

    async def get_by_task(self, task_id: str) -> List[DecisionLog]:
        """Get decision logs for a task."""
        return await self.query(filters={"task_id": task_id}, order_by="-created_at")

    async def get_by_agent(self, agent_id: str) -> List[DecisionLog]:
        """Get decision logs for an agent."""
        return await self.query(filters={"agent_id": agent_id}, order_by="-created_at")

    async def get_by_type(
        self, decision_type: str, limit: Optional[int] = 100
    ) -> List[DecisionLog]:
        """Get decision logs by type."""
        return await self.query(
            filters={"decision_type": decision_type},
            limit=limit,
            order_by="-created_at",
        )


# ==================== Error Recovery Repositories ====================


class ErrorTrackingRepository(BaseRepository):
    """Repository for error tracking."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ErrorTracking)

    async def get_by_task(self, task_id: str) -> List[ErrorTracking]:
        """Get errors for a task."""
        return await self.query(filters={"task_id": task_id}, order_by="-created_at")

    async def get_by_agent(self, agent_id: str) -> List[ErrorTracking]:
        """Get errors for an agent."""
        return await self.query(filters={"agent_id": agent_id}, order_by="-created_at")

    async def get_by_severity(self, severity: ErrorSeverity) -> List[ErrorTracking]:
        """Get errors by severity."""
        return await self.query(filters={"severity": severity}, order_by="-created_at")

    async def get_unresolved(self) -> List[ErrorTracking]:
        """Get all unresolved errors."""
        return await self.query(filters={"is_resolved": False}, order_by="-created_at")

    async def resolve(
        self, error_id: str, resolution_message: str
    ) -> Optional[ErrorTracking]:
        """Resolve an error."""
        return await self.update(
            error_id,
            is_resolved=True,
            resolution_message=resolution_message,
            resolved_at=datetime.now(timezone.utc),
        )


class CircuitBreakerRepository(BaseRepository):
    """Repository for circuit breakers."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CircuitBreaker)

    async def get_by_service(self, service_name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by service name."""
        try:
            result = await self.session.execute(
                select(CircuitBreaker).where(
                    CircuitBreaker.service_name == service_name
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting circuit breaker for {service_name}: {e}")
            return None

    async def get_by_state(self, state: CircuitState) -> List[CircuitBreaker]:
        """Get circuit breakers by state."""
        return await self.query(filters={"state": state}, order_by="-updated_at")

    async def update_state(
        self, circuit_id: str, state: CircuitState
    ) -> Optional[CircuitBreaker]:
        """Update circuit breaker state."""
        return await self.update(circuit_id, state=state)

    async def increment_failure(self, circuit_id: str) -> Optional[CircuitBreaker]:
        """Increment circuit breaker failure count."""
        circuit = await self.get_by_id(circuit_id)
        if circuit:
            return await self.update(
                circuit_id,
                failure_count=circuit.failure_count + 1,
                last_failure_time=datetime.now(timezone.utc),
            )
        return None

    async def reset_circuit(self, circuit_id: str) -> Optional[CircuitBreaker]:
        """Reset circuit breaker."""
        circuit = await self.get_by_id(circuit_id)
        if circuit:
            return await self.update(
                circuit_id,
                failure_count=0,
                success_count=0,
                state=CircuitState.CLOSED,
            )
        return None


class DeadLetterQueueRepository(BaseRepository):
    """Repository for dead letter queue."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DeadLetterQueue)

    async def get_by_task(self, task_id: str) -> List[DeadLetterQueue]:
        """Get DLQ entries for a task."""
        return await self.query(filters={"task_id": task_id}, order_by="-created_at")

    async def get_by_agent(self, agent_id: str) -> List[DeadLetterQueue]:
        """Get DLQ entries for an agent."""
        return await self.query(filters={"agent_id": agent_id}, order_by="-created_at")

    async def get_unprocessed(self) -> List[DeadLetterQueue]:
        """Get all unprocessed DLQ entries."""
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(DeadLetterQueue)
                .where(
                    and_(
                        DeadLetterQueue.is_processed == False,
                        DeadLetterQueue.next_retry_at <= now,
                    )
                )
                .order_by(DeadLetterQueue.next_retry_at.asc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting unprocessed DLQ entries: {e}")
            return []

    async def mark_processed(self, dlq_id: str) -> Optional[DeadLetterQueue]:
        """Mark DLQ entry as processed."""
        return await self.update(dlq_id, is_processed=True)


# ==================== Cache Repositories ====================


class CacheEntryRepository(BaseRepository):
    """Repository for cache entries."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CacheEntry)

    async def get_by_key(self, cache_key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        try:
            result = await self.session.execute(
                select(CacheEntry).where(CacheEntry.cache_key == cache_key)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting cache entry for {cache_key}: {e}")
            return None

    async def get_by_tier(self, cache_tier: CacheTier) -> List[CacheEntry]:
        """Get cache entries by tier."""
        return await self.query(
            filters={"cache_tier": cache_tier}, order_by="-heat_score"
        )

    async def get_expired(self) -> List[CacheEntry]:
        """Get expired cache entries."""
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(CacheEntry).where(
                    or_(
                        CacheEntry.expires_at < now,
                        CacheEntry.expires_at == None,
                    )
                )
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting expired cache entries: {e}")
            return []

    async def delete_expired(self) -> int:
        """Delete expired cache entries."""
        expired = await self.get_expired()
        ids = [entry.id for entry in expired]
        return await self.delete_bulk(ids)

    async def update_access(self, cache_key: str) -> Optional[CacheEntry]:
        """Update cache entry access."""
        entry = await self.get_by_key(cache_key)
        if entry:
            return await self.update(
                entry.id,
                last_accessed_at=datetime.now(timezone.utc),
                access_count=entry.access_count + 1,
                heat_score=min(100.0, entry.heat_score + 10.0),
            )
        return None


class CacheMetricsRepository(BaseRepository):
    """Repository for cache metrics."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CacheMetrics)

    async def get_by_tier(
        self, cache_tier: CacheTier, limit: Optional[int] = 100
    ) -> List[CacheMetrics]:
        """Get metrics by cache tier."""
        return await self.query(
            filters={"cache_tier": cache_tier}, limit=limit, order_by="-created_at"
        )

    async def get_by_metric_type(
        self, metric_type: str, limit: Optional[int] = 100
    ) -> List[CacheMetrics]:
        """Get metrics by type."""
        return await self.query(
            filters={"metric_type": metric_type}, limit=limit, order_by="-created_at"
        )


# ==================== WebSocket Repositories ====================


class WebSocketConnectionRepository(BaseRepository):
    """Repository for WebSocket connections."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WebSocketConnection)

    async def get_by_user(self, user_id: str) -> List[WebSocketConnection]:
        """Get connections for a user."""
        return await self.query(filters={"user_id": user_id})

    async def get_by_session(
        self, user_id: str, session_id: str
    ) -> Optional[WebSocketConnection]:
        """Get connection for a user session."""
        try:
            result = await self.session.execute(
                select(WebSocketConnection).where(
                    and_(
                        WebSocketConnection.user_id == user_id,
                        WebSocketConnection.session_id == session_id,
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting WebSocket connection: {e}")
            return None

    async def get_active_connections(self) -> List[WebSocketConnection]:
        """Get all active connections."""
        return await self.query(filters={"connection_state": ConnectionState.CONNECTED})

    async def update_state(
        self, connection_id: str, state: ConnectionState
    ) -> Optional[WebSocketConnection]:
        """Update connection state."""
        return await self.update(connection_id, connection_state=state)

    async def update_ping(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Update last ping time."""
        return await self.update(connection_id, last_ping_at=datetime.now(timezone.utc))

    async def update_pong(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Update last pong time."""
        return await self.update(connection_id, last_pong_at=datetime.now(timezone.utc))


class WebSocketMessageRepository(BaseRepository):
    """Repository for WebSocket messages."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WebSocketMessage)

    async def get_by_connection(
        self, connection_id: str, limit: Optional[int] = 100
    ) -> List[WebSocketMessage]:
        """Get messages for a connection."""
        return await self.query(
            filters={"connection_id": connection_id},
            limit=limit,
            order_by="-created_at",
        )

    async def get_unsent(self) -> List[WebSocketMessage]:
        """Get all unsent messages."""
        return await self.query(filters={"is_sent": False}, order_by="-created_at")

    async def mark_sent(self, message_id: str) -> Optional[WebSocketMessage]:
        """Mark message as sent."""
        return await self.update(message_id, is_sent=True)

    async def mark_received(self, message_id: str) -> Optional[WebSocketMessage]:
        """Mark message as received."""
        return await self.update(message_id, is_received=True)


# ==================== MCP Protocol Repositories ====================


class MCPOperationRepository(BaseRepository):
    """Repository for MCP operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MCPOperation)

    async def get_by_operation_id(self, operation_id: str) -> Optional[MCPOperation]:
        """Get operation by ID."""
        try:
            result = await self.session.execute(
                select(MCPOperation).where(MCPOperation.operation_id == operation_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting MCP operation {operation_id}: {e}")
            return None

    async def get_by_method(
        self, method: str, limit: Optional[int] = 100
    ) -> List[MCPOperation]:
        """Get operations by method."""
        return await self.query(
            filters={"method": method}, limit=limit, order_by="-created_at"
        )

    async def get_by_status(
        self, status: str, limit: Optional[int] = 100
    ) -> List[MCPOperation]:
        """Get operations by status."""
        return await self.query(
            filters={"status": status}, limit=limit, order_by="-created_at"
        )

    async def complete_operation(
        self, operation_id: str, result: Dict[str, Any], execution_time_ms: int
    ) -> Optional[MCPOperation]:
        """Complete an MCP operation."""
        return await self.update(
            operation_id,
            result=result,
            execution_time_ms=execution_time_ms,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )

    async def fail_operation(
        self, operation_id: str, error: Dict[str, Any]
    ) -> Optional[MCPOperation]:
        """Fail an MCP operation."""
        return await self.update(
            operation_id,
            error=error,
            status="error",
            completed_at=datetime.now(timezone.utc),
        )


# ==================== Model Forge Repositories ====================


class ModelRepository(BaseRepository):
    """Repository for AI models."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Model)

    async def get_by_provider(self, provider: str) -> List[Model]:
        """Get models by provider."""
        return await self.query(filters={"provider": provider})

    async def get_by_type(self, model_type: str) -> List[Model]:
        """Get models by type."""
        return await self.query(filters={"model_type": model_type})

    async def get_active_models(self) -> List[Model]:
        """Get all active models."""
        return await self.query(filters={"is_active": True})

    async def update_performance(
        self, model_id: str, latency_ms: int, success_rate: float
    ) -> Optional[Model]:
        """Update model performance metrics."""
        model = await self.get_by_id(model_id)
        if model:
            # Weighted average
            new_latency = (model.average_latency_ms or 0) * 0.9 + latency_ms * 0.1
            new_success_rate = model.success_rate * 0.9 + success_rate * 0.1
            return await self.update(
                model_id,
                average_latency_ms=int(new_latency),
                success_rate=new_success_rate,
            )
        return None


class ModelUsageRepository(BaseRepository):
    """Repository for model usage tracking."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ModelUsage)

    async def get_by_model(
        self, model_id: str, limit: Optional[int] = 100
    ) -> List[ModelUsage]:
        """Get usage for a model."""
        return await self.query(
            filters={"model_id": model_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_user(
        self, user_id: str, limit: Optional[int] = 100
    ) -> List[ModelUsage]:
        """Get usage for a user."""
        return await self.query(
            filters={"user_id": user_id}, limit=limit, order_by="-created_at"
        )

    async def get_cached_usage(self) -> List[ModelUsage]:
        """Get all cached usage."""
        return await self.query(filters={"is_cached": True}, order_by="-created_at")

    async def get_recent(
        self, hours: int = 24, limit: Optional[int] = 100
    ) -> List[ModelUsage]:
        """Get recent model usage."""
        try:
            cutoff = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            result = await self.session.execute(
                select(ModelUsage)
                .where(ModelUsage.created_at >= cutoff)
                .order_by(ModelUsage.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting recent model usage: {e}")
            return []


# ==================== Sentinel Security Repositories ====================


class SecurityEventRepository(BaseRepository):
    """Repository for security events."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SecurityEvent)

    async def get_by_type(
        self, event_type: str, limit: Optional[int] = 100
    ) -> List[SecurityEvent]:
        """Get events by type."""
        return await self.query(
            filters={"event_type": event_type}, limit=limit, order_by="-created_at"
        )

    async def get_by_severity(
        self, severity: str, limit: Optional[int] = 100
    ) -> List[SecurityEvent]:
        """Get events by severity."""
        return await self.query(
            filters={"severity": severity}, limit=limit, order_by="-created_at"
        )

    async def get_by_user(
        self, user_id: str, limit: Optional[int] = 100
    ) -> List[SecurityEvent]:
        """Get events for a user."""
        return await self.query(
            filters={"user_id": user_id}, limit=limit, order_by="-created_at"
        )

    async def get_unresolved(self) -> List[SecurityEvent]:
        """Get all unresolved security events."""
        return await self.query(filters={"is_resolved": False}, order_by="-created_at")

    async def resolve(
        self, event_id: str, resolved_by: str, resolution_message: str
    ) -> Optional[SecurityEvent]:
        """Resolve a security event."""
        return await self.update(
            event_id,
            is_resolved=True,
            resolved_by=resolved_by,
            resolution_message=resolution_message,
            resolved_at=datetime.now(timezone.utc),
        )


class SecurityPolicyRepository(BaseRepository):
    """Repository for security policies."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SecurityPolicy)

    async def get_by_type(self, policy_type: str) -> List[SecurityPolicy]:
        """Get policies by type."""
        return await self.query(
            filters={"policy_type": policy_type, "is_active": True},
            order_by="-priority",
        )

    async def get_active_policies(self) -> List[SecurityPolicy]:
        """Get all active policies."""
        return await self.query(filters={"is_active": True}, order_by="-priority")


# ==================== Audit Repositories ====================


class AuditLogRepository(BaseRepository):
    """Repository for audit logs."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    async def get_by_user(
        self, user_id: str, limit: Optional[int] = 100
    ) -> List[AuditLog]:
        """Get audit logs for a user."""
        return await self.query(
            filters={"user_id": user_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_action(
        self, action: str, limit: Optional[int] = 100
    ) -> List[AuditLog]:
        """Get audit logs by action."""
        return await self.query(
            filters={"action": action}, limit=limit, order_by="-created_at"
        )

    async def get_by_resource(
        self, resource_type: str, resource_id: str, limit: Optional[int] = 100
    ) -> List[AuditLog]:
        """Get audit logs by resource."""
        return await self.query(
            filters={"resource_type": resource_type, "resource_id": resource_id},
            limit=limit,
            order_by="-created_at",
        )

    async def get_recent(
        self, hours: int = 24, limit: Optional[int] = 100
    ) -> List[AuditLog]:
        """Get recent audit logs."""
        try:
            cutoff = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            result = await self.session.execute(
                select(AuditLog)
                .where(AuditLog.created_at >= cutoff)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting recent audit logs: {e}")
            return []


# ==================== Skills System Repositories ====================


class SkillRepository(BaseRepository):
    """Repository for skills."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Skill)

    async def get_by_type(self, skill_type: str) -> List[Skill]:
        """Get skills by type."""
        return await self.query(filters={"skill_type": skill_type, "is_active": True})

    async def get_active_skills(self) -> List[Skill]:
        """Get all active skills."""
        return await self.query(filters={"is_active": True})


class AgentSkillRepository(BaseRepository):
    """Repository for agent-skill relationships."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AgentSkill)

    async def get_by_agent(self, agent_id: str) -> List[AgentSkill]:
        """Get skills for an agent."""
        return await self.query(
            filters={"agent_id": agent_id, "is_enabled": True},
            order_by="-proficiency_level",
        )

    async def get_by_skill(self, skill_id: str) -> List[AgentSkill]:
        """Get agents that have a skill."""
        return await self.query(
            filters={"skill_id": skill_id, "is_enabled": True},
            order_by="-proficiency_level",
        )

    async def update_proficiency(
        self, agent_id: str, skill_id: str, proficiency_level: int
    ) -> Optional[AgentSkill]:
        """Update agent's skill proficiency."""
        try:
            result = await self.session.execute(
                select(AgentSkill).where(
                    and_(
                        AgentSkill.agent_id == agent_id,
                        AgentSkill.skill_id == skill_id,
                    )
                )
            )
            agent_skill = result.scalar_one_or_none()
            if agent_skill:
                return await self.update(
                    agent_skill.id, proficiency_level=proficiency_level
                )
            return None
        except Exception as e:
            logger.error(f"Error updating skill proficiency: {e}")
            return None


class SkillExecutionRepository(BaseRepository):
    """Repository for skill executions."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SkillExecution)

    async def get_by_skill(
        self, skill_id: str, limit: Optional[int] = 100
    ) -> List[SkillExecution]:
        """Get executions for a skill."""
        return await self.query(
            filters={"skill_id": skill_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_agent(
        self, agent_id: str, limit: Optional[int] = 100
    ) -> List[SkillExecution]:
        """Get executions for an agent."""
        return await self.query(
            filters={"agent_id": agent_id}, limit=limit, order_by="-created_at"
        )

    async def get_by_task(self, task_id: str) -> List[SkillExecution]:
        """Get executions for a task."""
        return await self.query(filters={"task_id": task_id}, order_by="-created_at")

    async def get_by_status(
        self, status: str, limit: Optional[int] = 100
    ) -> List[SkillExecution]:
        """Get executions by status."""
        return await self.query(
            filters={"status": status}, limit=limit, order_by="-created_at"
        )

    async def complete_execution(
        self, execution_id: str, output_results: Dict[str, Any], execution_time_ms: int
    ) -> Optional[SkillExecution]:
        """Complete a skill execution."""
        return await self.update(
            execution_id,
            output_results=output_results,
            execution_time_ms=execution_time_ms,
            status="success",
        )

    async def fail_execution(
        self, execution_id: str, error_message: str
    ) -> Optional[SkillExecution]:
        """Fail a skill execution."""
        return await self.update(
            execution_id,
            error_message=error_message,
            status="error",
        )


# ==================== Repository Manager ====================


class RepositoryManager:
    """
    High-level manager for all repositories.

    Provides unified access to all repository instances.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository manager.

        Args:
            session: Database session
        """
        self.session = session

        # User repositories
        self.users = UserRepository(session)

        # Memory system repositories
        self.memory_m0 = MemoryM0Repository(session)
        self.memory_m1 = MemoryM1Repository(session)
        self.memory_m2 = MemoryM2Repository(session)
        self.memory_m3 = MemoryM3Repository(session)
        self.memory_m4 = MemoryM4Repository(session)

        # Agent system repositories
        self.agents = AgentRepository(session)
        self.tasks = TaskRepository(session)
        self.agent_performance = AgentPerformanceRepository(session)

        # Decision engine repositories
        self.decision_rules = DecisionRuleRepository(session)
        self.decision_logs = DecisionLogRepository(session)

        # Error recovery repositories
        self.error_tracking = ErrorTrackingRepository(session)
        self.circuit_breakers = CircuitBreakerRepository(session)
        self.dead_letter_queue = DeadLetterQueueRepository(session)

        # Cache repositories
        self.cache_entries = CacheEntryRepository(session)
        self.cache_metrics = CacheMetricsRepository(session)

        # WebSocket repositories
        self.websocket_connections = WebSocketConnectionRepository(session)
        self.websocket_messages = WebSocketMessageRepository(session)

        # MCP protocol repositories
        self.mcp_operations = MCPOperationRepository(session)

        # Model Forge repositories
        self.models = ModelRepository(session)
        self.model_usage = ModelUsageRepository(session)

        # Sentinel Security repositories
        self.security_events = SecurityEventRepository(session)
        self.security_policies = SecurityPolicyRepository(session)

        # Audit repositories
        self.audit_logs = AuditLogRepository(session)

        # Skills system repositories
        self.skills = SkillRepository(session)
        self.agent_skills = AgentSkillRepository(session)
        self.skill_executions = SkillExecutionRepository(session)

    async def commit(self) -> None:
        """Commit all changes."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback all changes."""
        await self.session.rollback()

    async def close(self) -> None:
        """Close database session."""
        await self.session.close()


# ==================== Example Usage ====================


async def example_usage():
    """Example usage of repository layer."""
    from .models import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        repos = RepositoryManager(session)

        # Create a user
        user = await repos.users.create(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
        )
        print(f"Created user: {user.username}")

        # Get user by username
        user = await repos.users.get_by_username("test_user")
        print(f"Found user: {user.username}")

        # Create an agent
        agent = await repos.agents.create(
            name="Test Agent",
            type="researcher",
            description="A test research agent",
            state=AgentState.IDLE,
        )
        print(f"Created agent: {agent.name}")

        # Create a task
        task = await repos.tasks.create(
            agent_id=agent.id,
            user_id=user.id,
            title="Test Task",
            description="A test task",
            task_type="research",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
        )
        print(f"Created task: {task.title}")

        # Get pending tasks
        pending_tasks = await repos.tasks.get_pending_tasks()
        print(f"Found {len(pending_tasks)} pending tasks")

        # Commit all changes
        await repos.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
