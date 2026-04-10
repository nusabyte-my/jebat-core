"""
JEBAT REST API

FastAPI-based REST API for JEBAT AI Assistant.

Endpoints:
- GET  /api/v1/health              - Health check
- GET  /api/v1/status              - System status
- GET  /api/v1/metrics             - System metrics
- GET  /api/v1/models              - List models (OpenAI-compatible, used by Zed)
- POST /api/v1/chat/completions    - Chat completions (OpenAI-compatible, used by Zed)
- GET  /api/v1/memories            - List memories
- POST /api/v1/memories            - Store memory
- GET  /api/v1/agents              - List agents
- GET  /api/v1/skills              - List skills (from VPS)
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .security_console import router as security_console_router

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
app.include_router(security_console_router)


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


class SkillInfo(BaseModel):
    """Skill metadata for listing"""
    name: str
    description: str = ""
    category: str = "general"
    version: str = "1.0.0"
    source: str = "vps"


# ==================== Global State ====================

# These will be initialized when the API starts
jebat_components = {
    "memory_manager": None,
    "ultra_loop": None,
    "ultra_think": None,
    "agent_orchestrator": None,
    "agent_registry": None,
}

# Skill directory configuration
VPS_SKILLS_DIR = os.path.expanduser("/root/jebat-core/skills")


# ==================== Startup/Shutdown ====================


@app.on_event("startup")
async def startup_event():
    """Initialize JEBAT components on startup"""
    logger.info("Starting JEBAT API...")

    # ── Agent Registry (must come first — no transitive import issues) ──
    try:
        from apps.api.core.agents.agent_registry import AgentRegistry, register_builtin_agents
        from apps.api.core.agents.orchestrator import AgentOrchestrator

        jebat_components["agent_registry"] = AgentRegistry()
        register_builtin_agents(jebat_components["agent_registry"])
        agent_count = len(jebat_components["agent_registry"].get_all_agents())
        logger.info(f"✓ Agent Registry initialized ({agent_count} agents)")

        jebat_components["agent_orchestrator"] = AgentOrchestrator(
            agent_registry=jebat_components["agent_registry"],
        )
        logger.info("✓ Agent Orchestrator initialized (wired to AgentRegistry)")
    except Exception as e:
        logger.error(f"Agent init error: {e}")

    # ── Memory Manager ──
    try:
        from apps.api.core.memory import MemoryManager
        jebat_components["memory_manager"] = MemoryManager()
        logger.info("✓ Memory Manager initialized")
    except Exception as e:
        logger.error(f"Memory init error: {e}")

    # ── Ultra-Loop (may fail if db/models import chain broken) ──
    try:
        from apps.api.features.ultra_loop import create_ultra_loop
        jebat_components["ultra_loop"] = await create_ultra_loop(
            config={"cycle_interval": 1.0, "max_cycles": 0},
            enable_db_persistence=False,
        )
        logger.info("✓ Ultra-Loop initialized")
        await jebat_components["ultra_loop"].start()
        logger.info("✓ Ultra-Loop started")
    except Exception as e:
        logger.error(f"Ultra-Loop init error: {e}")

    # ── Ultra-Think (may fail if db/models import chain broken) ──
    try:
        from apps.api.features.ultra_think import create_ultra_think
        jebat_components["ultra_think"] = await create_ultra_think(
            config={"max_thoughts": 20, "default_mode": "deliberate"},
            memory_manager=jebat_components["memory_manager"],
            enable_db_persistence=False,
            enable_memory_integration=True,
        )
        logger.info("✓ Ultra-Think initialized")
    except Exception as e:
        logger.error(f"Ultra-Think init error: {e}")

    logger.info("JEBAT API startup complete")


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
        from apps.api.core.memory.layers import MemoryLayer

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


@app.get("/api/v1/models", tags=["OpenAI Compatible"])
async def list_models():
    """
    List available models (OpenAI-compatible).

    Zed calls this endpoint to discover available models.
    """
    return {
        "object": "list",
        "data": [
            {"id": "jebat-pro", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-fast", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-deep", "object": "model", "owned_by": "jebat"},
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

    if not jebat_components.get("ultra_think"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ultra-Think not initialized",
        )

    try:
        from apps.api.features.ultra_think import ThinkingMode

        # Extract the last user message as the prompt
        user_messages = [m for m in request.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message provided",
            )
        prompt = user_messages[-1].content

        # Map model name to thinking mode
        mode_map = {
            "jebat-fast": ThinkingMode.FAST,
            "jebat-pro": ThinkingMode.DELIBERATE,
            "jebat-deep": ThinkingMode.DEEP,
        }
        thinking_mode = mode_map.get(request.model, ThinkingMode.DELIBERATE)

        # Run thinking session
        result = await jebat_components["ultra_think"].think(
            problem=prompt,
            mode=thinking_mode,
            timeout=60,
        )

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.conclusion,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(result.conclusion.split()),
                "total_tokens": len(prompt.split()) + len(result.conclusion.split()),
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
    registry = jebat_components.get("agent_registry")
    orchestrator = jebat_components.get("agent_orchestrator")

    if not registry:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Registry not initialized",
        )

    agents = registry.get_all_agents()
    agents_data = []
    for agent in agents:
        agents_data.append({
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_role": agent.agent_role,
            "provider": agent.provider,
            "model": agent.model,
            "capabilities": agent.capabilities,
            "languages": agent.languages,
            "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
        })

    stats = registry.get_stats()

    result = {
        "agents": agents_data,
        "total": len(agents_data),
        "status": "operational" if orchestrator else "partial",
        "stats": stats,
    }

    if orchestrator:
        result["orchestrator"] = orchestrator.get_stats()

    return result


@app.get("/api/v1/skills", tags=["Skills"])
async def list_skills():
    """
    List available skills from VPS.

    Scans the VPS skills directory for SKILL.md files and returns metadata.
    Skills are stored at /root/jebat-core/skills/ on the VPS.
    """
    skills = []
    skills_dir = VPS_SKILLS_DIR

    # Try VPS skills directory first
    if os.path.exists(skills_dir):
        try:
            for entry in os.listdir(skills_dir):
                skill_path = os.path.join(skills_dir, entry)
                if os.path.isdir(skill_path):
                    skill_md = os.path.join(skill_path, "SKILL.md")
                    if os.path.exists(skill_md):
                        with open(skill_md, "r") as f:
                            content = f.read()
                        # Parse frontmatter for metadata
                        name = entry
                        description = ""
                        category = "general"
                        version = "1.0.0"
                        if "---" in content:
                            parts = content.split("---", 2)
                            if len(parts) >= 2:
                                frontmatter = parts[1]
                                for line in frontmatter.split("\n"):
                                    if line.startswith("name:"):
                                        name = line.split(":", 1)[1].strip().strip("'\"")
                                    elif line.startswith("description:"):
                                        description = line.split(":", 1)[1].strip().strip("'\"")
                                    elif line.startswith("category:"):
                                        category = line.split(":", 1)[1].strip().strip("'\"")
                                    elif line.startswith("version:"):
                                        version = line.split(":", 1)[1].strip().strip("'\"")
                        skills.append({
                            "name": name,
                            "description": description,
                            "category": category,
                            "version": version,
                            "source": "vps",
                            "content": content[:500],  # First 500 chars preview
                        })
        except Exception as e:
            logger.error(f"Error reading skills directory: {e}")

    return {
        "skills": skills,
        "total": len(skills),
        "source": "vps",
        "path": skills_dir,
    }


# ==================== Run Server ====================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
