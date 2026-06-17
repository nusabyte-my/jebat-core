"""
JEBAT v6.1 — Full API Entry Point
====================================
Docker entrypoint that exposes the complete JEBAT API surface.

Routers:
    /api/status      — System status, health, LLM config
    /api/chat         — LLM chat with provider failover
    /api/agents       — Agent orchestrator and task execution
    /api/memory       — 5-layer eternal memory system
    /api/skills       — Skill registry and execution
    /api/think        — UltraThink deep reasoning engine
    /api/loop         — UltraLoop continuous processing
    /api/pentest      — Security scanning and pentest

Start:
    uvicorn main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response

from jebat.api.auth import APIKeyMiddleware
from jebat.api.logging import RequestLoggingMiddleware, clear_all_logs, export_logs, get_request_stats, get_recent_logs

from typing import Optional
from jebat.database.connection_manager import close_all, get_db_manager, get_redis_manager

from routers.agents import router as agents_router
from routers.auth import router as auth_router
from routers.catalyst import router as catalyst_router
from routers.chat import router as chat_router
from routers.ghost import router as ghost_router
from routers.loop import router as loop_router
from routers.memory import router as memory_router
from routers.pentest import router as pentest_router
from routers.skills import router as skills_router
from routers.status import router as status_router
from routers.think import router as think_router

_START_TIME = time.time()

# Feature flags — disable DB/Redis if env vars aren't set
DATABASE_ENABLED = os.getenv("JEBAT_DATABASE_ENABLED", "false").lower() in ("true", "1", "yes")
REDIS_ENABLED = os.getenv("JEBAT_REDIS_ENABLED", "false").lower() in ("true", "1", "yes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    version = os.getenv("JEBAT_VERSION", "6.1.0")
    host = os.getenv("JEBAT_API_HOST", "0.0.0.0")
    port = os.getenv("JEBAT_API_PORT", "8080")
    print(f"\n{'='*60}")
    print(f"  JEBAT v{version} API starting on {host}:{port}")
    print(f"  Endpoints: /api/status, /api/chat, /api/agents,")
    print(f"             /api/memory, /api/skills, /api/think, /api/loop")
    print(f"{'='*60}\n")

    # --- Initialize connections independently (respect feature flags) ---

    if DATABASE_ENABLED:
        try:
            from jebat.database.connection_manager import get_db_manager
            db = get_db_manager()
            await db.connect()
            print("  ✅ PostgreSQL connection pool ready")
        except Exception as exc:
            print(f"  ⚠️  PostgreSQL connection failed: {exc}")
            print("  ℹ️  Running in degraded mode (DB queries will fail)")
    else:
        print("  ℹ️  JEBAT_DATABASE_ENABLED not set — DB layer disabled")

    if REDIS_ENABLED:
        try:
            rm = get_redis_manager()
            if rm._client is None:
                await rm.connect()
            print("  ✅ Redis connection ready")
        except Exception as exc:
            print(f"  ⚠️  Redis connection failed: {exc}")
            print("  ℹ️  Running in degraded mode (cache will be in-memory)")
    else:
        print("  ℹ️  JEBAT_REDIS_ENABLED not set — Redis layer disabled")

    yield

    # --- Shutdown ---
    if DATABASE_ENABLED or REDIS_ENABLED:
        await close_all()
    print("\n🗡️  JEBAT API shutting down.\n")


app = FastAPI(
    title="JEBAT API",
    version=os.getenv("JEBAT_VERSION", "6.1.0"),
    description="Sovereign AI Platform — Private LLM Inference, Agent Orchestration & Eternal Memory",
    lifespan=lifespan,
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "root", "description": "API root and liveness checks."},
        {"name": "health", "description": "Health and readiness probes (\"/health\", \"/ready\")."},
        {"name": "status", "description": "System status, configuration, and diagnostics."},
        {"name": "chat", "description": "LLM chat with provider failover and streaming."},
        {"name": "agents", "description": "Agent orchestrator and task execution."},
        {"name": "memory", "description": "5-layer eternal memory system (episodic, semantic, procedural, working, meta)."},
        {"name": "skills", "description": "Skill registry, execution, and management."},
        {"name": "think", "description": "UltraThink deep reasoning engine."},
        {"name": "loop", "description": "UltraLoop continuous processing."},
        {"name": "pentest", "description": "Security scanning and penetration testing tools."},
        {"name": "auth", "description": "API key management — rotation, revocation, and metadata."},
        {"name": "logging", "description": "Request logging — query recent logs, export, and clear."},
        {"name": "monitoring", "description": "Prometheus-compatible metrics endpoint."},
        {
            "name": "ghost",
            "description": (
                "Ghost Database — ephemeral, forkable databases for isolated agent work. "
                "Create sandboxed databases, fork them for agent tasks, execute SQL, "
                "take checkpoints, and restore snapshots. Designed for safe multi-agent "
                "concurrency without data leakage between agents."
            ),
        },
        {
            "name": "catalyst",
            "description": (
                "Catalyst Observability — distributed tracing and performance analysis. "
                "Instrument JEBAT services, record spans and events, query trace histories, "
                "and run HALO analysis to compare traces for optimization recommendations. "
                "Provides end-to-end visibility into LLM calls, tool invocations, and "
                "agent workflows."
            ),
        },
    ],
)

# CORS — allow all origins in dev, lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("JEBAT_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication — protects /api/* routes
# Set JEBAT_API_KEY env var to enable; unset = dev mode (all open)
app.add_middleware(APIKeyMiddleware)

# Request logging — records method, path, status, latency, IP for /api/* routes to Redis
app.add_middleware(RequestLoggingMiddleware)

# ─── Mount all API routers ───
app.include_router(status_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(memory_router)
app.include_router(skills_router)
app.include_router(think_router)
app.include_router(loop_router)
app.include_router(pentest_router)
app.include_router(ghost_router)
app.include_router(catalyst_router)


# ─── Documentation Portal ───

def _load_docs_html() -> str:
    """Load the documentation portal HTML from disk (cached after first read)."""
    import functools

    @functools.lru_cache(maxsize=1)
    def _read() -> str:
        from pathlib import Path

        html_path = Path(__file__).parent / "docs.html"
        if html_path.exists():
            return html_path.read_text(encoding="utf-8")
        return "<h1>docs.html not found</h1>"

    return _read()


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def docs_portal():
    """Documentation portal — guides, deployment, and API reference."""
    return HTMLResponse(content=_load_docs_html())


# ─── Root & Health ───

@app.get("/", tags=["root"])
async def root():
    """API root — quick liveness check."""
    return {
        "service": "jebat-api",
        "version": os.getenv("JEBAT_VERSION", "6.1.0"),
        "status": "running",
        "docs": "/docs",
        "swagger": "/swagger",
        "endpoints": {
            "status": "/api/status",
            "chat": "/api/chat",
            "agents": "/api/agents",
            "memory": "/api/memory",
            "skills": "/api/skills",
            "think": "/api/think",
            "loop": "/api/loop",
            "pentest": "/api/pentest",
            "ghost": "/api/ghost",
            "catalyst": "/api/catalyst",
        },
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check — returns 200 when the process is alive."""
    return {
        "status": "healthy",
        "uptime_s": round(time.time() - _START_TIME, 1),
    }


@app.get("/ready", tags=["health"])
async def ready():
    """Readiness check — verifies PostgreSQL and Redis connectivity.

    Returns 200 only when all required backends respond.
    Returns 503 if any critical backend is down.
    """
    status_code = 200
    components: dict[str, dict] = {}

    # --- PostgreSQL check ---
    if DATABASE_ENABLED:
        try:
            db_mgr = get_db_manager()
            db_health = await db_mgr.health()
            components["postgres"] = db_health
            if db_health["status"] != "connected":
                status_code = 503
        except Exception as exc:
            components["postgres"] = {"status": "error", "error": str(exc)}
            status_code = 503
    else:
        components["postgres"] = {"status": "disabled", "reason": "JEBAT_DATABASE_ENABLED not set"}

    # --- Redis check ---
    if REDIS_ENABLED:
        try:
            redis_mgr = get_redis_manager()
            redis_health = await redis_mgr.health()
            components["redis"] = redis_health
            if redis_health["status"] != "connected":
                status_code = 503
        except Exception as exc:
            components["redis"] = {"status": "error", "error": str(exc)}
            status_code = 503
    else:
        components["redis"] = {"status": "disabled", "reason": "JEBAT_REDIS_ENABLED not set"}

    # --- Request stats from Redis ---
    if REDIS_ENABLED:
        try:
            stats = await get_request_stats()
            components["requests"] = stats
        except Exception as exc:
            components["requests"] = {"status": "error", "error": str(exc)}
    else:
        components["requests"] = {"status": "disabled", "reason": "JEBAT_REDIS_ENABLED not set"}

    overall = "ready" if status_code == 200 else "degraded"
    result = {
        "status": overall,
        "uptime_s": round(time.time() - _START_TIME, 1),
        "components": components,
    }

    return JSONResponse(content=result, status_code=status_code)


@app.get("/api/logs/recent", tags=["logging"])
async def logs_recent(
    limit: Optional[int] = 50,
    status: Optional[int] = None,
    path_contains: Optional[str] = None,
    method: Optional[str] = None,
):
    """Return the last N logged requests with optional filters.

    Query params:
        limit — Max entries (1-500, default 50)
        status — Filter by HTTP status code (e.g. 404, 500)
        path — Substring match on request path
        method — Filter by HTTP method (GET, POST, etc.)
    """
    return await get_recent_logs(limit=limit, status=status, path_filter=path_contains, method=method)


@app.delete("/api/logs/clear", tags=["logging"])
async def logs_clear():
    """Flush all request log data from Redis.

    Deletes the recent request list, all counters (total, errors, per-status),
    path counts, and the latency accumulator. Returns a summary of what was
    cleared.
    """
    return await clear_all_logs()


@app.get("/api/logs/export", tags=["logging"])
async def logs_export(format: Optional[str] = "json"):
    """Export all logged requests as a downloadable CSV or JSON file.

    Query params:
        format — "json" (default) or "csv"
    """
    fmt = (format or "json").lower()
    if fmt not in ("json", "csv"):
        fmt = "json"

    content, media_type, filename = await export_logs(format=fmt)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    return JSONResponse(
        content=(
            "# HELP jebat_uptime_seconds JEBAT API uptime\n"
            "# TYPE jebat_uptime_seconds gauge\n"
            f"jebat_uptime_seconds {round(time.time() - _START_TIME, 1)}\n"
        ),
        media_type="text/plain",
    )
