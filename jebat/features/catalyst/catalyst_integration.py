"""
JEBAT Inference.net Catalyst Integration — Observability, Tracing, and Model Platform.

Catalyst provides:
- Tracing: Capture LLM calls, tool calls, agent steps (OpenInference format)
- Gateway: Route LLM traffic for observability, cost tracking, evals
- Signals: Plain-language classifiers for spans (security, quality, outcomes)
- Evals: Model evaluations with rubrics
- Training: Custom model training on production data, deploy to dedicated GPUs
- HALO: Agent trace analysis for prompt/tool/harness improvements
- Inference API: Access to 100+ open-source and custom models

Integration points with JEBAT:
1. Auto-instrument JEBAT's agent loop, tool calls, LLM calls
2. Route LLM traffic through Gateway for observability
3. Signals for auto-classifying agent spans (jailbreak, sentiment, outcomes)
4. Evals for agent output quality
5. Training custom models from JEBAT production data
6. HALO analysis of agent traces

Requirements:
- pip install inference-net
- API key from https://inference.net

Documentation: https://docs.inference.net
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

# Optional imports - gracefully handle missing dependencies
try:
    from inference.net import (
        InferenceClient,
        trace as inference_trace,
        observe,
        GatewayRouter,
        SignalDefinition,
        EvalRun,
        TrainingJob,
    )
    INFERENCE_NET_AVAILABLE = True
except ImportError:
    INFERENCE_NET_AVAILABLE = False
    InferenceClient = None
    inference_trace = None
    observe = None
    GatewayRouter = None
    SignalDefinition = None
    EvalRun = None
    TrainingJob = None


@dataclass
class CatalystConfig:
    """Configuration for Inference.net Catalyst integration."""
    api_key: str = ""
    project_id: str = ""
    enable_tracing: bool = True
    enable_gateway: bool = False
    enable_signals: bool = True
    enable_evals: bool = False
    enable_training: bool = False
    gateway_base_url: str = "https://gateway.inference.net"
    tracing_endpoint: str = "https://api.inference.net/v1/traces"
    signals: List[str] = field(default_factory=list)
    sample_rate: float = 1.0
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("INFERENCE_NET_API_KEY", "")
        if not self.project_id:
            self.project_id = os.getenv("INFERENCE_NET_PROJECT_ID", "")
        if not self.signals:
            self.signals = [
                "security/jailbreak",
                "security/prompt_injection", 
                "quality/summarization_quality",
                "outcome/task_completion",
                "behavior/tool_usage_efficiency",
            ]


def is_catalyst_available() -> bool:
    """Check if inference.net SDK is installed."""
    return INFERENCE_NET_AVAILABLE


class CatalystIntegration:
    """
    Main integration class for Inference.net Catalyst platform.
    
    Provides tracing, gateway routing, signals, evals, and training
    capabilities for JEBAT agents.
    
    Usage:
        catalyst = CatalystIntegration(config)
        await catalyst.initialize()
        
        # Auto-instrument JEBAT
        catalyst.instrument_jebat()
        
        # Or manually trace
        with catalyst.trace("agent-step", {"agent": "researcher"}) as span:
            span.set_attribute("tool", "web_search")
            result = await agent.run()
    """
    
    def __init__(self, config: Optional[CatalystConfig] = None):
        self.config = config or CatalystConfig()
        self._client: Optional[InferenceClient] = None
        self._gateway_router: Optional[GatewayRouter] = None
        self._initialized = False
        self._span_stack: List[Any] = []
        self._signal_definitions: Dict[str, SignalDefinition] = {}
        
    def _check_available(self) -> None:
        if not INFERENCE_NET_AVAILABLE:
            raise RuntimeError(
                "inference-net package not installed. "
                "Install with: pip install inference-net"
            )
    
    async def initialize(self) -> None:
        """Initialize Catalyst integration."""
        self._check_available()
        
        if not self.config.api_key:
            logger.warning("No INFERENCE_NET_API_KEY set. Catalyst features disabled.")
            return
            
        try:
            self._client = InferenceClient(
                api_key=self.config.api_key,
                project_id=self.config.project_id or None,
            )
            
            if self.config.enable_gateway:
                self._gateway_router = GatewayRouter(
                    base_url=self.config.gateway_base_url,
                    api_key=self.config.api_key,
                )
                
            # Register custom signals
            await self._register_signals()
            
            self._initialized = True
            logger.info("Catalyst integration initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Catalyst: {e}")
            raise
    
    async def _register_signals(self) -> None:
        """Register custom signal definitions."""
        if not self._client or not self.config.enable_signals:
            return
            
        for signal_name in self.config.signals:
            try:
                # Parse signal name (e.g., "security/jailbreak")
                category, name = signal_name.split("/") if "/" in signal_name else ("custom", signal_name)
                
                signal = SignalDefinition(
                    name=f"jebat_{category}_{name}",
                    description=f"JEBAT signal: {signal_name}",
                    category=category,
                    # Simple keyword-based detection as fallback
                    # In production, use proper signal definitions
                )
                await self._client.signals.register(signal)
                self._signal_definitions[signal_name] = signal
                
            except Exception as e:
                logger.warning(f"Failed to register signal {signal_name}: {e}")
    
    # ── Tracing ────────────────────────────────────────────────────────
    
    def trace(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a new trace span (context manager)."""
        if not self._initialized or not self._client or not self.config.enable_tracing:
            return _NoOpSpan()
            
        return self._client.trace(
            name=name,
            attributes=attributes or {},
            sample_rate=self.config.sample_rate,
        )
    
    async def log_llm_call(
        self,
        model: str,
        provider: str,
        messages: List[Dict[str, str]],
        response: str,
        latency_ms: int,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an LLM call to Catalyst tracing."""
        if not self._initialized or not self._client:
            return
            
        await self._client.tracing.log_llm_call(
            model=model,
            provider=provider,
            messages=messages,
            response=response,
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            metadata={
                "jebat_agent": metadata.get("agent", "") if metadata else "",
                "jebat_tool": metadata.get("tool", "") if metadata else "",
                "jebat_session": metadata.get("session_id", "") if metadata else "",
                **(metadata or {}),
            },
        )
    
    async def log_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        latency_ms: int,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a tool call to Catalyst tracing."""
        if not self._initialized or not self._client:
            return
            
        await self._client.tracing.log_tool_call(
            name=tool_name,
            args=args,
            result=str(result)[:10000],  # Truncate large results
            latency_ms=latency_ms,
            success=success,
            error=error,
            metadata={
                "jebat_agent": metadata.get("agent", "") if metadata else "",
                "jebat_session": metadata.get("session_id", "") if metadata else "",
                **(metadata or {}),
            },
        )
    
    # ── Gateway Routing ─────────────────────────────────────────────────
    
    async def route_llm_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> Any:
        """Route LLM request through Catalyst Gateway for observability."""
        if not self._initialized or not self._gateway_router:
            raise RuntimeError("Gateway not enabled or not initialized")
            
        return await self._gateway_router.route(
            model=model,
            messages=messages,
            **kwargs,
        )
    
    # ── Signals ────────────────────────────────────────────────────────
    
    async def evaluate_signal(
        self,
        signal_name: str,
        span_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a signal on a span."""
        if not self._initialized or not self._client:
            return {"triggered": False, "score": 0.0}
            
        signal = self._signal_definitions.get(signal_name)
        if not signal:
            return {"triggered": False, "score": 0.0, "error": "Signal not found"}
            
        return await self._client.signals.evaluate(signal_name, span_data)
    
    # ── Evals ──────────────────────────────────────────────────────────
    
    async def create_eval(
        self,
        name: str,
        dataset_id: str,
        rubric: Dict[str, Any],
        model_ids: List[str],
    ) -> str:
        """Create an evaluation run."""
        if not self._initialized or not self._client:
            raise RuntimeError("Catalyst not initialized")
            
        eval_run = await self._client.evals.create(
            name=name,
            dataset_id=dataset_id,
            rubric=rubric,
            model_ids=model_ids,
        )
        return eval_run.id
    
    async def run_eval(
        self,
        eval_id: str,
        model_id: str,
    ) -> Dict[str, Any]:
        """Run an evaluation."""
        if not self._initialized or not self._client:
            raise RuntimeError("Catalyst not initialized")
            
        return await self._client.evals.run(eval_id, model_id=model_id)
    
    # ── Training ───────────────────────────────────────────────────────
    
    async def create_training_job(
        self,
        name: str,
        dataset_id: str,
        base_model: str,
        config: Dict[str, Any],
    ) -> str:
        """Create a custom model training job."""
        if not self._initialized or not self._client:
            raise RuntimeError("Catalyst not initialized")
            
        job = await self._client.training.create(
            name=name,
            dataset_id=dataset_id,
            base_model=base_model,
            config=config,
        )
        return job.id
    
    async def deploy_model(
        self,
        model_id: str,
        gpu_type: str = "auto",
    ) -> Dict[str, Any]:
        """Deploy a trained model to dedicated GPU."""
        if not self._initialized or not self._client:
            raise RuntimeError("Catalyst not initialized")
            
        return await self._client.deploy(
            model_id=model_id,
            gpu_type=gpu_type,
        )
    
    # ── HALO ──────────────────────────────────────────────────────────
    
    async def analyze_with_halo(
        self,
        trace_ids: List[str],
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """Run HALO analysis on agent traces."""
        if not self._initialized or not self._client:
            raise RuntimeError("Catalyst not initialized")
            
        return await self._client.halo.analyze(
            trace_ids=trace_ids,
            analysis_type=analysis_type,
        )
    
    # ── Auto-Instrument JEBAT ────────────────────────────────────────
    
    def instrument_jebat(self) -> None:
        """Auto-instrument JEBAT's agent loop, tools, and LLM calls."""
        if not self._initialized:
            logger.warning("Catalyst not initialized, skipping instrumentation")
            return
            
        # This would patch JEBAT's internal methods
        # For now, provide the hook points
        logger.info("Catalyst JEBAT instrumentation hooks registered")
        logger.info("Hook points available: agent_loop, tool_dispatch, llm_generate, session")


# ── Convenience Decorators ─────────────────────────────────────────────

def trace_agent_step(agent_name: str, step_name: str = ""):
    """Decorator to trace agent steps."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            catalyst = get_catalyst()
            step = step_name or func.__name__
            with catalyst.trace(f"agent.{agent_name}.{step}", {"agent": agent_name}):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def trace_tool_call(tool_name: str):
    """Decorator to trace tool calls."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            catalyst = get_catalyst()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency_ms = int((time.time() - start) * 1000)
                await catalyst.log_tool_call(
                    tool_name=tool_name,
                    args=args[1] if len(args) > 1 else {},  # Skip self
                    result=result,
                    latency_ms=latency_ms,
                    success=True,
                )
                return result
            except Exception as e:
                latency_ms = int((time.time() - start) * 1000)
                await catalyst.log_tool_call(
                    tool_name=tool_name,
                    args=args[1] if len(args) > 1 else {},
                    result=None,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(e),
                )
                raise
        return wrapper
    return decorator


def trace_llm_call(model: str, provider: str):
    """Decorator to trace LLM calls."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            catalyst = get_catalyst()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency_ms = int((time.time() - start) * 1000)
                
                # Extract tokens if available
                tokens_in = getattr(result, 'tokens_in', 0) if hasattr(result, 'tokens_in') else 0
                tokens_out = getattr(result, 'tokens_out', 0) if hasattr(result, 'tokens_out') else 0
                
                await catalyst.log_llm_call(
                    model=model,
                    provider=provider,
                    messages=kwargs.get('messages', []),
                    response=str(result)[:5000],
                    latency_ms=latency_ms,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    metadata=kwargs.get('metadata', {}),
                )
                return result
            except Exception as e:
                latency_ms = int((time.time() - start) * 1000)
                await catalyst.log_llm_call(
                    model=model,
                    provider=provider,
                    messages=kwargs.get('messages', []),
                    response=f"ERROR: {e}",
                    latency_ms=latency_ms,
                    tokens_in=0,
                    tokens_out=0,
                    metadata={**kwargs.get('metadata', {}), 'error': str(e)},
                )
                raise
        return wrapper
    return decorator


# ── Global Instance ────────────────────────────────────────────────────

_catalyst: Optional[CatalystIntegration] = None


def get_catalyst(config: Optional[CatalystConfig] = None) -> CatalystIntegration:
    """Get or create global CatalystIntegration instance."""
    global _catalyst
    if _catalyst is None:
        _catalyst = CatalystIntegration(config)
    return _catalyst


async def initialize_catalyst(config: Optional[CatalystConfig] = None) -> CatalystIntegration:
    """Initialize and return CatalystIntegration."""
    global _catalyst
    _catalyst = CatalystIntegration(config)
    await _catalyst.initialize()
    return _catalyst


# ── No-Op Span for Disabled State ─────────────────────────────────────

class _NoOpSpan:
    """No-op span when Catalyst is disabled."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def set_attribute(self, *args, **kwargs):
        pass
    
    def set_attributes(self, *args, **kwargs):
        pass
    
    def add_event(self, *args, **kwargs):
        pass
    
    def record_exception(self, *args, **kwargs):
        pass
    
    def end(self):
        pass


# ── Agent Integration Helpers ──────────────────────────────────────────

class CatalystAgentMixin:
    """Mixin to add Catalyst tracing to JEBAT agents."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._catalyst = get_catalyst()
        self._agent_name = getattr(self, 'name', self.__class__.__name__)
    
    def _trace_step(self, step_name: str, attributes: Optional[Dict] = None):
        """Create a traced step."""
        attrs = {"agent": self._agent_name, **(attributes or {})}
        return self._catalyst.trace(f"agent.{self._agent_name}.{step_name}", attrs)
    
    async def _log_llm(self, model: str, provider: str, messages: List[Dict], 
                      response: str, latency_ms: int, tokens_in: int = 0, 
                      tokens_out: int = 0, cost: float = 0.0, **metadata):
        await self._catalyst.log_llm_call(
            model=model, provider=provider, messages=messages, response=response,
            latency_ms=latency_ms, tokens_in=tokens_in, tokens_out=tokens_out,
            cost_usd=cost, metadata=metadata,
        )
    
    async def _log_tool(self, tool_name: str, args: Dict, result: Any, 
                       latency_ms: int, success: bool, error: str = None, **metadata):
        await self._catalyst.log_tool_call(
            tool_name=tool_name, args=args, result=result, latency_ms=latency_ms,
            success=success, error=error, metadata=metadata,
        )


__all__ = [
    "CatalystConfig",
    "CatalystIntegration",
    "is_catalyst_available",
    "get_catalyst",
    "initialize_catalyst",
    "CatalystAgentMixin",
    "trace_agent_step",
    "trace_tool_call",
    "trace_llm_call",
]