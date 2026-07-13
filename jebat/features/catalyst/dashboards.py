"""Catalyst O11y — Grafana Dashboard Exports."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_OVERVIEW_DASHBOARD = {
    "dashboard": {
        "title": "JEBAT System Overview",
        "uid": "jebat-system-overview",
        "tags": ["jebat", "system", "overview"],
        "timezone": "utc",
        "refresh": "30s",
        "panels": [
            {
                "id": 1,
                "title": "LLM Request Rate",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_llm_requests_total[5m])) by (provider, model)", "legendFormat": "{{provider}}/{{model}}"},
                ],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 2,
                "title": "LLM Latency (p50, p95, p99)",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "histogram_quantile(0.50, sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, provider))", "legendFormat": "p50"},
                    {"expr": "histogram_quantile(0.95, sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, provider))", "legendFormat": "p95"},
                    {"expr": "histogram_quantile(0.99, sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, provider))", "legendFormat": "p99"},
                ],
                "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 3,
                "title": "LLM Error Rate",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_llm_requests_total{status='error'}[5m])) by (provider) / sum(rate(jebat_llm_requests_total[5m])) by (provider)", "legendFormat": "{{provider}}"},
                ],
                "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
            },
            {
                "id": 4,
                "title": "Tool Invocation Rate",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_tool_invocations_total[5m])) by (tool, status)", "legendFormat": "{{tool}} ({{status}})"},
                ],
                "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
            },
            {
                "id": 5,
                "title": "Active Agents",
                "type": "stat",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_active_agents", "legendFormat": ""},
                ],
                "gridPos": {"x": 0, "y": 16, "w": 6, "h": 4},
            },
            {
                "id": 6,
                "title": "Agent Handoffs/min",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "rate(jebat_agent_handoffs_total[5m])", "legendFormat": "{{from_agent}} → {{to_agent}}"},
                ],
                "gridPos": {"x": 6, "y": 16, "w": 18, "h": 8},
            },
            {
                "id": 7,
                "title": "Memory Layer Usage",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_memory_usage_bytes", "legendFormat": "{{layer}}"},
                ],
                "gridPos": {"x": 0, "y": 24, "w": 12, "h": 8},
            },
            {
                "id": 8,
                "title": "Memory Operations",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_memory_operations_total[5m])) by (layer, operation, status)", "legendFormat": "{{layer}}/{{operation}} ({{status}})"},
                ],
                "gridPos": {"x": 12, "y": 24, "w": 12, "h": 8},
            },
            {
                "id": 9,
                "title": "MCP Request Rate",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_mcp_requests_total[5m])) by (method, transport, status)", "legendFormat": "{{method}} ({{transport}}) {{status}}"},
                ],
                "gridPos": {"x": 0, "y": 32, "w": 12, "h": 8},
            },
            {
                "id": 10,
                "title": "MCP Latency",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "histogram_quantile(0.99, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method))", "legendFormat": "p99 {{method}}"},
                ],
                "gridPos": {"x": 12, "y": 32, "w": 12, "h": 8},
            },
        ],
    },
}


LLM_HEALTH_DASHBOARD = {
    "dashboard": {
        "title": "JEBAT LLM Provider Health",
        "uid": "jebat-llm-health",
        "tags": ["jebat", "llm", "health"],
        "timezone": "utc",
        "refresh": "30s",
        "panels": [
            {
                "id": 1,
                "title": "Request Volume by Provider",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_llm_requests_total[5m])) by (provider)", "legendFormat": "{{provider}}"},
                ],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 2,
                "title": "Cost per Hour by Provider",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "increase(jebat_llm_cost_usd_total[1h])", "legendFormat": "{{provider}} - {{model}}"},
                ],
                "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 3,
                "title": "Latency Percentiles by Model",
                "type": "heatmap",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, model)", "format": "heatmap"},
                ],
                "gridPos": {"x": 0, "y": 8, "w": 24, "h": 10},
            },
            {
                "id": 4,
                "title": "Token Usage",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_llm_tokens_total{type='prompt'}[5m])) by (model)", "legendFormat": "Prompt {{model}}"},
                    {"expr": "sum(rate(jebat_llm_tokens_total{type='completion'}[5m])) by (model)", "legendFormat": "Completion {{model}}"},
                ],
                "gridPos": {"x": 0, "y": 18, "w": 12, "h": 8},
            },
            {
                "id": 5,
                "title": "Error Rate by Provider/Model",
                "type": "table",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": 'sum(rate(jebat_llm_requests_total{status="error"}[5m])) by (provider, model) / sum(rate(jebat_llm_requests_total[5m])) by (provider, model)', "format": "table"},
                ],
                "gridPos": {"x": 12, "y": 18, "w": 12, "h": 8},
            },
        ],
    },
}


AGENT_ORCHESTRATION_DASHBOARD = {
    "dashboard": {
        "title": "JEBAT Agent Orchestration",
        "uid": "jebat-agent-orchestration",
        "tags": ["jebat", "agents", "orchestration"],
        "timezone": "utc",
        "refresh": "30s",
        "panels": [
            {
                "id": 1,
                "title": "Agent Handoff Flow",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "rate(jebat_agent_handoffs_total[5m])", "legendFormat": "{{from_agent}} → {{to_agent}}"},
                ],
                "gridPos": {"x": 0, "y": 0, "w": 24, "h": 8},
            },
            {
                "id": 2,
                "title": "Swarm Efficiency",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_swarm_task_completion_rate", "legendFormat": "Completion Rate"},
                    {"expr": "jebat_swarm_task_failure_rate", "legendFormat": "Failure Rate"},
                ],
                "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
            },
            {
                "id": 3,
                "title": "Agent Utilization",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_agent_utilization", "legendFormat": "{{agent}}"},
                ],
                "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
            },
        ],
    },
}


MEMORY_LAYERS_DASHBOARD = {
    "dashboard": {
        "title": "JEBAT Memory Layers",
        "uid": "jebat-memory-layers",
        "tags": ["jebat", "memory"],
        "timezone": "utc",
        "refresh": "30s",
        "panels": [
            {
                "id": 1,
                "title": "Memory Layer Usage",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_memory_usage_bytes", "legendFormat": "{{layer}}"},
                ],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 2,
                "title": "Memory Operations",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_memory_operations_total[5m])) by (layer, operation, status)", "legendFormat": "{{layer}}/{{operation}} ({{status}})"},
                ],
                "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 3,
                "title": "Consolidation Duration",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_memory_consolidation_duration_seconds", "legendFormat": "{{layer}}"},
                ],
                "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
            },
        ],
    },
}


MCP_BUS_DASHBOARD = {
    "dashboard": {
        "title": "JEBAT MCP Protocol Bus",
        "uid": "jebat-mcp-bus",
        "tags": ["jebat", "mcp"],
        "timezone": "utc",
        "refresh": "30s",
        "panels": [
            {
                "id": 1,
                "title": "MCP Request Rate",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_mcp_requests_total[5m])) by (method, transport, status)", "legendFormat": "{{method}} ({{transport}}) {{status}}"},
                ],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 2,
                "title": "MCP Latency (p50/p95/p99)",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "histogram_quantile(0.50, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method))", "legendFormat": "p50 {{method}}"},
                    {"expr": "histogram_quantile(0.95, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method))", "legendFormat": "p95 {{method}}"},
                    {"expr": "histogram_quantile(0.99, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method))", "legendFormat": "p99 {{method}}"},
                ],
                "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 3,
                "title": "Tools Registered",
                "type": "stat",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_mcp_tools_registered", "legendFormat": ""},
                ],
                "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4},
            },
            {
                "id": 4,
                "title": "Active Connections",
                "type": "stat",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_mcp_active_connections", "legendFormat": ""},
                ],
                "gridPos": {"x": 6, "y": 8, "w": 6, "h": 4},
            },
        ],
    },
}


# ── Context Budget Dashboard ────────────────────────────────────────────────

CONTEXT_BUDGET_DASHBOARD = {
    "dashboard": {
        "title": "JEBAT Context Budget",
        "uid": "jebat-context-budget",
        "tags": ["jebat", "context", "tokens", "budget"],
        "timezone": "utc",
        "refresh": "10s",
        "panels": [
            {
                "id": 1,
                "title": "Token Budget Allocation",
                "type": "pie",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_context_tokens_total{section='system_prompt'}", "legendFormat": "System Prompt"},
                    {"expr": "jebat_context_tokens_total{section='memory_context'}", "legendFormat": "Memory Context"},
                    {"expr": "jebat_context_tokens_total{section='working_memory'}", "legendFormat": "Working Memory"},
                    {"expr": "jebat_context_tokens_total{section='cross_session'}", "legendFormat": "Cross-Session"},
                    {"expr": "jebat_context_tokens_total{section='history'}", "legendFormat": "History"},
                ],
                "gridPos": {"x": 0, "y": 0, "w": 8, "h": 8},
            },
            {
                "id": 2,
                "title": "Token Usage Over Time",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "rate(jebat_context_tokens_total[1m])", "legendFormat": "{{section}}"},
                ],
                "gridPos": {"x": 8, "y": 0, "w": 16, "h": 8},
            },
            {
                "id": 3,
                "title": "Context Utilization %",
                "type": "gauge",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_context_utilization_ratio * 100", "legendFormat": "{{section}}"},
                ],
                "gridPos": {"x": 0, "y": 8, "w": 12, "h": 6},
                "options": {
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 90},
                        ]
                    },
                },
            },
            {
                "id": 4,
                "title": "Adaptive Compaction Events",
                "type": "stat",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_compaction_events_total[5m]))", "legendFormat": "compactions/min"},
                ],
                "gridPos": {"x": 12, "y": 8, "w": 6, "h": 6},
            },
            {
                "id": 5,
                "title": "Memory Recall Hits",
                "type": "stat",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "sum(rate(jebat_memory_recall_total[5m]))", "legendFormat": "recalls/min"},
                ],
                "gridPos": {"x": 18, "y": 8, "w": 6, "h": 6},
            },
            {
                "id": 6,
                "title": "Working Memory Utilization",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "jebat_working_memory_goals", "legendFormat": "Goals"},
                    {"expr": "jebat_working_memory_facts", "legendFormat": "Facts"},
                    {"expr": "jebat_working_memory_constraints", "legendFormat": "Constraints"},
                ],
                "gridPos": {"x": 0, "y": 14, "w": 12, "h": 8},
            },
            {
                "id": 7,
                "title": "Cost per Token by Provider",
                "type": "graph",
                "datasource": "Prometheus",
                "targets": [
                    {"expr": "rate(jebat_cost_usd_total[5m]) / rate(jebat_tokens_total[5m])", "legendFormat": "{{provider}}"},
                ],
                "gridPos": {"x": 12, "y": 14, "w": 12, "h": 8},
            },
        ],
    },
}


ALL_DASHBOARDS = {
    "system-overview": SYSTEM_OVERVIEW_DASHBOARD,
    "llm-health": LLM_HEALTH_DASHBOARD,
    "agent-orchestration": AGENT_ORCHESTRATION_DASHBOARD,
    "memory-layers": MEMORY_LAYERS_DASHBOARD,
    "mcp-bus": MCP_BUS_DASHBOARD,
    "context-budget": CONTEXT_BUDGET_DASHBOARD,
}


def get_dashboard(dashboard_id: str) -> dict[str, Any]:
    """Get dashboard JSON by ID."""
    return ALL_DASHBOARDS.get(dashboard_id, {})


def list_dashboards() -> list[dict[str, str]]:
    """List available dashboards."""
    return [
        {"id": k, "title": v["dashboard"]["title"], "description": "JEBAT " + v["dashboard"]["title"]}
        for k, v in ALL_DASHBOARDS.items()
    ]


def export_all_dashboards(output_dir: str = "./dashboards") -> None:
    """Export all dashboards as JSON files."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    for dash_id, dashboard in ALL_DASHBOARDS.items():
        with open(os.path.join(output_dir, f"{dash_id}.json"), "w") as f:
            json.dump(dashboard, f, indent=2)
    print(f"Exported {len(ALL_DASHBOARDS)} dashboards to {output_dir}")