"""
Channel models for JEBAT SDK.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChannelInfo(BaseModel):
    """Channel information."""
    id: str
    name: str
    description: str
    status: str = Field(..., description="connected, disconnected")
    config: Dict[str, Any] = Field(default_factory=dict)


class ChannelConfig(BaseModel):
    """Channel configuration."""
    bot_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    access_token: Optional[str] = None
    verify_token: Optional[str] = None


class ChannelStatus(BaseModel):
    """Channel status update."""
    channel_id: str
    status: str
    message: Optional[str] = None


class ChannelListResponse(BaseModel):
    """Channel list response."""
    channels: list
    total: int
    connected: int
    disconnected: int