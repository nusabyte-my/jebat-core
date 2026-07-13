"""Catalyst O11y — CLI Commands for JEBAT."""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Optional

from .client import CatalystClient, CatalystConfig
from .halo import run_halo_analysis
from .alerting import AlertManager, BUILTIN_ALERT_RULES, AlertRule, AlertSeverity
from .dashboards import list_dashboards, get_dashboard, export_all_dashboards


def add_catalyst_commands(subparsers: argparse._SubParsersAction) -> None:
    """Add Catalyst commands to CLI."""
    cat_parser = subparsers.add_parser("catalyst", help="Catalyst observability")
    cat_sub = cat_parser.add_subparsers(dest="catalyst_cmd", required=True)

    # status
    cat_sub.add_parser("status", help="Show Catalyst status").set_defaults(func=cmd_status)

    # init
    init_p = cat_sub.add_parser("init", help="Initialize Catalyst")
    init_p.add_argument("--gateway", action="store_true", help="With Gateway")
    init_p.set_defaults(func=cmd_init)

    # instrument
    cat_sub.add_parser("instrument", help="Auto-instrument JEBAT").set_defaults(func=cmd_instrument)

    # trace
    trace_p = cat_sub.add_parser("trace", help="Start a trace")
    trace_p.add_argument("name", help="Trace name")
    trace_p.set_defaults(func=cmd_trace)

    # list traces
    list_p = cat_sub.add_parser("list", help="List recent traces")
    list_p.add_argument("--limit", type=int, default=10)
    list_p.set_defaults(func=cmd_list)

    # get trace
    get_p = cat_sub.add_parser("get", help="Get trace details")
    get_p.add_argument("trace_id", help="Trace ID")
    get_p.set_defaults(func=cmd_get)

    # halo
    halo_p = cat_sub.add_parser("halo", help="HALO analysis between traces")
    halo_p.add_argument("trace_a", help="Baseline trace ID")
    halo_p.add_argument("trace_b", help="Current trace ID")
    halo_p.add_argument("--type", default="full", choices=["full", "performance", "anomaly"])
    halo_p.set_defaults(func=cmd_halo)

    # metrics
    metrics_p = cat_sub.add_parser("metrics", help="Query metrics")
    metrics_p.add_argument("query", nargs="?", help="PromQL query")
    metrics_p.add_argument("--builtin", help="Built-in metric name")
    metrics_p.set_defaults(func=cmd_metrics)

    # alerts
    alert_p = cat_sub.add_parser("alerts", help="Alert operations")
    alert_sub = alert_p.add_subparsers(dest="alert_cmd", required=True)
    alert_sub.add_parser("list", help="List firing alerts").set_defaults(func=cmd_alerts_list)
    alert_sub.add_parser("rules", help="List alert rules").set_defaults(func=cmd_alerts_rules)

    # dashboards
    dash_p = cat_sub.add_parser("dashboard", help="Dashboard operations")
    dash_sub = dash_p.add_subparsers(dest="dash_cmd", required=True)
    dash_sub.add_parser("list", help="List dashboards").set_defaults(func=cmd_dashboard_list)
    dash_sub.add_parser("export", help="Export all dashboards").set_defaults(func=cmd_dashboard_export)

    # health
    cat_sub.add_parser("health", help="System health check").set_defaults(func=cmd_health)


# ─── Command Handlers ──────────────────────────────────────────

_client: Optional[CatalystClient] = None


def _get_client() -> CatalystClient:
    global _client
    if _client is None:
        _client = CatalystClient(CatalystConfig())
    return _client


def cmd_init(args: argparse.Namespace) -> int:
    client = _get_client()
    result = client.instrument()
    mode = "Gateway-integrated" if args.gateway else "Standalone"
    print(f"✓ Catalyst initialized ({mode})")
    print(f"  Instrumented: {', '.join(result.get('components', []))}")
    return 0


def cmd_instrument(args: argparse.Namespace) -> int:
    client = _get_client()
    result = client.instrument()
    print(f"✓ Instrumentation active")
    print(f"  Components: {', '.join(result.get('components', []))}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    client = _get_client()
    stats = client.get_stats()
    print("Catalyst — Status")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    return 0


def cmd_trace(args: argparse.Namespace) -> int:
    client = _get_client()
    span = client.start_span(args.name)
    print(f"Trace started: {span.trace_id}")
    print(f"Span: {span.id}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    client = _get_client()
    traces = client.list_traces(args.limit)
    if not traces:
        print("No traces recorded.")
        return 0

    print(f"Recent Traces ({len(traces)}):")
    for t in traces:
        status_icon = {"ok": "✅", "error": "❌", "timeout": "⚠️", "cancelled": "⏸️"}.get(t.status.value, "?")
        print(f"  {t.id}  {t.name:<30s} spans={len(t.spans)} duration={t.duration_ms:.0f}ms {status_icon}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    client = _get_client()
    trace = client.get_trace(args.trace_id)
    if not trace:
        print(f"Trace {args.trace_id} not found", file=sys.stderr)
        return 1

    print(f"Trace: {trace.name} ({trace.id})")
    print(f"  Status: {trace.status.value}")
    print(f"  Duration: {trace.duration_ms:.0f}ms")
    print(f"  Spans: {len(trace.spans)}")
    for s in trace.spans:
        print(f"  ├─ {s.name} ({s.kind.value}) {s.duration_ms:.1f}ms [{s.status.value}]")
    return 0


def cmd_halo(args: argparse.Namespace) -> int:
    client = _get_client()
    trace_a = client.get_trace(args.trace_a)
    trace_b = client.get_trace(args.trace_b)

    if not trace_a or not trace_b:
        print("One or both traces not found", file=sys.stderr)
        return 1

    from .halo import run_halo_analysis
    comparison = run_halo_analysis(trace_a, trace_b, args.type)

    print(f"HALO Analysis ({args.type}):")
    print(f"  Trace A: {comparison.trace_a.name} ({len(comparison.trace_a.spans)} spans, {comparison.trace_a.duration_ms:.0f}ms)")
    print(f"  Trace B: {comparison.trace_b.name} ({len(comparison.trace_b.spans)} spans, {comparison.trace_b.duration_ms:.0f}ms)")
    print(f"  Span diff: {comparison.span_diff:+d}")
    print(f"  Duration change: {comparison.duration_change_pct:+.1f}%")

    if comparison.regressions:
        print("\n  🔴 Regressions:")
        for r in comparison.regressions:
            print(f"    {r['span']}: {r['metric']} {r['baseline']:.1f}ms → {r['current']:.1f}ms ({r['change_pct']:+.1f}%)")

    if comparison.improvements:
        print("\n  🟢 Improvements:")
        for i in comparison.improvements:
            print(f"    {i['span']}: {i['metric']} {i['baseline']:.1f}ms → {i['current']:.1f}ms ({i['change_pct']:+.1f}%)")

    if comparison.anomalies:
        print("\n  ⚠️ Anomalies:")
        for a in comparison.anomalies:
            print(f"    {a['span_name']}: z-score={a['zscore']:.2f}")

    print("\n  💡 Recommendations:")
    for rec in comparison.recommendations:
        print(f"    → {rec}")

    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    if args.builtin:
        builtin = {
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
        if args.builtin not in builtin:
            print(f"Unknown builtin metric: {args.builtin}", file=sys.stderr)
            print(f"Available: {', '.join(builtin.keys())}")
            return 1
        print(f"Built-in metric: {args.builtin}")
        print(f"PromQL: {builtin[args.builtin]}")
        return 0

    if args.query:
        print(f"Query: {args.query}")
        print("Use Prometheus HTTP API directly for query execution")
        return 0

    print("Provide --builtin <metric> or a PromQL query")
    return 1


def cmd_alerts_list(args: argparse.Namespace) -> int:
    from .alerting import AlertManager
    config = type("Config", (), {"rules": [], "notifiers": [], "evaluation_interval": "30s"})()
    am = AlertManager(config)
    alerts = am.get_active_alerts()
    if not alerts:
        print("No firing alerts")
        return 0
    for a in alerts:
        print(f"  🚨 {a.rule.name} [{a.rule.severity.value.upper()}] value={a.value}")
        for k, v in a.labels.items():
            print(f"    {k}: {v}")
    return 0


def cmd_alerts_rules(args: argparse.Namespace) -> int:
    from .alerting import BUILTIN_ALERT_RULES
    for r in BUILTIN_ALERT_RULES:
        print(f"  {r.name} [{r.severity.value.upper()}]")
        print(f"    Expr: {r.expr}")
        print(f"    For: {r.for_duration}")
        print()
    return 0


def cmd_dashboard_list(args: argparse.Namespace) -> int:
    from .dashboards import list_dashboards
    dashboards = list_dashboards()
    for d in dashboards:
        print(f"  {d['id']}: {d['title']}")
    return 0


def cmd_dashboard_export(args: argparse.Namespace) -> int:
    from .dashboards import export_all_dashboards
    export_all_dashboards()
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    client = _get_client()
    stats = client.get_stats()
    health = {
        "status": "healthy" if stats["active_spans"] < 1000 else "degraded",
        "catalyst": stats,
    }
    print(json.dumps(health, indent=2))
    return 0