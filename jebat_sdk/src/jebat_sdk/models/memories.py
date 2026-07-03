"""
Memory models for JEBAT SDK.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """Memory item."""
    id: str
    content: str
    layer: str = Field(..., description="Memory layer: M0_IMMEDIATE, M1_EPISODIC, M2_SEMANTIC, M3_PROCEDURAL, M4_STRATEGIC")
    user_id: str
    created_at: datetime
    heat_score: float = Field(..., ge=0, le=1, description="Heat score 0-1")
    metadata: Optional[dict] = None


class MemoryListResponse(BaseModel):
    """Paginated memory list response."""
    memories: List[MemoryItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class MemoryCreateRequest(BaseModel):
    """Memory creation request."""
    content: str = Field(..., description="Memory content")
    user_id: str = Field(..., description="User identifier")
    layer: Optional[str] = Field("M1_EPISODIC", description="Memory layer")
    metadata: Optional[dict] = None


class MemorySearchRequest(BaseModel):
    """Memory search request."""
    query: str = Field(..., description="Search query")
    user_id: Optional[str] = None
    layer: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)