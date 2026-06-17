"""Catalyst JEBAT Tools — registered tools for tracing and observability.

These tools are registered with the JEBAT tool registry and can be
invoked by the agent orchestrator or directly via the API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from jebat.features.catalyst.catalyst_integration import (
    CatalystClient,
    SpanKind,
    SpanStatus,
    create_catalyst_client,
)

logger = logging.getLogger(__name__)


@dataclass
class CatalystTool:
    """A single Catalyst tool definition."""
    name: str
    description: str
    category: str
    handler: Optional[Callable] = None
    parameters: Dict[str, str] = field(default_factory=dict)


class CatalystToolRegistry:
    """Registry of Catalyst tools for JEBAT agent use."""

    def __init__(self):
        self._client: Optional[CatalystClient] = None
        self._tools: Dict[str, CatalystTool] = {}
        self._register_all()

    async def _ensure_client(self) -> CatalystClient:
        if self._client is None:
            self._client = await create_catalyst_client()
        return self._client

    def _register_all(self) -> None:
        """Register all Catalyst tools."""
        tools = [
            CatalystTool(
                name="catalyst.status",
                description="Check Catalyst instrumentation status and stats",
                category="system",
            ),
            CatalystTool(
                name="catalyst.instrument",
                description="Auto-instrument JEBAT components for tracing",
                category="instrumentation",
            ),
            CatalystTool(
                name="catalyst.trace.start",
                description="Start a new named trace",
                category="tracing",
                parameters={"name": "Trace name"},
            ),
            CatalystTool(
                name="catalyst.span.start",
                description="Start a new span within a trace",
                category="tracing",
                parameters={"name": "Span name", "trace_id": "Parent trace ID", "kind": "Span kind (llm/tool/agent/database/http)"},
            ),
            CatalystTool(
                name="catalyst.span.end",
                description="End an active span and record its duration",
                category="tracing",
                parameters={"span_id": "Span ID", "status": "ok/error/timeout"},
            ),
            CatalystTool(
                name="catalyst.span.event",
                description="Record an event on an active span",
                category="tracing",
                parameters={"span_id": "Span ID", "name": "Event name"},
            ),
            CatalystTool(
                name="catalyst.trace.get",
                description="Get a trace and all its spans",
                category="tracing",
                parameters={"trace_id": "Trace ID"},
            ),
            CatalystTool(
                name="catalyst.trace.list",
                description="List recent traces",
                category="tracing",
                parameters={"limit": "Max results"},
            ),
            CatalystTool(
                name="catalyst.halo",
                description="Run HALO analysis comparing two traces",
                category="analysis",
                parameters={
                    "trace_a": "Start trace ID",
                    "trace_b": "End trace ID",
                    "type": "Analysis type: full, performance, correctness",
                },
            ),
        ]
        for tool in tools:
            self._tools[tool.name] = tool

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "category": t.category, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> Optional[CatalystTool]:
        return self._tools.get(name)

    async def execute(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a Catalyst tool by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}

        client = await self._ensure_client()

        try:
            if tool_name == "catalyst.status":
                return {"success": True, "data": client.get_stats()}

            elif tool_name == "catalyst.instrument":
                result = await client.instrument()
                return {"success": True, "data": result}

            elif tool_name == "catalyst.trace.start":
                span = await client.start_span(name=kwargs.get("name", "unnamed"))
                return {"success": True, "data": {"trace_id": span.trace_id, "span_id": span.id}}

            elif tool_name == "catalyst.span.start":
                kind_str = kwargs.get("kind", "internal")
                kind_map = {k.value: k for k in SpanKind}
                kind = kind_map.get(kind_str, SpanKind.INTERNAL)
                span = await client.start_span(
                    name=kwargs.get("name", "unnamed"),
                    trace_id=kwargs.get("trace_id"),
                    parent_id=kwargs.get("parent_id"),
                    kind=kind,
                )
                return {"success": True, "data": {"span_id": span.id, "trace_id": span.trace_id}}

            elif tool_name == "catalyst.span.end":
                status_str = kwargs.get("status", "ok")
                status_map = {s.value: s for s in SpanStatus}
                status = status_map.get(status_str, SpanStatus.OK)
                span = await client.end_span(span_id=kwargs.get("span_id", ""), status=status)
                if not span:
                    return {"success": False, "error": "Span not found"}
                return {"success": True, "data": {"span_id": span.id, "duration_ms": span.duration_ms}}

            elif tool_name == "catalyst.span.event":
                ok = await client.record_event(
                    span_id=kwargs.get("span_id", ""),
                    name=kwargs.get("name", "event"),
                )
                return {"success": ok}

            elif tool_name == "catalyst.trace.get":
                trace = await client.get_trace(kwargs.get("trace_id", ""))
                if not trace:
                    return {"success": False, "error": "Trace not found"}
                return {"success": True, "data": {
                    "id": trace.id, "name": trace.name,
                    "spans": len(trace.spans), "duration_ms": trace.duration_ms,
                }}

            elif tool_name == "catalyst.trace.list":
                traces = await client.list_traces(limit=kwargs.get("limit", 50))
                return {"success": True, "data": [
                    {"id": t.id, "name": t.name, "spans": len(t.spans)}
                    for t in traces
                ]}

            elif tool_name == "catalyst.halo":
                result = await client.halo_analysis(
                    trace_id_start=kwargs.get("trace_a", ""),
                    trace_id_end=kwargs.get("trace_b", ""),
                    analysis_type=kwargs.get("type", "full"),
                )
                return {"success": True, "data": result}

            return {"success": False, "error": f"Tool '{tool_name}' not implemented"}

        except Exception as e:
            logger.error(f"Catalyst tool '{tool_name}' failed: {e}")
            return {"success": False, "error": str(e)}


# Singleton registry instance
catalyst_tool_registry = CatalystToolRegistry()
