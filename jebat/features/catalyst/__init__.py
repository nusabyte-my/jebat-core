"""
JEBAT Inference.net Catalyst Features — Observability & Model Platform.

Provides:
- Tracing: Auto-instrument JEBAT agent loop, tool calls, LLM calls
- Gateway: Route LLM traffic for observability, cost tracking, evals
- Signals: Plain-language classifiers (jailbreak, sentiment, NSFW, outcomes)
- Evals: Model evaluations with rubrics
- Training: Custom model training on production data, deploy to GPUs
- HALO: Agent trace analysis for prompt/tool/harness improvements
- Inference API: Access to 100+ open-source and custom models

Requirements:
- pip install inference-net
- INFERENCE_NET_API_KEY environment variable

Documentation: https://docs.inference.net
"""

from .catalyst_integration import (
    CatalystConfig,
    CatalystIntegration,
    is_catalyst_available,
    get_catalyst,
    initialize_catalyst,
    CatalystAgentMixin,
    trace_agent_step,
    trace_tool_call,
    trace_llm_call,
)

from .catalyst_tools import (
    catalyst_init_tool,
    catalyst_status_tool,
    catalyst_trace_tool,
    catalyst_log_llm_tool,
    catalyst_log_tool_tool,
    catalyst_gateway_route_tool,
    catalyst_signal_eval_tool,
    catalyst_eval_create_tool,
    catalyst_eval_run_tool,
    catalyst_train_tool,
    catalyst_deploy_tool,
    catalyst_halo_analyze_tool,
    catalyst_instrument_jebat_tool,
)

__all__ = [
    # Classes
    "CatalystConfig",
    "CatalystIntegration",
    "CatalystAgentMixin",
    # Functions
    "is_catalyst_available",
    "get_catalyst",
    "initialize_catalyst",
    # Decorators
    "trace_agent_step",
    "trace_tool_call",
    "trace_llm_call",
    # Tools
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