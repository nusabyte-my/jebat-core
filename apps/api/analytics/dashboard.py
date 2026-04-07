"""
JEBAT Analytics Dashboard - Streamlit Web Interface

Real-time analytics dashboard for JEBAT AI Assistant.

Features:
- Usage analytics visualization
- User behavior tracking
- Conversation insights
- Memory usage patterns
- Agent performance reports
- Predictive analytics

Usage:
    streamlit run jebat/analytics/dashboard.py
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import streamlit as st

from jebat.analytics.engine import AnalyticsEngine, get_analytics_engine


def format_timestamp(ts: Optional[datetime]) -> str:
    """Format timestamp for display"""
    if ts:
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def render_sidebar():
    """Render sidebar with filters"""
    st.sidebar.title("📊 Filters")

    # Time period selector
    period = st.sidebar.selectbox(
        "Time Period",
        ["hour", "day", "week", "month"],
        index=1,
    )

    # Tenant filter (if multi-tenancy enabled)
    tenant_id = st.sidebar.text_input("Tenant ID (optional)", "")

    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)

    return period, tenant_id if tenant_id else None, auto_refresh


def render_system_overview(engine: AnalyticsEngine):
    """Render system overview metrics"""
    st.subheader("🎯 System Overview")

    # Calculate metrics
    total_events = len(engine.events)
    unique_users = len(engine.user_behaviors)

    # Event counts by type
    event_counts = {}
    for event in engine.events:
        event_type = event.event_type
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Events", f"{total_events:,}", delta=None)

    with col2:
        st.metric("Unique Users", f"{unique_users}", delta=None)

    with col3:
        conversations = event_counts.get("conversation_start", 0)
        st.metric("Conversations", f"{conversations}", delta=None)

    with col4:
        agent_executions = event_counts.get("agent_execution", 0)
        st.metric("Agent Executions", f"{agent_executions}", delta=None)


def render_usage_trends(engine: AnalyticsEngine, period: str):
    """Render usage trends chart"""
    st.subheader("📈 Usage Trends")

    # Get usage report
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    report = loop.run_until_complete(engine.get_usage_report(period=period))
    loop.close()

    # Create DataFrame for chart
    if report["by_type"]:
        df = pd.DataFrame(
            list(report["by_type"].items()), columns=["Event Type", "Count"]
        )

        # Bar chart
        st.bar_chart(df.set_index("Event Type"))

        # Display stats
        st.write(f"**Total Events**: {report['total_events']:,}")
        st.write(f"**Unique Users**: {report['unique_users']}")
        st.write(f"**Avg Duration**: {report['avg_duration']:.2f}s")
        st.write(f"**Peak Hour**: {report['peak_hour']}:00")
    else:
        st.info("No usage data available yet")


def render_user_behavior(engine: AnalyticsEngine):
    """Render user behavior analytics"""
    st.subheader("👥 User Behavior")

    if engine.user_behaviors:
        # Create DataFrame
        user_data = []
        for user_id, behavior in engine.user_behaviors.items():
            user_data.append(
                {
                    "User ID": user_id,
                    "Interactions": behavior.total_interactions,
                    "Retention Score": f"{behavior.retention_score:.1%}",
                    "Last Active": format_timestamp(behavior.last_active),
                    "Features": ", ".join(behavior.favorite_features[:3]),
                }
            )

        df = pd.DataFrame(user_data)

        # Display table
        st.dataframe(df, use_container_width=True)

        # Top users
        if len(user_data) > 0:
            st.write("**Top Users by Interactions**")
            top_users = sorted(
                engine.user_behaviors.items(),
                key=lambda x: x[1].total_interactions,
                reverse=True,
            )[:5]

            for user_id, behavior in top_users:
                st.write(f"- **{user_id}**: {behavior.total_interactions} interactions")
    else:
        st.info("No user behavior data available yet")


def render_conversation_insights(engine: AnalyticsEngine):
    """Render conversation insights"""
    st.subheader("💬 Conversation Insights")

    # Get conversation insights
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    insights = loop.run_until_complete(engine.get_conversation_insights())
    loop.close()

    if insights:
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Total Conversations",
                insights.get("total_conversations", 0),
                delta=None,
            )

        with col2:
            avg_msgs = insights.get("avg_messages_per_conversation", 0)
            st.metric("Avg Messages/Conversation", f"{avg_msgs:.1f}", delta=None)

        # Sentiment distribution
        sentiment = insights.get("sentiment_distribution", {})
        if sentiment:
            st.write("**Sentiment Distribution**")
            sent_df = pd.DataFrame(
                list(sentiment.items()), columns=["Sentiment", "Percentage"]
            )
            sent_df["Percentage"] = sent_df["Percentage"] * 100
            st.bar_chart(sent_df.set_index("Sentiment"))

        # Common topics
        topics = insights.get("common_topics", [])
        if topics:
            st.write("**Common Topics**")
            for i, topic in enumerate(topics[:10], 1):
                st.write(f"{i}. {topic}")
    else:
        st.info("No conversation data available yet")


def render_memory_analytics(engine: AnalyticsEngine):
    """Render memory usage analytics"""
    st.subheader("🧠 Memory Analytics")

    # Get memory analytics
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    memory_stats = loop.run_until_complete(engine.get_memory_analytics())
    loop.close()

    if memory_stats and memory_stats.get("total_memories", 0) > 0:
        col1, col2, col3 = st.columns(3)

        with col1:
            total = memory_stats["total_memories"]
            st.metric("Total Memories", f"{total:,}", delta=None)

        with col2:
            avg_size = memory_stats["avg_memory_size"]
            st.metric("Avg Memory Size", f"{avg_size:.0f} B", delta=None)

        with col3:
            total_storage = memory_stats["total_storage_bytes"]
            if total_storage > 1024 * 1024:
                st.metric("Total Storage", f"{total_storage / (1024 * 1024):.2f} MB")
            elif total_storage > 1024:
                st.metric("Total Storage", f"{total_storage / 1024:.2f} KB")
            else:
                st.metric("Total Storage", f"{total_storage} B")

        # Memory by layer
        by_layer = memory_stats.get("by_layer", {})
        if by_layer:
            st.write("**Memories by Layer**")
            layer_df = pd.DataFrame(list(by_layer.items()), columns=["Layer", "Count"])
            st.bar_chart(layer_df.set_index("Layer"))
    else:
        st.info("No memory data available yet")


def render_agent_performance(engine: AnalyticsEngine):
    """Render agent performance analytics"""
    st.subheader("🤖 Agent Performance")

    # Get agent performance
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    perf = loop.run_until_complete(engine.get_agent_performance())
    loop.close()

    if perf and perf.get("total_agent_executions", 0) > 0:
        st.metric("Total Agent Executions", perf["total_agent_executions"], delta=None)

        by_agent = perf.get("by_agent", {})
        if by_agent:
            # Create DataFrame
            agent_data = []
            for agent_id, stats in by_agent.items():
                agent_data.append(
                    {
                        "Agent": agent_id,
                        "Executions": stats["executions"],
                        "Success Rate": f"{stats.get('success_rate', 0):.1%}",
                        "Avg Duration": f"{stats.get('avg_duration', 0):.2f}s",
                    }
                )

            df = pd.DataFrame(agent_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No agent performance data available yet")


def render_insights(engine: AnalyticsEngine, period: str):
    """Render analytics insights"""
    st.subheader("💡 Insights")

    # Get insights
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    insights = loop.run_until_complete(engine.get_insights(period=period))
    loop.close()

    if insights:
        for insight in insights:
            delta = f"{insight.change:+.1f}%" if insight.change != 0 else "0%"
            st.metric(
                f"{insight.metric} ({period})",
                f"{insight.value:,}",
                delta=delta,
            )
    else:
        st.info("No insights available yet")


def render_event_log(engine: AnalyticsEngine, limit: int = 50):
    """Render recent event log"""
    st.subheader("📋 Recent Events")

    if engine.events:
        # Get recent events
        recent = sorted(engine.events, key=lambda e: e.timestamp, reverse=True)[:limit]

        # Create DataFrame
        event_data = []
        for event in recent:
            event_data.append(
                {
                    "Time": event.timestamp.strftime("%H:%M:%S"),
                    "Type": event.event_type,
                    "User": event.user_id or "-",
                    "Duration": f"{event.metadata.get('duration', 0):.2f}s"
                    if "duration" in event.metadata
                    else "-",
                }
            )

        df = pd.DataFrame(event_data)
        st.dataframe(df, use_container_width=True)

        # Clear old events button
        if st.button("🗑️ Clear Events Older Than 1 Hour"):
            cutoff = datetime.utcnow() - timedelta(hours=1)
            engine.clear_events(older_than=cutoff)
            st.success("Events cleared!")
            st.rerun()
    else:
        st.info("No events logged yet")


def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="JEBAT Analytics Dashboard",
        page_icon="🗡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Header
    st.title("🗡️ JEBAT Analytics Dashboard")
    st.markdown("**Real-time analytics and insights for JEBAT AI Assistant**")

    # Initialize analytics engine
    engine = get_analytics_engine()

    # Render sidebar
    period, tenant_id, auto_refresh = render_sidebar()

    # Render main content
    render_system_overview(engine)

    st.divider()

    # Usage trends
    render_usage_trends(engine, period)

    st.divider()

    # User behavior and insights
    col1, col2 = st.columns(2)
    with col1:
        render_user_behavior(engine)
    with col2:
        render_insights(engine, period)

    st.divider()

    # Conversation and memory analytics
    col1, col2 = st.columns(2)
    with col1:
        render_conversation_insights(engine)
    with col2:
        render_memory_analytics(engine)

    st.divider()

    # Agent performance
    render_agent_performance(engine)

    st.divider()

    # Event log
    render_event_log(engine)

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

    # Footer
    st.divider()
    st.markdown(
        """
        ---
        **JEBAT Analytics** | Last Updated: """
        + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )


if __name__ == "__main__":
    main()
