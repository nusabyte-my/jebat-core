"""
Perisai — Nexus Multi-Channel Bot Orchestrator

Orchestrates bots across Telegram, Discord, Slack, Signal,
Matrix, and WhatsApp with unified message routing.
"""

from .perisai import PerisaiNexus, ChannelConfig, NexusStore

__all__ = ["PerisaiNexus", "ChannelConfig", "NexusStore"]
