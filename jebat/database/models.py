"""Database ORM models for all JEBAT subsystems."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MemoryLayer(str, enum.Enum):
    M0 = "M0"
    M0_SENSORY = "M0"
    M1 = "M1"
    M1_EPISODIC = "M1"
    M2 = "M2"
    M2_SEMANTIC = "M2"
    M3 = "M3"
    M3_CONCEPTUAL = "M3"
    M4 = "M4"
    M4_PERMANENT = "M4"


class AgentState(str, enum.Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    TERMINATED = "TERMINATED"


class TaskPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


@dataclass
class User:
    id: uuid4 = field(default_factory=uuid4)
    username: str = ""
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    is_active: bool = True
    is_admin: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Agent:
    id: uuid4 = field(default_factory=uuid4)
    name: str = ""
    type: str = ""
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    state: AgentState = AgentState.IDLE
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Task:
    id: uuid4 = field(default_factory=uuid4)
    agent_id: uuid4 = field(default_factory=uuid4)
    user_id: uuid4 = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    task_type: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemoryM0:
    id: uuid4 = field(default_factory=uuid4)
    user_id: uuid4 = field(default_factory=uuid4)
    session_id: uuid4 = field(default_factory=uuid4)
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    heat_score: float = 100.0
    access_count: int = 0
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemoryM1:
    id: uuid4 = field(default_factory=uuid4)
    user_id: uuid4 = field(default_factory=uuid4)
    session_id: uuid4 = field(default_factory=uuid4)
    content: str = ""
    embedding: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    heat_score: float = 80.0
    access_count: int = 0
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemoryM2:
    id: uuid4 = field(default_factory=uuid4)
    user_id: uuid4 = field(default_factory=uuid4)
    content: str = ""
    embedding: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    heat_score: float = 60.0
    access_count: int = 0
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemoryM3:
    id: uuid4 = field(default_factory=uuid4)
    user_id: uuid4 = field(default_factory=uuid4)
    content: str = ""
    summary: str = ""
    embedding: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    heat_score: float = 40.0
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemoryM4:
    id: uuid4 = field(default_factory=uuid4)
    user_id: uuid4 = field(default_factory=uuid4)
    content: str = ""
    summary: str = ""
    embedding: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    heat_score: float = 20.0
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    archived_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime(9999, 12, 31, tzinfo=timezone.utc))
