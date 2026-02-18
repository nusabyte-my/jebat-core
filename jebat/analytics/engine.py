"""
JEBAT Analytics Dashboard

Analytics and reporting for JEBAT AI Assistant.

Features:
- Usage analytics
- User behavior tracking
- Conversation insights
- Memory usage patterns
- Agent performance reports
- Predictive analytics

Usage:
    from jebat.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    await engine.track_event("chat_completion", {"user_id": "123", "duration": 1.5})
    insights = await engine.get_insights(period="day")
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Analytics event"""

    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Insight:
    """Analytics insight"""

    metric: str
    value: Any
    change: float  # Percentage change
    period: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserBehavior:
    """User behavior metrics"""

    user_id: str
    total_interactions: int = 0
    avg_session_duration: float = 0.0
    favorite_features: List[str] = field(default_factory=list)
    last_active: Optional[datetime] = None
    retention_score: float = 0.0


class AnalyticsEngine:
    """
    Analytics engine for JEBAT.

    Features:
    - Event tracking
    - Metrics aggregation
    - User behavior analysis
    - Predictive analytics
    - Report generation
    """

    def __init__(self):
        """Initialize analytics engine"""
        self.events: List[Event] = []
        self.metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.user_behaviors: Dict[str, UserBehavior] = {}

        # Aggregation caches
        self._hourly_cache: Dict[str, Any] = {}
        self._daily_cache: Dict[str, Any] = {}

        logger.info("AnalyticsEngine initialized")

    async def track_event(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Track analytics event.

        Args:
            event_type: Type of event
            metadata: Event metadata
            user_id: User identifier
            tenant_id: Tenant identifier
        """
        event = Event(
            event_type=event_type,
            metadata=metadata or {},
            user_id=user_id,
            tenant_id=tenant_id,
        )

        self.events.append(event)

        # Update real-time metrics
        await self._update_metrics(event)

        # Update user behavior
        if user_id:
            await self._update_user_behavior(user_id, event)

        logger.debug(f"Tracked event: {event_type} (user={user_id})")

    async def _update_metrics(self, event: Event):
        """Update real-time metrics"""
        # Count events by type
        type_key = f"{event.event_type}_count"
        self.metrics[type_key]["total"] = (
            self.metrics.get(type_key, {}).get("total", 0) + 1
        )

        # Track by hour
        hour_key = event.timestamp.strftime("%Y-%m-%d-%H")
        self._hourly_cache[f"{event.event_type}_{hour_key}"] = (
            self._hourly_cache.get(f"{event.event_type}_{hour_key}", 0) + 1
        )

        # Track by day
        day_key = event.timestamp.strftime("%Y-%m-%d")
        self._daily_cache[f"{event.event_type}_{day_key}"] = (
            self._daily_cache.get(f"{event.event_type}_{day_key}", 0) + 1
        )

    async def _update_user_behavior(self, user_id: str, event: Event):
        """Update user behavior tracking"""
        if user_id not in self.user_behaviors:
            self.user_behaviors[user_id] = UserBehavior(user_id=user_id)

        behavior = self.user_behaviors[user_id]
        behavior.total_interactions += 1
        behavior.last_active = event.timestamp

        # Track favorite features
        feature = event.metadata.get("feature")
        if feature:
            if feature not in behavior.favorite_features:
                behavior.favorite_features.append(feature)

        # Calculate retention score (simplified)
        if behavior.total_interactions > 10:
            behavior.retention_score = 0.8
        elif behavior.total_interactions > 5:
            behavior.retention_score = 0.6
        elif behavior.total_interactions > 1:
            behavior.retention_score = 0.4
        else:
            behavior.retention_score = 0.2

    async def get_insights(
        self,
        period: str = "day",
        tenant_id: Optional[str] = None,
    ) -> List[Insight]:
        """
        Get analytics insights.

        Args:
            period: Time period (hour, day, week, month)
            tenant_id: Filter by tenant

        Returns:
            List of insights
        """
        insights = []

        # Calculate metrics based on period
        now = datetime.utcnow()

        if period == "hour":
            start = now - timedelta(hours=1)
            prev_start = now - timedelta(hours=2)
            prev_end = now - timedelta(hours=1)
        elif period == "day":
            start = now - timedelta(days=1)
            prev_start = now - timedelta(days=2)
            prev_end = now - timedelta(days=1)
        elif period == "week":
            start = now - timedelta(weeks=1)
            prev_start = now - timedelta(weeks=2)
            prev_end = now - timedelta(weeks=1)
        else:  # month
            start = now - timedelta(days=30)
            prev_start = now - timedelta(days=60)
            prev_end = now - timedelta(days=30)

        # Filter events
        current_events = [
            e
            for e in self.events
            if start <= e.timestamp <= now
            and (not tenant_id or e.tenant_id == tenant_id)
        ]

        previous_events = [
            e
            for e in self.events
            if prev_start <= e.timestamp <= prev_end
            and (not tenant_id or e.tenant_id == tenant_id)
        ]

        # Calculate insights by event type
        event_types = set(e.event_type for e in current_events)

        for event_type in event_types:
            current_count = len(
                [e for e in current_events if e.event_type == event_type]
            )
            previous_count = len(
                [e for e in previous_events if e.event_type == event_type]
            )

            change = 0.0
            if previous_count > 0:
                change = ((current_count - previous_count) / previous_count) * 100

            insights.append(
                Insight(
                    metric=f"{event_type}_count",
                    value=current_count,
                    change=change,
                    period=period,
                )
            )

        return insights

    async def get_usage_report(
        self,
        tenant_id: Optional[str] = None,
        period: str = "day",
    ) -> Dict[str, Any]:
        """
        Get usage report.

        Args:
            tenant_id: Filter by tenant
            period: Time period

        Returns:
            Usage report dict
        """
        now = datetime.utcnow()

        if period == "day":
            start = now - timedelta(days=1)
        elif period == "week":
            start = now - timedelta(weeks=1)
        else:
            start = now - timedelta(days=30)

        # Filter events
        events = [
            e
            for e in self.events
            if start <= e.timestamp <= now
            and (not tenant_id or e.tenant_id == tenant_id)
        ]

        # Aggregate by event type
        by_type = defaultdict(int)
        for e in events:
            by_type[e.event_type] += 1

        # Aggregate by user
        by_user = defaultdict(int)
        for e in events:
            if e.user_id:
                by_user[e.user_id] += 1

        # Calculate averages
        durations = [
            e.metadata.get("duration", 0) for e in events if "duration" in e.metadata
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "period": period,
            "tenant_id": tenant_id,
            "total_events": len(events),
            "by_type": dict(by_type),
            "by_user": dict(by_user),
            "unique_users": len(by_user),
            "avg_duration": avg_duration,
            "peak_hour": self._get_peak_hour(events),
        }

    def _get_peak_hour(self, events: List[Event]) -> int:
        """Get peak usage hour"""
        hour_counts = defaultdict(int)
        for e in events:
            hour_counts[e.timestamp.hour] += 1

        if not hour_counts:
            return 0

        return max(hour_counts, key=hour_counts.get)

    async def get_user_analytics(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get analytics for specific user"""
        if user_id not in self.user_behaviors:
            return {"error": "User not found"}

        behavior = self.user_behaviors[user_id]

        return {
            "user_id": user_id,
            "total_interactions": behavior.total_interactions,
            "avg_session_duration": behavior.avg_session_duration,
            "favorite_features": behavior.favorite_features[:5],
            "last_active": behavior.last_active.isoformat()
            if behavior.last_active
            else None,
            "retention_score": behavior.retention_score,
        }

    async def get_conversation_insights(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get conversation-specific insights"""
        # Filter conversation events
        conv_events = [
            e
            for e in self.events
            if e.event_type.startswith("conversation_")
            and (not tenant_id or e.tenant_id == tenant_id)
        ]

        # Calculate metrics
        total_conversations = len(
            [e for e in conv_events if e.event_type == "conversation_start"]
        )
        avg_messages = 0
        if total_conversations > 0:
            total_messages = len([e for e in conv_events if e.event_type == "message"])
            avg_messages = total_messages / total_conversations

        # Sentiment analysis (placeholder)
        sentiment_distribution = {
            "positive": 0.6,
            "neutral": 0.3,
            "negative": 0.1,
        }

        return {
            "total_conversations": total_conversations,
            "avg_messages_per_conversation": avg_messages,
            "sentiment_distribution": sentiment_distribution,
            "common_topics": self._extract_common_topics(conv_events),
        }

    def _extract_common_topics(self, events: List[Event]) -> List[str]:
        """Extract common topics from events"""
        topics = defaultdict(int)
        for e in events:
            topic = e.metadata.get("topic")
            if topic:
                topics[topic] += 1

        return sorted(topics.keys(), key=lambda x: topics[x], reverse=True)[:10]

    async def get_memory_analytics(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get memory usage analytics"""
        # Filter memory events
        mem_events = [
            e
            for e in self.events
            if e.event_type.startswith("memory_")
            and (not tenant_id or e.tenant_id == tenant_id)
        ]

        # Count by layer
        by_layer = defaultdict(int)
        for e in mem_events:
            layer = e.metadata.get("layer", "unknown")
            by_layer[layer] += 1

        # Calculate storage
        total_storage = sum(
            e.metadata.get("size_bytes", 0)
            for e in mem_events
            if "size_bytes" in e.metadata
        )

        return {
            "total_memories": len(mem_events),
            "by_layer": dict(by_layer),
            "total_storage_bytes": total_storage,
            "avg_memory_size": total_storage / len(mem_events) if mem_events else 0,
        }

    async def get_agent_performance(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get agent performance analytics"""
        # Filter agent events
        agent_events = [
            e
            for e in self.events
            if e.event_type.startswith("agent_")
            and (not tenant_id or e.tenant_id == tenant_id)
        ]

        # Performance by agent
        by_agent = defaultdict(
            lambda: {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_duration": 0,
            }
        )

        for e in agent_events:
            agent_id = e.metadata.get("agent_id", "unknown")
            by_agent[agent_id]["executions"] += 1

            if e.metadata.get("success", False):
                by_agent[agent_id]["successes"] += 1
            else:
                by_agent[agent_id]["failures"] += 1

            by_agent[agent_id]["total_duration"] += e.metadata.get("duration", 0)

        # Calculate averages
        for agent_id in by_agent:
            executions = by_agent[agent_id]["executions"]
            if executions > 0:
                by_agent[agent_id]["avg_duration"] = (
                    by_agent[agent_id]["total_duration"] / executions
                )
                by_agent[agent_id]["success_rate"] = (
                    by_agent[agent_id]["successes"] / executions
                )

        return {
            "total_agent_executions": len(agent_events),
            "by_agent": dict(by_agent),
        }

    def clear_events(self, older_than: Optional[datetime] = None):
        """Clear old events"""
        if older_than:
            self.events = [e for e in self.events if e.timestamp > older_than]
        else:
            self.events.clear()

        logger.info(f"Cleared events (older_than={older_than})")


# Global analytics engine
_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get global analytics engine"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


# Convenience functions


async def track_event(
    event_type: str,
    metadata: Optional[Dict] = None,
    user_id: Optional[str] = None,
):
    """Track event using global engine"""
    engine = get_analytics_engine()
    await engine.track_event(event_type, metadata, user_id)


async def get_insights(period: str = "day") -> List[Insight]:
    """Get insights from global engine"""
    engine = get_analytics_engine()
    return await engine.get_insights(period)
