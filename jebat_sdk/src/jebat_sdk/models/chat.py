"""
Chat models for JEBAT SDK.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    mode: Optional[str] = Field(
        "deliberate",
        description="Thinking mode: fast, deliberate, deep, strategic, creative, critical"
    )
    timeout: Optional[int] = Field(30, description="Timeout in seconds")
    stream: bool = Field(False, description="Stream response")


class ChatResponse(BaseModel):
    """Chat response."""
    response: str = Field(..., description="Assistant response")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    thinking_steps: int = Field(..., description="Number of thinking steps")
    execution_time: float = Field(..., description="Execution time in seconds")
    user_id: Optional[str] = None
    swarm_lead: Optional[Dict[str, Any]] = None
    reducer: Optional[Dict[str, Any]] = None
    doctrine: Optional[Dict[str, Any]] = None
    security_layer: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Chat message."""
    id: str
    role: str = Field(..., description="Role: user, assistant, system")
    content: str
    timestamp: datetime
    is_streaming: bool = False
    confidence: Optional[float] = None
    thinking_steps: Optional[int] = None


class OpenAIMessage(BaseModel):
    """OpenAI-compatible message."""
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat request."""
    model: str = "jebat-pro"
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class OpenAIChatChoice(BaseModel):
    """OpenAI-compatible choice."""
    index: int
    message: OpenAIMessage
    finish_reason: Optional[str] = None


class OpenAIChatResponse(BaseModel):
    """OpenAI-compatible chat response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChatChoice]
    usage: Dict[str, int]


# ==================== Swarm Models ====================

class SwarmTaskRequest(BaseModel):
    """Direct swarm execution request."""
    description: str = Field(..., description="Task description for the swarm")
    user_id: Optional[str] = Field("default", description="User identifier")
    execution_mode: Optional[str] = Field("consensus", description="single, swarm, or consensus")
    required_capabilities: List[str] = Field(default_factory=list, description="Capabilities to route against")
    enable_search: bool = Field(True, description="Whether agents should search before judging")
    search_queries: List[str] = Field(default_factory=list, description="Optional explicit search queries")
    max_agents: int = Field(5, ge=1, le=8, description="Maximum number of agents to involve")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional task parameters")


class SwarmTaskResponse(BaseModel):
    """Direct swarm execution response."""

    task_id: str
    success: bool
    execution_mode: str
    execution_time: float
    result: Any = None
    error: Optional[str] = None
    swarm_lead: Optional[Dict[str, Any]] = None
    reducer: Optional[Dict[str, Any]] = None
    doctrine: Optional[Dict[str, Any]] = None
    security_layer: Optional[Dict[str, Any]] = None
    full_orchestration: bool = False
    stats: Dict[str, Any] = Field(default_factory=dict)


class SwarmPlanResponse(BaseModel):
    """Read-only swarm planning response."""

    task_id: str
    execution_mode: str
    required_capabilities: List[str] = Field(default_factory=list)
    preferred_roles: List[str] = Field(default_factory=list)
    recommended_delivery_mode: str
    search_enabled: bool
    require_consensus: bool
    full_orchestration: bool
    security_layer: Dict[str, Any] = Field(default_factory=dict)
    swarm_lead: Optional[Dict[str, Any]] = None
    ranked_agents: List[Dict[str, Any]] = Field(default_factory=list)
    selected_agents: List[Dict[str, Any]] = Field(default_factory=list)