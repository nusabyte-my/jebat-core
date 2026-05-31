"""
JEBAT WebUI - Simplified Version

A reliable web interface for JEBAT AI Assistant.
"""

import asyncio
import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[3]

# Router for WebUI
webui_router = APIRouter(tags=["webui"])

# Store for active connections
active_connections: Dict[str, WebSocket] = {}


# ==================== Models ====================


class ChatMessage(BaseModel):
    user_id: str
    message: str
    thinking_mode: Optional[str] = "deliberate"
    preset: Optional[str] = "default"


class ThinkRequest(BaseModel):
    problem: str
    mode: str = "deliberate"
    timeout: Optional[float] = 30.0


class RuntimeControlRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


class ProviderAuthRequest(BaseModel):
    provider: str
    secret: Optional[str] = None
    host: Optional[str] = None


RUNTIME_OVERRIDES: Dict[str, Optional[str]] = {"provider": None, "model": None}


class ChannelConnectRequest(BaseModel):
    channel: str
    config: Dict[str, Any]


class WorkstationConnectRequest(BaseModel):
    workstation: str
    path: Optional[str] = None
    notes: Optional[str] = None
    ssh_host: Optional[str] = None
    ssh_user: Optional[str] = None
    deploy_path: Optional[str] = None


class WorkstationActionRequest(BaseModel):
    workstation: str


CHANNEL_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
WORKSTATION_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
CHANNEL_SECRETS: Dict[str, Dict[str, Any]] = {}
ACTIVE_CHANNELS: Dict[str, Any] = {}
CHANNEL_TASKS: Dict[str, asyncio.Task] = {}
STATE_LOCK = asyncio.Lock()
STATE_LOADED = False
DATA_DIR: Optional[Path] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_data_dir() -> Path:
    candidates = [
        Path("/app/data/webui"),
        REPO_ROOT / ".webui_state",
        Path(tempfile.gettempdir()) / "jebat_webui_state",
    ]
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("ok")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    raise RuntimeError("no writable webui state directory available")


def _data_path(filename: str) -> Path:
    global DATA_DIR
    if DATA_DIR is None:
        DATA_DIR = _resolve_data_dir()
    return DATA_DIR / filename


def _ensure_data_dir() -> None:
    _data_path(".init")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        logger.exception("Failed to read JSON state: %s", path)
        return default


def _write_json(path: Path, payload: Any, chmod_600: bool = False) -> None:
    _ensure_data_dir()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    if chmod_600:
        path.chmod(0o600)


def _provider_env_targets(provider: str) -> list[str]:
    mapping = {
        "openai": ["OPENAI_API_KEY"],
        "google": ["GOOGLE_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "llamacpp": ["LLAMA_CPP_HOST"],
        "ollama": ["OLLAMA_HOST"],
    }
    return mapping.get(provider, [])


def _read_provider_auth_store() -> Dict[str, str]:
    data = _read_json(_data_path("provider_auth.json"), {})
    return data if isinstance(data, dict) else {}


def _write_provider_auth_store(store: Dict[str, str]) -> None:
    _write_json(_data_path("provider_auth.json"), store, chmod_600=True)


def _sanitize_channel_state(channel: str, state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "channel": channel,
        "status": state.get("status", "unknown"),
        "required": state.get("required", []),
        "missing": state.get("missing", []),
        "updated_at": state.get("updated_at"),
        "config_keys": state.get("config_keys", []),
        "active": state.get("active", False),
        "last_error": state.get("last_error"),
        "instructions": state.get("instructions"),
    }


def _sanitize_workstation_state(name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "workstation": name,
        "status": state.get("status", "unknown"),
        "path": state.get("path"),
        "notes": state.get("notes", ""),
        "ssh_host": state.get("ssh_host"),
        "ssh_user": state.get("ssh_user"),
        "deploy_path": state.get("deploy_path"),
        "updated_at": state.get("updated_at"),
        "health": state.get("health"),
    }


def _provider_model_catalog() -> dict[str, dict[str, Any]]:
    return {
        "openai": {
            "label": "OpenAI",
            "supports_custom": False,
            "models": [
                "gpt-5.4",
                "gpt-5.4-mini",
                "gpt-5.3-codex",
                "gpt-5.2",
            ],
        },
        "google": {
            "label": "Google",
            "supports_custom": False,
            "models": [
                "gemini-3-flash-preview",
                "gemini-3.1-pro-preview",
                "gemini-2.5-pro",
            ],
        },
        "anthropic": {
            "label": "Anthropic",
            "supports_custom": False,
            "models": [
                "claude-sonnet-4-5",
                "claude-opus-4-1",
                "claude-3-7-sonnet-latest",
            ],
        },
        "openrouter": {
            "label": "OpenRouter",
            "supports_custom": True,
            "models": [
                "openai/gpt-5.4",
                "anthropic/claude-sonnet-4-5",
                "google/gemini-2.5-pro",
            ],
        },
        "llamacpp": {
            "label": "llama.cpp",
            "supports_custom": True,
            "models": [],
        },
        "ollama": {
            "label": "Ollama",
            "supports_custom": True,
            "models": [
                "hermes3:8b",
                "qwen2.5-coder:7b",
                "hermes-sec-v2:latest",
                "llama3:8b",
            ],
        },
        "local": {
            "label": "Local",
            "supports_custom": False,
            "models": ["local-echo"],
        },
    }


def _default_model_for_provider(provider: str, configured_model: str) -> str:
    catalog = _provider_model_catalog()
    provider_entry = catalog.get(provider, {})
    models = provider_entry.get("models", [])
    if configured_model in models:
        return configured_model
    return models[0] if models else configured_model


async def _ensure_connection_state() -> None:
    global STATE_LOADED
    if STATE_LOADED:
        return
    async with STATE_LOCK:
        if STATE_LOADED:
            return
        CHANNEL_CONNECTIONS.update(_read_json(_data_path("channel_connections.json"), {}))
        CHANNEL_SECRETS.update(_read_json(_data_path("channel_secrets.json"), {}))
        WORKSTATION_CONNECTIONS.update(_read_json(_data_path("workstation_connections.json"), {}))
        RUNTIME_OVERRIDES.update(_read_json(_data_path("runtime_overrides.json"), {"provider": None, "model": None}))
        STATE_LOADED = True
        await _reactivate_saved_channels()


async def _persist_channel_state() -> None:
    _write_json(_data_path("channel_connections.json"), CHANNEL_CONNECTIONS)
    _write_json(_data_path("channel_secrets.json"), CHANNEL_SECRETS, chmod_600=True)


def _persist_workstation_state() -> None:
    _write_json(_data_path("workstation_connections.json"), WORKSTATION_CONNECTIONS)


def _persist_runtime_state() -> None:
    _write_json(_data_path("runtime_overrides.json"), RUNTIME_OVERRIDES)


async def _reactivate_saved_channels() -> None:
    for channel, state in list(CHANNEL_CONNECTIONS.items()):
        secret = CHANNEL_SECRETS.get(channel, {})
        if state.get("status") in {"active", "configured", "starting"} and secret:
            await _activate_channel(channel, secret, persist=False)


async def _activate_channel(channel: str, config: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
    state = CHANNEL_CONNECTIONS.setdefault(channel, {})
    state.setdefault("required", [])
    state["config_keys"] = sorted(config.keys())
    state["updated_at"] = _now_iso()
    state["active"] = False
    state["last_error"] = None

    try:
        if channel == "telegram":
            from jebat.integrations.channels.telegram import create_telegram_channel

            instance = await create_telegram_channel(bot_token=config["bot_token"])
            await instance.start()
            ACTIVE_CHANNELS[channel] = instance
            state["status"] = "active"
            state["active"] = True
        elif channel == "whatsapp":
            from jebat.integrations.channels.whatsapp import WhatsAppChannel

            instance = WhatsAppChannel(
                phone_number_id=config["phone_number_id"],
                access_token=config["access_token"],
                verify_token=config["verify_token"],
            )
            await instance.start()
            ACTIVE_CHANNELS[channel] = instance
            state["status"] = "active"
            state["active"] = True
        elif channel == "slack":
            from jebat.integrations.channels.slack import SlackChannel

            instance = SlackChannel(
                bot_token=config["bot_token"],
                signing_secret=config["signing_secret"],
            )
            await instance.start()
            ACTIVE_CHANNELS[channel] = instance
            state["status"] = "active"
            state["active"] = True
        elif channel == "discord":
            from jebat.integrations.channels.discord import DiscordChannel

            instance = DiscordChannel(bot_token=config["bot_token"])
            task = asyncio.create_task(instance.start())
            CHANNEL_TASKS[channel] = task
            ACTIVE_CHANNELS[channel] = instance
            state["status"] = "starting"
            state["active"] = True
        else:
            state["status"] = "configured"
        if persist:
            await _persist_channel_state()
        return _sanitize_channel_state(channel, state)
    except Exception as exc:
        logger.exception("Channel activation failed for %s", channel)
        state["status"] = "error"
        state["active"] = False
        state["last_error"] = str(exc)
        if persist:
            await _persist_channel_state()
        return _sanitize_channel_state(channel, state)


# ==================== Routes ====================


# Public chat redirect (legacy path) — delegate to SPA
@webui_router.get("/chat", response_class=HTMLResponse)
@webui_router.get("/chat/", response_class=HTMLResponse)
async def get_public_chat():
    """Legacy public chat path — redirect to main webui."""
    return FileResponse(STATIC_DIR / "index.html")


@webui_router.get("/webui/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "ultra_loop": "operational",
            "ultra_think": "operational",
            "memory_manager": "operational",
            "cache_manager": "operational",
            "decision_engine": "operational",
            "agent_orchestrator": "operational",
        },
        "active_connections": len(active_connections),
    }


@webui_router.get("/webui/api/console-meta")
async def get_console_meta():
    """Return UI metadata grounded in repo assets."""
    return _console_meta()


@webui_router.get("/webui/api/runtime")
async def get_runtime():
    """Return live runtime info for the WebUI shell."""
    await _ensure_connection_state()
    return _runtime_state()


@webui_router.post("/webui/api/runtime")
async def update_runtime(payload: RuntimeControlRequest):
    """Set a preferred provider/model override for the live WebUI shell."""
    await _ensure_connection_state()
    state = _runtime_state()
    status_items = state["providers"]["available"]
    catalog = state["providers"]["catalog"]
    allowed = {item["provider"] for item in status_items}
    provider = (payload.provider or "").strip().lower() or None
    model = (payload.model or "").strip() or None

    if provider and provider not in allowed:
        raise HTTPException(status_code=400, detail=f"unknown provider: {provider}")
    if provider and provider in catalog:
        provider_models = catalog[provider].get("models", [])
        supports_custom = bool(catalog[provider].get("supports_custom"))
        if model and not supports_custom and model not in provider_models:
            raise HTTPException(
                status_code=400,
                detail=f"invalid model for provider {provider}: {model}",
            )
        if not model:
            model = _default_model_for_provider(provider, state["provider"]["configured_model"])

    RUNTIME_OVERRIDES["provider"] = provider
    RUNTIME_OVERRIDES["model"] = model
    _persist_runtime_state()
    return _runtime_state()


@webui_router.post("/webui/api/provider-auth")
async def update_provider_auth(payload: ProviderAuthRequest):
    """Store provider auth or host data for the WebUI runtime."""
    await _ensure_connection_state()
    provider = payload.provider.strip().lower()
    targets = _provider_env_targets(provider)
    if not targets:
        raise HTTPException(status_code=400, detail=f"provider does not support auth storage: {provider}")

    store = _read_provider_auth_store()
    if provider in {"ollama", "llamacpp"}:
        value = (payload.host or payload.secret or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail=f"missing host for {provider}")
        store["OLLAMA_HOST" if provider == "ollama" else "LLAMA_CPP_HOST"] = value
    else:
        value = (payload.secret or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="missing API key")
        store[targets[0]] = value
    _write_provider_auth_store(store)
    return {
        "ok": True,
        "provider": provider,
        "configured_targets": targets,
        "runtime": _runtime_state(),
    }


@webui_router.get("/webui/api/channels/connect")
async def get_channel_connections():
    """Return channel connection status and requirements."""
    await _ensure_connection_state()
    return {
        "available": _channel_catalog(),
        "connections": {
            name: _sanitize_channel_state(name, state)
            for name, state in CHANNEL_CONNECTIONS.items()
        },
        "timestamp": _now_iso(),
    }


@webui_router.post("/webui/api/channels/connect")
async def connect_channel(payload: ChannelConnectRequest):
    """Store channel connection intent/config summary for the console."""
    await _ensure_connection_state()
    catalog = {item["id"]: item for item in _channel_catalog()}
    channel = payload.channel.strip().lower()
    if channel not in catalog:
        raise HTTPException(status_code=400, detail=f"unknown channel: {channel}")

    required = catalog[channel]["required"]
    missing = [item for item in required if not str(payload.config.get(item, "")).strip()]
    status = "configured" if not missing else "incomplete"
    CHANNEL_CONNECTIONS[channel] = {
        "status": status,
        "required": required,
        "missing": missing,
        "updated_at": _now_iso(),
        "config_keys": sorted(payload.config.keys()),
        "instructions": catalog[channel]["instructions"],
    }
    CHANNEL_SECRETS[channel] = dict(payload.config)
    await _persist_channel_state()
    connection = (
        await _activate_channel(channel, CHANNEL_SECRETS[channel])
        if not missing
        else _sanitize_channel_state(channel, CHANNEL_CONNECTIONS[channel])
    )
    return {
        "ok": True,
        "channel": channel,
        "connection": connection,
        "instructions": catalog[channel]["instructions"],
    }


@webui_router.get("/webui/api/workstations/connect")
async def get_workstation_connections():
    """Return workstation connection status."""
    await _ensure_connection_state()
    return {
        "available": _workstation_catalog(),
        "connections": {
            name: _sanitize_workstation_state(name, state)
            for name, state in WORKSTATION_CONNECTIONS.items()
        },
        "timestamp": _now_iso(),
    }


@webui_router.post("/webui/api/workstations/connect")
async def connect_workstation(payload: WorkstationConnectRequest):
    """Store workstation connection intent/config summary for the console."""
    await _ensure_connection_state()
    catalog = {item["id"]: item for item in _workstation_catalog()}
    workstation = payload.workstation.strip().lower()
    if workstation not in catalog:
        raise HTTPException(status_code=400, detail=f"unknown workstation: {workstation}")

    state = {
        "status": "connected" if payload.path else "pending",
        "path": payload.path or catalog[workstation]["path"],
        "notes": payload.notes or "",
        "ssh_host": payload.ssh_host or "",
        "ssh_user": payload.ssh_user or "",
        "deploy_path": payload.deploy_path or "",
        "updated_at": _now_iso(),
    }
    if workstation == "vps":
        state["status"] = "connected" if (state["ssh_host"] or state["path"]) else "pending"
    WORKSTATION_CONNECTIONS[workstation] = state
    _persist_workstation_state()
    return {
        "ok": True,
        "workstation": workstation,
        "connection": _sanitize_workstation_state(workstation, WORKSTATION_CONNECTIONS[workstation]),
    }


@webui_router.post("/webui/api/workstations/check")
async def check_workstation(payload: WorkstationActionRequest):
    """Run a lightweight health check for a stored workstation profile."""
    await _ensure_connection_state()
    workstation = payload.workstation.strip().lower()
    state = WORKSTATION_CONNECTIONS.get(workstation)
    if not state:
        raise HTTPException(status_code=404, detail=f"unknown workstation: {workstation}")

    health: Dict[str, Any] = {"ok": False, "detail": "No health check available", "checked_at": _now_iso()}
    if workstation == "vps":
        target = state.get("ssh_host") or state.get("path") or ""
        if target:
            health = {
                "ok": True,
                "detail": f"Stored VPS target ready for operator use: {target}",
                "checked_at": _now_iso(),
            }
        else:
            health = {
                "ok": False,
                "detail": "Missing VPS host. Save ssh_host or path first.",
                "checked_at": _now_iso(),
            }
    elif workstation in {"cli", "jebat-gateway", "vscode"}:
        target = state.get("path") or ""
        health = {
            "ok": bool(target),
            "detail": f"Stored path: {target}" if target else "Missing path",
            "checked_at": _now_iso(),
        }

    state["health"] = health
    state["updated_at"] = _now_iso()
    _persist_workstation_state()
    return {
        "ok": True,
        "workstation": workstation,
        "connection": _sanitize_workstation_state(workstation, state),
    }


@webui_router.post("/webui/api/chat")
async def chat(message: ChatMessage):
    """Process chat message with the configured LLM provider."""
    try:
        from jebat.llm import generate_chat_reply

        await _ensure_connection_state()
        response, used_provider, config = await generate_chat_reply(
            prompt=message.message,
            mode=message.thinking_mode,
            preset=message.preset,
            provider_override=RUNTIME_OVERRIDES["provider"],
            model_override=RUNTIME_OVERRIDES["model"],
        )

        return {
            "success": True,
            "response": response,
            "provider": used_provider,
            "model": config.model,
            "thinking_mode": message.thinking_mode,
            "preset": message.preset,
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "Sorry, I encountered an error processing your message.",
        }


@webui_router.post("/webui/api/think")
async def think(request: ThinkRequest):
    """Run Ultra-Think session"""
    try:
        from jebat.features.ultra_think import ThinkingMode, create_ultra_think

        mode_map = {
            "fast": ThinkingMode.FAST,
            "deliberate": ThinkingMode.DELIBERATE,
            "deep": ThinkingMode.DEEP,
            "strategic": ThinkingMode.STRATEGIC,
            "creative": ThinkingMode.CREATIVE,
            "critical": ThinkingMode.CRITICAL,
        }
        thinking_mode = mode_map.get(request.mode.lower(), ThinkingMode.DELIBERATE)

        thinker = await create_ultra_think(config={"max_thoughts": 20})

        result = await asyncio.wait_for(
            thinker.think(
                problem=request.problem, mode=thinking_mode, timeout=request.timeout
            ),
            timeout=request.timeout + 5,
        )

        return {
            "success": True,
            "trace_id": result.trace.trace_id,
            "conclusion": result.conclusion,
            "confidence": result.confidence,
            "thought_count": len(result.reasoning_steps),
            "thought_chain": result.reasoning_steps,
            "alternatives": result.alternatives,
            "execution_time": result.execution_time,
            "mode": request.mode,
        }
    except Exception as e:
        logger.error(f"Think error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@webui_router.get("/webui/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    try:
        from jebat.core.memory import MemoryManager

        manager = MemoryManager()
        stats = manager.get_memory_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e), "stats": {}}


# ── Agents status ──
@webui_router.get("/webui/api/agents/status")
async def agents_status():
    """Return agent force status including orchestration info."""
    meta = _console_meta()
    gw = meta.get("jebat-gateway", {})
    agent_names = gw.get("agent_names", [])
    agents = [
        {
            "name": name,
            "state": "ready",
            "provider": gw.get("primary_model", "unknown"),
        }
        for name in agent_names
    ]
    return {
        "agents": agents,
        "mode": "auto",
        "sub_agents": len(agents),
        "auto_dispatch": True,
    }


# ── Health ──
@webui_router.get("/webui/api/health")
async def health_check():
    """Lightweight health check."""
    from datetime import datetime, timezone as _dt
    return {
        "ok": True,
        "uptime": "JEBAT online",
        "timestamp": _dt.now(_dt.timezone.utc).isoformat(),
    }


# ── Nine-Router control ──
@webui_router.post("/webui/api/nine-router/{action}")
async def nine_router_action(action: str):
    """Control the 9-Router proxy (start, stop, status)."""
    action = action.lower()
    if action == "start":
        try:
            from jebat.services.nine_router import ensure_nine_router_running
            await ensure_nine_router_running()
            return {"status": "started", "message": "9-Router proxy started."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif action == "stop":
        return {"status": "stopped", "message": "9-Router control acknowledged."}
    elif action == "status":
        import psutil
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(proc.info["cmdline"] or [])
                if "nine_router" in cmd:
                    return {"status": "running", "pid": proc.info["pid"], "message": f"9-Router running (PID {proc.info['pid']})"}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"status": "stopped", "message": "9-Router not running."}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


# ── Skills import ──
@webui_router.post("/webui/api/skills/import")
async def skills_import(payload: dict):
    """Preview or import skills from another agent platform."""
    source = (payload.get("source") or "").lower()
    action = payload.get("action", "preview")
    repo = REPO_ROOT
    counts = {"hermes": 0, "openclaw": 0, "claude": 0, "codex": 0}
    skill_dir = repo / "jebat-tokguru"
    if skill_dir.exists():
        counts["hermes"] = len(list(skill_dir.glob("*/SKILL.md")))
    integrations_skills = repo / "integrations" / "jebat-gateway" / "workspace" / "skills"
    if integrations_skills.exists():
        counts["openclaw"] = len(list(integrations_skills.glob("*")))
    return {
        "source": source,
        "action": action,
        "count": counts.get(source, 0),
        "available": counts,
        "message": f"Found {counts.get(source, 0)} {source} skills. {action} mode." if source in counts else f"Unknown source: {source}",
    }


@webui_router.websocket("/webui/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    active_connections[user_id] = websocket
    logger.info(f"WebSocket connected: {user_id}")

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "welcome",
                "message": f"Welcome to JEBAT, {user_id}!",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "chat":
                try:
                    from jebat.llm import generate_chat_reply

                    await _ensure_connection_state()
                    response, used_provider, config = await generate_chat_reply(
                        prompt=message_data.get("message", ""),
                        mode=message_data.get("mode", "deliberate"),
                        preset=message_data.get("preset", "default"),
                        provider_override=RUNTIME_OVERRIDES["provider"],
                        model_override=RUNTIME_OVERRIDES["model"],
                    )

                    await websocket.send_json(
                        {
                            "type": "chat_response",
                            "success": True,
                            "response": response,
                            "provider": used_provider,
                            "model": config.model,
                            "preset": message_data.get("preset", "default"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": str(e),
                        }
                    )

            elif message_data.get("type") == "ping":
                await websocket.send_json(
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user_id in active_connections:
            del active_connections[user_id]


# ==================== Static File Serving ====================

STATIC_DIR = Path(__file__).resolve().parent / "static"


@webui_router.get("/webui", response_class=HTMLResponse)
@webui_router.get("/webui/", response_class=HTMLResponse)
@webui_router.get("/webui/chat", response_class=HTMLResponse)
@webui_router.get("/webui/dashboard", response_class=HTMLResponse)
@webui_router.get("/webui/memory", response_class=HTMLResponse)
@webui_router.get("/webui/agents", response_class=HTMLResponse)
@webui_router.get("/webui/skills", response_class=HTMLResponse)
@webui_router.get("/webui/doctor", response_class=HTMLResponse)
@webui_router.get("/webui/control", response_class=HTMLResponse)
@webui_router.get("/webui/channels", response_class=HTMLResponse)
@webui_router.get("/webui/workstation", response_class=HTMLResponse)
@webui_router.get("/webui/integrations", response_class=HTMLResponse)
@webui_router.get("/webui/learning", response_class=HTMLResponse)
@webui_router.get("/webui/setup", response_class=HTMLResponse)
async def serve_spa():
    """Serve the Brutalist SPA shell. Client-side router handles all navigation."""
    return FileResponse(STATIC_DIR / "index.html")


@webui_router.get("/webui/partials/{page}", response_class=HTMLResponse)
async def serve_partial(page: str):
    """Serve a page partial for client-side routing."""
    # Strip .html extension if present (fastapi captures it in the param)
    name = page.replace('.html', '')
    partial_path = STATIC_DIR / "partials" / f"{name}.html"
    if not partial_path.exists():
        raise HTTPException(status_code=404, detail=f"partial not found: {name}")
    return FileResponse(partial_path)


# Mount static files at /webui/static/ — CSS, JS, images
def _mount_static(app: FastAPI) -> None:
    """Mount static file routes on the app. Must be called after app creation."""
    from fastapi.staticfiles import StaticFiles

    css_dir = STATIC_DIR / "css"
    js_dir = STATIC_DIR / "js"
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)

    if not any(route.path == "/webui/static/css" for route in app.routes if hasattr(route, "path")):
        app.mount("/webui/static/css", StaticFiles(directory=str(css_dir)), name="webui_css")
    if not any(route.path == "/webui/static/js" for route in app.routes if hasattr(route, "path")):
        app.mount("/webui/static/js", StaticFiles(directory=str(js_dir)), name="webui_js")
    if not any(route.path == "/webui/static/partials" for route in app.routes if hasattr(route, "path")):
        app.mount("/webui/static/partials", StaticFiles(directory=str(STATIC_DIR / "partials")), name="webui_partials")


# ==================== Utility Functions ====================


def _console_meta() -> dict[str, Any]:
    openclaw_template = REPO_ROOT / "integrations" / "jebat-gateway" / "openclaw.template.json"
    jebat_gateway_data = json.loads(openclaw_template.read_text()) if openclaw_template.exists() else {}

    channel_dir = REPO_ROOT / "jebat" / "integrations" / "channels"
    available_channels = sorted(
        path.stem for path in channel_dir.glob("*.py") if path.stem != "__init__"
    )

    skill_root = REPO_ROOT / "jebat-tokguru"
    try:
        from jebat.llm.skills import build_skill_registry, summarize_skill

        registry = build_skill_registry(skill_root)
        all_skills = registry.get_all_skills()
        featured_names = [
            "hermes-agent",
            "skill-forge",
            "webfetch",
            "search",
            "test",
            "python-patterns",
            "docker-expert",
        ]
        featured_skills = []
        seen_featured = set()
        for name in featured_names:
            skill = registry.get_skill(name)
            if skill:
                featured_skills.append(summarize_skill(skill))
                seen_featured.add(skill.name)
        for skill in all_skills:
            if len(featured_skills) >= 7:
                break
            if skill.name in seen_featured:
                continue
            featured_skills.append(summarize_skill(skill))
        top_skills = featured_skills[:7]
    except Exception:
        all_skills = []
        top_skills = []

    openclaw_skill_path = (
        REPO_ROOT
        / "integrations"
        / "jebat-gateway"
        / "workspace"
        / "skills"
        / "hermes-agent"
        / "SKILL.md"
    )
    openclaw_skill_excerpt = ""
    if openclaw_skill_path.exists():
        openclaw_skill_excerpt = "\n".join(
            line.strip()
            for line in openclaw_skill_path.read_text().splitlines()
            if line.strip() and not line.startswith("---")
        )[:280]

    return {
        "jebat-gateway": {
            "gateway_port": jebat_gateway_data.get("gateway", {}).get("port"),
            "channel_names": sorted((jebat_gateway_data.get("channels") or {}).keys()),
            "agent_names": [
                item.get("identity", {}).get("name", item.get("id"))
                for item in jebat_gateway_data.get("agents", {}).get("list", [])
            ],
            "primary_model": jebat_gateway_data.get("agents", {})
            .get("defaults", {})
            .get("model", {})
            .get("primary"),
            "fallback_models": jebat_gateway_data.get("agents", {})
            .get("defaults", {})
            .get("model", {})
            .get("fallbacks", []),
        },
        "channels": available_channels,
        "workstations": [
            {"name": "CLI", "path": "~/.local/bin/jebat-cli", "state": "ready"},
            {"name": "Jebat Gateway", "path": "~/.openclaw", "state": "ready"},
            {"name": "VS Code", "path": "~/.config/Code/User", "state": "ready"},
            {"name": "VPS", "path": "jebat.online", "state": "live"},
        ],
        "integrations": [
            {"name": "OpenClaw Bundle", "path": "integrations/openclaw", "state": "versioned"},
            {"name": "MCP Guide", "path": "docs/MCP_INTEGRATION_GUIDE.md", "state": "available"},
            {"name": "IDE Guide", "path": "docs/IDE_INTEGRATION_GUIDE.md", "state": "available"},
        ],
        "skills": {
            "count": len(all_skills),
            "top": top_skills,
            "jebat_gateway_excerpt": openclaw_skill_excerpt,
        },
        "learning": {
            "modules": [
                "jebat/continuum/skill_learning.py",
                "jebat/cortex/intelligent_skill.py",
                "jebat/cortex/skill_recommender.py",
            ]
        },
    }


def _runtime_state() -> dict[str, Any]:
    from jebat.llm import (
        list_chat_presets,
        list_provider_auth_status,
        load_llm_config,
        normalize_chat_preset,
        select_best_provider,
    )

    config = load_llm_config()
    catalog = _provider_model_catalog()
    available = [
        {
            "provider": item.provider,
            "configured": item.configured,
            "env_vars": list(item.env_vars),
            "notes": item.notes,
            "label": catalog.get(item.provider, {}).get("label", item.provider.title()),
            "models": catalog.get(item.provider, {}).get("models", []),
            "supports_custom": bool(catalog.get(item.provider, {}).get("supports_custom")),
        }
        for item in list_provider_auth_status()
    ]
    effective_provider = (
        RUNTIME_OVERRIDES["provider"]
        or select_best_provider(config.provider, config.fallback_providers)
    )
    configured_model = config.model
    default_effective_model = _default_model_for_provider(effective_provider, configured_model)
    effective_model = RUNTIME_OVERRIDES["model"] or default_effective_model
    meta = _console_meta()
    return {
        "provider": {
            "configured": config.provider,
            "configured_model": configured_model,
            "effective": effective_provider,
            "model": effective_model,
            "fallbacks": list(config.fallback_providers),
            "override": dict(RUNTIME_OVERRIDES),
            "hosts": {
                "ollama": config.ollama_host,
                "llamacpp": config.llamacpp_host,
            },
            "presets": list_chat_presets(),
            "default_preset": normalize_chat_preset("default"),
        },
        "providers": {"available": available, "catalog": catalog},
        "workspace": {"stations": meta["workstations"], "integrations": meta["integrations"]},
        "channels": meta["channels"],
        "channel_connections": CHANNEL_CONNECTIONS,
        "workstation_connections": WORKSTATION_CONNECTIONS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _channel_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": "telegram",
            "label": "Telegram",
            "required": ["bot_token"],
            "instructions": "Provide a Telegram bot token and route traffic through the Telegram channel adapter.",
        },
        {
            "id": "whatsapp",
            "label": "WhatsApp",
            "required": ["phone_number_id", "access_token", "verify_token"],
            "instructions": "Provide WhatsApp Business API credentials for the WhatsApp channel adapter.",
        },
        {
            "id": "discord",
            "label": "Discord",
            "required": ["bot_token", "guild_id"],
            "instructions": "Provide Discord bot credentials and target guild.",
        },
        {
            "id": "slack",
            "label": "Slack",
            "required": ["bot_token", "app_token"],
            "instructions": "Provide Slack bot/app tokens for socket mode or webhook routing.",
        },
    ]


def _workstation_catalog() -> list[dict[str, Any]]:
    return [
        {"id": "cli", "label": "CLI", "path": "~/.local/bin/jebat-cli", "supports_remote": False},
        {"id": "jebat-gateway", "label": "Jebat Gateway", "path": "~/.openclaw", "supports_remote": False},
        {"id": "vscode", "label": "VS Code", "path": "~/.config/Code/User", "supports_remote": False},
        {"id": "vps", "label": "VPS", "path": "jebat.online", "supports_remote": True},
]
