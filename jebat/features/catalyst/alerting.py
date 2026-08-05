"""Catalyst O11y — Alerting Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class AlertRule:
    """Alert rule definition (PrometheusRule compatible)."""
    name: str
    expr: str
    severity: AlertSeverity
    for_duration: str = "5m"  # e.g., "5m", "1h"
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def to_prometheus_rule(self) -> dict[str, Any]:
        """Convert to PrometheusRule format."""
        return {
            "alert": self.name,
            "expr": self.expr,
            "for": self.for_duration,
            "labels": {
                "severity": self.severity.value,
                **self.labels,
            },
            "annotations": self.annotations,
        }


# ─── Built-in Alert Rules ────────────────────────────────────────

BUILTIN_ALERT_RULES = [
    # LLM Alerts
    AlertRule(
        name="LLMHighLatency",
        expr='histogram_quantile(0.99, sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, provider, model)) > 30',
        severity=AlertSeverity.CRITICAL,
        for_duration="5m",
        labels={"component": "llm", "team": "platform"},
        annotations={
            "summary": "LLM p99 latency > 30s for {{ $labels.provider }}/{{ $labels.model }}",
            "description": "LLM provider {{ $labels.provider }} model {{ $labels.model }} has p99 latency of {{ $value }}s",
            "runbook": "https://runbooks.jebat.ai/llm-high-latency",
        },
    ),
    AlertRule(
        name="LLMHighErrorRate",
        expr='sum(rate(jebat_llm_requests_total{status="error"}[5m])) by (provider, model) / sum(rate(jebat_llm_requests_total[5m])) by (provider, model) > 0.05',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "llm", "team": "platform"},
        annotations={
            "summary": "LLM error rate > 5% for {{ $labels.provider }}/{{ $labels.model }}",
            "description": "Error rate is {{ $value | humanizePercentage }} for {{ $labels.provider }}/{{ $labels.model }}",
        },
    ),
    AlertRule(
        name="LLMHighCost",
        expr='increase(jebat_llm_cost_usd_total[1h]) > 100',
        severity=AlertSeverity.WARNING,
        for_duration="1h",
        labels={"component": "llm", "team": "finance"},
        annotations={
            "summary": "LLM cost > $100/hour for {{ $labels.provider }}/{{ $labels.model }}",
        },
    ),

    # Tool Alerts
    AlertRule(
        name="ToolHighFailureRate",
        expr='sum(rate(jebat_tool_invocations_total{status="error"}[5m])) by (tool) / sum(rate(jebat_tool_invocations_total[5m])) by (tool) > 0.1',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "tools", "team": "platform"},
        annotations={
            "summary": "Tool {{ $labels.tool }} failure rate > 10%",
        },
    ),
    AlertRule(
        name="ToolHighLatency",
        expr='histogram_quantile(0.95, sum(rate(jebat_tool_duration_seconds_bucket[5m])) by (le, tool)) > 10',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "tools", "team": "platform"},
        annotations={
            "summary": "Tool {{ $labels.tool }} p95 latency > 10s",
        },
    ),

    # Agent Alerts
    AlertRule(
        name="AgentStuck",
        expr='time() - jebat_agent_last_activity_timestamp_seconds > 600',
        severity=AlertSeverity.CRITICAL,
        for_duration="10m",
        labels={"component": "agents", "team": "platform"},
        annotations={
            "summary": "Agent {{ $labels.agent_id }} stuck for > 10 minutes",
        },
    ),

    # Memory Alerts
    AlertRule(
        name="MemoryHighPressure",
        expr='jebat_memory_usage_bytes / jebat_memory_limit_bytes > 0.85',
        severity=AlertSeverity.WARNING,
        for_duration="10m",
        labels={"component": "memory", "team": "platform"},
        annotations={
            "summary": "Memory layer {{ $labels.layer }} at {{ $value | humanizePercentage }} capacity",
        },
    ),
    AlertRule(
        name="MemoryConsolidationLag",
        expr='time() - jebat_memory_last_consolidation_timestamp_seconds > 3600',
        severity=AlertSeverity.WARNING,
        for_duration="1h",
        labels={"component": "memory", "team": "platform"},
        annotations={
            "summary": "Memory consolidation hasn't run in > 1 hour for {{ $labels.layer }}",
        },
    ),

    # MCP Alerts
    AlertRule(
        name="MCPHighLatency",
        expr='histogram_quantile(0.99, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method, transport)) > 10',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "mcp", "team": "platform"},
        annotations={
            "summary": "MCP {{ $labels.method }} p99 latency > 10s",
        },
    ),
    AlertRule(
        name="MCPRequestFailures",
        expr='sum(rate(jebat_mcp_requests_total{status="error"}[5m])) by (method, transport) / sum(rate(jebat_mcp_requests_total[5m])) by (method, transport) > 0.02',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "mcp", "team": "platform"},
        annotations={
            "summary": "MCP {{ $labels.method }} failure rate > 2%",
        },
    ),

    # System Alerts
    AlertRule(
        name="HighMemoryUsage",
        expr='jebat_memory_usage_bytes > 8e9',  # 8GB
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "system", "team": "platform"},
        annotations={
            "summary": "Process memory usage > 8GB",
        },
    ),
    AlertRule(
        name="HighCPUUsage",
        expr='rate(process_cpu_seconds_total[5m]) > 4',  # 4 cores
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "system", "team": "platform"},
        annotations={
            "summary": "Process CPU usage > 400% (4 cores)",
        },
    ),
]

# ─── Alert Config ──────────────────────────────────────────────────

@dataclass
class AlertConfig:
    """Alerting configuration."""
    evaluation_interval: str = "30s"
    default_for: str = "5m"
    notifiers: list[dict[str, Any]] = field(default_factory=list)
    rules: list[AlertRule] = field(default_factory=list)


# ─── Alert Manager ──────────────────────────────────────────────

@dataclass
class Alert:
    """Fired alert instance."""
    rule: AlertRule
    value: float
    labels: dict[str, str]
    annotations: dict[str, str]
    fired_at: float
    status: str = "firing"  # firing, resolved


class AlertManager:
    """Manages alert evaluation and notification."""

    def __init__(self, evaluation_interval: float = 30.0):
        self.rules: list[AlertRule] = []
        self.active_alerts: dict[str, Alert] = {}
        self.notifiers: list[Callable[[Alert], None]] = []
        self.evaluation_interval = evaluation_interval

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules.append(rule)

    def add_notifier(self, notifier: Callable[[Alert], None]) -> None:
        """Add a notification callback."""
        self.notifiers.append(notifier)

    def evaluate(self, query_fn: Callable[[str], dict[str, Any]]) -> list[Alert]:
        """Evaluate all rules against Prometheus queries."""
        fired = []

        for rule in self.rules:
            try:
                result = query_fn(rule.expr)
                # result should be: {"metric": {...}, "value": [timestamp, value]}
                for series in result.get("data", {}).get("result", []):
                    value = float(series["value"][1])
                    labels = series.get("metric", {})

                    alert_key = f"{rule.name}:{json.dumps(labels, sort_keys=True)}"

                    if alert_key not in self.active_alerts:
                        # New alert
                        alert = Alert(
                            rule=rule,
                            value=value,
                            labels=labels,
                            annotations=self._render_annotations(rule, labels, value),
                            fired_at=time.time(),
                        )
                        self.active_alerts[alert_key] = alert
                        fired.append(alert)
                        self._notify(alert)
                    else:
                        # Update existing
                        self.active_alerts[alert_key].value = value
            except Exception as e:
                logging.getLogger(__name__).error(f"Alert evaluation failed for {rule.name}: {e}")

        return fired

    def _render_annotations(self, rule: AlertRule, labels: dict, value: float) -> dict[str, str]:
        """Render annotation templates."""
        context = {"labels": labels, "value": value}
        rendered = {}
        for k, v in rule.annotations.items():
            try:
                rendered[k] = v.format(**context)
            except Exception:
                rendered[k] = v
        return rendered

    def _notify(self, alert: Alert) -> None:
        """Send notifications for alert."""
        for notifier in self.notifiers:
            try:
                notifier(alert)
            except Exception as e:
                logging.getLogger(__name__).error(f"Notifier failed: {e}")

    def get_active_alerts(self) -> list[Alert]:
        """Get all currently firing alerts."""
        return list(self.active_alerts.values())

    def get_alert_summary(self) -> dict[str, int]:
        """Get alert counts by severity."""
        summary = {s.value: 0 for s in AlertSeverity}
        for alert in self.active_alerts.values():
            summary[alert.rule.severity.value] += 1
        return summary


# ─── Notifier Classes ──────────────────────────────────────────────

class WebhookNotifier:
    """HTTP webhook notifier."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
        template: str | None = None,
    ):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.template = template
        import httpx
        self._client = httpx.Client(timeout=timeout)

    def notify(self, alert: Alert, is_resolved: bool = False) -> None:
        payload = {
            "alert": {
                "rule": alert.rule.name,
                "severity": alert.rule.severity.value,
                "state": "resolved" if is_resolved else "firing",
                "labels": alert.labels,
                "annotations": alert.annotations,
                "value": alert.value,
                "starts_at": alert.fired_at,
                "ends_at": alert.fired_at,
                "fingerprint": alert.fingerprint,
            }
        }

        if self.template:
            import string
            t = string.Template(self.template)
            payload = json.loads(t.safe_substitute(payload=json.dumps(payload)))

        try:
            response = self._client.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            logging.getLogger(__name__).error(f"Webhook notification failed: {e}")


class SlackNotifier:
    """Slack webhook notifier."""

    def __init__(self, webhook_url: str, channel: str | None = None, username: str = "Catalyst"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        import httpx
        self._client = httpx.Client(timeout=10.0)

    def notify(self, alert: Alert, is_resolved: bool = False) -> None:
        color = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.CRITICAL: "#ff0000",
        }.get(alert.rule.severity, "#808080")

        if is_resolved:
            color = "#36a64f"

        payload = {
            "username": self.username,
            "attachments": [{
                "color": color,
                "title": f"{'✅ Resolved' if is_resolved else '🚨 Firing'}: {alert.rule.name}",
                "fields": [
                    {"title": "Severity", "value": alert.rule.severity.value.upper(), "short": True},
                    {"title": "Value", "value": str(alert.value), "short": True},
                ],
                "footer": "Catalyst O11y",
                "ts": int(alert.fired_at),
            }],
        }

        if self.channel:
            payload["channel"] = self.channel

        for k, v in alert.labels.items():
            payload["attachments"][0]["fields"].append({"title": k, "value": v, "short": True})
        for k, v in alert.annotations.items():
            payload["attachments"][0]["fields"].append({"title": k, "value": v, "short": True})

        try:
            self._client.post(self.webhook_url, json=payload)
        except Exception as e:
            logging.getLogger(__name__).error(f"Slack notification failed: {e}")


class PagerDutyNotifier:
    """PagerDuty Events API v2 notifier."""

    def __init__(self, integration_key: str, severity: str = "critical"):
        self.integration_key = integration_key
        self.default_severity = severity
        import httpx
        self._client = httpx.Client(timeout=10.0)
        self._endpoint = "https://events.pagerduty.com/v2/enqueue"

    def notify(self, alert: Alert, is_resolved: bool = False) -> None:
        event_action = "resolve" if is_resolved else "trigger"
        severity = "info" if is_resolved else (
            self.default_severity if alert.rule.severity == AlertSeverity.CRITICAL else alert.rule.severity.value
        )

        payload = {
            "routing_key": self.integration_key,
            "event_action": event_action,
            "dedup_key": alert.fingerprint,
            "payload": {
                "summary": f"{'Resolved' if is_resolved else 'Alert'}: {alert.rule.name}",
                "severity": severity,
                "source": "catalyst",
                "custom_details": {
                    "rule": alert.rule.name,
                    "labels": alert.labels,
                    "annotations": alert.annotations,
                    "value": alert.value,
                },
            },
        }

        try:
            self._client.post(self._endpoint, json=payload)
        except Exception as e:
            logging.getLogger(__name__).error(f"PagerDuty notification failed: {e}")


# Alias for backward compatibility
DEFAULT_ALERT_RULES = BUILTIN_ALERT_RULES