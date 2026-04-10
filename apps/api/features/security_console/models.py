from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TargetType(str, Enum):
    WEB = "web"
    API = "api"
    HOST = "host"
    CONTAINER = "container"
    WORKSPACE = "workspace"


class SessionStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Target(BaseModel):
    id: str = Field(default_factory=lambda: f"target_{uuid4().hex[:10]}")
    name: str
    type: TargetType
    scope: str
    tags: list[str] = Field(default_factory=list)
    engagement_mode: str = "manual"
    allowed_tools: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class SecuritySession(BaseModel):
    id: str = Field(default_factory=lambda: f"session_{uuid4().hex[:10]}")
    target_id: str
    status: SessionStatus = SessionStatus.IDLE
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None
    operator: str = "local-operator"
    provider: str = "ollama"
    model: str = "qwen2.5-coder:7b"
    notes: str = ""


class CommandRun(BaseModel):
    id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:10]}")
    session_id: str
    tool: str
    command: str
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: f"finding_{uuid4().hex[:10]}")
    session_id: str
    target_id: str
    title: str
    severity: Severity = Severity.MEDIUM
    confidence: float = 0.5
    category: str = "general"
    cwe: str | None = None
    owasp: str | None = None
    asset: str | None = None
    evidence_summary: str = ""
    remediation: str = ""
    source_tool: str = "manual"
    status: str = "open"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class CopilotMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:10]}")
    session_id: str
    role: str
    provider: str
    model: str
    content: str
    context_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class CreateTargetRequest(BaseModel):
    name: str
    type: TargetType
    scope: str
    tags: list[str] = Field(default_factory=list)
    engagement_mode: str = "manual"
    allowed_tools: list[str] = Field(default_factory=list)


class CreateSessionRequest(BaseModel):
    target_id: str
    operator: str = "local-operator"
    provider: str = "ollama"
    model: str = "qwen2.5-coder:7b"
    notes: str = ""


class CreateRunRequest(BaseModel):
    tool: str
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    status: RunStatus = RunStatus.COMPLETE


class ExecuteCommandRequest(BaseModel):
    tool: str
    command: str
    cwd: str | None = None
    timeout_seconds: int = 120


class CreateFindingRequest(BaseModel):
    title: str
    severity: Severity = Severity.MEDIUM
    confidence: float = 0.5
    category: str = "general"
    cwe: str | None = None
    owasp: str | None = None
    asset: str | None = None
    evidence_summary: str = ""
    remediation: str = ""
    source_tool: str = "manual"
    status: str = "open"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CopilotChatRequest(BaseModel):
    message: str
    mode: str = "suggest_next_step"
    context: dict[str, Any] = Field(default_factory=dict)


class CopilotChatResponse(BaseModel):
    session: SecuritySession
    provider: str
    model: str
    response: str
    messages: list[CopilotMessage]


class SecurityConsoleSnapshot(BaseModel):
    targets: list[Target]
    sessions: list[SecuritySession]
    findings: list[Finding]
    runs: list[CommandRun]
