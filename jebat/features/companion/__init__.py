"""
Sahabat Companion — Conversational AI for Daily Operations

Named after the Malay word for "friend/companion".
Provides persistent conversational memory, daily briefings,
meeting summaries, and integrated task management.

Part of the JEBAT Platform Suite.
"""

from .companion import SahabatCompanion
from .briefing import DailyBriefing
from .tasks import TaskManager
from .meeting import MeetingSummarizer

__all__ = ["SahabatCompanion", "DailyBriefing", "TaskManager", "MeetingSummarizer"]
