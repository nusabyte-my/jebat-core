"""
JEBAT REST API

FastAPI-based REST API for JEBAT AI Assistant.

Endpoints:
- GET  /api/v1/health              - Health check
- GET  /api/v1/status              - System status
- GET  /api/v1/metrics             - System metrics
- POST /api/v1/chat                - Chat with selective swarm routing
- GET  /api/v1/models              - List models (OpenAI-compatible, used by Zed)
- POST /api/v1/chat/completions    - Chat completions (OpenAI-compatible, used by Zed)
- GET  /api/v1/memories            - List memories
- POST /api/v1/memories            - Store memory
- GET  /api/v1/agents              - List agents
- POST /api/v1/swarm/execute       - Execute a task through the swarm orchestrator
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="JEBAT API",
    description="JEBAT AI Assistant - REST API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Models ====================


class StatusResponse(BaseModel):
    """System status response"""

    status: str
    version: str
    timestamp: str
    components: Dict[str, str]


class HealthResponse(BaseModel):
    """Health check response"""

    healthy: bool
    database: bool
    redis: bool
    timestamp: str


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    mode: Optional[str] = Field("deliberate", description="Thinking mode")
    timeout: Optional[int] = Field(30, description="Timeout in seconds")


class ChatResponse(BaseModel):
    """Chat response model"""

    response: str
    confidence: float
    thinking_steps: int
    execution_time: float
    user_id: Optional[str]
    swarm_lead: Optional[Dict[str, Any]] = None
    reducer: Optional[Dict[str, Any]] = None
    doctrine: Optional[Dict[str, Any]] = None
    security_layer: Optional[Dict[str, Any]] = None


class OpenAIMessage(BaseModel):
    """OpenAI-compatible message"""

    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat completion request (used by Zed)"""

    model: str = "jebat-pro"
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class OpenAIChatResponse(BaseModel):
    """OpenAI-compatible chat completion response"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class MemoryStoreRequest(BaseModel):
    """Memory store request model"""

    content: str = Field(..., description="Memory content")
    user_id: str = Field(..., description="User identifier")
    layer: Optional[str] = Field("M1_EPISODIC", description="Memory layer")


class MemoryResponse(BaseModel):
    """Memory response model"""

    id: str
    content: str
    layer: str
    user_id: str
    created_at: str
    heat_score: float


class MetricsResponse(BaseModel):
    """System metrics response"""

    ultra_loop: Dict[str, Any]
    ultra_think: Dict[str, Any]
    memory: Dict[str, Any]
    timestamp: str


class SwarmTaskRequest(BaseModel):
    """Direct swarm execution request."""

    description: str = Field(..., description="Task description for the swarm")
    user_id: Optional[str] = Field("default", description="User identifier")
    execution_mode: Optional[str] = Field("consensus", description="single, swarm, or consensus")
    required_capabilities: List[str] = Field(default_factory=list, description="Capabilities to route against")
    enable_search: bool = Field(True, description="Whether agents should search before judging")
    search_queries: List[str] = Field(default_factory=list, description="Optional explicit search queries")
    max_agents: int = Field(5, ge=1, le=8, description="Maximum number of agents to involve")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional task parameters")


class SwarmTaskResponse(BaseModel):
    """Direct swarm execution response."""

    task_id: str
    success: bool
    execution_mode: str
    execution_time: float
    result: Any = None
    error: Optional[str] = None
    swarm_lead: Optional[Dict[str, Any]] = None
    reducer: Optional[Dict[str, Any]] = None
    doctrine: Optional[Dict[str, Any]] = None
    security_layer: Optional[Dict[str, Any]] = None
    full_orchestration: bool = False
    stats: Dict[str, Any] = Field(default_factory=dict)


class SwarmPlanResponse(BaseModel):
    """Read-only swarm planning response."""

    task_id: str
    execution_mode: str
    required_capabilities: List[str] = Field(default_factory=list)
    preferred_roles: List[str] = Field(default_factory=list)
    recommended_delivery_mode: str
    search_enabled: bool
    require_consensus: bool
    full_orchestration: bool
    security_layer: Dict[str, Any] = Field(default_factory=dict)
    swarm_lead: Optional[Dict[str, Any]] = None
    ranked_agents: List[Dict[str, Any]] = Field(default_factory=list)
    selected_agents: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== Global State ====================

# These will be initialized when the API starts
jebat_components = {
    "memory_manager": None,
    "ultra_loop": None,
    "ultra_think": None,
    "agent_orchestrator": None,
}


async def _persist_model_usage(
    *,
    username: str,
    model_name: str,
    provider: str,
    usage: Dict[str, int],
    latency_ms: int,
    is_cached: bool = False,
) -> None:
    """Best-effort persistence for model usage telemetry."""
    if not model_name or not provider:
        return

    try:
        from jebat.database.models import AsyncSessionLocal
        from jebat.database.repositories import RepositoryManager

        async with AsyncSessionLocal() as session:
            repos = RepositoryManager(session)

            user = await repos.users.get_by_username(username)
            if user is None:
                safe_username = username[:120] or "default"
                safe_email = f"{safe_username}@jebat.local"
                user = await repos.users.create(
                    username=safe_username,
                    email=safe_email,
                    password_hash="!disabled-api-user!",
                    full_name=safe_username,
                    is_active=True,
                )

            models = await repos.models.query(filters={"model_name": model_name}, limit=1)
            model = models[0] if models else None
            if model is None:
                model = await repos.models.create(
                    model_name=model_name,
                    provider=provider,
                    model_type="chat",
                    max_tokens=max(1, int(usage.get("total_tokens", 0) or 1)),
                    is_active=True,
                )

            await repos.model_usage.create(
                model_id=model.id,
                user_id=user.id,
                input_tokens=int(usage.get("prompt_tokens", 0) or 0),
                output_tokens=int(usage.get("completion_tokens", 0) or 0),
                latency_ms=max(0, int(latency_ms)),
                is_cached=bool(is_cached),
            )
            await repos.commit()
    except Exception as exc:
        logger.warning("Skipping model usage persistence: %s", exc)


# ==================== Startup/Shutdown ====================


@app.on_event("startup")
async def startup_event():
    """Initialize JEBAT components on startup"""
    logger.info("Starting JEBAT API...")

    try:
        # Import JEBAT components
        from jebat import MemoryManager
        from jebat.core.agents.orchestrator import AgentOrchestrator
        from jebat.core.agents.search_backend import SwarmSearchBackend
        from jebat.features.ultra_loop import create_ultra_loop
        from jebat.features.ultra_think import create_ultra_think

        # Initialize components
        jebat_components["memory_manager"] = MemoryManager()
        logger.info("✓ Memory Manager initialized")

        jebat_components["ultra_loop"] = await create_ultra_loop(
            config={"cycle_interval": 1.0, "max_cycles": 0},
            enable_db_persistence=False,
        )
        logger.info("✓ Ultra-Loop initialized")

        jebat_components["ultra_think"] = await create_ultra_think(
            config={"max_thoughts": 20, "default_mode": "deliberate"},
            memory_manager=jebat_components["memory_manager"],
            enable_db_persistence=False,
            enable_memory_integration=True,
        )
        logger.info("✓ Ultra-Think initialized")

        jebat_components["agent_orchestrator"] = AgentOrchestrator(
            config={
                "full_orchestration": True,
                "force_swarm_for_all_tasks": True,
                "full_orchestration_enable_search": True,
                "full_orchestration_execution_mode": "consensus",
                "default_swarm_size": 5,
                "full_orchestration_max_agents": 8,
            }
        )
        builtins_registered = jebat_components["agent_orchestrator"].register_builtin_agents()
        search_backend = SwarmSearchBackend()
        jebat_components["agent_orchestrator"].register_search_handler(search_backend.search)
        await jebat_components["agent_orchestrator"].start()
        logger.info("✓ Agent Orchestrator initialized with %s built-in agents", builtins_registered)

        # Start Ultra-Loop
        await jebat_components["ultra_loop"].start()
        logger.info("✓ Ultra-Loop started")

        logger.info("JEBAT API startup complete")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Don't fail startup - components can be initialized lazily


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down JEBAT API...")

    if jebat_components["ultra_loop"]:
        await jebat_components["ultra_loop"].stop()
        logger.info("✓ Ultra-Loop stopped")

    if jebat_components["agent_orchestrator"]:
        await jebat_components["agent_orchestrator"].stop()
        logger.info("✓ Agent Orchestrator stopped")

    logger.info("JEBAT API shutdown complete")


# ==================== Endpoints ====================


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "JEBAT API",
        "version": "1.0.0",
        "description": "JEBAT AI Assistant REST API",
        "docs": "/api/docs",
        "health": "/api/v1/health",
        "status": "/api/v1/status",
        "chat": "/api/v1/chat",
        "swarm": "/api/v1/swarm/execute",
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the health status of all system components.
    """
    health = {
        "healthy": True,
        "database": True,  # Would check actual DB connection
        "redis": True,  # Would check actual Redis connection
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Check components
    if not jebat_components.get("memory_manager"):
        health["healthy"] = False

    return health


@app.get("/api/v1/status", response_model=StatusResponse, tags=["Status"])
async def get_status():
    """
    Get system status.

    Returns detailed status of all JEBAT components.
    """
    components = {}

    # Check each component
    components["memory_manager"] = (
        "ready" if jebat_components.get("memory_manager") else "not_initialized"
    )
    components["ultra_loop"] = (
        "ready" if jebat_components.get("ultra_loop") else "not_initialized"
    )
    components["ultra_think"] = (
        "ready" if jebat_components.get("ultra_think") else "not_initialized"
    )
    components["agent_orchestrator"] = (
        "ready" if jebat_components.get("agent_orchestrator") else "not_initialized"
    )

    # Get metrics if available
    if jebat_components.get("ultra_loop"):
        loop_metrics = jebat_components["ultra_loop"].get_metrics()
        components["ultra_loop_cycles"] = loop_metrics.get("total_cycles", 0)

    if jebat_components.get("ultra_think"):
        think_stats = jebat_components["ultra_think"].get_stats()
        components["ultra_think_sessions"] = think_stats.get("total_sessions", 0)

    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": components,
    }


@app.get("/api/v1/metrics", response_model=MetricsResponse, tags=["Metrics"])
async def get_metrics():
    """
    Get system metrics.

    Returns performance metrics for all components.
    """
    ultra_loop_metrics = {}
    ultra_think_stats = {}
    memory_stats = {}

    if jebat_components.get("ultra_loop"):
        ultra_loop_metrics = jebat_components["ultra_loop"].get_metrics()

    if jebat_components.get("ultra_think"):
        ultra_think_stats = jebat_components["ultra_think"].get_stats()

    if jebat_components.get("memory_manager"):
        memory_stats = {
            "layers": "5 (M0-M4)",
            "status": "operational",
        }

    # Get orchestrator stats if available
    orchestrator_stats = {}
    if jebat_components.get("agent_orchestrator"):
        orchestrator_stats = jebat_components["agent_orchestrator"].get_stats()
    
    # Get decision engine stats if available
    decision_engine_stats = {}
    if jebat_components.get("decision_engine"):
        decision_engine_stats = jebat_components["decision_engine"].get_stats()
    
    # Get smart cache stats if available
    smart_cache_stats = {}
    if jebat_components.get("smart_cache"):
        smart_cache_stats = jebat_components["smart_cache"].get_stats()
    
    # Get channel manager stats if available
    channel_manager_stats = {}
    if jebat_components.get("channel_manager"):
        channel_manager_stats = jebat_components["channel_manager"].get_stats()
    
    # Get intelligent skill stats if available
    intelligent_skill_stats = {}
    if jebat_components.get("intelligent_skill"):
        intelligent_skill_stats = jebat_components["intelligent_skill"].get_stats()
    
    return {
        "ultra_loop": ultra_loop_metrics,
        "ultra_think": ultra_think_stats,
        "memory": memory_stats,
        "orchestrator": orchestrator_stats,
        "decision_engine": decision_engine_stats,
        "smart_cache": smart_cache_stats,
        "channel_manager": channel_manager_stats,
        "intelligent_skill": intelligent_skill_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/memories", response_model=List[MemoryResponse], tags=["Memory"])
async def list_memories(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    query: Optional[str] = Query(None, description="Search query"),
):
    """
    List or search memories.

    Returns memories for a specific user, optionally filtered by search query.
    """
    if not jebat_components.get("memory_manager"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory Manager not initialized",
        )

    try:
        if query:
            # Search memories
            memories = jebat_components["memory_manager"].search(
                query=query,
                user_id=user_id,
                limit=limit,
            )
        else:
            # List all memories (simplified - would need actual implementation)
            memories = []

        return [
            MemoryResponse(
                id=getattr(m, "memory_id", str(i)),
                content=m.content if hasattr(m, "content") else str(m),
                layer=getattr(m, "layer", "M1_EPISODIC"),
                user_id=user_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                heat_score=getattr(m, "heat_score", 0.5),
            )
            for i, m in enumerate(memories)
        ]

    except Exception as e:
        logger.error(f"List memories error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/api/v1/memories", response_model=MemoryResponse, tags=["Memory"])
async def store_memory(request: MemoryStoreRequest):
    """
    Store a memory.

    Creates a new memory entry for the specified user.
    """
    if not jebat_components.get("memory_manager"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory Manager not initialized",
        )

    try:
        from jebat.core.memory.layers import MemoryLayer

        # Map layer string to MemoryLayer
        try:
            layer = MemoryLayer(request.layer)
        except ValueError:
            layer = MemoryLayer.M1_EPISODIC

        # Store memory
        memory_id = await jebat_components["memory_manager"].store(
            content=request.content,
            layer=layer,
            user_id=request.user_id,
        )

        return MemoryResponse(
            id=memory_id,
            content=request.content,
            layer=request.layer,
            user_id=request.user_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            heat_score=0.8,
        )

    except Exception as e:
        logger.error(f"Store memory error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


async def _run_swarm_prompt(
    prompt: str,
    *,
    user_id: str = "default",
    requested_model: Optional[str] = None,
):
    """Run a prompt through the swarm orchestrator and format the result."""
    if not jebat_components.get("agent_orchestrator"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Orchestrator not initialized",
        )

    from jebat.core.agents import format_swarm_result_text, infer_swarm_task

    orchestrator = jebat_components["agent_orchestrator"]
    task = infer_swarm_task(
        prompt,
        user_id=user_id,
        requested_model=requested_model,
        orchestrator=orchestrator,
    )
    result = await orchestrator.execute_task(task)
    response_text = format_swarm_result_text(result.result if isinstance(result.result, dict) else {})
    return response_text, result, orchestrator


def _build_swarm_task_from_request(request: SwarmTaskRequest):
    """Build a canonical swarm task from an API request."""
    from jebat.core.agents import AgentTask, ExecutionMode

    execution_mode = request.execution_mode or "consensus"
    return AgentTask(
        description=request.description,
        user_id=request.user_id or "default",
        execution_mode=ExecutionMode(execution_mode),
        required_capabilities=request.required_capabilities,
        enable_search=request.enable_search,
        search_queries=request.search_queries,
        max_agents=request.max_agents,
        require_consensus=execution_mode == "consensus",
        parameters=request.parameters,
    )


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint with selective swarm routing.
    """
    import time

    start = time.time()

    try:
        from jebat.core.agents import classify_prompt_with_hang_nadim
        from jebat.llm import generate_chat_reply, usage_from_texts

        decision = classify_prompt_with_hang_nadim(request.message)
        if decision.route in {"swarm", "legendary_swarm"}:
            response_text, swarm_result, _orchestrator = await _run_swarm_prompt(
                request.message,
                user_id=request.user_id or "default",
            )
            agreement = 0.0
            if isinstance(swarm_result.result, dict):
                agreement = (
                    swarm_result.result.get("consensus", {}).get("agreement", 0.0)
                )
                thinking_steps = len(swarm_result.result.get("agent_results", []))
                swarm_lead = swarm_result.result.get("swarm_lead")
                reducer = swarm_result.result.get("reducer")
                doctrine = swarm_result.result.get("doctrine")
                security_layer = swarm_result.result.get("security_layer")
            else:
                thinking_steps = 0
                swarm_lead = None
                reducer = None
                doctrine = None
                security_layer = None

            usage = usage_from_texts(
                request.message,
                response_text,
                model="jebat-legend" if decision.route == "legendary_swarm" else "jebat-swarm",
                provider="swarm",
            )
            await _persist_model_usage(
                username=request.user_id or "default",
                model_name="jebat-legend" if decision.route == "legendary_swarm" else "jebat-swarm",
                provider="swarm",
                usage={
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                latency_ms=int(max(swarm_result.execution_time, 0) * 1000),
            )
            return ChatResponse(
                response=response_text,
                confidence=float(agreement),
                thinking_steps=thinking_steps,
                execution_time=swarm_result.execution_time,
                user_id=request.user_id,
                swarm_lead=swarm_lead,
                reducer=reducer,
                doctrine=doctrine,
                security_layer=security_layer,
            )

        response_text, _used_provider, active_config, generation_meta = await generate_chat_reply(
            prompt=request.message,
            mode=request.mode,
            return_metadata=True,
        )
        elapsed = time.time() - start
        await _persist_model_usage(
            username=request.user_id or "default",
            model_name=active_config.model,
            provider=_used_provider,
            usage=generation_meta.usage,
            latency_ms=int(max(elapsed, 0) * 1000),
        )
        return ChatResponse(
            response=response_text,
            confidence=0.85,
            thinking_steps=1,
            execution_time=elapsed,
            user_id=request.user_id,
            swarm_lead=None,
            reducer=None,
            doctrine=None,
            security_layer=None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/models", tags=["OpenAI Compatible"])
async def list_models():
    """
    List available models (OpenAI-compatible).

    Zed calls this endpoint to discover available models.
    """
    from jebat.llm import load_llm_config

    config = load_llm_config()
    return {
        "object": "list",
        "data": [
            {"id": "jebat-pro", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-fast", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-deep", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-swarm", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-legend", "object": "model", "owned_by": "jebat"},
            {"id": "jebatcpp-coding", "object": "model", "owned_by": "llamacpp"},
            {"id": "jebatcpp-roleplay", "object": "model", "owned_by": "llamacpp"},
            {"id": "jebatcpp-uncensored", "object": "model", "owned_by": "llamacpp"},
            {"id": config.model, "object": "model", "owned_by": config.provider},
        ],
    }


@app.post("/api/v1/chat/completions", tags=["OpenAI Compatible"])
async def openai_chat_completion(request: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint.

    This is the primary endpoint used by Zed editor.
    Accepts standard OpenAI request format and returns OpenAI-compatible response.
    """
    import time
    import uuid

    start = time.time()

    try:
        from jebat.core.agents import (
            LEGENDARY_MODEL_ALIASES,
            SWARM_MODEL_ALIASES,
            classify_prompt_with_hang_nadim,
        )
        from jebat.llm import generate_chat_reply, load_llm_config, prepare_chat_prompt, usage_from_texts

        # Extract the last user message as the prompt
        user_messages = [m for m in request.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message provided",
            )
        prompt = user_messages[-1].content
        requested_model = (request.model or "").strip()
        conversation_messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ]

        decision = classify_prompt_with_hang_nadim(prompt, requested_model)
        route_to_swarm = decision.route in {"swarm", "legendary_swarm"}
        explicit_swarm = requested_model.lower() in (SWARM_MODEL_ALIASES | LEGENDARY_MODEL_ALIASES)

        if route_to_swarm:
            try:
                prepared_prompt = prepare_chat_prompt(
                    prompt,
                    mode="deliberate",
                    model=requested_model,
                    provider="swarm",
                    conversation_messages=conversation_messages,
                )
                response_text, swarm_result, _orchestrator = await _run_swarm_prompt(
                    prompt,
                    user_id="openai-compatible",
                    requested_model=requested_model,
                )
                usage = usage_from_texts(
                    prepared_prompt.prompt,
                    response_text,
                    model=requested_model,
                    provider="swarm",
                )
                await _persist_model_usage(
                    username="openai-compatible",
                    model_name="jebat-legend" if decision.route == "legendary_swarm" else "jebat-swarm",
                    provider="swarm",
                    usage={
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                    latency_ms=int(max(swarm_result.execution_time, 0) * 1000),
                )
                return {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "jebat-legend" if decision.route == "legendary_swarm" else "jebat-swarm",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text,
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                    "provider": "swarm",
                    "routing": {
                        "route": decision.route,
                        "reason": decision.reason,
                        "required_capabilities": decision.required_capabilities,
                    },
                    "swarm_lead": (
                        swarm_result.result.get("swarm_lead")
                        if isinstance(swarm_result.result, dict)
                        else None
                    ),
                    "reducer": (
                        swarm_result.result.get("reducer")
                        if isinstance(swarm_result.result, dict)
                        else None
                    ),
                    "doctrine": (
                        swarm_result.result.get("doctrine")
                        if isinstance(swarm_result.result, dict)
                        else None
                    ),
                    "security_layer": (
                        swarm_result.result.get("security_layer")
                        if isinstance(swarm_result.result, dict)
                        else None
                    ),
                    "swarm": swarm_result.result,
                }
            except HTTPException:
                if explicit_swarm:
                    raise
                logger.warning("Swarm routing unavailable, falling back to single-model path")
            except Exception as exc:
                if explicit_swarm:
                    raise
                logger.warning("Swarm routing failed (%s), falling back to single-model path", exc)

        mode_map = {
            "jebat-fast": "fast",
            "jebat-pro": "deliberate",
            "jebat-deep": "deep",
            "jebat-swarm": "deliberate",
            "jebat-legend": "deliberate",
        }
        preset_map = {
            "jebatcpp-coding": "coding",
            "jebatcpp-roleplay": "roleplay",
            "jebatcpp-uncensored": "uncensored",
        }
        config = load_llm_config()
        model_override = None if requested_model in {
            "",
            "jebat-fast",
            "jebat-pro",
            "jebat-deep",
            "jebat-swarm",
            "jebat-legend",
            "jebatcpp-coding",
            "jebatcpp-roleplay",
            "jebatcpp-uncensored",
        } else requested_model
        requested_max_tokens = request.max_tokens
        if requested_max_tokens is not None:
            requested_max_tokens = max(1, min(int(requested_max_tokens), 512))

        # Keep public llama.cpp responses short enough to avoid edge 504s on CPU VPSes.
        if config.provider == "llamacpp":
            effective_max_tokens = min(requested_max_tokens or 128, 128)
        else:
            effective_max_tokens = requested_max_tokens or config.max_tokens

        response_text, used_provider, active_config, generation_meta = await generate_chat_reply(
            prompt=prompt,
            mode=mode_map.get(requested_model, "deliberate"),
            preset=preset_map.get(requested_model, "default"),
            model_override=model_override or config.model,
            temperature_override=request.temperature,
            max_tokens_override=effective_max_tokens,
            conversation_messages=conversation_messages,
            return_metadata=True,
        )
        await _persist_model_usage(
            username="openai-compatible",
            model_name=active_config.model,
            provider=used_provider,
            usage=generation_meta.usage,
            latency_ms=int(max(time.time() - start, 0) * 1000),
        )

        if used_provider == "local":
            logger.warning(
                "Suppressed local echo fallback for model=%s provider=%s",
                requested_model or active_config.model,
                config.provider,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Primary LLM backend unavailable; local echo fallback suppressed",
            )

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": active_config.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": generation_meta.usage,
            "provider": used_provider,
            "prompt_profile": generation_meta.prompt_profile,
            "conversation": {
                "history_summary_turns": generation_meta.history_summary_turns,
                "recent_turns": generation_meta.recent_turns,
                "estimated_prompt_tokens": generation_meta.prompt_tokens_estimate,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OpenAI chat completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/api/v1/agents", tags=["Agents"])
async def list_agents():
    """
    List available agents.

    Returns information about all registered agents.
    """
    if not jebat_components.get("agent_orchestrator"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Orchestrator not initialized",
        )

    # Return agent information
    orchestrator = jebat_components["agent_orchestrator"]
    agents = orchestrator.list_agents()
    return {
        "agents": agents,
        "total": len(agents),
        "status": "operational",
        "stats": orchestrator.get_stats(),
    }


@app.post("/api/v1/swarm/plan", response_model=SwarmPlanResponse, tags=["Agents"])
async def plan_swarm_task(request: SwarmTaskRequest):
    """
    Preview swarm routing, ranking, and lead selection without executing the task.
    """
    if not jebat_components.get("agent_orchestrator"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Orchestrator not initialized",
        )

    try:
        task = _build_swarm_task_from_request(request)
        orchestrator = jebat_components["agent_orchestrator"]
        plan = orchestrator.plan_task(task)
        return SwarmPlanResponse(**plan)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid execution mode: {request.execution_mode}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Swarm plan error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.post("/api/v1/swarm/execute", response_model=SwarmTaskResponse, tags=["Agents"])
async def execute_swarm_task(request: SwarmTaskRequest):
    """
    Execute a task through the JEBAT swarm orchestrator.

    This is the direct automation entrypoint for multi-agent routing,
    search, and consensus judgment.
    """
    if not jebat_components.get("agent_orchestrator"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Orchestrator not initialized",
        )

    try:
        task = _build_swarm_task_from_request(request)

        orchestrator = jebat_components["agent_orchestrator"]
        result = await orchestrator.execute_task(task)
        return SwarmTaskResponse(
            task_id=result.task_id,
            success=result.success,
            execution_mode=str(result.metadata.get("execution_mode", request.execution_mode or "consensus")),
            execution_time=result.execution_time,
            result=result.result,
            error=result.error,
            swarm_lead=(
                result.result.get("swarm_lead")
                if isinstance(result.result, dict)
                else None
            ),
            reducer=(
                result.result.get("reducer")
                if isinstance(result.result, dict)
                else None
            ),
            doctrine=(
                result.result.get("doctrine")
                if isinstance(result.result, dict)
                else None
            ),
            security_layer=(
                result.result.get("security_layer")
                if isinstance(result.result, dict)
                else result.metadata.get("security_layer")
            ),
            full_orchestration=bool(result.metadata.get("full_orchestration", False)),
            stats=orchestrator.get_stats(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid execution mode: {request.execution_mode}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Swarm execution error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ==================== Run Server ====================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "jebat_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
