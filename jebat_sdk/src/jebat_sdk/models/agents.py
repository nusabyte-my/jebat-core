"""
Agent models for JEBAT SDK.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """Agent information."""
    id: str
    name: str
    type: str = Field(..., description="Agent type: specialist, generalist, etc.")
    status: str = Field(..., description="Agent status: idle, active, busy, error")
    capabilities: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class AgentListResponse(BaseModel):
    """Agent list response."""
    agents: List[AgentInfo]
    total: int
    active: int
    idle: int


class AgentExecuteRequest(BaseModel):
    """Agent execution request."""
    task: str = Field(..., description="Task description")
    agent_id: Optional[str] = None
    mode: str = Field("deliberate", description="Execution mode")
    timeout: int = Field(30, ge=1, le=300)


class AgentExecuteResponse(BaseModel):
    """Agent execution response."""
    task_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    agent_id: str