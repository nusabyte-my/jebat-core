"""
JEBAT Catalyst Tools — Registered tools for Inference.net Catalyst platform.

These tools provide access to tracing, gateway routing, signals, evals,
training, and HALO analysis from within JEBAT agents.

Requirements:
- pip install inference-net
- INFERENCE_NET_API_KEY environment variable
- Optional: INFERENCE_NET_PROJECT_ID
"""

from __future__ import annotations

from typing import Any

from jebat.tools import register_tool

from jebat.features.catalyst.catalyst_integration import (
    get_catalyst,
    initialize_catalyst,
    CatalystConfig,
    is_catalyst_available,
)


def _ensure_catalyst() -> CatalystConfig:
    """Ensure Catalyst is available and return config."""
    if not is_catalyst_available():
        raise RuntimeError(
            "inference-net package not installed. "
            "Install with: pip install inference-net"
        )
    
    config = CatalystConfig()
    if not config.api_key:
        raise RuntimeError(
            "INFERENCE_NET_API_KEY not set. "
            "Get your API key from https://inference.net"
        )
    return config


# ── Configuration ──────────────────────────────────────────────────────

@register_tool(
    "catalyst_init",
    schema={
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "Inference.net API key",
            },
            "project_id": {
                "type": "string",
                "description": "Inference.net project ID",
            },
            "enable_gateway": {
                "type": "boolean",
                "description": "Enable Gateway routing",
                "default": False,
            },
            "sample_rate": {
                "type": "number",
                "description": "Trace sample rate (0.0-1.0)",
                "default": 1.0,
            },
        },
    },
    safety_tier="confirm",
    timeout=30,
    description="Initialize Inference.net Catalyst integration",
)
async def catalyst_init_tool(
    api_key: str = "",
    project_id: str = "",
    enable_gateway: bool = False,
    sample_rate: float = 1.0,
) -> dict[str, Any]:
    """Initialize Inference.net Catalyst integration for tracing and observability."""
    config = CatalystConfig(
        api_key=api_key,
        project_id=project_id,
        enable_gateway=enable_gateway,
        sample_rate=sample_rate,
    )
    catalyst = await initialize_catalyst(config)
    return {
        "initialized": True,
        "tracing": True,
        "gateway": enable_gateway,
        "signals": len(config.signals),
        "sample_rate": sample_rate,
    }


@register_tool(
    "catalyst_status",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=10,
    description="Check Catalyst integration status",
)
async def catalyst_status_tool() -> dict[str, Any]:
    """Check Catalyst integration status and availability."""
    available = is_catalyst_available()
    catalyst = get_catalyst()
    
    return {
        "available": available,
        "initialized": catalyst._initialized if catalyst else False,
        "tracing_enabled": catalyst.config.enable_tracing if catalyst else False,
        "gateway_enabled": catalyst.config.enable_gateway if catalyst else False,
    }


# ── Tracing ────────────────────────────────────────────────────────────

@register_tool(
    "catalyst_trace",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Trace span name (e.g., 'agent.research.search')",
            },
            "attributes": {
                "type": "object",
                "description": "Custom attributes to attach to span",
            },
        },
        "required": ["name"],
    },
    safety_tier="auto",
    timeout=10,
    description="Create a trace span for agent/workflow tracing",
)
async def catalyst_trace_tool(name: str, attributes: dict = None) -> dict[str, Any]:
    """Create a traced span. Use as context manager in agents."""
    catalyst = get_catalyst()
    span = catalyst.trace(name, attributes or {})
    
    # Return a handle for manual span management
    return {
        "span_id": id(span),
        "name": name,
        "attributes": attributes or {},
        "usage": "Use 'with' context manager or call .set_attribute() / .end()",
    }


@register_tool(
    "catalyst_log_llm",
    schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Model name (e.g., gpt-4, qwen2.5-coder:7b)"},
            "provider": {"type": "string", "description": "Provider (openai, anthropic, ollama, etc.)"},
            "messages": {"type": "array", "items": {"type": "object"}, "description": "Input messages"},
            "response": {"type": "string", "description": "Model response"},
            "latency_ms": {"type": "integer", "description": "Latency in milliseconds"},
            "tokens_in": {"type": "integer", "description": "Input tokens", "default": 0},
            "tokens_out": {"type": "integer", "description": "Output tokens", "default": 0},
            "cost_usd": {"type": "number", "description": "Cost in USD", "default": 0.0},
            "metadata": {"type": "object", "description": "Additional metadata (agent, tool, session)"},
        },
        "required": ["model", "provider", "messages", "response", "latency_ms"],
    },
    safety_tier="auto",
    timeout=10,
    description="Log an LLM call to Catalyst tracing",
)
async def catalyst_log_llm_tool(
    model: str,
    provider: str,
    messages: list,
    response: str,
    latency_ms: int,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_usd: float = 0.0,
    metadata: dict = None,
) -> dict[str, Any]:
    """Log an LLM call to Catalyst for tracing and observability."""
    catalyst = get_catalyst()
    await catalyst.log_llm_call(
        model=model,
        provider=provider,
        messages=messages,
        response=response,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        metadata=metadata or {},
    )
    return {"logged": True, "model": model, "provider": provider}


@register_tool(
    "catalyst_log_tool",
    schema={
        "type": "object",
        "properties": {
            "tool_name": {"type": "string", "description": "Tool name"},
            "args": {"type": "object", "description": "Tool arguments"},
            "result": {"type": "string", "description": "Tool result (truncated)"},
            "latency_ms": {"type": "integer", "description": "Latency in milliseconds"},
            "success": {"type": "boolean", "description": "Whether tool succeeded"},
            "error": {"type": "string", "description": "Error message if failed"},
            "metadata": {"type": "object", "description": "Additional metadata (agent, session)"},
        },
        "required": ["tool_name", "args", "latency_ms", "success"],
    },
    safety_tier="auto",
    timeout=10,
    description="Log a tool call to Catalyst tracing",
)
async def catalyst_log_tool_tool(
    tool_name: str,
    args: dict,
    result: str = "",
    latency_ms: int = 0,
    success: bool = True,
    error: str = "",
    metadata: dict = None,
) -> dict[str, Any]:
    """Log a tool call to Catalyst for tracing and observability."""
    catalyst = get_catalyst()
    await catalyst.log_tool_call(
        tool_name=tool_name,
        args=args,
        result=result,
        latency_ms=latency_ms,
        success=success,
        error=error or None,
        metadata=metadata or {},
    )
    return {"logged": True, "tool": tool_name, "success": success}


# ── Gateway Routing ────────────────────────────────────────────────────

@register_tool(
    "catalyst_gateway_route",
    schema={
        "type": "object",
        "properties": {
            "model": {"type": "string", "description": "Target model"},
            "messages": {"type": "array", "items": {"type": "object"}, "description": "Chat messages"},
            "temperature": {"type": "number", "default": 0.7},
            "max_tokens": {"type": "integer", "default": 4096},
        },
        "required": ["model", "messages"],
    },
    safety_tier="confirm",
    timeout=120,
    description="Route LLM request through Catalyst Gateway for observability",
)
async def catalyst_gateway_route_tool(
    model: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """Route an LLM request through Catalyst Gateway for full observability."""
    catalyst = get_catalyst()
    result = await catalyst.route_llm_request(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "routed": True,
        "model": model,
        "response": result,
    }


# ── Signals ────────────────────────────────────────────────────────────

@register_tool(
    "catalyst_signal_eval",
    schema={
        "type": "object",
        "properties": {
            "signal": {
                "type": "string",
                "description": "Signal name (e.g., security/jailbreak, quality/summarization, outcome/task_completion)",
            },
            "span_data": {
                "type": "object",
                "description": "Span data to evaluate (messages, tool_calls, etc.)",
            },
        },
        "required": ["signal", "span_data"],
    },
    safety_tier="auto",
    timeout=30,
    description="Evaluate a Catalyst signal on span data",
)
async def catalyst_signal_eval_tool(signal: str, span_data: dict) -> dict[str, Any]:
    """Evaluate a Catalyst signal on span data to detect issues."""
    catalyst = get_catalyst()
    result = await catalyst.evaluate_signal(signal, span_data)
    return {
        "signal": signal,
        "triggered": result.get("triggered", False),
        "score": result.get("score", 0.0),
        "details": result.get("details", {}),
    }


# ── Evals ──────────────────────────────────────────────────────────────

@register_tool(
    "catalyst_eval_create",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Evaluation name"},
            "dataset_id": {"type": "string", "description": "Dataset ID from Catalyst"},
            "rubric": {"type": "object", "description": "Evaluation rubric/criteria"},
            "model_ids": {"type": "array", "items": {"type": "string"}, "description": "Models to evaluate"},
        },
        "required": ["name", "dataset_id", "rubric", "model_ids"],
    },
    safety_tier="confirm",
    timeout=30,
    description="Create a model evaluation run",
)
async def catalyst_eval_create_tool(name: str, dataset_id: str, rubric: dict, model_ids: list) -> dict[str, Any]:
    """Create a model evaluation run in Catalyst."""
    catalyst = get_catalyst()
    eval_id = await catalyst.create_eval(name, dataset_id, rubric, model_ids)
    return {"eval_id": eval_id, "name": name}


@register_tool(
    "catalyst_eval_run",
    schema={
        "type": "object",
        "properties": {
            "eval_id": {"type": "string", "description": "Evaluation ID"},
            "model_id": {"type": "string", "description": "Model to evaluate"},
        },
        "required": ["eval_id", "model_id"],
    },
    safety_tier="confirm",
    timeout=300,
    description="Run an evaluation",
)
async def catalyst_eval_run_tool(eval_id: str, model_id: str) -> dict[str, Any]:
    """Run a Catalyst evaluation."""
    catalyst = get_catalyst()
    result = await catalyst.run_eval(eval_id, model_id)
    return {"eval_id": eval_id, "model_id": model_id, "result": result}


# ── Training & Deployment ────────────────────────────────────────────

@register_tool(
    "catalyst_train",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Training job name"},
            "dataset_id": {"type": "string", "description": "Dataset ID from Catalyst"},
            "base_model": {"type": "string", "description": "Base model to fine-tune (e.g., llama-3.1-8b)"},
            "config": {"type": "object", "description": "Training configuration (lr, epochs, etc.)"},
        },
        "required": ["name", "dataset_id", "base_model", "config"],
    },
    safety_tier="confirm",
    timeout=60,
    description="Create a custom model training job",
)
async def catalyst_train_tool(name: str, dataset_id: str, base_model: str, config: dict) -> dict[str, Any]:
    """Create a custom model training job using production data."""
    catalyst = get_catalyst()
    job_id = await catalyst.create_training_job(name, dataset_id, base_model, config)
    return {"job_id": job_id, "name": name, "base_model": base_model}


@register_tool(
    "catalyst_deploy",
    schema={
        "type": "object",
        "properties": {
            "model_id": {"type": "string", "description": "Trained model ID"},
            "gpu_type": {"type": "string", "description": "GPU type (auto, h100, a100, etc.)", "default": "auto"},
        },
        "required": ["model_id"],
    },
    safety_tier="confirm",
    timeout=120,
    description="Deploy a trained model to dedicated GPU",
)
async def catalyst_deploy_tool(model_id: str, gpu_type: str = "auto") -> dict[str, Any]:
    """Deploy a custom model to dedicated GPU."""
    catalyst = get_catalyst()
    result = await catalyst.deploy_model(model_id, gpu_type)
    return {"deployed": True, "model_id": model_id, "endpoint": result.get("endpoint")}


# ── HALO Analysis ────────────────────────────────────────────────────

@register_tool(
    "catalyst_halo_analyze",
    schema={
        "type": "object",
        "properties": {
            "trace_ids": {"type": "array", "items": {"type": "string"}, "description": "Trace IDs to analyze"},
            "analysis_type": {"type": "string", "description": "Analysis type (full, prompt, tool, reasoning)", "default": "full"},
        },
        "required": ["trace_ids"],
    },
    safety_tier="auto",
    timeout=120,
    description="Run HALO analysis on agent traces for improvements",
)
async def catalyst_halo_analyze_tool(trace_ids: list, analysis_type: str = "full") -> dict[str, Any]:
    """Run HALO analysis on agent traces to identify improvements."""
    catalyst = get_catalyst()
    result = await catalyst.analyze_with_halo(trace_ids, analysis_type)
    return {
        "traces_analyzed": len(trace_ids),
        "analysis_type": analysis_type,
        "report": result.get("report", ""),
        "improvements": result.get("improvements", []),
        "metrics": result.get("metrics", {}),
    }


# ── Agent Integration ────────────────────────────────────────────────

@register_tool(
    "catalyst_instrument_jebat",
    schema={
        "type": "object",
        "properties": {
            "enable_tracing": {"type": "boolean", "default": True, "description": "Enable agent loop tracing"},
            "enable_gateway": {"type": "boolean", "default": False, "description": "Route LLMs through Gateway"},
            "enable_signals": {"type": "boolean", "default": True, "description": "Enable signal evaluation"},
        },
    },
    safety_tier="confirm",
    timeout=30,
    description="Auto-instrument JEBAT agent loop with Catalyst tracing",
)
async def catalyst_instrument_jebat_tool(
    enable_tracing: bool = True,
    enable_gateway: bool = False,
    enable_signals: bool = True,
) -> dict[str, Any]:
    """Auto-instrument JEBAT's agent loop, tools, and LLM calls with Catalyst."""
    catalyst = get_catalyst()
    catalyst.instrument_jebat()
    
    # Update config
    catalyst.config.enable_tracing = enable_tracing
    catalyst.config.enable_gateway = enable_gateway
    catalyst.config.enable_signals = enable_signals
    
    return {
        "instrumented": True,
        "tracing": enable_tracing,
        "gateway": enable_gateway,
        "signals": enable_signals,
        "hooks": ["agent_loop", "tool_dispatch", "llm_generate", "session"],
    }


__all__ = [
    "catalyst_init_tool",
    "catalyst_status_tool",
    "catalyst_trace_tool",
    "catalyst_log_llm_tool",
    "catalyst_log_tool_tool",
    "catalyst_gateway_route_tool",
    "catalyst_signal_eval_tool",
    "catalyst_eval_create_tool",
    "catalyst_eval_run_tool",
    "catalyst_train_tool",
    "catalyst_deploy_tool",
    "catalyst_halo_analyze_tool",
    "catalyst_instrument_jebat_tool",
]