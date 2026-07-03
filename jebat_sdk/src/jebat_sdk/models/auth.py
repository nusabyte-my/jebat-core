"""
Authentication models for JEBAT SDK.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TokenRequest(BaseModel):
    """Token request (login)."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token response (login/refresh)."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")


class APIKeyCreateRequest(BaseModel):
    """API key creation request."""
    name: str = Field(..., description="API key name")
    expires_in_days: Optional[int] = Field(None, description="Expiry in days")


class APIKeyResponse(BaseModel):
    """API key response."""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    prefix: str = Field(..., description="Key prefix (e.g., jebat_abc123)")
    key: Optional[str] = Field(None, description="Full key (only returned on creation)")
    is_active: bool = Field(..., description="Whether key is active")
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime