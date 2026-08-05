"""JEBAT SDK — Request/Response Models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ─── Enums ────────────────────────────────────────────────────────────

class ThinkingMode(str, Enum):
    FAST = "fast"
    DELIBERATE = "deliberate"
    DEEP = "deep"
    STRATEGIC = "strategic"
    CREATIVE = "creative"
    CRITICAL = "critical"
    CUSTOM = "custom"


class MemoryLayer(str, Enum):
    M0 = "M0"  # Sensory
    M1 = "M1"  # Working
    M2 = "M2"  # Episodic
    M3 = "M3"  # Semantic
    M4 = "M4"  # Procedural


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanProfile(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    FULL = "full"
    VULNERABILITY = "vulnerability"


class ScanStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SandboxLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"


class MCPTransport(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    STREAMABLE_HTTP = "streamable-http"


# ─── Core Chat ────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompleteRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = "jebat-core-v8.2"
    mode: str = "deliberate"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = "auto"
    stream: bool = False
    metadata: dict[str, Any] | None = None


class ChatCompleteResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int]
    system_fingerprint: str | None = None


class ChatStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict[str, Any]]
    system_fingerprint: str | None = None


# ─── Memory ───────────────────────────────────────────────────────────

class MemoryQueryRequest(BaseModel):
    query: str
    layer: str = "all"
    limit: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: dict[str, Any] | None = None
    include_metadata: bool = True


class MemoryQueryResponse(BaseModel):
    results: list[dict[str, Any]]
    total: int
    query_time_ms: float


class MemoryAddRequest(BaseModel):
    content: str
    layer: str
    metadata: dict[str, Any] | None = None
    ttl_seconds: int | None = None


class MemoryAddResponse(BaseModel):
    id: str
    layer: str
    created_at: datetime


# ─── Agents ──────────────────────────────────────────────────────────

class AgentCreateRequest(BaseModel):
    name: str
    description: str
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    thinking_mode: str = "deliberate"
    memory_layers: list[str] = Field(default_factory=lambda: ["M2", "M3"])
    max_iterations: int = Field(default=10, ge=1, le=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class AgentCreateResponse(BaseModel):
    id: str
    name: str
    status: str = "pending"
    created_at: datetime


class AgentRunRequest(BaseModel):
    input: str
    context: dict[str, Any] | None = None
    files: list[str] | None = None
    stream: bool = False


class AgentRunResponse(BaseModel):
    run_id: str
    agent_id: str
    status: str
    output: str | None = None
    error: str | None = None
    steps: list[dict[str, Any]] | None = None
    started_at: datetime
    completed_at: datetime | None = None
    usage: dict[str, int] | None = None


# ─── Tools ────────────────────────────────────────────────────────────

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str] = Field(default_factory=list)


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any]
    trace_id: str | None = None


class ToolCallResponse(BaseModel):
    result: Any
    error: str | None = None


# ─── Sentinel (Security) ─────────────────────────────────────────────

class ScanRequest(BaseModel):
    target: str
    profile: str = "standard"
    config: dict[str, Any] | None = None


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    target: str
    profile: str
    created_at: datetime


class CVEResult(BaseModel):
    cve_id: str
    severity: str
    cvss_score: float
    description: str
    affected_versions: list[str]
    fixed_versions: list[str] | None = None
    references: list[str] = Field(default_factory=list)


class ScanReport(BaseModel):
    scan_id: str
    target: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    findings: list[CVEResult]
    summary: dict[str, int]


# ─── DevSuite ─────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    language: str = "python"
    context: dict[str, Any] | None = None
    files: list[str] | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)


class GenerateResponse(BaseModel):
    code: str
    files: dict[str, str] | None = None
    explanation: str | None = None
    usage: dict[str, int]


class ReviewRequest(BaseModel):
    code: str
    language: str
    focus: list[str] | None = None
    diff: str | None = None


class ReviewResponse(BaseModel):
    issues: list[dict[str, Any]]
    suggestions: list[str]
    score: float
    summary: str


class SandboxRunRequest(BaseModel):
    code: str
    language: str
    input_data: str | None = None
    timeout: int = Field(default=30, ge=1, le=300)
    dependencies: list[str] | None = None


class SandboxRunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    error: str | None = None


# ─── Companion ────────────────────────────────────────────────────────

class CompanionChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    context: dict[str, Any] | None = None


class CompanionChatResponse(BaseModel):
    response: str
    session_id: str
    citations: list[dict[str, Any]] | None = None


class BriefingRequest(BaseModel):
    date: str | None = None
    format: Literal["markdown", "html", "json"] = "markdown"


class BriefingResponse(BaseModel):
    briefing: str
    date: str
    sections: dict[str, str]


class MeetingSummarizeRequest(BaseModel):
    transcript: str
    participants: list[str] | None = None
    format: Literal["markdown", "html", "json"] = "markdown"


class MeetingSummarizeResponse(BaseModel):
    summary: str
    action_items: list[dict[str, Any]]
    decisions: list[str]
    participants: list[str]


class TaskListRequest(BaseModel):
    session_id: str | None = None
    status: str | None = None
    assignee: str | None = None


class TaskListResponse(BaseModel):
    tasks: list[dict[str, Any]]


# ─── Nexus (Bot Orchestration) ────────────────────────────────────────

class BotCreateRequest(BaseModel):
    name: str
    platform: str
    config: dict[str, Any]


class BotCreateResponse(BaseModel):
    bot_id: str
    name: str
    platform: str
    status: str
    webhook_url: str | None = None


class BroadcastRequest(BaseModel):
    message: str
    platforms: list[str] | None = None
    channels: list[str] | None = None
    format: str = "markdown"


class BroadcastResponse(BaseModel):
    sent: int
    failed: int
    errors: list[dict[str, Any]] | None = None


class ChannelListResponse(BaseModel):
    channels: list[dict[str, Any]]


# ─── MCP ──────────────────────────────────────────────────────────────

class MCPToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any]
    request_id: str | None = None


class MCPToolCallResponse(BaseModel):
    result: Any
    error: str | None = None


class MCPToolListResponse(BaseModel):
    tools: list[ToolDefinition]


class MCPResourceListResponse(BaseModel):
    resources: list[dict[str, Any]]


# ─── Admin ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    components: dict[str, str]


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=list)
    expires_in_days: int | None = None


class APIKeyCreateResponse(BaseModel):
    key_id: str
    key: str
    name: str
    scopes: list[str]
    expires_at: datetime | None = None


class APIKeyListResponse(BaseModel):
    keys: list[dict[str, Any]]


# ─── RBAC / Enterprise ────────────────────────────────────────────────

class OrgCreateRequest(BaseModel):
    name: str
    slug: str
    billing_email: str | None = None


class OrgCreateResponse(BaseModel):
    org_id: str
    name: str
    slug: str
    created_at: datetime


class TeamCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None


class TeamCreateResponse(BaseModel):
    team_id: str
    name: str
    slug: str


class ProjectCreateRequest(BaseModel):
    name: str
    slug: str
    team_id: str | None = None
    environment: Literal["development", "staging", "production"] = "development"


class ProjectCreateResponse(BaseModel):
    project_id: str
    name: str
    slug: str
    team_id: str | None


class RoleAssignRequest(BaseModel):
    user_id: str
    role: str
    scope: Literal["org", "team", "project"]
    scope_id: str | None = None


class AuditLogEntry(BaseModel):
    id: str
    timestamp: datetime
    actor: dict[str, str]
    action: str
    resource: dict[str, str]
    outcome: Literal["success", "failure", "partial"]
    severity: Literal["low", "medium", "high", "critical"]
    metadata: dict[str, Any]


# ─── Service Accounts ─────────────────────────────────────────────────

class ServiceAccountCreateRequest(BaseModel):
    name: str
    description: str | None = None
    role: str = "role:service"
    expires_in_days: int | None = None


class ServiceAccountCreateResponse(BaseModel):
    sa_id: str
    name: str
    role: str
    created_at: datetime


class ServiceAccountKeyCreateRequest(BaseModel):
    name: str
    expires_in_days: int | None = None
    ip_allowlist: list[str] | None = None
    allowed_paths: list[str] | None = None


class ServiceAccountKeyCreateResponse(BaseModel):
    key_id: str
    key: str
    name: str
    prefix: str
    expires_at: datetime | None


# ─── MCP Server ───────────────────────────────────────────────────────

class MCPServerConfig(BaseModel):
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    transport: Literal["stdio", "http", "streamable-http"] = "stdio"
    port: int | None = None
    host: str = "127.0.0.1"


# ─── WebSocket Events ─────────────────────────────────────────────────

class WSEvent(BaseModel):
    type: str
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentStatusEvent(WSEvent):
    type: Literal["agent.status"] = "agent.status"
    data: dict[str, Any]


class ChannelEvent(WSEvent):
    type: Literal["channel.message"] = "channel.message"
    data: dict[str, Any]


class MetricEvent(WSEvent):
    type: Literal["metric.update"] = "metric.update"
    data: dict[str, Any]


# ─── Pagination ───────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort: str | None = None
    order: Literal["asc", "desc"] = "desc"


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    per_page: int
    total_pages: int


# ─── Webhook ──────────────────────────────────────────────────────────

class WebhookConfig(BaseModel):
    url: HttpUrl
    events: list[str]
    secret: str | None = None
    active: bool = True


class WebhookDelivery(BaseModel):
    id: str
    event: str
    payload: dict[str, Any]
    status: Literal["pending", "delivered", "failed"]
    attempts: int
    created_at: datetime
    delivered_at: datetime | None = None