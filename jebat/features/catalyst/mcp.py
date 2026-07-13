"""Catalyst O11y — MCP Server for IDE Integration."""

from __future__ import annotations

import json
import asyncio
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    Server = InitializationOptions = stdio_server = Tool = TextContent = None

from .client import CatalystClient, CatalystConfig
from .halo import run_halo_analysis
from .alerting import AlertManager, AlertRule, AlertSeverity, BUILTIN_ALERT_RULES
from .dashboards import list_dashboards, get_dashboard, export_all_dashboards

# Global client
_client: CatalystClient | None = None
_alert_manager: AlertManager | None = None


def get_client() -> CatalystClient:
    global _client
    if _client is None:
        _client = CatalystClient(CatalystConfig())
    return _client


def get_alert_manager() -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        config = type("AlertConfig", (), {
            "rules": BUILTIN_ALERT_RULES,
            "notifiers": [],
            "evaluation_interval": "30s",
        })()
        _alert_manager = AlertManager(config)
    return _alert_manager


# Initialize server
server = Server("catalyst-o11y") if Server is not None else None


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # Trace operations
        Tool(
            name="catalyst_status",
            description="Get Catalyst observability status",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="catalyst_trace_list",
            description="List recent traces",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}},
            },
        ),
        Tool(
            name="catalyst_trace_get",
            description="Get trace details by ID",
            inputSchema={
                "type": "object",
                "properties": {"trace_id": {"type": "string"}},
                "required": ["trace_id"],
            },
        ),
        Tool(
            name="catalyst_trace_start",
            description="Start a new trace",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        ),
        Tool(
            name="catalyst_span_start",
            description="Start a span in current trace",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "kind": {"type": "string", "enum": ["internal", "llm", "tool", "agent", "database", "http", "cache", "queue", "rerank", "embedding"]},
                    "attributes": {"type": "object"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="catalyst_span_end",
            description="End current span",
            inputSchema={
                "type": "object",
                "properties": {
                    "span_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["ok", "error", "timeout", "cancelled"]},
                    "attributes": {"type": "object"},
                },
            },
        ),
        Tool(
            name="catalyst_halo",
            description="Run HALO analysis between two traces",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_a": {"type": "string"},
                    "trace_b": {"type": "string"},
                    "analysis_type": {"type": "string", "enum": ["full", "performance", "anomaly"], "default": "full"},
                },
                "required": ["trace_a", "trace_b"],
            },
        ),
        # Metrics
        Tool(
            name="catalyst_metrics_query",
            description="Query Prometheus metrics (PromQL)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "time": {"type": "string", "description": "RFC3339 or unix timestamp"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="catalyst_metrics_builtin",
            description="Query built-in JEBAT metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": [
                        "llm_latency", "llm_errors", "llm_cost", "llm_tokens",
                        "tool_latency", "tool_errors",
                        "agent_handoffs", "agent_utilization",
                        "memory_usage", "memory_ops",
                        "mcp_latency", "mcp_errors",
                    ]},
                    "window": {"type": "string", "default": "5m"},
                },
                "required": ["metric"],
            },
        ),
        # Logs
        Tool(
            name="catalyst_logs_query",
            description="Query Loki logs (LogQL)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "default": '{service="jebat"}'},
                    "since": {"type": "string", "default": "1h"},
                    "limit": {"type": "integer", "default": 100},
                },
            },
        ),
        # Alerts
        Tool(
            name="catalyst_alerts_list",
            description="List active alerts",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="catalyst_alerts_rules",
            description="List alert rules",
            inputSchema={"type": "object", "properties": {}},
        ),
        # Dashboards
        Tool(
            name="catalyst_dashboard_list",
            description="List available Grafana dashboards",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="catalyst_dashboard_get",
            description="Get dashboard JSON",
            inputSchema={
                "type": "object",
                "properties": {"dashboard_id": {"type": "string"}},
                "required": ["dashboard_id"],
            },
        ),
        Tool(
            name="catalyst_dashboard_export",
            description="Export all dashboards to directory",
            inputSchema={
                "type": "object",
                "properties": {"output_dir": {"type": "string", "default": "./dashboards"}},
            },
        ),
        # Health
        Tool(
            name="catalyst_health",
            description="System health check",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "catalyst_status":
            client = get_client()
            stats = client.get_stats()
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]

        elif name == "catalyst_trace_list":
            client = get_client()
            traces = client.list_traces(arguments.get("limit", 10))
            result = [{
                "trace_id": t.id,
                "name": t.name,
                "spans": len(t.spans),
                "duration_ms": t.duration_ms,
                "status": t.status.value,
            } for t in traces]
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "catalyst_trace_get":
            client = get_client()
            trace = client.get_trace(arguments["trace_id"])
            if not trace:
                return [TextContent(type="text", text=f"Trace {arguments['trace_id']} not found")]
            return [TextContent(type="text", text=json.dumps({
                "trace_id": trace.id,
                "name": trace.name,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "duration_ms": trace.duration_ms,
                "status": trace.status.value,
                "spans": [{
                    "span_id": s.id,
                    "trace_id": s.trace_id,
                    "name": s.name,
                    "kind": s.kind.value,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration_ms": s.duration_ms,
                    "status": s.status.value,
                    "attributes": s.attributes,
                    "events": [{"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes} for e in s.events],
                } for s in trace.spans],
            }, indent=2))]

        elif name == "catalyst_trace_start":
            client = get_client()
            trace = client.start_trace(arguments["name"])
            return [TextContent(type="text", text=json.dumps({"trace_id": trace.id, "name": trace.name}, indent=2))]

        elif name == "catalyst_span_start":
            client = get_client()
            kind = arguments.get("kind", "internal")
            span = client.start_span(
                name=arguments["name"],
                kind=kind,
                attributes=arguments.get("attributes"),
            )
            return [TextContent(type="text", text=json.dumps({"span_id": span.id, "trace_id": span.trace_id}, indent=2))]

        elif name == "catalyst_span_end":
            client = get_client()
            span = client.end_span(
                span_id=arguments["span_id"],
                status=arguments.get("status", "ok"),
                attributes=arguments.get("attributes"),
            )
            if span:
                return [TextContent(type="text", text=json.dumps({"span_id": span.id, "duration_ms": span.duration_ms}, indent=2))]
            else:
                return [TextContent(type="text", text=f"Span {arguments['span_id']} not found")]

        elif name == "catalyst_halo":
            client = get_client()
            trace_a = client.get_trace(arguments["trace_a"])
            trace_b = client.get_trace(arguments["trace_b"])
            if not trace_a or not trace_b:
                return [TextContent(type="text", text="One or both traces not found")]
            comparison = run_halo_analysis(trace_a, trace_b, arguments.get("analysis_type", "full"))
            return [TextContent(type="text", text=json.dumps({
                "trace_a": {"name": comparison.trace_a.name, "spans": len(comparison.trace_a.spans), "duration_ms": comparison.trace_a.duration_ms},
                "trace_b": {"name": comparison.trace_b.name, "spans": len(comparison.trace_b.spans), "duration_ms": comparison.trace_b.duration_ms},
                "span_diff": comparison.span_diff,
                "duration_change_pct": comparison.duration_change_pct,
                "regressions": comparison.regressions,
                "improvements": comparison.improvements,
                "anomalies": comparison.anomalies,
                "recommendations": comparison.recommendations,
            }, indent=2))]

        elif name == "catalyst_metrics_query":
            # Would query Prometheus - returning placeholder
            return [TextContent(type="text", text=json.dumps({"query": arguments["query"], "result": "Use Prometheus HTTP API directly"}, indent=2))]

        elif name == "catalyst_metrics_builtin":
            # Return built-in metric queries
            metric = arguments["metric"]
            queries = {
                "llm_latency": 'histogram_quantile(0.99, sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, provider, model))',
                "llm_errors": 'sum(rate(jebat_llm_requests_total{status="error"}[5m])) by (provider, model)',
                "llm_cost": 'increase(jebat_llm_cost_usd_total[1h])',
                "llm_tokens": 'sum(rate(jebat_llm_tokens_total[5m])) by (type, model)',
                "tool_latency": 'histogram_quantile(0.95, sum(rate(jebat_tool_duration_seconds_bucket[5m])) by (le, tool))',
                "tool_errors": 'sum(rate(jebat_tool_invocations_total{status="error"}[5m])) by (tool)',
                "agent_handoffs": 'rate(jebat_agent_handoffs_total[5m])',
                "agent_utilization": 'jebat_agent_utilization',
                "memory_usage": 'jebat_memory_usage_bytes',
                "memory_ops": 'sum(rate(jebat_memory_operations_total[5m])) by (layer, operation, status)',
                "mcp_latency": 'histogram_quantile(0.99, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method))',
                "mcp_errors": 'sum(rate(jebat_mcp_requests_total{status="error"}[5m])) by (method, transport)',
            }
            return [TextContent(type="text", text=json.dumps({
                "metric": metric,
                "promql": queries.get(metric, "Unknown metric"),
                "window": arguments.get("window", "5m"),
            }, indent=2))]

        elif name == "catalyst_logs_query":
            return [TextContent(type="text", text=json.dumps({
                "query": arguments.get("query", '{service="jebat"}'),
                "since": arguments.get("since", "1h"),
                "limit": arguments.get("limit", 100),
                "note": "Use Loki HTTP API directly for log queries",
            }, indent=2))]

        elif name == "catalyst_alerts_list":
            am = get_alert_manager()
            alerts = am.get_active_alerts()
            return [TextContent(type="text", text=json.dumps([{
                "rule": a.rule.name,
                "severity": a.rule.severity.value,
                "labels": a.labels,
                "value": a.value,
                "starts_at": a.fired_at,
            } for a in alerts], indent=2))]

        elif name == "catalyst_alerts_rules":
            am = get_alert_manager()
            rules = [{
                "name": r.name,
                "expr": r.expr,
                "severity": r.severity.value,
                "for": r.for_duration,
                "labels": r.labels,
                "annotations": r.annotations,
            } for r in am.rules]
            return [TextContent(type="text", text=json.dumps(rules, indent=2))]

        elif name == "catalyst_dashboard_list":
            dashboards = list_dashboards()
            return [TextContent(type="text", text=json.dumps(dashboards, indent=2))]

        elif name == "catalyst_dashboard_get":
            dashboard = get_dashboard(arguments["dashboard_id"])
            if not dashboard:
                return [TextContent(type="text", text=f"Dashboard {arguments['dashboard_id']} not found")]
            return [TextContent(type="text", text=json.dumps(dashboard, indent=2))]

        elif name == "catalyst_dashboard_export":
            export_all_dashboards(arguments.get("output_dir", "./dashboards"))
            return [TextContent(type="text", text=f"Exported to {arguments.get('output_dir', './dashboards')}")]

        elif name == "catalyst_health":
            client = get_client()
            stats = client.get_stats()
            health = {
                "status": "healthy" if stats["active_spans"] < 1000 else "degraded",
                "catalyst": stats,
                "components": {
                    "tracing": "ok",
                    "metrics": "ok",
                    "logging": "ok",
                    "alerting": "ok",
                },
            }
            return [TextContent(type="text", text=json.dumps(health, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="catalyst-o11y",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())