"""JEBAT Telemetry — Opt-in usage analytics.

Privacy-first telemetry system:
  - OPT-IN only — never sends data without explicit consent
  - Local-first — all data stays in ~/.jebat/telemetry/ until exported
  - Anonymous — no personal data, no file contents, no prompts
  - Configurable — user controls what categories are tracked

Tracks:
  - Feature usage counts (which tools are used most)
  - Performance metrics (latency, success rates)
  - Session statistics (duration, model choices)
  - Error patterns (crashes, timeouts) — no stack traces with user data

This is the Pengawas (Observer) — watches from a distance, respects privacy.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

TELEMETRY_DIR = os.path.expanduser("~/.jebat/telemetry")
TELEMETRY_CONFIG_PATH = os.path.join(TELEMETRY_DIR, "config.json")


# ── Telemetry Categories ─────────────────────────────────────────────────

CATEGORY_FEATURE_USAGE = "feature_usage"
CATEGORY_PERFORMANCE = "performance"
CATEGORY_SESSION_STATS = "session_stats"
CATEGORY_ERRORS = "errors"

ALL_CATEGORIES = [
    CATEGORY_FEATURE_USAGE,
    CATEGORY_PERFORMANCE,
    CATEGORY_SESSION_STATS,
    CATEGORY_ERRORS,
]


@dataclass(slots=True)
class TelemetryConfig:
    """User's telemetry preferences."""
    enabled: bool = False  # Default: disabled — must opt-in
    categories: list[str] = field(default_factory=lambda: ALL_CATEGORIES)
    anonymize: bool = True
    export_interval_hours: int = 24
    retention_days: int = 30


@dataclass(slots=True)
class TelemetryEvent:
    """Single telemetry event."""
    category: str = ""
    event_type: str = ""
    timestamp: str = ""
    duration_ms: int = 0
    success: bool = True
    model: str = ""
    provider: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Config Management ─────────────────────────────────────────────────────

def load_config() -> TelemetryConfig:
    """Load telemetry config from disk."""
    if not os.path.exists(TELEMETRY_CONFIG_PATH):
        config = TelemetryConfig()
        save_config(config)
        return config

    try:
        with open(TELEMETRY_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TelemetryConfig(
            enabled=data.get("enabled", False),
            categories=data.get("categories", ALL_CATEGORIES),
            anonymize=data.get("anonymize", True),
            export_interval_hours=data.get("export_interval_hours", 24),
            retention_days=data.get("retention_days", 30),
        )
    except (json.JSONDecodeError, OSError):
        return TelemetryConfig()


def save_config(config: TelemetryConfig) -> None:
    """Save telemetry config to disk."""
    os.makedirs(TELEMETRY_DIR, exist_ok=True)

    with open(TELEMETRY_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "enabled": config.enabled,
            "categories": config.categories,
            "anonymize": config.anonymize,
            "export_interval_hours": config.export_interval_hours,
            "retention_days": config.retention_days,
        }, f, indent=2)


def enable_telemetry(categories: list[str] | None = None) -> TelemetryConfig:
    """Enable telemetry (opt-in).

    Args:
        categories: Specific categories to enable, or None for all

    Returns:
        Updated TelemetryConfig
    """
    config = load_config()
    config.enabled = True
    if categories:
        config.categories = categories
    else:
        config.categories = ALL_CATEGORIES
    save_config(config)
    return config


def disable_telemetry() -> TelemetryConfig:
    """Disable telemetry."""
    config = load_config()
    config.enabled = False
    save_config(config)
    return config


# ── Event Recording ──────────────────────────────────────────────────────

def record_event(
    category: str,
    event_type: str,
    duration_ms: int = 0,
    success: bool = True,
    model: str = "",
    provider: str = "",
    metadata: dict[str, Any] | None = None,
) -> TelemetryEvent | None:
    """Record a telemetry event.

    Only records if telemetry is enabled AND the category is allowed.

    Args:
        category: Event category (feature_usage, performance, etc.)
        event_type: What happened (e.g. 'tool_call', 'llm_request')
        duration_ms: Duration in milliseconds
        success: Whether the operation succeeded
        model: LLM model used
        provider: LLM provider used
        metadata: Additional anonymized metadata

    Returns:
        TelemetryEvent if recorded, None if telemetry disabled
    """
    config = load_config()

    if not config.enabled:
        return None

    if category not in config.categories:
        return None

    # Anonymize metadata if configured
    safe_metadata = {}
    if metadata and config.anonymize:
        # Only keep safe keys — strip anything that could contain user data
        safe_keys = {"tool_name", "feature", "count", "latency", "status", "model", "provider"}
        for key, value in metadata.items():
            if key in safe_keys:
                safe_metadata[key] = value
    elif metadata:
        safe_metadata = metadata

    event = TelemetryEvent(
        category=category,
        event_type=event_type,
        timestamp=datetime.now().isoformat(),
        duration_ms=duration_ms,
        success=success,
        model=model,
        provider=provider,
        metadata=safe_metadata,
    )

    # Save event
    _save_event(event)

    return event


def _save_event(event: TelemetryEvent) -> None:
    """Save a telemetry event to the daily log."""
    os.makedirs(TELEMETRY_DIR, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(TELEMETRY_DIR, f"events_{date_str}.json")

    # Load existing events for the day
    events: list[dict[str, Any]] = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                events = json.load(f)
        except (json.JSONDecodeError, OSError):
            events = []

    # Append new event
    events.append({
        "category": event.category,
        "event_type": event.event_type,
        "timestamp": event.timestamp,
        "duration_ms": event.duration_ms,
        "success": event.success,
        "model": event.model,
        "provider": event.provider,
        "metadata": event.metadata,
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)


# ── Analytics ─────────────────────────────────────────────────────────────

def get_feature_usage(days: int = 7) -> dict[str, int]:
    """Get feature usage counts for the last N days.

    Returns:
        Dict of feature_name → count
    """
    usage: dict[str, int] = {}

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_path = os.path.join(TELEMETRY_DIR, f"events_{date}.json")

        if not os.path.exists(log_path):
            continue

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                events = json.load(f)
            for event in events:
                if event.get("category") == CATEGORY_FEATURE_USAGE:
                    name = event.get("metadata", {}).get("tool_name", event.get("event_type", "unknown"))
                    usage[name] = usage.get(name, 0) + 1
        except (json.JSONDecodeError, OSError):
            continue

    return usage


def get_performance_stats(days: int = 7) -> dict[str, dict[str, Any]]:
    """Get performance statistics for the last N days.

    Returns:
        Dict of event_type → {avg_ms, success_rate, count}
    """
    stats: dict[str, dict[str, Any]] = {}

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_path = os.path.join(TELEMETRY_DIR, f"events_{date}.json")

        if not os.path.exists(log_path):
            continue

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                events = json.load(f)
            for event in events:
                if event.get("category") == CATEGORY_PERFORMANCE:
                    etype = event.get("event_type", "unknown")
                    if etype not in stats:
                        stats[etype] = {"total_ms": 0, "success_count": 0, "count": 0}
                    stats[etype]["total_ms"] += event.get("duration_ms", 0)
                    stats[etype]["count"] += 1
                    if event.get("success", True):
                        stats[etype]["success_count"] += 1
        except (json.JSONDecodeError, OSError):
            continue

    # Calculate averages
    for etype, data in stats.items():
        data["avg_ms"] = data["total_ms"] / max(data["count"], 1)
        data["success_rate"] = data["success_count"] / max(data["count"], 1)

    return stats


def get_session_stats(days: int = 7) -> dict[str, Any]:
    """Get session statistics for the last N days.

    Returns:
        Dict with total_sessions, models_used, providers_used, avg_duration_ms
    """
    sessions: dict[str, Any] = {
        "total_sessions": 0,
        "models_used": {},
        "providers_used": {},
        "avg_duration_ms": 0,
        "total_duration_ms": 0,
    }

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_path = os.path.join(TELEMETRY_DIR, f"events_{date}.json")

        if not os.path.exists(log_path):
            continue

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                events = json.load(f)
            for event in events:
                if event.get("category") == CATEGORY_SESSION_STATS:
                    sessions["total_sessions"] += 1
                    model = event.get("model", "unknown")
                    provider = event.get("provider", "unknown")
                    sessions["models_used"][model] = sessions["models_used"].get(model, 0) + 1
                    sessions["providers_used"][provider] = sessions["providers_used"].get(provider, 0) + 1
                    sessions["total_duration_ms"] += event.get("duration_ms", 0)
        except (json.JSONDecodeError, OSError):
            continue

    if sessions["total_sessions"] > 0:
        sessions["avg_duration_ms"] = sessions["total_duration_ms"] / sessions["total_sessions"]

    return sessions


def purge_old_events(retention_days: int = 30) -> int:
    """Purge telemetry events older than retention period.

    Args:
        retention_days: Number of days to retain

    Returns:
        Number of files purged
    """
    if not os.path.exists(TELEMETRY_DIR):
        return 0

    cutoff = datetime.now() - timedelta(days=retention_days)
    purged = 0

    for f in os.listdir(TELEMETRY_DIR):
        if f.startswith("events_") and f.endswith(".json"):
            # Parse date from filename
            date_str = f.replace("events_", "").replace(".json", "")
            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d")
                if event_date < cutoff:
                    os.remove(os.path.join(TELEMETRY_DIR, f))
                    purged += 1
            except ValueError:
                continue

    return purged


def format_telemetry_report(days: int = 7) -> str:
    """Format a comprehensive telemetry report.

    Args:
        days: Number of days to include

    Returns:
        Formatted report string
    """
    config = load_config()
    usage = get_feature_usage(days)
    perf = get_performance_stats(days)
    sessions = get_session_stats(days)

    lines = [
        "=== JEBAT Telemetry Report ===",
        f"Period: last {days} days",
        f"Telemetry: {'ENABLED' if config.enabled else 'DISABLED'}",
        f"Categories: {', '.join(config.categories) if config.enabled else 'N/A'}",
        "",
        "--- Feature Usage ---",
    ]

    for feature, count in sorted(usage.items(), key=lambda x: -x[1]):
        lines.append(f"  {feature}: {count} uses")

    lines.append("\n--- Performance ---")
    for etype, data in sorted(perf.items()):
        lines.append(f"  {etype}: avg {data['avg_ms']:.0f}ms, {data['success_rate']:.1%} success ({data['count']} calls)")

    lines.append("\n--- Sessions ---")
    lines.append(f"  Total: {sessions['total_sessions']}")
    lines.append(f"  Avg duration: {sessions['avg_duration_ms']:.0f}ms")
    if sessions["models_used"]:
        lines.append("  Models used:")
        for model, count in sorted(sessions["models_used"].items(), key=lambda x: -x[1]):
            lines.append(f"    {model}: {count}")
    if sessions["providers_used"]:
        lines.append("  Providers used:")
        for provider, count in sorted(sessions["providers_used"].items(), key=lambda x: -x[1]):
            lines.append(f"    {provider}: {count}")

    return "\n".join(lines)


# ── Telemetry Tools Registry ─────────────────────────────────────────────

TELEMETRY_TOOLS: dict[str, dict[str, Any]] = {
    "enable_telemetry": {
        "description": "Enable telemetry (opt-in, privacy-first)",
        "safety": "confirm",
        "handler": enable_telemetry,
        "parameters": {"categories": {"type": "array", "description": "Categories to enable"}},
    },
    "disable_telemetry": {
        "description": "Disable telemetry",
        "safety": "auto",
        "handler": disable_telemetry,
        "parameters": {},
    },
    "record_event": {
        "description": "Record a telemetry event (only if enabled)",
        "safety": "auto",
        "handler": record_event,
        "parameters": {
            "category": {"type": "string"},
            "event_type": {"type": "string"},
            "duration_ms": {"type": "integer"},
            "success": {"type": "boolean"},
        },
    },
    "get_feature_usage": {
        "description": "Get feature usage counts",
        "safety": "auto",
        "handler": get_feature_usage,
        "parameters": {"days": {"type": "integer", "default": 7}},
    },
    "format_telemetry_report": {
        "description": "Format comprehensive telemetry report",
        "safety": "auto",
        "handler": format_telemetry_report,
        "parameters": {"days": {"type": "integer", "default": 7}},
    },
    "purge_old_events": {
        "description": "Purge telemetry events older than retention period",
        "safety": "confirm",
        "handler": purge_old_events,
        "parameters": {"retention_days": {"type": "integer", "default": 30}},
    },
}


def list_telemetry_tools() -> list[dict[str, str]]:
    """List all telemetry tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in TELEMETRY_TOOLS.items()
    ]

# ── Register with JEBAT tool system ────────────────────────────────────────
from jebat.tools import register_tool  # noqa: E402
register_tool("telemetry_enable", handler=enable_telemetry, description="Opt-in to privacy-first telemetry (no personal data sent).", schema={"categories": {"type": "array", "description": "Categories to enable (leave empty for all)"}})
register_tool("telemetry_disable", handler=disable_telemetry, description="Disable all telemetry.", schema={})
register_tool("telemetry_record", handler=record_event, description="Record an anonymized telemetry event (only if enabled).", schema={"category": {"type": "string"}, "event_type": {"type": "string"}, "duration_ms": {"type": "integer"}, "success": {"type": "boolean"}})
register_tool("telemetry_usage", handler=get_feature_usage, description="Get feature usage stats for the last N days.", schema={"days": {"type": "integer", "default": 7}})
register_tool("telemetry_performance", handler=get_performance_stats, description="Get performance stats (avg latency, success rate) for last N days.", schema={"days": {"type": "integer", "default": 7}})
register_tool("telemetry_sessions", handler=get_session_stats, description="Get session statistics for last N days.", schema={"days": {"type": "integer", "default": 7}})
register_tool("telemetry_report", handler=format_telemetry_report, description="Generate comprehensive telemetry report.", schema={"days": {"type": "integer", "default": 7}})
register_tool("telemetry_purge", handler=purge_old_events, description="Purge telemetry events older than N days.", schema={"retention_days": {"type": "integer", "default": 30}})
