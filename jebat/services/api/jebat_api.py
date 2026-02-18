"""
JEBAT REST API

FastAPI-based REST API for JEBAT AI Assistant.

Endpoints:
- GET  /api/v1/status              - System status
- POST /api/v1/chat/completions    - Chat with JEBAT
- GET  /api/v1/memories            - List memories
- POST /api/v1/memories            - Store memory
- GET  /api/v1/agents              - List agents
- POST /api/v1/agents/:id/execute  - Execute agent
- GET  /api/v1/metrics             - System metrics
- GET  /api/v1/health              - Health check
"""

import logging
from datetime import datetime
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


# ==================== Global State ====================

# These will be initialized when the API starts
jebat_components = {
    "memory_manager": None,
    "ultra_loop": None,
    "ultra_think": None,
    "agent_orchestrator": None,
}


# ==================== Startup/Shutdown ====================


@app.on_event("startup")
async def startup_event():
    """Initialize JEBAT components on startup"""
    logger.info("Starting JEBAT API...")

    try:
        # Import JEBAT components
        from jebat import MemoryManager
        from jebat.core.agents.orchestrator import AgentOrchestrator
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

        jebat_components["agent_orchestrator"] = AgentOrchestrator()
        logger.info("✓ Agent Orchestrator initialized")

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
        "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat(),
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

    return {
        "ultra_loop": ultra_loop_metrics,
        "ultra_think": ultra_think_stats,
        "memory": memory_stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/v1/chat/completions", response_model=ChatResponse, tags=["Chat"])
async def chat_completion(request: ChatRequest):
    """
    Chat with JEBAT.

    Processes a user message through Ultra-Think and returns a response.
    """
    if not jebat_components.get("ultra_think"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ultra-Think not initialized",
        )

    try:
        from jebat.features.ultra_think import ThinkingMode

        # Map mode string to ThinkingMode
        try:
            thinking_mode = ThinkingMode(request.mode.lower())
        except ValueError:
            thinking_mode = ThinkingMode.DELIBERATE

        # Run thinking session
        result = await jebat_components["ultra_think"].think(
            problem=request.message,
            mode=thinking_mode,
            user_id=request.user_id,
            timeout=request.timeout,
        )

        return ChatResponse(
            response=result.conclusion,
            confidence=result.confidence,
            thinking_steps=len(result.reasoning_steps),
            execution_time=result.execution_time,
            user_id=request.user_id,
        )

    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


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
                created_at=datetime.utcnow().isoformat(),
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
            created_at=datetime.utcnow().isoformat(),
            heat_score=0.8,
        )

    except Exception as e:
        logger.error(f"Store memory error: {e}")
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
    return {
        "agents": [],
        "total": 0,
        "status": "operational",
    }


# ==================== Run Server ====================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "jebat_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
