# ==================== JEBAT AI System - Database Models ====================
# Version: 1.0.0
# SQLAlchemy ORM models for all JEBAT database tables
#
# This module provides ORM models for:
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

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, INET, UUID, array
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func as sql_func
from sqlalchemy.types import ARRAY as SQLArray

# ==================== Base and Engine Setup ====================


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Database URL should be configured from environment
DATABASE_URL = (
    "postgresql+asyncpg://jebat:jebat_secure_password@localhost:5432/jebat_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncAttrs,
    expire_on_commit=False,
    autoflush=False,
)


# ==================== Enum Types ====================


class MemoryLayer(str, PyEnum):
    """Memory layer enumeration"""

    M0 = "M0"  # Working Memory (5 min retention)
    M1 = "M1"  # Short-term Memory (24 hours)
    M2 = "M2"  # Medium-term Memory (7 days)
    M3 = "M3"  # Long-term Memory (90 days)
    M4 = "M4"  # Permanent Memory (indefinite)


class AgentState(str, PyEnum):
    """Agent state enumeration"""

    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    TERMINATED = "TERMINATED"


class TaskPriority(str, PyEnum):
    """Task priority enumeration"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


class TaskStatus(str, PyEnum):
    """Task status enumeration"""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class ErrorSeverity(str, PyEnum):
    """Error severity enumeration"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class CacheTier(str, PyEnum):
    """Cache tier enumeration"""

    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"


class CircuitState(str, PyEnum):
    """Circuit breaker state enumeration"""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class ConnectionState(str, PyEnum):
    """WebSocket connection state enumeration"""

    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"


# ==================== Memory System Models ====================


class User(Base):
    """User account model"""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memory_m0_entries: Mapped[List["MemoryM0"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memory_m1_entries: Mapped[List["MemoryM1"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memory_m2_entries: Mapped[List["MemoryM2"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memory_m3_entries: Mapped[List["MemoryM3"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memory_m4_entries: Mapped[List["MemoryM4"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    websocket_connections: Mapped[List["WebSocketConnection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    security_events: Mapped[List["SecurityEvent"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    model_usage: Mapped[List["ModelUsage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    skill_executions: Mapped[List["SkillExecution"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class MemoryM0(Base):
    """M0: Working Memory - Immediate access, very short retention (5 minutes)"""

    __tablename__ = "memory_m0"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    heat_score: Mapped[float] = mapped_column(Float, default=100.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.cast("5 minutes", sqlalchemy.interval),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memory_m0_entries")

    # Indexes
    __table_args__ = (
        Index("idx_memory_m0_user_session", "user_id", "session_id"),
        Index(
            "idx_memory_m0_heat_score",
            "heat_score",
            postgresql_ops={"heat_score": "DESC"},
        ),
        Index("idx_memory_m0_expires_at", "expires_at"),
    )


class MemoryM1(Base):
    """M1: Short-term Memory - Recent conversations, temporary context (24 hours)"""

    __tablename__ = "memory_m1"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float, dimensions=1536)
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    heat_score: Mapped[float] = mapped_column(Float, default=80.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.cast("24 hours", sqlalchemy.interval),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memory_m1_entries")

    # Indexes
    __table_args__ = (
        Index("idx_memory_m1_user_session", "user_id", "session_id"),
        Index(
            "idx_memory_m1_heat_score",
            "heat_score",
            postgresql_ops={"heat_score": "DESC"},
        ),
        Index("idx_memory_m1_expires_at", "expires_at"),
    )


class MemoryM2(Base):
    """M2: Medium-term Memory - Learning patterns, preferences (7 days)"""

    __tablename__ = "memory_m2"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float, dimensions=1536)
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    heat_score: Mapped[float] = mapped_column(Float, default=60.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.cast("7 days", sqlalchemy.interval),
    )
    compressed: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memory_m2_entries")

    # Indexes
    __table_args__ = (
        Index("idx_memory_m2_user", "user_id"),
        Index(
            "idx_memory_m2_heat_score",
            "heat_score",
            postgresql_ops={"heat_score": "DESC"},
        ),
        Index("idx_memory_m2_expires_at", "expires_at"),
    )


class MemoryM3(Base):
    """M3: Long-term Memory - Permanent knowledge, experiences (90 days)"""

    __tablename__ = "memory_m3"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float, dimensions=1536)
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    heat_score: Mapped[float] = mapped_column(Float, default=40.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.cast("90 days", sqlalchemy.interval),
    )
    compressed: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    tags: Mapped[List[str]] = mapped_column(SQLArray(String), default=lambda: [])

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memory_m3_entries")

    # Indexes
    __table_args__ = (
        Index("idx_memory_m3_user", "user_id"),
        Index(
            "idx_memory_m3_heat_score",
            "heat_score",
            postgresql_ops={"heat_score": "DESC"},
        ),
        Index("idx_memory_m3_expires_at", "expires_at"),
        Index("idx_memory_m3_tags", "tags", postgresql_using="gin"),
    )


class MemoryM4(Base):
    """M4: Permanent Memory - Archived, immutable records (indefinite)"""

    __tablename__ = "memory_m4"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float, dimensions=1536)
    )
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    heat_score: Mapped[float] = mapped_column(Float, default=20.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.parse_iso8601("9999-12-31 23:59:59.999999+00"),
    )
    compressed: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    tags: Mapped[List[str]] = mapped_column(SQLArray(String), default=lambda: [])
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memory_m4_entries")

    # Indexes
    __table_args__ = (
        Index("idx_memory_m4_user", "user_id"),
        Index("idx_memory_m4_tags", "tags", postgresql_using="gin"),
        Index(
            "idx_memory_m4_archived_at",
            "archived_at",
            postgresql_ops={"archived_at": "DESC"},
        ),
    )


# ==================== Agent System Models ====================


class Agent(Base):
    """Agent configuration and state model"""

    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # 'researcher', 'analyst', 'executor', 'memory', 'custom'
    description: Mapped[Optional[str]] = mapped_column(Text)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    capabilities: Mapped[List[str]] = mapped_column(JSON, default=lambda: [])
    state: Mapped[AgentState] = mapped_column(
        ENUM(AgentState, name="agent_state", create_type=True), default=AgentState.IDLE
    )
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, default=5)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[List["AgentPerformance"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    error_tracking: Mapped[List["ErrorTracking"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    agent_skills: Mapped[List["AgentSkill"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    skill_executions: Mapped[List["SkillExecution"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    dead_letter_queue: Mapped[List["DeadLetterQueue"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_agents_type", "type"),
        Index("idx_agents_state", "state"),
        Index("idx_agents_active", "is_active", postgresql_where=is_active == True),
    )


class AgentPerformance(Base):
    """Agent performance metrics - TimescaleDB hypertable"""

    __tablename__ = "agent_performance"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    agent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    metric_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'execution_time', 'success_rate', 'error_count', 'memory_usage', 'cpu_usage'
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="performance_metrics")
    task: Mapped[Optional["Task"]] = relationship()


class Task(Base):
    """Task execution model"""

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    agent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    parent_task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    priority: Mapped[TaskPriority] = mapped_column(
        ENUM(TaskPriority, name="task_priority", create_type=True),
        default=TaskPriority.MEDIUM,
    )
    status: Mapped[TaskStatus] = mapped_column(
        ENUM(TaskStatus, name="task_status", create_type=True),
        default=TaskStatus.PENDING,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tasks")
    agent: Mapped["Agent"] = relationship(back_populates="tasks")
    parent_task: Mapped[Optional["Task"]] = relationship("Task", remote_side=[id])
    child_tasks: Mapped[List["Task"]] = relationship(
        "Task", cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[List["AgentPerformance"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    decision_logs: Mapped[List["DecisionLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    error_tracking: Mapped[List["ErrorTracking"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    dead_letter_queue: Mapped[List["DeadLetterQueue"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    model_usage: Mapped[List["ModelUsage"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    skill_executions: Mapped[List["SkillExecution"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_priority", "priority"),
        Index("idx_tasks_type", "task_type"),
        Index("idx_tasks_parent", "parent_task_id"),
    )


# ==================== Decision Engine Models ====================


class DecisionRule(Base):
    """Decision engine rule model"""

    __tablename__ = "decision_rules"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    rule_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'agent_selection', 'task_routing', 'priority_assignment', 'cache_strategy'
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    actions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    decision_logs: Mapped[List["DecisionLog"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_decision_rules_type", "rule_type"),
        Index(
            "idx_decision_rules_active", "is_active", postgresql_where=is_active == True
        ),
    )


class DecisionLog(Base):
    """Decision engine execution log"""

    __tablename__ = "decision_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    agent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL")
    )
    rule_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_rules.id", ondelete="SET NULL")
    )
    decision_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    output_decision: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    task: Mapped[Optional["Task"]] = relationship(back_populates="decision_logs")
    agent: Mapped[Optional["Agent"]] = relationship()
    rule: Mapped[Optional["DecisionRule"]] = relationship(
        back_populates="decision_logs"
    )


# ==================== Error Recovery Models ====================


class ErrorTracking(Base):
    """Error tracking and logging model"""

    __tablename__ = "error_tracking"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    agent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL")
    )
    error_type: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    error_stack: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[ErrorSeverity] = mapped_column(
        ENUM(ErrorSeverity, name="error_severity", create_type=True),
        default=ErrorSeverity.ERROR,
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_message: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    task: Mapped[Optional["Task"]] = relationship(back_populates="error_tracking")
    agent: Mapped["Agent"] = relationship(back_populates="error_tracking")

    # Indexes
    __table_args__ = (
        Index("idx_error_tracking_resolved", "is_resolved"),
        Index("idx_error_tracking_severity", "severity"),
    )


class CircuitBreaker(Base):
    """Circuit breaker state model"""

    __tablename__ = "circuit_breakers"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[CircuitState] = mapped_column(
        ENUM(CircuitState, name="circuit_state", create_type=True),
        default=CircuitState.CLOSED,
        index=True,
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_threshold: Mapped[int] = mapped_column(Integer, default=5)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    success_threshold: Mapped[int] = mapped_column(Integer, default=2)
    last_failure_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    open_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    half_open_max_calls: Mapped[int] = mapped_column(Integer, default=3)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeadLetterQueue(Base):
    """Dead letter queue for failed tasks"""

    __tablename__ = "dead_letter_queue"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    agent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL")
    )
    original_message: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    task: Mapped[Optional["Task"]] = relationship(back_populates="dead_letter_queue")
    agent: Mapped["Agent"] = relationship(back_populates="dead_letter_queue")

    # Indexes
    __table_args__ = (Index("idx_dead_letter_queue_processed", "is_processed"),)


# ==================== Cache Models ====================


class CacheEntry(Base):
    """Cache entry model for multi-tier caching"""

    __tablename__ = "cache_entries"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    cache_key: Mapped[str] = mapped_column(
        String(500), unique=True, nullable=False, index=True
    )
    cache_value: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    cache_tier: Mapped[CacheTier] = mapped_column(
        ENUM(CacheTier, name="cache_tier", create_type=True), nullable=False, index=True
    )
    heat_score: Mapped[float] = mapped_column(Float, default=100.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    ttl_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_cache_entries_heat",
            "heat_score",
            postgresql_ops={"heat_score": "DESC"},
        ),
    )


class CacheMetrics(Base):
    """Cache metrics - TimescaleDB hypertable"""

    __tablename__ = "cache_metrics"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    cache_tier: Mapped[CacheTier] = mapped_column(
        ENUM(CacheTier, name="cache_tier", create_type=True), nullable=False
    )
    metric_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'hits', 'misses', 'evictions', 'size'
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


# ==================== WebSocket Models ====================


class WebSocketConnection(Base):
    """WebSocket connection tracking model"""

    __tablename__ = "websocket_connections"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    connection_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    connection_state: Mapped[ConnectionState] = mapped_column(
        ENUM(ConnectionState, name="connection_state", create_type=True),
        default=ConnectionState.CONNECTING,
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_ping_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_pong_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})

    # Relationships
    user: Mapped["User"] = relationship(back_populates="websocket_connections")
    messages: Mapped[List["WebSocketMessage"]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_websocket_connections_session", "session_id"),
        Index("idx_websocket_connections_state", "connection_state"),
    )


class WebSocketMessage(Base):
    """WebSocket message tracking model"""

    __tablename__ = "websocket_messages"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    connection_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("websocket_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'request', 'response', 'notification', 'error'
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_received: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    connection: Mapped["WebSocketConnection"] = relationship(back_populates="messages")


# ==================== MCP Protocol Models ====================


class MCPOperation(Base):
    """MCP protocol server operation model"""

    __tablename__ = "mcp_operations"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    operation_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    method: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # JSON-RPC 2.0 method names
    params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'pending', 'processing', 'completed', 'error'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ==================== Model Forge Models ====================


class Model(Base):
    """AI model configuration model"""

    __tablename__ = "models"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    model_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # 'openai', 'anthropic', 'ollama', 'custom'
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'chat', 'completion', 'embedding', 'image'
    api_endpoint: Mapped[Optional[str]] = mapped_column(Text)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    supports_function_calling: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_per_1k_tokens: Mapped[Optional[float]] = mapped_column(Float)
    average_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    model_usage: Mapped[List["ModelUsage"]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_models_provider", "provider"),
        Index("idx_models_type", "model_type"),
        Index("idx_models_active", "is_active", postgresql_where=is_active == True),
    )


class ModelUsage(Base):
    """Model usage tracking - TimescaleDB hypertable"""

    __tablename__ = "model_usage"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    model_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    cost: Mapped[Optional[float]] = mapped_column(Float)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    is_cached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    model: Mapped["Model"] = relationship(back_populates="model_usage")
    task: Mapped[Optional["Task"]] = relationship(back_populates="model_usage")
    user: Mapped["User"] = relationship(back_populates="model_usage")


# ==================== Sentinel Security Models ====================


class SecurityEvent(Base):
    """Security event tracking model"""

    __tablename__ = "security_events"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # 'anomaly_detected', 'threat_blocked', 'policy_violation', 'unauthorized_access'
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'low', 'medium', 'high', 'critical'
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        back_populates="security_events", foreign_keys=[user_id]
    )
    resolver: Mapped[Optional["User"]] = relationship(foreign_keys=[resolved_by])

    # Indexes
    __table_args__ = (
        Index("idx_security_events_type", "event_type"),
        Index("idx_security_events_severity", "severity"),
        Index("idx_security_events_resolved", "is_resolved"),
    )


class SecurityPolicy(Base):
    """Security policy configuration model"""

    __tablename__ = "security_policies"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    policy_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    policy_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'rate_limiting', 'content_filtering', 'access_control', 'data_retention'
    rules: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    actions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_security_policies_type", "policy_type"),
        Index(
            "idx_security_policies_active",
            "is_active",
            postgresql_where=is_active == True,
        ),
    )


# ==================== Audit Models ====================


class AuditLog(Base):
    """Audit log model for tracking all system changes"""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
    )


# ==================== Skills System Models ====================


class Skill(Base):
    """Skill model for agent capabilities"""

    __tablename__ = "skills"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    skill_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    skill_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'search', 'analyze', 'execute', 'remember', 'custom'
    description: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    capabilities: Mapped[List[str]] = mapped_column(JSON, default=lambda: [])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent_skills: Mapped[List["AgentSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    skill_executions: Mapped[List["SkillExecution"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_skills_type", "skill_type"),
        Index("idx_skills_active", "is_active", postgresql_where=is_active == True),
    )


class AgentSkill(Base):
    """Agent-skill relationship model with proficiency levels"""

    __tablename__ = "agent_skills"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    agent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    proficiency_level: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="agent_skills")
    skill: Mapped["Skill"] = relationship(back_populates="agent_skills")


class SkillExecution(Base):
    """Skill execution tracking model"""

    __tablename__ = "skill_executions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    skill_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL")
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    input_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    output_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'success', 'error', 'timeout'
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    skill: Mapped["Skill"] = relationship(back_populates="skill_executions")
    agent: Mapped["Agent"] = relationship(back_populates="skill_executions")
    task: Mapped[Optional["Task"]] = relationship(back_populates="skill_executions")
    user: Mapped[Optional["User"]] = relationship(back_populates="skill_executions")


# ==================== Database Session Helper ====================


async def get_db():
    """
    Dependency for getting async database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==================== Utility Functions ====================


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def init_db():
    """Initialize database with tables and initial data."""
    await create_tables()
    # Add any initial data here if needed


# ==================== Example Usage ====================


async def example_usage():
    """Example usage of database models."""
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Create a new user
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Query users
        result = await session.execute(select(User).where(User.username == "test_user"))
        user = result.scalar_one()
        print(f"Found user: {user.username}")

        # Create an agent
        agent = Agent(
            name="Test Agent",
            type="researcher",
            description="A test research agent",
            state=AgentState.IDLE,
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        print(f"Created agent: {agent.name} with state {agent.state}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
