"""JEBAT Cost Tracking — Token usage and cost dashboard per session.

Tracks:
  - Token usage per provider/model
  - Estimated cost per session/day/week
  - Rate limits and quota monitoring
  - Export to CSV/JSON for analysis

This is the Bendahara (Treasurer) — every token spent is accounted for.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ── Pricing Data (per 1M tokens) ─────────────────────────────────────────

# These prices are approximate and should be updated periodically
PRICING_TABLE: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    # Anthropic
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-opus-4": {"input": 15.00, "output": 75.00},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.00},
    # Google
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    # GLM / MiniMax (9Router)
    "glm-4-flash": {"input": 0.06, "output": 0.06},
    "MiniMax-Text-01": {"input": 0.02, "output": 0.02},
    # Free models (via 9Router)
    "kr/claude-sonnet-4.5": {"input": 0.00, "output": 0.00},
    "kr/claude-opus-4": {"input": 0.00, "output": 0.00},
    "oc/claude-sonnet-4.5": {"input": 0.00, "output": 0.00},
    "vtx/gemini-2.5-pro": {"input": 0.00, "output": 0.00},
    # Ollama (local — free)
    "llama3": {"input": 0.00, "output": 0.00},
    "mistral": {"input": 0.00, "output": 0.00},
    "codellama": {"input": 0.00, "output": 0.00},
}

COST_DATA_DIR = os.path.expanduser("~/.jebat/cost_tracking")


@dataclass(slots=True)
class TokenRecord:
    """Single token usage record."""
    timestamp: str = ""
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    session_id: str = ""
    operation: str = ""  # chat, agent, search, etc.


@dataclass(slots=True)
class CostSummary:
    """Cost summary for a time period."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    by_provider: dict[str, float] = field(default_factory=dict)
    by_model: dict[str, float] = field(default_factory=dict)
    by_operation: dict[str, float] = field(default_factory=dict)
    records_count: int = 0


# ── Cost Tracking Engine ──────────────────────────────────────────────────

def record_usage(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    operation: str = "chat",
    session_id: str = "",
) -> TokenRecord:
    """Record token usage and calculate cost.

    Args:
        provider: LLM provider name
        model: Model name
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        operation: Type of operation (chat, agent, search)
        session_id: Session identifier

    Returns:
        TokenRecord with calculated cost
    """
    # Calculate cost
    pricing = PRICING_TABLE.get(model, {"input": 0.0, "output": 0.0})
    cost = (
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"]
    )

    record = TokenRecord(
        timestamp=datetime.now().isoformat(),
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_usd=cost,
        session_id=session_id or datetime.now().strftime("%Y%m%d"),
        operation=operation,
    )

    # Save to daily log
    _save_record(record)

    return record


def _save_record(record: TokenRecord) -> None:
    """Save a token record to the daily CSV log."""
    os.makedirs(COST_DATA_DIR, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(COST_DATA_DIR, f"{date_str}.csv")

    # Create file with header if it doesn't exist
    if not os.path.exists(log_path):
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "provider", "model", "input_tokens",
                "output_tokens", "total_tokens", "cost_usd",
                "session_id", "operation",
            ])

    # Append record
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            record.timestamp, record.provider, record.model,
            record.input_tokens, record.output_tokens,
            record.total_tokens, f"{record.cost_usd:.6f}",
            record.session_id, record.operation,
        ])


def get_daily_summary(date: str | None = None) -> CostSummary:
    """Get cost summary for a specific day.

    Args:
        date: Date string (YYYY-MM-DD), defaults to today

    Returns:
        CostSummary with aggregated stats
    """
    date_str = date or datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(COST_DATA_DIR, f"{date_str}.csv")

    if not os.path.exists(log_path):
        return CostSummary()

    summary = CostSummary()
    by_provider: dict[str, float] = {}
    by_model: dict[str, float] = {}
    by_operation: dict[str, float] = {}

    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            summary.total_input_tokens += int(row.get("input_tokens", 0))
            summary.total_output_tokens += int(row.get("output_tokens", 0))
            summary.total_tokens += int(row.get("total_tokens", 0))
            summary.total_cost_usd += float(row.get("cost_usd", 0))
            summary.records_count += 1

            provider = row.get("provider", "unknown")
            model = row.get("model", "unknown")
            operation = row.get("operation", "unknown")
            cost = float(row.get("cost_usd", 0))

            by_provider[provider] = by_provider.get(provider, 0) + cost
            by_model[model] = by_model.get(model, 0) + cost
            by_operation[operation] = by_operation.get(operation, 0) + cost

    summary.by_provider = by_provider
    summary.by_model = by_model
    summary.by_operation = by_operation

    return summary


def get_weekly_summary() -> CostSummary:
    """Get cost summary for the last 7 days."""
    weekly = CostSummary()

    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        daily = get_daily_summary(date)

        weekly.total_input_tokens += daily.total_input_tokens
        weekly.total_output_tokens += daily.total_output_tokens
        weekly.total_tokens += daily.total_tokens
        weekly.total_cost_usd += daily.total_cost_usd
        weekly.records_count += daily.records_count

        # Merge by-provider/model/operation dicts
        for key, val in daily.by_provider.items():
            weekly.by_provider[key] = weekly.by_provider.get(key, 0) + val
        for key, val in daily.by_model.items():
            weekly.by_model[key] = weekly.by_model.get(key, 0) + val
        for key, val in daily.by_operation.items():
            weekly.by_operation[key] = weekly.by_operation.get(key, 0) + val

    return weekly


def format_summary(summary: CostSummary, period: str = "daily") -> str:
    """Format a CostSummary as a readable report.

    Args:
        summary: CostSummary to format
        period: Period label (daily/weekly)

    Returns:
        Formatted string report
    """
    lines = [
        f"=== JEBAT Cost Report ({period}) ===",
        f"Total tokens: {summary.total_tokens:,}",
        f"  Input:  {summary.total_input_tokens:,}",
        f"  Output: {summary.total_output_tokens:,}",
        f"Total cost: ${summary.total_cost_usd:.4f}",
        f"Records: {summary.records_count}",
        "",
    ]

    if summary.by_provider:
        lines.append("By Provider:")
        for provider, cost in sorted(summary.by_provider.items(), key=lambda x: -x[1]):
            lines.append(f"  {provider}: ${cost:.4f}")

    if summary.by_model:
        lines.append("\nBy Model:")
        for model, cost in sorted(summary.by_model.items(), key=lambda x: -x[1]):
            lines.append(f"  {model}: ${cost:.4f}")

    if summary.by_operation:
        lines.append("\nBy Operation:")
        for op, cost in sorted(summary.by_operation.items(), key=lambda x: -x[1]):
            lines.append(f"  {op}: ${cost:.4f}")

    return "\n".join(lines)


def export_to_json(days: int = 7, output_path: str | None = None) -> str:
    """Export cost tracking data to JSON.

    Args:
        days: Number of days to export
        output_path: Output file path (default: auto-generated)

    Returns:
        Path to exported JSON file
    """
    records: list[dict[str, Any]] = []

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_path = os.path.join(COST_DATA_DIR, f"{date}.csv")

        if not os.path.exists(log_path):
            continue

        with open(log_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)

    if output_path is None:
        output_path = os.path.join(
            COST_DATA_DIR,
            f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    return output_path


# ── Cost Tools Registry ──────────────────────────────────────────────────

COST_TOOLS: dict[str, dict[str, Any]] = {
    "record_usage": {
        "description": "Record token usage and calculate cost",
        "safety": "auto",
        "handler": record_usage,
        "parameters": {
            "provider": {"type": "string"},
            "model": {"type": "string"},
            "input_tokens": {"type": "integer"},
            "output_tokens": {"type": "integer"},
            "operation": {"type": "string", "default": "chat"},
        },
    },
    "get_daily_summary": {
        "description": "Get cost summary for today (or a specific day)",
        "safety": "auto",
        "handler": get_daily_summary,
        "parameters": {"date": {"type": "string", "description": "YYYY-MM-DD or empty for today"}},
    },
    "get_weekly_summary": {
        "description": "Get cost summary for the last 7 days",
        "safety": "auto",
        "handler": get_weekly_summary,
        "parameters": {},
    },
    "format_summary": {
        "description": "Format a cost summary as readable report",
        "safety": "auto",
        "handler": format_summary,
        "parameters": {"period": {"type": "string", "default": "daily"}},
    },
    "export_to_json": {
        "description": "Export cost tracking data to JSON",
        "safety": "auto",
        "handler": export_to_json,
        "parameters": {"days": {"type": "integer", "default": 7}},
    },
}


def list_cost_tools() -> list[dict[str, str]]:
    """List all cost tracking tools."""
    return [
        {"name": name, "description": info["description"], "safety": info["safety"]}
        for name, info in COST_TOOLS.items()
    ]


# ── Tool Handler Wrappers ─────────────────────────────────────────────────

def get_summary(period: str = "daily", date: str | None = None) -> str:
    """Get cost summary for a period (daily or weekly).

    Args:
        period: 'daily' or 'weekly'
        date: Date string (YYYY-MM-DD) for daily; ignored for weekly

    Returns:
        Formatted cost summary string
    """
    if period == "weekly":
        summary = get_weekly_summary()
    else:
        summary = get_daily_summary(date)
    return format_summary(summary, period)


def get_pricing() -> str:
    """Show the pricing table for all supported models.

    Returns:
        Formatted pricing table string
    """
    lines = ["=== JEBAT Pricing Table (per 1M tokens) ===", ""]
    lines.append(f"{'Model':<30} {'Input':>10} {'Output':>10}")
    lines.append("-" * 52)
    for model in sorted(PRICING_TABLE.keys()):
        p = PRICING_TABLE[model]
        lines.append(f"{model:<30} ${p['input']:>8.2f} ${p['output']:>8.2f}")
    return "\n".join(lines)


# ── Tool Registration ────────────────────────────────────────────────────

from jebat.tools import register_tool  # noqa: E402

# ── Auto-profile Tuner ─────────────────────────────────────────────────────
# Uses real cost data to recommend profile switching when budgets are exceeded.

BUDGET_CAPS: dict[str, float] = {
    "daily_warn": 0.50,   # Warn at $0.50/day
    "daily_critical": 1.00,  # Force reduction at $1.00/day
    "weekly_warn": 3.00,
    "weekly_critical": 5.00,
}


def recommend_profile() -> dict:
    """Analyse recent cost data and recommend a profile level + action.

    Returns:
        dict with keys: recommended_profile, reason, cost_today, cost_weekly, action
    """
    from jebat.features.cost_tracking.cost_tracking import get_daily_summary, get_weekly_summary

    today = get_daily_summary()
    week = get_weekly_summary()

    cost_today = today.total_cost_usd
    cost_weekly = week.total_cost_usd

    recommendation = "cavement"
    reasons: list[str] = []

    if cost_today >= BUDGET_CAPS["daily_critical"] or cost_weekly >= BUDGET_CAPS["weekly_critical"]:
        recommendation = "cavement"
        reasons.append(f"cost critical - ${cost_today:.2f} today, ${cost_weekly:.2f}/week")
    elif cost_today >= BUDGET_CAPS["daily_warn"] or cost_weekly >= BUDGET_CAPS["weekly_warn"]:
        recommendation = "lean"
        reasons.append(f"cost warning - ${cost_today:.2f} today, ${cost_weekly:.2f}/week")
    else:
        recommendation = "deep"
        reasons.append("budget healthy")

    return {
        "recommended_profile": recommendation,
        "reason": "; ".join(reasons),
        "cost_today": round(cost_today, 4),
        "cost_weekly": round(cost_weekly, 4),
        "action": "switch" if recommendation != "deep" else "keep",
    }


def tune_prompt_profile(current_profile: str = "deep") -> str:
    """Return the recommended profile based on real cost data.

    Args:
        current_profile: The profile currently active.

    Returns:
        Recommended profile name (cavement, lean, or deep).
    """
    rec = recommend_profile()
    return rec["recommended_profile"]



register_tool(
    name="cost_record",
    description="Record token usage with provider/model/tokens and calculate cost",
    handler=record_usage,
    schema={
        "provider": {"type": "string", "description": "LLM provider name (e.g. openai, anthropic)"},
        "model": {"type": "string", "description": "Model name (e.g. gpt-4o, claude-sonnet-4-5)"},
        "input_tokens": {"type": "integer", "description": "Number of input/prompt tokens"},
        "output_tokens": {"type": "integer", "description": "Number of output/completion tokens"},
        "operation": {"type": "string", "description": "Type of operation (chat, agent, search)", "default": "chat"},
        "session_id": {"type": "string", "description": "Session identifier", "default": ""},
    },
)

register_tool(
    name="cost_summary",
    description="Get cost summary for a period (daily or weekly)",
    handler=get_summary,
    schema={
        "period": {"type": "string", "description": "Summary period: 'daily' or 'weekly'", "default": "daily"},
        "date": {"type": "string", "description": "Date string (YYYY-MM-DD) for daily summaries", "default": None},
    },
)

register_tool(
    name="cost_pricing",
    description="Show the pricing table for all supported LLM models",
    handler=get_pricing,
    schema={},
)