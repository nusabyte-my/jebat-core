"""
Common models shared across the SDK.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ErrorDetail(BaseModel):
    """Error detail from API response."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    errors: Optional[List[ErrorDetail]] = None
    status_code: Optional[int] = None


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""
    created_at: datetime
    updated_at: Optional[datetime] = None


class DateTimeRange(BaseModel):
    """Date time range filter."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None