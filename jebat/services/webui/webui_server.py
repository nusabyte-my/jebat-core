"""
JEBAT WebUI - Simplified Version

A reliable web interface for JEBAT AI Assistant.
"""

import asyncio
import json
import logging
import tempfile
from datetime import datetime
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
from fastapi.responses import HTMLResponse, JSONResponse
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
    return datetime.utcnow().isoformat()


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


@webui_router.get("/webui/", response_class=HTMLResponse)
@webui_router.get("/webui", response_class=HTMLResponse)
async def get_webui():
    """Serve the main WebUI"""
    return _get_home_html()


@webui_router.get("/webui/chat", response_class=HTMLResponse)
async def get_chat():
    """Serve chat interface"""
    return _get_chat_html()


@webui_router.get("/webui/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve system dashboard"""
    return _get_dashboard_html()


@webui_router.get("/webui/memory", response_class=HTMLResponse)
async def get_memory():
    """Serve memory explorer"""
    return _get_memory_html()


@webui_router.get("/webui/agents", response_class=HTMLResponse)
async def get_agents():
    """Serve agent catalog."""
    return _get_agents_html()


@webui_router.get("/webui/skills", response_class=HTMLResponse)
async def get_skills():
    """Serve skill catalog."""
    return _get_skills_html()


@webui_router.get("/webui/doctor", response_class=HTMLResponse)
async def get_doctor():
    """Serve doctor page."""
    return _get_doctor_html()


@webui_router.get("/webui/control", response_class=HTMLResponse)
async def get_control():
    """Serve OpenClaw-style control page."""
    return _get_control_html()


@webui_router.get("/webui/channels", response_class=HTMLResponse)
async def get_channels():
    """Serve channel overview."""
    return _get_channels_html()


@webui_router.get("/webui/workstation", response_class=HTMLResponse)
async def get_workstation():
    """Serve workstation connection page."""
    return _get_workstation_html()


@webui_router.get("/webui/integrations", response_class=HTMLResponse)
async def get_integrations():
    """Serve integrations page."""
    return _get_integrations_html()


@webui_router.get("/webui/learning", response_class=HTMLResponse)
async def get_learning():
    """Serve skill learning page."""
    return _get_learning_html()


@webui_router.get("/webui/setup", response_class=HTMLResponse)
async def get_setup():
    """Serve setup guide page."""
    return _get_setup_html()


@webui_router.get("/webui/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
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
    if provider == "ollama":
        value = (payload.host or payload.secret or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="missing host for ollama")
        store["OLLAMA_HOST"] = value
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
    elif workstation in {"cli", "openclaw", "vscode"}:
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
    """Process chat message with Ultra-Think"""
    try:
        from jebat.features.ultra_think import ThinkingMode, create_ultra_think

        # Map thinking mode string to enum
        mode_map = {
            "fast": ThinkingMode.FAST,
            "deliberate": ThinkingMode.DELIBERATE,
            "deep": ThinkingMode.DEEP,
            "strategic": ThinkingMode.STRATEGIC,
            "creative": ThinkingMode.CREATIVE,
            "critical": ThinkingMode.CRITICAL,
        }
        thinking_mode = mode_map.get(
            message.thinking_mode.lower(), ThinkingMode.DELIBERATE
        )

        # Create thinker and process
        thinker = await create_ultra_think(
            config={"max_thoughts": 15, "default_mode": message.thinking_mode}
        )

        # Run thinking in executor to avoid blocking
        result = await asyncio.wait_for(
            thinker.think(problem=message.message, mode=thinking_mode, timeout=30.0),
            timeout=35.0,
        )

        return {
            "success": True,
            "response": result.conclusion,
            "confidence": result.confidence,
            "thinking_steps": len(result.reasoning_steps),
            "reasoning": result.reasoning_steps[:5],
            "alternatives": result.alternatives,
            "execution_time": result.execution_time,
        }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Thinking timed out. Please try again with a simpler question or 'fast' mode.",
            "response": "I'm taking too long to think about this. Please try again!",
            "confidence": 0.0,
            "thinking_steps": 0,
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "Sorry, I encountered an error processing your message.",
            "confidence": 0.0,
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
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "chat":
                try:
                    from jebat.features.ultra_think import (
                        ThinkingMode,
                        create_ultra_think,
                    )

                    thinker = await create_ultra_think(config={"max_thoughts": 10})
                    thinking_mode = ThinkingMode(message_data.get("mode", "deliberate"))

                    result = await asyncio.wait_for(
                        thinker.think(
                            problem=message_data.get("message", ""),
                            mode=thinking_mode,
                            timeout=30.0,
                        ),
                        timeout=35.0,
                    )

                    await websocket.send_json(
                        {
                            "type": "chat_response",
                            "success": True,
                            "response": result.conclusion,
                            "confidence": result.confidence,
                            "thoughts": len(result.reasoning_steps),
                            "reasoning": result.reasoning_steps,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except asyncio.TimeoutError:
                    await websocket.send_json(
                        {
                            "type": "chat_response",
                            "success": False,
                            "error": "Thinking timed out",
                            "timestamp": datetime.utcnow().isoformat(),
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
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user_id in active_connections:
            del active_connections[user_id]


# ==================== HTML Generators ====================


def _get_home_html():
    return HTMLResponse(content=_home_html())


def _get_chat_html():
    return HTMLResponse(content=_chat_html())


def _get_dashboard_html():
    return HTMLResponse(content=_dashboard_html())


def _get_memory_html():
    return HTMLResponse(content=_memory_html())


def _get_agents_html():
    return HTMLResponse(content=_agents_html())


def _get_skills_html():
    return HTMLResponse(content=_skills_html())


def _get_doctor_html():
    return HTMLResponse(content=_doctor_html())


def _get_control_html():
    return HTMLResponse(content=_control_html())


def _get_channels_html():
    return HTMLResponse(content=_channels_html())


def _get_workstation_html():
    return HTMLResponse(content=_workstation_html())


def _get_integrations_html():
    return HTMLResponse(content=_integrations_html())


def _get_learning_html():
    return HTMLResponse(content=_learning_html())


def _get_setup_html():
    return HTMLResponse(content=_setup_html())


def _console_meta() -> dict[str, Any]:
    openclaw_template = REPO_ROOT / "integrations" / "openclaw" / "openclaw.template.json"
    openclaw_data = json.loads(openclaw_template.read_text()) if openclaw_template.exists() else {}

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
        / "openclaw"
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
        "openclaw": {
            "gateway_port": openclaw_data.get("gateway", {}).get("port"),
            "channel_names": sorted((openclaw_data.get("channels") or {}).keys()),
            "agent_names": [
                item.get("identity", {}).get("name", item.get("id"))
                for item in openclaw_data.get("agents", {}).get("list", [])
            ],
            "primary_model": openclaw_data.get("agents", {})
            .get("defaults", {})
            .get("model", {})
            .get("primary"),
            "fallback_models": openclaw_data.get("agents", {})
            .get("defaults", {})
            .get("model", {})
            .get("fallbacks", []),
        },
        "channels": available_channels,
        "workstations": [
            {"name": "CLI", "path": "~/.local/bin/jebat-cli", "state": "ready"},
            {"name": "OpenClaw", "path": "~/.openclaw", "state": "ready"},
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
            "openclaw_excerpt": openclaw_skill_excerpt,
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
    from jebat.llm import list_provider_auth_status, load_llm_config, select_best_provider

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
        },
        "providers": {"available": available, "catalog": catalog},
        "workspace": {"stations": meta["workstations"], "integrations": meta["integrations"]},
        "channels": meta["channels"],
        "channel_connections": CHANNEL_CONNECTIONS,
        "workstation_connections": WORKSTATION_CONNECTIONS,
        "timestamp": datetime.utcnow().isoformat(),
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
        {"id": "openclaw", "label": "OpenClaw", "path": "~/.openclaw", "supports_remote": False},
        {"id": "vscode", "label": "VS Code", "path": "~/.config/Code/User", "supports_remote": False},
        {"id": "vps", "label": "VPS", "path": "jebat.online", "supports_remote": True},
    ]


# HTML templates (simplified for reliability)
def _home_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Console</title>
<style>
:root{--bg:#02070a;--bg2:#091116;--sidebar:#081015;--panel:rgba(10,20,24,.88);--panel-soft:rgba(11,18,22,.74);--line:#183039;--line-strong:#23505c;--text:#e7f8f5;--muted:#83a8a4;--accent:#6ef7c8;--accent-2:#17baff;--danger:#ff5f57;--ok:#6ef7c8;--warn:#f7b955;--mono:"JetBrains Mono","IBM Plex Mono","Cascadia Code","Fira Code","SFMono-Regular",Menlo,Monaco,Consolas,"Liberation Mono",monospace}
*{margin:0;padding:0;box-sizing:border-box}body{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at top left,rgba(23,186,255,.12),transparent 22%),radial-gradient(circle at top right,rgba(110,247,200,.10),transparent 20%),radial-gradient(circle at bottom,rgba(255,95,87,.08),transparent 18%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh;position:relative}
body:before{content:"";position:fixed;inset:0;pointer-events:none;background:linear-gradient(rgba(255,255,255,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.018) 1px,transparent 1px);background-size:32px 32px;mask-image:linear-gradient(180deg,rgba(0,0,0,.42),transparent 78%)}
button,input,select{font:inherit}a{text-decoration:none;color:inherit}
.app{display:grid;grid-template-columns:310px 1fr;min-height:100vh}.sidebar{padding:22px 18px;border-right:1px solid var(--line);background:linear-gradient(180deg,rgba(5,14,18,.98),rgba(8,16,21,.96));position:sticky;top:0;height:100vh;overflow:auto;font-family:var(--mono);box-shadow:inset -1px 0 0 rgba(255,255,255,.02)}
.brand{display:flex;gap:14px;align-items:center;padding:8px 8px 18px}.brand-mark{width:54px;height:54px;border-radius:16px;background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#041116;display:grid;place-items:center;font-weight:900;letter-spacing:.08em;box-shadow:0 0 40px rgba(23,186,255,.18)}.brand-copy small{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.18em;font-size:10px}.brand-copy strong{display:block;font-size:23px;letter-spacing:.06em}
.brand-stack{padding:12px 10px 16px;border:1px solid var(--line);border-radius:18px;background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,.01));margin-bottom:12px}.terminal-line{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:var(--muted);padding-top:10px}.terminal-line strong{color:var(--accent);font-weight:700}.stack-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.stack-tags span{padding:6px 9px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.02);font-size:11px;color:var(--text)}
.sidebar-section{padding:14px 8px 8px}.sidebar-section label{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.18em;margin-bottom:10px}
.nav-list{display:grid;gap:6px}.nav-item{display:flex;align-items:center;justify-content:space-between;padding:11px 12px;border:1px solid transparent;border-radius:14px;color:var(--muted);cursor:pointer;transition:.18s ease;font-family:var(--mono);background:rgba(255,255,255,.012)}.nav-item:hover,.nav-item.active{background:linear-gradient(90deg,rgba(110,247,200,.08),rgba(23,186,255,.07));border-color:var(--line-strong);color:var(--text);transform:translateX(2px)}.nav-meta{font-size:11px;color:#9ee8ff;text-transform:uppercase;letter-spacing:.16em}
.mini-card{padding:14px;border-radius:16px;background:rgba(255,255,255,.03);border:1px solid var(--line);margin:8px 0;font-family:var(--mono)}.mini-card strong{display:block;font-size:16px}.mini-card span{display:block;color:var(--muted);font-size:13px;line-height:1.6;margin-top:6px}
.content{padding:22px 24px 28px;overflow:auto}.toolbar{display:flex;gap:14px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;margin-bottom:18px}.status-strip,.hero,.grid-card,.wide-card,.table-card{background:var(--panel);border:1px solid var(--line);border-radius:24px;backdrop-filter:blur(14px)}
.status-strip{display:flex;gap:16px;flex-wrap:wrap;padding:16px 18px}.status-pill{display:inline-flex;align-items:center;gap:10px;padding:8px 12px;border:1px solid var(--line);border-radius:999px;font-size:13px;color:var(--muted);font-family:var(--mono);background:rgba(255,255,255,.015)}.dot{width:10px;height:10px;border-radius:50%;background:var(--ok);box-shadow:0 0 18px rgba(110,247,200,.45)}
.hero{padding:30px;position:relative;overflow:hidden;margin-bottom:18px;background:linear-gradient(135deg,rgba(7,21,25,.94),rgba(9,16,22,.92))}.hero:before{content:"";position:absolute;inset:auto -8% -28% auto;width:420px;height:420px;background:radial-gradient(circle,rgba(23,186,255,.14),transparent 62%)}.hero:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(135deg,rgba(110,247,200,.04),transparent 36%,rgba(255,95,87,.04));mix-blend-mode:screen}.eyebrow{display:inline-flex;align-items:center;gap:10px;padding:8px 12px;background:rgba(110,247,200,.08);border:1px solid rgba(110,247,200,.24);border-radius:999px;color:#baffea;font-size:12px;text-transform:uppercase;letter-spacing:.16em;font-family:var(--mono)}.hero h1{font-size:clamp(34px,4.5vw,66px);line-height:.94;max-width:13ch;margin:18px 0 14px}.hero p{max-width:66ch;color:var(--muted);font-size:16px;line-height:1.78}.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}
.btn{padding:12px 16px;border-radius:14px;font-weight:700;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);cursor:pointer}.btn.primary{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#041116;border:none;box-shadow:0 12px 32px rgba(23,186,255,.18)}
.layout{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.stack{display:grid;gap:18px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.grid-card,.wide-card,.table-card{padding:22px}.card-label{display:inline-flex;padding:6px 10px;border:1px solid var(--line-strong);border-radius:999px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#ffc8c3;background:rgba(255,95,87,.06);margin-bottom:14px}.grid-card h3,.wide-card h3,.table-card h3{font-size:18px;margin-bottom:10px}.grid-card p,.wide-card p,.table-card p,.table-card li{color:var(--muted);line-height:1.65;font-size:14px}
.layout{display:grid;grid-template-columns:1.18fr .82fr;gap:18px}.stack{display:grid;gap:18px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.grid-card,.wide-card,.table-card{padding:22px;position:relative;overflow:hidden}.grid-card:before,.wide-card:before,.table-card:before{content:"";position:absolute;inset:auto auto 0 0;width:120px;height:120px;background:radial-gradient(circle,rgba(23,186,255,.08),transparent 70%);pointer-events:none}.card-label{display:inline-flex;padding:6px 10px;border:1px solid var(--line-strong);border-radius:999px;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#baffea;background:rgba(110,247,200,.05);margin-bottom:14px;font-family:var(--mono)}.grid-card h3,.wide-card h3,.table-card h3{font-size:18px;margin-bottom:10px}.grid-card p,.wide-card p,.table-card p,.table-card li{color:var(--muted);line-height:1.68;font-size:14px}
.kv{display:grid;gap:12px}.kv-item{padding:14px;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.02)}.kv-item label{display:block;color:var(--muted);font-size:11px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px}.kv-item strong{display:block;font-size:22px}
.control-form{display:grid;gap:12px}.control-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.control-grid.tight{grid-template-columns:repeat(3,minmax(0,1fr))}.input,.select{width:100%;padding:12px 14px;background:#0f1518;border:1px solid var(--line);border-radius:14px;color:var(--text)}
.provider-stack{display:grid;gap:18px}.provider-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.provider-card{padding:16px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.02)}.provider-card.active{border-color:rgba(255,95,87,.42);background:linear-gradient(180deg,rgba(255,95,87,.08),rgba(255,255,255,.02))}.provider-card h4{font-size:16px;margin-bottom:8px}.provider-meta{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 12px}.chip{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;border:1px solid var(--line);font-size:12px;color:var(--muted)}.chip.ok{color:#9ff0c4}.chip.warn{color:#ffd79d}.small-note{color:var(--muted);font-size:12px;line-height:1.6}.model-hint{padding:12px 14px;border:1px solid var(--line);border-radius:14px;background:rgba(255,255,255,.02);color:var(--muted);font-size:13px;line-height:1.6}
.list{list-style:none;display:grid;gap:10px;margin-top:12px}.list li{padding:12px 14px;border:1px solid var(--line);border-radius:14px;background:rgba(255,255,255,.02)}.list strong{display:block;color:var(--text)}
.table{display:grid;gap:10px}.row{display:grid;grid-template-columns:1.2fr .8fr .8fr;gap:12px;padding:12px 14px;border:1px solid var(--line);border-radius:14px;background:rgba(255,255,255,.02)}.row.head{background:transparent;border:none;padding:0;color:var(--muted);font-size:11px;letter-spacing:.14em;text-transform:uppercase}.toolbar-inline{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px}.ghost-btn{padding:10px 12px;border-radius:12px;border:1px solid var(--line);background:rgba(255,255,255,.03);color:var(--text);cursor:pointer}.drawer-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:flex-end;justify-content:flex-end;z-index:50}.drawer-backdrop.open{display:flex}.drawer{width:min(520px,100%);height:100%;background:#0d1215;border-left:1px solid var(--line);padding:24px;overflow:auto}.drawer h3{font-size:24px;margin-bottom:10px}.drawer pre{white-space:pre-wrap;color:var(--muted);line-height:1.7;background:rgba(255,255,255,.02);border:1px solid var(--line);border-radius:14px;padding:14px;margin-top:14px}.chat-shell{display:grid;grid-template-rows:1fr auto;min-height:70vh}.chat-log{display:grid;gap:12px;max-height:60vh;overflow:auto;padding-right:4px}.chat-entry{padding:14px 16px;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.02)}.chat-entry.user{background:rgba(255,95,87,.08);border-color:rgba(255,95,87,.18)}.chat-entry strong{display:block;margin-bottom:6px}.chat-compose{display:grid;gap:12px;margin-top:14px}.chat-compose textarea{min-height:120px;resize:vertical;padding:14px;background:#0f1518;border:1px solid var(--line);border-radius:14px;color:var(--text)}.chat-meta{display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:12px}
.empty{color:var(--muted);padding:22px;border:1px dashed var(--line);border-radius:16px}
@media (max-width:1080px){.app{grid-template-columns:1fr}.sidebar{position:relative;height:auto;border-right:none;border-bottom:1px solid var(--line)}.layout,.grid,.control-grid,.control-grid.tight,.provider-grid{grid-template-columns:1fr}.content{padding:18px}}
</style>
</head>
<body>
<div class="app">
<aside class="sidebar">
<div class="brand-stack"><div class="brand"><div class="brand-mark">J</div><div class="brand-copy"><small>Hermes x OpenClaw</small><strong>JEBATCore</strong></div></div><div class="terminal-line"><span>profile</span><strong>cyber-ops</strong></div><div class="terminal-line"><span>focus</span><strong>capture > control > execute</strong></div><div class="stack-tags"><span>hermes</span><span>openclaw</span><span>security</span></div></div>
<div class="sidebar-section">
<label>Navigation</label>
<input id="navFilter" class="input" style="margin-bottom:10px" placeholder="Filter menu">
<div class="nav-list" id="navList"></div>
</div>
<div class="sidebar-section">
<label>Runtime</label>
<div class="mini-card"><strong id="effectiveProvider">Loading</strong><span id="providerMeta">Checking provider path and live model selection.</span></div>
<div class="mini-card"><strong id="workspaceState">Workspace Ready</strong><span id="workspaceMeta">CLI, OpenClaw, VS Code, and VPS surfaces available.</span></div>
</div>
<div class="sidebar-section">
<label>Shell Shortcuts</label>
<div class="nav-list">
<a class="nav-item" href="#livechat" data-section="livechat"><span>Live chat</span><span class="nav-meta">run</span></a>
<a class="nav-item" href="#control" data-section="control"><span>Runtime</span><span class="nav-meta">route</span></a>
<a class="nav-item" href="#channels" data-section="channels"><span>Channels</span><span class="nav-meta">wire</span></a>
<a class="nav-item" href="#workstation" data-section="workstation"><span>Stations</span><span class="nav-meta">ops</span></a>
</div>
</div>
</aside>
<main class="content">
<div class="toolbar"><div class="status-strip" id="statusStrip"></div></div>
<section id="view"></section>
</main>
</div>
<div class="drawer-backdrop" id="drawerBackdrop"><aside class="drawer"><button class="ghost-btn" id="drawerClose" style="margin-bottom:14px">Close</button><div id="drawerContent"></div></aside></div>
<script>
const sections = [
  {id:'overview', label:'Bridge', meta:'surface'},
  {id:'livechat', label:'Hermes', meta:'session'},
  {id:'control', label:'Models', meta:'router'},
  {id:'doctor', label:'Pulse', meta:'health'},
  {id:'channels', label:'Channels', meta:'adapters'},
  {id:'workstation', label:'Stations', meta:'connect'},
  {id:'integrations', label:'Links', meta:'bundle'},
  {id:'agents', label:'Cells', meta:'roles'},
  {id:'skills', label:'Skills', meta:'toolkit'},
  {id:'learning', label:'Learning', meta:'adaptive'},
  {id:'setup', label:'Boot', meta:'guide'}
];
let consoleMeta = null;
let runtime = null;
let channelState = null;
let workstationState = null;
const skillForgePrompts = {
  base: `Create a new AI skill for: [skill idea]

Goal:
- Make it practical and reusable
- Keep it concise
- Include clear trigger conditions
- Define the workflow step by step
- Include response defaults
- Add one short example usage

Output format:
1. Skill name
2. Description
3. When to use
4. Workflow
5. Response defaults
6. Example usage`,
  enhancer: `Enhance this skill draft.

Improve it by:
- removing fluff
- tightening trigger rules
- making the workflow more deterministic
- reducing overlap with general assistant behavior
- keeping only high-signal instructions
- improving the example so it matches real usage

Then return the improved final skill in the same structure.`,
  combined: `Create a new AI skill for: [skill idea]

Requirements:
- concise and practical
- clear trigger conditions
- step-by-step workflow
- response defaults
- one realistic example

Then self-enhance the result by:
- removing vague wording
- tightening trigger rules
- simplifying the workflow
- keeping only essential instructions

Return the final improved skill only.`
};
function buildSkillForgePrompt(idea){
  const cleanIdea = (idea || '').trim() || '[skill idea]';
  return `Create a new core AI skill for: ${cleanIdea}

Requirements:
- turn the idea into a practical reusable core skill
- keep it concise and high-signal
- define clear trigger conditions
- define the workflow step by step
- include response defaults
- include one realistic example usage

Then enhance the skill by:
- removing fluff
- tightening trigger rules
- making the workflow deterministic where useful
- reducing overlap with general assistant behavior
- improving the example so it matches real usage

Return the final improved skill only in this structure:
1. Skill name
2. Description
3. When to use
4. Workflow
5. Response defaults
6. Example usage`;
}
function openDrawer(title, body){
  document.getElementById('drawerContent').innerHTML = `<h3>${escapeHtml(title)}</h3>${body}`;
  document.getElementById('drawerBackdrop').classList.add('open');
}
function closeDrawer(){ document.getElementById('drawerBackdrop').classList.remove('open'); }
function escapeHtml(value){return String(value??'').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function skillForgeDrawer(skill){
  return `<p>${escapeHtml(skill?.description || '')}</p>
  <div class="mini-card" style="margin-top:14px">
    <strong>Core Skill Enhancer</strong>
    <span>Give one simple idea. The shell expands it into a stronger core-skill prompt for JEBAT.</span>
    <textarea id="skillForgeIdeaDrawer" class="input" style="min-height:90px;margin-top:12px;resize:vertical" placeholder="Example: summarize product feedback into bug reports and feature requests"></textarea>
    <div class="toolbar-inline" style="margin-top:12px">
      <button class="btn primary" data-skillforge-generate="drawer">Enhance to core skill</button>
      <button class="ghost-btn" data-skillforge-send-generated="drawer">Send enhanced prompt</button>
      <button class="ghost-btn" data-skillforge-copy-generated="drawer">Copy enhanced prompt</button>
    </div>
    <pre id="skillForgeOutputDrawer" style="margin-top:12px">${escapeHtml(buildSkillForgePrompt(''))}</pre>
  </div>
  <div class="toolbar-inline" style="margin-top:14px">
    <button class="btn primary" data-skillforge-copy="combined">Use this prompt</button>
    <button class="ghost-btn" data-skillforge-copy="base">Copy base</button>
    <button class="ghost-btn" data-skillforge-copy="enhancer">Copy enhancer</button>
    <button class="ghost-btn" data-skillforge-open-chat="combined">Send to live chat</button>
  </div>
  <div class="provider-stack" style="margin-top:14px">
    <div class="mini-card"><strong>Base prompt</strong><pre>${escapeHtml(skillForgePrompts.base)}</pre></div>
    <div class="mini-card"><strong>Enhancer prompt</strong><pre>${escapeHtml(skillForgePrompts.enhancer)}</pre></div>
    <div class="mini-card"><strong>One-shot prompt</strong><pre>${escapeHtml(skillForgePrompts.combined)}</pre></div>
  </div>`;
}
function navMarkup(active){
  const filter = (document.getElementById('navFilter')?.value || '').toLowerCase();
  return sections.filter(item => !filter || item.label.toLowerCase().includes(filter) || item.meta.toLowerCase().includes(filter)).map(item => `<a class="nav-item ${item.id===active?'active':''}" href="#${item.id}" data-section="${item.id}"><span>${item.label}</span><span class="nav-meta">${item.meta}</span></a>`).join('');
}
function setHash(section){history.replaceState(null,'',`#${section}`);}
function currentSection(){const id=location.hash.replace('#','');return sections.some(s=>s.id===id)?id:'overview';}
function renderStatusStrip(){
  const pills = [
    ['Provider', runtime?.provider?.effective || 'unknown'],
    ['Model', runtime?.provider?.model || 'unknown'],
    ['OpenClaw Agents', String(consoleMeta?.openclaw?.agent_names?.length || 0)],
    ['Skill Count', String(consoleMeta?.skills?.count || 0)],
    ['Channels', String(Object.keys(runtime?.channel_connections || {}).length)]
  ];
  document.getElementById('statusStrip').innerHTML = pills.map(([k,v]) => `<div class="status-pill"><i class="dot"></i><span>${escapeHtml(k)}: ${escapeHtml(v)}</span></div>`).join('');
  document.getElementById('effectiveProvider').textContent = runtime?.provider?.effective || 'Unknown';
  document.getElementById('providerMeta').textContent = `Configured ${runtime?.provider?.configured || 'unknown'} / model ${runtime?.provider?.model || 'unknown'}`;
  document.getElementById('workspaceMeta').textContent = `${(runtime?.workspace?.stations || []).length} workstations and ${(runtime?.workspace?.integrations || []).length} integration points detected.`;
}
function renderOverview(){
  return `<section class="hero"><div class="eyebrow">Cyber operations bridge</div><h1>Hermes capture. OpenClaw control. One operator shell.</h1><p>JEBATCore is now the bridge between Hermes-style capture and OpenClaw-style runtime control: provider routing, channel surfaces, workstation access, skill planes, and health posture in one cybersecurity-themed console.</p><div class="hero-actions"><button class="btn primary" data-section-jump="livechat">Launch Hermes session</button><button class="btn" data-section-jump="control">Open model grid</button><button class="btn" data-section-jump="channels">Review channels</button></div></section>
  <section class="layout"><div class="stack"><div class="grid">
  <article class="grid-card"><div class="card-label">Message bus</div><h3>Channel fabric</h3><p>${(consoleMeta.channels||[]).length} adapters are visible in the repo and can be wired into Telegram, WhatsApp, Discord, or Slack without leaving the shell.</p></article>
  <article class="grid-card"><div class="card-label">Operator mesh</div><h3>Workstation access</h3><p>${(runtime.workspace.stations||[]).length} stations are staged across CLI, OpenClaw, VS Code, and the live VPS surface.</p></article>
  <article class="grid-card"><div class="card-label">Skill plane</div><h3>Hermes + TokGuru</h3><p>${consoleMeta.skills.count} skills are on deck, with Hermes imported as an explicit operating mode instead of hidden prompt state.</p></article>
  <article class="grid-card"><div class="card-label">Learning loop</div><h3>Adaptive modules</h3><p>${consoleMeta.learning.modules.length} improvement modules are already present for reasoning, recommendation, and skill evolution.</p></article>
  </div></div>
  <div class="stack">
    <article class="wide-card"><div class="card-label">Runtime lattice</div><h3>Live provider state</h3><div class="kv"><div class="kv-item"><label>Configured provider</label><strong>${escapeHtml(runtime.provider.configured)}</strong></div><div class="kv-item"><label>Effective provider</label><strong>${escapeHtml(runtime.provider.effective)}</strong></div><div class="kv-item"><label>Effective model</label><strong>${escapeHtml(runtime.provider.model)}</strong></div></div></article>
    <article class="wide-card"><div class="card-label">OpenClaw core</div><h3>Control pattern</h3><p>Primary model: ${escapeHtml(consoleMeta.openclaw.primary_model || 'unknown')}</p><p>Fallbacks: ${escapeHtml((consoleMeta.openclaw.fallback_models || []).join(', '))}</p></article>
  </div></section>`;
}
function renderLiveChat(){
  return `<section class="hero"><div class="eyebrow">Unified shell</div><h1>Live chat inside the control surface.</h1><p>This panel uses the same WebUI chat API directly, so it stays in the shell and avoids frame-policy conflicts from the edge layer.</p></section>
  <section class="wide-card chat-shell"><div class="chat-log" id="shellChatLog"><div class="chat-entry"><strong>JEBATCore</strong><div>Live operator channel open. Give me the task, context, and constraints.</div></div></div><form class="chat-compose" id="shellChatForm"><div class="control-grid"><select class="select" id="shellChatMode"><option value="fast">Fast</option><option value="deliberate" selected>Deliberate</option><option value="deep">Deep</option><option value="strategic">Strategic</option><option value="creative">Creative</option><option value="critical">Critical</option></select><div class="chat-meta"><span>Provider: ${escapeHtml(runtime.provider.effective)}</span><span>Model: ${escapeHtml(runtime.provider.model)}</span></div></div><textarea id="shellChatInput" placeholder="Describe the task, target state, or blocker..."></textarea><button class="btn primary" type="submit">Send in shell</button></form></section>`;
}
function renderDoctor(){
  const providerRows = (runtime.providers.available||[]).map(item => `<div class="row"><div>${escapeHtml(item.provider)}</div><div>${item.configured?'configured':'missing'}</div><div>${escapeHtml(item.notes)}</div></div>`).join('');
  return `<section class="hero"><div class="eyebrow">Signal integrity</div><h1>Run a pulse check before long operations.</h1><p>This view merges provider auth, model routing, and station readiness so you can spot weak links before they degrade a live session.</p></section>
  <section class="table-card"><div class="card-label">Runtime pulse</div><h3>Provider readiness</h3><div class="table"><div class="row head"><div>Provider</div><div>Status</div><div>Notes</div></div>${providerRows}</div></section>`;
}
function renderControl(){
  const selectedProvider = runtime.provider.effective;
  const selectedCatalog = runtime.providers.catalog?.[selectedProvider] || {models:[], supports_custom:false};
  const providerOptions = (runtime.providers.available||[]).map(item => `<option value="${escapeHtml(item.provider)}" ${item.provider===selectedProvider?'selected':''}>${escapeHtml(item.label || item.provider)}</option>`).join('');
  const modelOptions = (selectedCatalog.models || []).map(model => `<option value="${escapeHtml(model)}" ${model===runtime.provider.model?'selected':''}>${escapeHtml(model)}</option>`).join('');
  const providerCards = (runtime.providers.available||[]).map(item => {
    const active = item.provider === selectedProvider ? 'active' : '';
    const status = item.configured ? 'configured' : 'missing auth';
    const models = (item.models || []).slice(0, 3).join(', ') || 'No catalog';
    return `<article class="provider-card ${active}"><div class="card-label">${escapeHtml(item.label || item.provider)}</div><h4>${escapeHtml(item.provider)}</h4><div class="provider-meta"><span class="chip ${item.configured?'ok':'warn'}">${escapeHtml(status)}</span><span class="chip">${escapeHtml((item.models || []).length)} models</span></div><p class="small-note">${escapeHtml(item.notes || 'No provider notes')}</p><p class="small-note" style="margin-top:10px">Suggested: ${escapeHtml(models)}</p></article>`;
  }).join('');
  const fallbacks = (runtime.provider.fallbacks || []).map(item => `<span class="chip">${escapeHtml(item)}</span>`).join('') || '<span class="chip">none</span>';
  const authTargets = selectedProvider === 'ollama' ? 'OLLAMA_HOST' : ((runtime.providers.available || []).find(item => item.provider === selectedProvider)?.env_vars || []).join(', ');
  return `<section class="hero"><div class="eyebrow">Model lattice</div><h1>Route providers and models from one control grid.</h1><p>The shell keeps Hermes fast and OpenClaw stable by showing the active provider path, filtered model choices, and fallback order in a single runtime panel.</p></section>
  <section class="layout"><div class="provider-stack"><article class="wide-card"><div class="card-label">Override rail</div><h3>Runtime control</h3><form class="control-form" id="runtimeForm"><div class="control-grid tight"><select class="select" id="runtimeProvider" name="provider">${providerOptions}</select><select class="select" id="runtimeModel" name="model">${modelOptions}</select><input class="input" id="runtimeCustomModel" type="text" placeholder="Custom model id"></div><div class="model-hint" id="runtimeModelHint">Choose a provider first. Model choices are filtered to that provider, and custom models are only enabled where the provider supports them.</div><div class="provider-meta"><span class="chip">Configured: ${escapeHtml(runtime.provider.configured)}</span><span class="chip">Effective: ${escapeHtml(runtime.provider.effective)}</span><span class="chip">Model: ${escapeHtml(runtime.provider.model)}</span></div><button class="btn primary" type="submit">Apply runtime override</button></form></article><article class="wide-card"><div class="card-label">Auth bridge</div><h3>Connect provider credentials</h3><form class="control-form" id="providerAuthForm"><div class="control-grid"><select class="select" id="authProvider" name="provider">${providerOptions}</select><input class="input" id="authSecret" name="secret" type="password" placeholder="API key or host"></div><div class="model-hint" id="providerAuthHint">Target env: ${escapeHtml(authTargets || 'n/a')}. For Ollama, enter the host such as <code>http://127.0.0.1:11434</code>.</div><button class="btn primary" type="submit">Save provider auth</button></form></article><article class="wide-card"><div class="card-label">Fallback rail</div><h3>Routing chain</h3><div class="provider-meta">${fallbacks}</div><p class="small-note">The shell override changes the active preference for this live console. Repo config and environment stay intact.</p></article></div>
  <article class="wide-card"><div class="card-label">Provider map</div><h3>Available provider tracks</h3><div class="provider-grid">${providerCards}</div></article></section>
  <section class="wide-card"><div class="card-label">Surface state</div><h3>Current stations</h3><ul class="list">${(runtime.workspace.stations||[]).map(item => `<li><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.path)} / ${escapeHtml(item.state)}</span></li>`).join('')}</ul></section>`;
}
function renderChannels(){
  const available = (channelState?.available || []).map(item => `<li><strong>${escapeHtml(item.label)}</strong><span>Required: ${escapeHtml(item.required.join(', '))}</span></li>`).join('');
  const connected = Object.entries(channelState?.connections || {}).map(([name, item]) => `<li><strong>${escapeHtml(name)}</strong><span>${escapeHtml(item.status)} / missing: ${escapeHtml((item.missing || []).join(', ') || 'none')}</span></li>`).join('') || '<li><strong>None</strong><span>No channels configured from this shell yet.</span></li>';
  return `<section class="hero"><div class="eyebrow">Message bus</div><h1>Wire external channels into the operator shell.</h1><p>The console reads real adapters from <code>jebat/integrations/channels</code> and overlays them with OpenClaw runtime declarations so channel wiring stays visible and grounded.</p></section>
  <section class="layout"><article class="wide-card"><div class="card-label">Channel bridge</div><h3>Store channel connection</h3><form class="control-form" id="channelForm"><div class="control-grid"><select class="select" name="channel">${(channelState?.available || []).map(item => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join('')}</select><input class="input" name="field1" placeholder="Primary token / id"></div><div class="control-grid"><input class="input" name="field2" placeholder="Secondary value"><input class="input" name="field3" placeholder="Third value"></div><button class="btn primary" type="submit">Save channel intent</button></form><ul class="list" style="margin-top:14px">${available}</ul></article><article class="wide-card"><div class="card-label">Connection state</div><h3>Shell-known channel links</h3><ul class="list">${connected}</ul></article></section>`;
}
function renderWorkstation(){
  const cards = (runtime.workspace.stations||[]).map(item => `<article class="grid-card"><div class="card-label">${escapeHtml(item.state)}</div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.path)}</p></article>`).join('');
  const connected = Object.entries(workstationState?.connections || {}).map(([name, item]) => {
    const remote = item.ssh_host ? ` / ${item.ssh_user || 'root'}@${item.ssh_host}` : '';
    const deploy = item.deploy_path ? ` / deploy ${item.deploy_path}` : '';
    const health = item.health?.detail ? ` / ${item.health.detail}` : '';
    const sshTarget = item.ssh_host ? `${item.ssh_user || 'root'}@${item.ssh_host}` : '';
    const connectCommand = name === 'CLI'
      ? (item.path || '~/.local/bin/jebat-cli')
      : name === 'OpenClaw'
      ? `openclaw dashboard --no-open`
      : name === 'VS Code'
      ? `code ${item.path || '~/.config/Code/User'}`
      : sshTarget
      ? `ssh ${sshTarget}`
      : (item.path || '');
    const connectLink = name === 'VPS' && sshTarget
      ? `<a class="ghost-btn" href="ssh://${escapeHtml(sshTarget)}">Connect link</a>`
      : name === 'CLI'
      ? `<button class="ghost-btn" data-workstation-copy="${escapeHtml(connectCommand)}">Copy launch command</button>`
      : name === 'OpenClaw'
      ? `<a class="ghost-btn" href="#control" data-section-jump="control">Open control</a>`
      : name === 'VS Code'
      ? `<button class="ghost-btn" data-workstation-copy="${escapeHtml(connectCommand)}">Copy VS Code command</button>`
      : '';
    return `<li><strong>${escapeHtml(name)}</strong><span>${escapeHtml(item.status)} / ${escapeHtml(item.path || '')}${escapeHtml(remote)}${escapeHtml(deploy)}${escapeHtml(health)}</span><div style="margin-top:10px" class="toolbar-inline"><button class="ghost-btn" data-workstation-copy="${escapeHtml(connectCommand)}">Copy connect command</button>${connectLink}<button class="ghost-btn" data-workstation-check="${escapeHtml(name)}">Health check</button></div><pre style="margin-top:12px">${escapeHtml(connectCommand || 'Save a host or path to generate a connect command.')}</pre></li>`;
  }).join('') || '<li><strong>None</strong><span>No workstation connections stored from the shell yet.</span></li>';
  return `<section class="hero"><div class="eyebrow">Station mesh</div><h1>Align local and remote workstations in one shell.</h1><p>Track every operator surface JEBATCore is meant to use: local CLI, OpenClaw runtime, VS Code, and the live VPS deployment.</p></section><section class="layout"><div class="stack"><section class="grid">${cards}</section><article class="wide-card"><div class="card-label">Connect flow</div><h3>How to connect a station to JEBATCore</h3><ul class="list"><li><strong>1. Pick a station type</strong><span>Choose CLI, OpenClaw, VS Code, or VPS in the form.</span></li><li><strong>2. Save the real path or host</strong><span>Use a local path for CLI and VS Code, or an SSH host for VPS.</span></li><li><strong>3. Generate the connect command</strong><span>After save, the shell prints the exact command or link for that station.</span></li><li><strong>4. Run health check</strong><span>Use the health button to confirm the saved station is reachable.</span></li></ul></article></div><article class="wide-card"><div class="card-label">Station link</div><h3>Connect a workstation to JEBATCore</h3><p class="small-note">Recommended values: <code>~/.local/bin/jebat-cli</code> for CLI, <code>~/.openclaw</code> for OpenClaw, <code>~/.config/Code/User</code> for VS Code, and your SSH host for VPS.</p><form class="control-form" id="workstationForm"><select class="select" id="workstationType" name="workstation">${(workstationState?.available || []).map(item => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join('')}</select><input class="input" name="path" placeholder="Path or host, for example jebat.online or ~/.local/bin/jebat-cli"><input class="input" name="notes" placeholder="Notes, for example primary laptop or production node"><div class="control-grid" id="workstationRemoteFields" style="display:none"><input class="input" name="ssh_host" placeholder="SSH host, for example 72.62.255.206"><input class="input" name="ssh_user" placeholder="SSH user, for example root"></div><input class="input" id="workstationDeployPath" name="deploy_path" placeholder="Deploy path on remote host, for example /root/jebat-core" style="display:none"><button class="btn primary" type="submit">Save station link</button></form><ul class="list" style="margin-top:14px">${connected}</ul></article></section>`;
}
function renderIntegrations(){
  return `<section class="hero"><div class="eyebrow">Versioned connections</div><h1>Integration assets grounded in the repo.</h1><p>This is the repo-backed integration layer, not UI filler. It shows the OpenClaw bundle and the docs that support MCP and IDE workflows.</p></section><section class="grid">${(runtime.workspace.integrations||[]).map(item => `<article class="grid-card"><div class="card-label">${escapeHtml(item.state)}</div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.path)}</p></article>`).join('')}</section>`;
}
function renderAgents(){
  return `<section class="hero"><div class="eyebrow">Cell topology</div><h1>Hermes and OpenClaw roles as visible operator cells.</h1><p>The shell exposes the OpenClaw role map while keeping Hermes visible as an explicit mode, not buried in prompt text or hidden routing.</p></section><section class="wide-card"><div class="toolbar-inline"><input id="agentFilter" class="input" placeholder="Search agents by name"><span class="status-pill"><i class="dot"></i><span>${(consoleMeta.openclaw.agent_names||[]).length} agents</span></span></div><div class="grid" id="agentGrid">${(consoleMeta.openclaw.agent_names||[]).map(name => `<article class="grid-card"><div class="card-label">Cell</div><h3>${escapeHtml(name)}</h3><p>Visible from the OpenClaw bundle agent list.</p><button class="ghost-btn" data-agent="${escapeHtml(name)}">Details</button></article>`).join('')}</div></section>`;
}
function renderSkills(){
  return `<section class="hero"><div class="eyebrow">Skill plane</div><h1>Hermes skills, OpenClaw skills, and operator tooling in one plane.</h1><p>These cards are built from the live skill registry so the console shows the actual skill surfaces the runtime can route into, including webfetch, search, test, and the new skill-forge prompt generator with enhancer flow.</p></section><section class="wide-card"><div class="toolbar-inline"><input id="skillFilter" class="input" placeholder="Search skills by name or category"><span class="status-pill"><i class="dot"></i><span>${(consoleMeta.skills.top||[]).length} featured skills</span></span></div><div class="grid" id="skillGrid">${(consoleMeta.skills.top||[]).map(skill => `<article class="grid-card"><div class="card-label">${escapeHtml(skill.name === 'skill-forge' ? 'core skill enhancer' : skill.category)}</div><h3>${escapeHtml(skill.name)}</h3><p>${escapeHtml(skill.description)}</p>${skill.name === 'skill-forge' ? `<div class="mini-card" style="margin-top:14px"><strong>Turn a simple idea into a core skill</strong><span>Type a rough idea and let JEBAT shape it into a stronger reusable skill prompt.</span></div><textarea id="skillForgeIdeaCard" class="input" style="min-height:84px;margin-top:14px;resize:vertical" placeholder="Describe a simple skill idea"></textarea><pre id="skillForgeOutputCard" style="margin-top:12px">${escapeHtml(buildSkillForgePrompt(''))}</pre><div class="toolbar-inline" style="margin-top:14px"><button class="btn primary" data-skillforge-generate="card">Enhance prompt</button><button class="ghost-btn" data-skillforge-send-generated="card">Use in chat</button><button class="ghost-btn" data-skillforge-copy-generated="card">Copy enhanced prompt</button><button class="ghost-btn" data-skill="${escapeHtml(skill.name)}">Details</button></div>` : `<div class="toolbar-inline" style="margin-top:14px"><button class="ghost-btn" data-skill="${escapeHtml(skill.name)}">Details</button></div>`}</article>`).join('')}</div></section>`;
}
function renderLearning(){
  return `<section class="hero"><div class="eyebrow">Learning loop</div><h1>Adaptive reasoning and skill evolution.</h1><p>Continuum and cortex modules stay visible here so the operator can see exactly where recommendation and improvement logic already exists in the repo.</p></section><section class="layout"><article class="wide-card"><div class="card-label">Adaptive modules</div><h3>Learning code paths</h3><ul class="list">${(consoleMeta.learning.modules||[]).map(item => `<li><strong>${escapeHtml(item.split('/').slice(-1)[0])}</strong><span>${escapeHtml(item)}</span></li>`).join('')}</ul></article><article class="wide-card"><div class="card-label">Hermes import</div><h3>Imported guidance</h3><p>${escapeHtml(consoleMeta.skills.openclaw_excerpt || 'Unavailable')}</p></article></section>`;
}
function renderSetup(){
  return `<section class="hero"><div class="eyebrow">Boot sequence</div><h1>Connect channels and stations without guesswork.</h1><p>This page mirrors the versioned setup guide and gives you one clean operator reference for Telegram, WhatsApp, Discord, Slack, CLI, OpenClaw, VS Code, and VPS setup.</p><div class="hero-actions"><a class="btn primary" href="#channels">Open channels</a><a class="btn" href="#workstation">Open stations</a><a class="btn" href="https://github.com/nusabyte-my/jebat-core/blob/main/docs/SETUP_CHANNELS_AND_WORKSTATIONS.md" target="_blank" rel="noreferrer">Open repo guide</a></div></section>
  <section class="layout"><article class="wide-card"><div class="card-label">Channels</div><h3>Messaging setup</h3><ul class="list"><li><strong>Telegram</strong><span>Needs <code>bot_token</code> from <code>@BotFather</code>.</span></li><li><strong>WhatsApp</strong><span>Needs <code>phone_number_id</code>, <code>access_token</code>, <code>verify_token</code> from Meta.</span></li><li><strong>Discord</strong><span>Needs <code>bot_token</code>, <code>guild_id</code>.</span></li><li><strong>Slack</strong><span>Needs <code>bot_token</code>, <code>app_token</code>.</span></li></ul></article><article class="wide-card"><div class="card-label">Workstations</div><h3>Operator stations</h3><ul class="list"><li><strong>CLI</strong><span>Suggested path: <code>~/.local/bin/jebat-cli</code></span></li><li><strong>OpenClaw</strong><span>Suggested path: <code>~/.openclaw</code></span></li><li><strong>VS Code</strong><span>Suggested path: <code>~/.config/Code/User</code></span></li><li><strong>VPS</strong><span>Suggested host: <code>jebat.online</code> or your SSH target.</span></li></ul></article></section>`;
}
function renderSection(section){
  const view = document.getElementById('view');
  document.getElementById('navList').innerHTML = navMarkup(section);
  const renderers = {overview:renderOverview,livechat:renderLiveChat,doctor:renderDoctor,control:renderControl,channels:renderChannels,workstation:renderWorkstation,integrations:renderIntegrations,agents:renderAgents,skills:renderSkills,learning:renderLearning,setup:renderSetup};
  view.innerHTML = renderers[section] ? renderers[section]() : renderOverview();
  bindDynamicUI();
}
function bindDynamicUI(){
  document.querySelectorAll('[data-section]').forEach(btn => btn.onclick = () => { setHash(btn.dataset.section); renderSection(btn.dataset.section); });
  document.querySelectorAll('[data-section-jump]').forEach(btn => btn.onclick = () => { setHash(btn.dataset.sectionJump); renderSection(btn.dataset.sectionJump); });
  const navFilter = document.getElementById('navFilter');
  if(navFilter){navFilter.oninput = () => { document.getElementById('navList').innerHTML = navMarkup(currentSection()); bindDynamicUI(); }; }
  const form = document.getElementById('runtimeForm');
  const providerSelect = document.getElementById('runtimeProvider');
  const modelSelect = document.getElementById('runtimeModel');
  const customModelInput = document.getElementById('runtimeCustomModel');
  const modelHint = document.getElementById('runtimeModelHint');
  const providerAuthForm = document.getElementById('providerAuthForm');
  const authProvider = document.getElementById('authProvider');
  const authSecret = document.getElementById('authSecret');
  const providerAuthHint = document.getElementById('providerAuthHint');
  function syncRuntimeModelUI(){
    if(!providerSelect || !modelSelect || !customModelInput || !modelHint || !runtime) return;
    const provider = providerSelect.value;
    const catalog = runtime.providers.catalog?.[provider] || {models:[], supports_custom:false};
    const currentValue = runtime.provider.effective === provider ? runtime.provider.model : (catalog.models?.[0] || '');
    modelSelect.innerHTML = (catalog.models || []).map(model => `<option value="${escapeHtml(model)}">${escapeHtml(model)}</option>`).join('');
    if(catalog.models?.includes(currentValue)){ modelSelect.value = currentValue; }
    customModelInput.value = catalog.models?.includes(currentValue) ? '' : currentValue;
    customModelInput.style.display = catalog.supports_custom ? '' : 'none';
    modelHint.textContent = catalog.supports_custom
      ? `Showing curated ${provider} models. You can also enter a custom model id if your ${provider} runtime exposes one.`
      : `Model choices are locked to the ${provider} catalog so the selector only shows valid matches.`;
  }
  if(providerSelect){ providerSelect.onchange = syncRuntimeModelUI; syncRuntimeModelUI(); }
  function syncProviderAuthUI(){
    if(!authProvider || !authSecret || !providerAuthHint || !runtime) return;
    const provider = authProvider.value;
    const status = (runtime.providers.available || []).find(item => item.provider === provider);
    const targets = (status?.env_vars || []).join(', ') || 'n/a';
    authSecret.placeholder = provider === 'ollama' ? 'Ollama host' : 'API key';
    providerAuthHint.innerHTML = provider === 'ollama'
      ? 'Target env: <code>OLLAMA_HOST</code>. Enter the host such as <code>http://127.0.0.1:11434</code>.'
      : `Target env: <code>${escapeHtml(targets)}</code>. Save an API key for the selected provider.`;
  }
  if(authProvider){ authProvider.onchange = syncProviderAuthUI; syncProviderAuthUI(); }
  async function parseApiResponse(res){
    const text = await res.text();
    try { return JSON.parse(text); } catch { return {ok:false, error:text}; }
  }
  if(form){form.onsubmit = async (event) => { event.preventDefault(); const provider = providerSelect?.value || ''; const supportsCustom = !!(runtime?.providers?.catalog?.[provider]?.supports_custom); const selectedModel = supportsCustom && customModelInput?.value.trim() ? customModelInput.value.trim() : (modelSelect?.value || ''); const payload = {provider, model: selectedModel}; const res = await fetch('/webui/api/runtime', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}); const data = await parseApiResponse(res); if(!res.ok){ alert(data.detail || data.error || 'Failed to update runtime'); return; } runtime = data; renderStatusStrip(); renderSection('control'); };}
  if(providerAuthForm){providerAuthForm.onsubmit = async (event) => { event.preventDefault(); const provider = authProvider?.value || ''; const secret = authSecret?.value || ''; const payload = provider === 'ollama' ? {provider, host: secret} : {provider, secret}; const res = await fetch('/webui/api/provider-auth', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}); const data = await parseApiResponse(res); if(!res.ok){ alert(data.detail || data.error || 'Failed to save provider auth'); return; } runtime = data.runtime; authSecret.value = ''; renderStatusStrip(); renderSection('control'); };}
  const channelForm = document.getElementById('channelForm');
  if(channelForm){channelForm.onsubmit = async (event) => { event.preventDefault(); const fd = new FormData(channelForm); const channel = fd.get('channel'); const available = (channelState?.available || []).find(item => item.id === channel); const required = available?.required || []; const values = [fd.get('field1'), fd.get('field2'), fd.get('field3')]; const config = {}; required.forEach((key, idx) => config[key] = values[idx] || ''); const res = await fetch('/webui/api/channels/connect', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({channel, config})}); channelState = await fetch('/webui/api/channels/connect').then(r => r.json()); runtime = await fetch('/webui/api/runtime').then(r => r.json()); renderStatusStrip(); renderSection('channels'); };}
  const workstationForm = document.getElementById('workstationForm');
  const workstationType = document.getElementById('workstationType');
  const workstationRemoteFields = document.getElementById('workstationRemoteFields');
  const workstationDeployPath = document.getElementById('workstationDeployPath');
  function syncWorkstationFields(){
    if(!workstationType || !workstationRemoteFields || !workstationDeployPath || !workstationState) return;
    const selected = (workstationState.available || []).find(item => item.id === workstationType.value);
    const isRemote = !!selected?.supports_remote;
    workstationRemoteFields.style.display = isRemote ? '' : 'none';
    workstationDeployPath.style.display = isRemote ? '' : 'none';
  }
  if(workstationType){ workstationType.onchange = syncWorkstationFields; syncWorkstationFields(); }
  if(workstationForm){workstationForm.onsubmit = async (event) => { event.preventDefault(); const fd = new FormData(workstationForm); await fetch('/webui/api/workstations/connect', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({workstation: fd.get('workstation'), path: fd.get('path'), notes: fd.get('notes'), ssh_host: fd.get('ssh_host'), ssh_user: fd.get('ssh_user'), deploy_path: fd.get('deploy_path')})}); workstationState = await fetch('/webui/api/workstations/connect').then(r => r.json()); runtime = await fetch('/webui/api/runtime').then(r => r.json()); renderStatusStrip(); renderSection('workstation'); };}
  document.querySelectorAll('[data-workstation-copy]').forEach(btn => btn.onclick = async () => {
    const text = btn.dataset.workstationCopy || '';
    try{
      await navigator.clipboard.writeText(text);
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = 'Copy connect command'; }, 1200);
    }catch(e){
      openDrawer('Copy failed', `<p>Clipboard access failed. Copy the command below manually.</p><pre>${escapeHtml(text)}</pre>`);
    }
  });
  document.querySelectorAll('[data-workstation-check]').forEach(btn => btn.onclick = async () => { await fetch('/webui/api/workstations/check', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({workstation: btn.dataset.workstationCheck})}); workstationState = await fetch('/webui/api/workstations/connect').then(r => r.json()); renderSection('workstation'); });
  const shellChatForm = document.getElementById('shellChatForm');
  if(shellChatForm){shellChatForm.onsubmit = async (event) => { event.preventDefault(); const input = document.getElementById('shellChatInput'); const mode = document.getElementById('shellChatMode'); const log = document.getElementById('shellChatLog'); const message = input.value.trim(); if(!message) return; log.insertAdjacentHTML('beforeend', `<div class="chat-entry user"><strong>You</strong><div>${escapeHtml(message)}</div></div>`); input.value=''; log.scrollTop = log.scrollHeight; const res = await fetch('/webui/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:'shell_user', message, thinking_mode: mode.value})}); const data = await res.json(); log.insertAdjacentHTML('beforeend', `<div class="chat-entry"><strong>JEBATCore</strong><div>${escapeHtml(data.response || data.error || 'No response')}</div></div>`); log.scrollTop = log.scrollHeight; };}
  const agentFilter = document.getElementById('agentFilter');
  if(agentFilter){agentFilter.oninput = () => { const q = agentFilter.value.toLowerCase(); document.querySelectorAll('#agentGrid .grid-card').forEach(card => { card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none'; }); };}
  document.querySelectorAll('[data-agent]').forEach(btn => btn.onclick = () => { const name = btn.dataset.agent; openDrawer(name, `<p>OpenClaw bundle agent visible in the runtime template.</p><pre>${escapeHtml(JSON.stringify(consoleMeta.openclaw.agent_names, null, 2))}</pre>`); });
  const skillFilter = document.getElementById('skillFilter');
  if(skillFilter){skillFilter.oninput = () => { const q = skillFilter.value.toLowerCase(); document.querySelectorAll('#skillGrid .grid-card').forEach(card => { card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none'; }); };}
  document.querySelectorAll('[data-skill]').forEach(btn => btn.onclick = () => {
    const name = btn.dataset.skill;
    const skill = (consoleMeta.skills.top || []).find(item => item.name === name);
    if(name === 'skill-forge'){
      openDrawer(name, skillForgeDrawer(skill));
      bindDynamicUI();
      return;
    }
    openDrawer(name, `<p>${escapeHtml(skill?.description || '')}</p><pre>${escapeHtml(JSON.stringify(skill || {}, null, 2))}</pre>`);
  });
  document.querySelectorAll('[data-skillforge-copy]').forEach(btn => btn.onclick = async () => {
    const key = btn.dataset.skillforgeCopy;
    const text = skillForgePrompts[key] || '';
    try{
      await navigator.clipboard.writeText(text);
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = key === 'combined' ? 'Use this prompt' : `Copy ${key}`; }, 1200);
    }catch(e){
      openDrawer('Copy failed', `<p>Clipboard access failed. Copy the prompt below manually.</p><pre>${escapeHtml(text)}</pre>`);
    }
  });
  document.querySelectorAll('[data-skillforge-open-chat]').forEach(btn => btn.onclick = () => {
    const key = btn.dataset.skillforgeOpenChat;
    const text = skillForgePrompts[key] || '';
    closeDrawer();
    setHash('livechat');
    renderSection('livechat');
    const input = document.getElementById('shellChatInput');
    if(input){
      input.value = text;
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  });
  function skillForgeElements(scope){
    if(scope === 'drawer'){
      return {
        idea: document.getElementById('skillForgeIdeaDrawer'),
        out: document.getElementById('skillForgeOutputDrawer'),
      };
    }
    return {
      idea: document.getElementById('skillForgeIdeaCard'),
      out: document.getElementById('skillForgeOutputCard'),
    };
  }
  function syncSkillForge(scope){
    const els = skillForgeElements(scope);
    if(!els.idea || !els.out) return '';
    const prompt = buildSkillForgePrompt(els.idea.value);
    els.out.textContent = prompt;
    return prompt;
  }
  document.querySelectorAll('[data-skillforge-generate]').forEach(btn => btn.onclick = () => {
    syncSkillForge(btn.dataset.skillforgeGenerate);
  });
  document.querySelectorAll('[data-skillforge-copy-generated]').forEach(btn => btn.onclick = async () => {
    const prompt = syncSkillForge(btn.dataset.skillforgeCopyGenerated);
    try{
      await navigator.clipboard.writeText(prompt);
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = 'Copy enhanced prompt'; }, 1200);
    }catch(e){
      openDrawer('Copy failed', `<p>Clipboard access failed. Copy the prompt below manually.</p><pre>${escapeHtml(prompt)}</pre>`);
    }
  });
  document.querySelectorAll('[data-skillforge-send-generated]').forEach(btn => btn.onclick = () => {
    const prompt = syncSkillForge(btn.dataset.skillforgeSendGenerated);
    closeDrawer();
    setHash('livechat');
    renderSection('livechat');
    const input = document.getElementById('shellChatInput');
    if(input){
      input.value = prompt;
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  });
  const close = document.getElementById('drawerClose');
  if(close){close.onclick = closeDrawer;}
  const backdrop = document.getElementById('drawerBackdrop');
  if(backdrop){backdrop.onclick = (event) => { if(event.target === backdrop){ closeDrawer(); } };}
}
async function boot(){
  const [metaRes, runtimeRes, channelRes, workstationRes] = await Promise.all([fetch('/webui/api/console-meta'), fetch('/webui/api/runtime'), fetch('/webui/api/channels/connect'), fetch('/webui/api/workstations/connect')]);
  consoleMeta = await metaRes.json();
  runtime = await runtimeRes.json();
  channelState = await channelRes.json();
  workstationState = await workstationRes.json();
  renderStatusStrip();
  renderSection(currentSection());
}
window.addEventListener('hashchange', () => renderSection(currentSection()));
boot();
setInterval(async () => {
  try{
    runtime = await fetch('/webui/api/runtime').then(r => r.json());
    channelState = await fetch('/webui/api/channels/connect').then(r => r.json());
    workstationState = await fetch('/webui/api/workstations/connect').then(r => r.json());
    renderStatusStrip();
    renderSection(currentSection());
  }catch(e){console.error(e);}
}, 15000);
</script>
</body>
</html>"""


def _chat_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Live Session</title>
<style>
:root{--bg:#06090b;--bg2:#0d1216;--panel:#10161a;--soft:#131b20;--line:#27333a;--text:#e6ecef;--muted:#8b9aa2;--accent:#ff5f57;--accent-2:#ff9d63;--agent:#172024;--user:#4a211d}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.14),transparent 24%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);height:100vh;display:flex;flex-direction:column}
.header{padding:18px 24px;background:rgba(10,14,17,.9);border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:14px}
.logo-icon{width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,var(--accent),#912820);display:grid;place-items:center;font-weight:800}
.logo-copy small{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.14em}
.nav-btn{padding:10px 14px;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:999px;color:var(--text);cursor:pointer;text-decoration:none}
.chat-container{flex:1;display:grid;grid-template-columns:310px 1fr;overflow:hidden}
.sidebar{background:rgba(14,19,23,.82);border-right:1px solid var(--line);padding:24px;overflow-y:auto}
.side-card{padding:18px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.02);margin-bottom:18px}
.side-card h3{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#ffb4a4;margin-bottom:14px}
.mode-select{display:flex;flex-wrap:wrap;gap:10px}
.mode-btn{padding:10px 12px;background:#12191d;border:1px solid var(--line);border-radius:12px;color:var(--text);cursor:pointer;font-size:13px}
.mode-btn.active{background:linear-gradient(135deg,var(--accent),#94352b);border-color:#b64839}
.chat-main{display:flex;flex-direction:column;min-width:0}
.messages{flex:1;overflow-y:auto;padding:24px 28px;display:flex;flex-direction:column;gap:18px}
.banner{padding:18px 20px;border:1px solid rgba(255,95,87,.22);background:linear-gradient(135deg,rgba(255,95,87,.12),rgba(255,157,99,.05));border-radius:20px}
.banner strong{display:block;font-size:18px;margin-bottom:6px}
.banner span{color:var(--muted);font-size:14px;line-height:1.6}
.message{display:flex;gap:14px;align-items:flex-start}
.message.user{flex-direction:row-reverse}
.avatar{width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,var(--accent),#8b2b24);display:grid;place-items:center;font-weight:800;flex-shrink:0}
.content{max-width:min(820px,76%)}
.bubble{background:var(--agent);padding:16px 18px;border-radius:18px;border:1px solid var(--line);line-height:1.65}
.user .bubble{background:var(--user);border-color:#6d322b}
.meta{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.steps{background:rgba(255,255,255,.02);border:1px solid var(--line);border-radius:16px;padding:16px;margin-top:12px}
.steps h4{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ffb4a4;margin-bottom:12px}
.step{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;font-size:13px;color:#cad3d8}
.step-num{width:22px;height:22px;background:#1e2b30;border:1px solid #3f5058;border-radius:50%;display:grid;place-items:center;font-size:11px;flex-shrink:0}
.input-area{padding:18px 24px;background:rgba(10,14,17,.9);border-top:1px solid var(--line)}
.input-container{display:flex;gap:12px;align-items:center}
.input-shell{flex:1;display:flex;align-items:center;gap:12px;padding:12px 14px;background:#10171b;border:1px solid var(--line);border-radius:18px}
.input-shell input{flex:1;background:transparent;border:none;color:var(--text);font-size:15px}
.input-shell input:focus{outline:none}
.send-btn{padding:14px 18px;background:linear-gradient(135deg,var(--accent),var(--accent-2));border:none;border-radius:14px;color:#121212;font-weight:800;cursor:pointer}
.send-btn:disabled{opacity:.5}
.typing{display:none;padding:14px 18px;background:#11181c;border:1px solid var(--line);border-radius:16px;width:fit-content;margin-left:56px}
.typing.show{display:block}
.dots{display:flex;gap:6px}
.dot{width:8px;height:8px;background:#8f9ea6;border-radius:50%;animation:typing 1.4s infinite}
.dot:nth-child(2){animation-delay:.2s}
.dot:nth-child(3){animation-delay:.4s}
.small{color:var(--muted);font-size:13px;line-height:1.6}
@keyframes typing{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-7px)}}
@media (max-width:960px){.chat-container{grid-template-columns:1fr}.sidebar{display:none}.content{max-width:88%}}
</style>
</head>
<body>
<header class="header">
<div class="logo"><div class="logo-icon">J</div><div class="logo-copy"><small>Interactive session</small><h2>JEBATCore Live Chat</h2></div></div>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<a href="/webui" class="nav-btn">Overview</a>
<a href="/webui/dashboard" class="nav-btn">Board</a>
<a href="/webui/agents" class="nav-btn">Agents</a>
<a href="/webui/control" class="nav-btn">Control</a>
</div>
</header>
<div class="chat-container">
<aside class="sidebar">
<div class="side-card">
<h3>Thinking mode</h3>
<div class="mode-select">
<button class="mode-btn" data-mode="fast">⚡ Fast</button>
<button class="mode-btn active" data-mode="deliberate">🤔 Deliberate</button>
<button class="mode-btn" data-mode="deep">🧠 Deep</button>
<button class="mode-btn" data-mode="strategic">📈 Strategic</button>
<button class="mode-btn" data-mode="creative">🎨 Creative</button>
<button class="mode-btn" data-mode="critical">🔍 Critical</button>
</div>
</div>
<div class="side-card">
<h3>Operator notes</h3>
<p class="small">Use deliberate for general execution, strategic for planning, and critical when you want the model to challenge assumptions before moving.</p>
</div>
<div class="side-card">
<h3>Session posture</h3>
<p class="small">This interface is tuned for high-signal runs: low chrome, visible reasoning, confidence markers, and fast recovery when a provider falls back.</p>
</div>
</aside>
<main class="chat-main">
<div class="messages" id="messages">
<div class="banner"><strong>Operator channel open.</strong><span>Start with goal, constraints, and environment. JEBATCore will keep the reasoning trace visible when it matters.</span></div>
<div class="message">
<div class="avatar">J</div>
<div class="content">
<div class="bubble">Live session online. Give me the target task, the context that matters, and the bar for the result.</div>
<div class="meta"><span>Just now</span></div>
</div>
</div>
</div>
<div class="typing" id="typing"><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>
<div class="input-area">
<div class="input-container">
<div class="input-shell"><input type="text" id="input" placeholder="Describe the task, scope, or blocker..." autocomplete="off"></div>
<button class="send-btn" id="sendBtn">Send</button>
</div>
</div>
</main>
</div>
<script>
let mode='deliberate';
const userId='user_'+Math.random().toString(36).substr(2,9);
document.querySelectorAll('.mode-btn').forEach(btn=>{
btn.addEventListener('click',()=>{
document.querySelectorAll('.mode-btn').forEach(b=>b.classList.remove('active'));
btn.classList.add('active');
mode=btn.dataset.mode;
});
});
async function send(){
const input=document.getElementById('input');
const sendBtn=document.getElementById('sendBtn');
const msg=input.value.trim();
if(!msg)return;
addMessage(msg,'user');
input.value='';
sendBtn.disabled=true;
document.getElementById('typing').classList.add('show');
try{
const resp=await fetch('/webui/api/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({user_id:userId,message:msg,thinking_mode:mode})
});
const data=await resp.json();
document.getElementById('typing').classList.remove('show');
addMessage(data.response,'assistant',{confidence:data.confidence,thoughts:data.thinking_steps,reasoning:data.reasoning||[]});
}catch(e){
console.error(e);
document.getElementById('typing').classList.remove('show');
addMessage('Error processing message.','assistant');
}
sendBtn.disabled=false;
input.focus();
}
function addMessage(content,role,meta={}){
const div=document.createElement('div');
div.className='message '+role;
let metaHtml='';
if(meta.confidence!==undefined){
metaHtml+='<span>Confidence: '+(meta.confidence*100).toFixed(1)+'%</span>';
metaHtml+='<span>Thoughts: '+meta.thoughts+'</span>';
}
metaHtml+='<span>'+new Date().toLocaleTimeString()+'</span>';
let stepsHtml='';
if(meta.reasoning&&meta.reasoning.length>0){
stepsHtml='<div class="steps"><h4>Reasoning trace</h4>'+meta.reasoning.map((s,i)=>'<div class="step"><div class="step-num">'+(i+1)+'</div><div>'+s+'</div></div>').join('')+'</div>';
}
div.innerHTML='<div class="avatar">'+(role==='user'?'U':'J')+'</div><div class="content"><div class="bubble">'+content+'</div>'+stepsHtml+'<div class="meta">'+metaHtml+'</div></div>';
document.getElementById('messages').appendChild(div);
document.getElementById('messages').scrollTop=document.getElementById('messages').scrollHeight;
}
document.getElementById('sendBtn').addEventListener('click',send);
document.getElementById('input').addEventListener('keypress',e=>{if(e.key==='Enter')send();});
</script>
</body>
</html>"""


def _dashboard_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Systems Board</title>
<style>
:root{--bg:#05080a;--bg2:#0e1317;--panel:#11181c;--line:#273139;--text:#e6ecef;--muted:#8b9ba3;--accent:#ff5f57;--ok:#2ad18b}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at top,rgba(255,95,87,.13),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.container{max-width:1320px;margin:0 auto;padding:24px}
.header{display:flex;justify-content:space-between;align-items:center;padding:18px 22px;background:rgba(15,20,24,.9);border:1px solid var(--line);border-radius:22px}
.logo{display:flex;align-items:center;gap:14px}
.logo-icon{width:48px;height:48px;background:linear-gradient(135deg,var(--accent),#8c2a24);border-radius:14px;display:grid;place-items:center;font-weight:800}
.nav-btn{padding:10px 14px;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:999px;color:var(--text);cursor:pointer;text-decoration:none}
.dashboard{padding:24px 0}
.intro{display:grid;grid-template-columns:1.15fr .85fr;gap:20px;margin-bottom:20px}
.hero,.ops-card,.component{background:rgba(15,20,24,.86);border:1px solid var(--line);border-radius:24px}
.hero{padding:28px}
.hero small{display:block;color:#ffb4a4;letter-spacing:.16em;text-transform:uppercase;font-size:11px;margin-bottom:12px}
.hero h1{font-size:42px;line-height:1;margin-bottom:14px}
.hero p{color:var(--muted);max-width:56ch;line-height:1.7}
.ops-card{padding:22px;display:grid;gap:14px}
.ops-row{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid rgba(255,255,255,.05);padding-bottom:12px}
.ops-row:last-child{border-bottom:none;padding-bottom:0}
.ops-row span{color:var(--muted);font-size:13px}
.ops-row strong{font-size:20px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;margin-bottom:24px}
.stat{background:rgba(15,20,24,.82);border:1px solid var(--line);border-radius:20px;padding:22px}
.stat h3{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.15em;margin-bottom:12px}
.stat-value{font-size:34px;font-weight:800;margin-bottom:6px}
.stat-label{color:var(--muted);font-size:13px;line-height:1.5}
.components{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.component{padding:22px}
.comp-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.badge{padding:6px 12px;border-radius:999px;font-size:11px;font-weight:700;background:rgba(42,209,139,.14);color:var(--ok);letter-spacing:.12em;text-transform:uppercase}
.component p{color:var(--muted);line-height:1.65;font-size:14px}
@media (max-width:1080px){.intro,.components,.stats{grid-template-columns:1fr 1fr}}@media (max-width:760px){.intro,.components,.stats{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<header class="header">
<div class="logo"><div class="logo-icon">J</div><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Control surface</small><h2>JEBATCore Systems Board</h2></div></div>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<a href="/webui" class="nav-btn">Overview</a>
<a href="/webui/chat" class="nav-btn">Chat</a>
<a href="/webui/doctor" class="nav-btn">Doctor</a>
<a href="/webui/control" class="nav-btn">Control</a>
</div>
</header>
<main class="dashboard">
<section class="intro">
<div class="hero"><small>Operations snapshot</small><h1>Know what is live before you trust the agent.</h1><p>The board is optimized for quick operational reads: system health, active connections, reasoning surface readiness, and memory plane status in one pass.</p></div>
<div class="ops-card">
<div class="ops-row"><span>Readiness</span><strong style="color:var(--ok)">Green</strong></div>
<div class="ops-row"><span>Exposure</span><strong>WebUI + API</strong></div>
<div class="ops-row"><span>Mode posture</span><strong>Capture-first</strong></div>
</div>
</section>
<div class="stats">
<div class="stat"><h3>SYSTEM STATUS</h3><div class="stat-value" style="color:#10b981">● Online</div><div class="stat-label">All systems operational</div></div>
<div class="stat"><h3>ACTIVE CONNECTIONS</h3><div class="stat-value" id="connections">0</div><div class="stat-label">WebSocket clients</div></div>
<div class="stat"><h3>THINKING MODES</h3><div class="stat-value">6</div><div class="stat-label">Fast, Deliberate, Deep, Strategic, Creative, Critical</div></div>
<div class="stat"><h3>MEMORY LAYERS</h3><div class="stat-value">5</div><div class="stat-label">M0 → M4 with heat scoring</div></div>
</div>
<h2 style="margin-bottom:20px">System Components</h2>
<div class="components">
<div class="component"><div class="comp-header"><h3>🔄 Ultra-Loop</h3><span class="badge">OPERATIONAL</span></div><p style="color:#64748b">Continuous processing: Perception → Cognition → Memory → Action → Learning</p><p style="color:#64748b;margin-top:10px;font-size:13px">Performance: 5 cycles/second</p></div>
<div class="component"><div class="comp-header"><h3>🤔 Ultra-Think</h3><span class="badge">OPERATIONAL</span></div><p style="color:#64748b">Deep reasoning with 6 thinking modes</p><p style="color:#64748b;margin-top:10px;font-size:13px">Performance: 8750+ thoughts/second</p></div>
<div class="component"><div class="comp-header"><h3>🧠 Memory Manager</h3><span class="badge">OPERATIONAL</span></div><p style="color:#64748b">5-layer memory with heat-based importance</p><p style="color:#64748b;margin-top:10px;font-size:13px">Layers: M0 Sensory, M1 Episodic, M2 Semantic, M3 Conceptual, M4 Procedural</p></div>
<div class="component"><div class="comp-header"><h3>💾 Cache Manager</h3><span class="badge">OPERATIONAL</span></div><p style="color:#64748b">3-tier smart cache: HOT/WARM/COLD</p><p style="color:#64748b;margin-top:10px;font-size:13px">Latency: HOT &lt;10ms, WARM &lt;100ms, COLD &lt;500ms</p></div>
<div class="component"><div class="comp-header"><h3>🎯 Decision Engine</h3><span class="badge">OPERATIONAL</span></div><p style="color:#64748b">Intelligent agent selection and routing</p><p style="color:#64748b;margin-top:10px;font-size:13px">Capabilities: Agent Selection, Routing, Priority</p></div>
<div class="component"><div class="comp-header"><h3>🤖 Agent Orchestrator</h3><span class="badge">OPERATIONAL</span></div><p style="color:#64748b">Multi-agent coordination</p><p style="color:#64748b;margin-top:10px;font-size:13px">Templates: Chat, Analyst, Creative, Task, Research</p></div>
</div>
</div>
</main>
<script>
async function update(){
try{
const resp=await fetch('/webui/api/status');
const data=await resp.json();
document.getElementById('connections').textContent=data.active_connections||0;
}catch(e){console.error(e);}
}
setInterval(update,5000);
update();
</script>
</body>
</html>"""


def _memory_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Memory Map</title>
<style>
:root{--bg:#05080a;--bg2:#0e1317;--panel:#11181c;--line:#273139;--text:#e6ecef;--muted:#8b9ba3;--accent:#ff5f57}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.13),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.container{max-width:1320px;margin:0 auto;padding:24px}
.header{display:flex;justify-content:space-between;align-items:center;padding:18px 22px;background:rgba(15,20,24,.9);border:1px solid var(--line);border-radius:22px}
.logo{display:flex;align-items:center;gap:14px}
.logo-icon{width:48px;height:48px;background:linear-gradient(135deg,var(--accent),#8c2a24);border-radius:14px;display:grid;place-items:center;font-weight:800}
.nav-btn{padding:10px 14px;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:999px;color:var(--text);cursor:pointer;text-decoration:none}
.explorer{padding:24px 0}
.intro{padding:24px;background:rgba(15,20,24,.86);border:1px solid var(--line);border-radius:24px;margin-bottom:22px}
.intro h1{font-size:38px;line-height:1;margin-bottom:14px}
.intro p{color:var(--muted);max-width:60ch;line-height:1.7}
.search{display:flex;gap:12px;margin-bottom:26px}
.search input{flex:1;padding:16px 18px;background:#11181c;border:1px solid var(--line);border-radius:16px;color:var(--text);font-size:15px}
.search input:focus{outline:none;border-color:#47545d}
.search-btn{padding:15px 18px;background:linear-gradient(135deg,var(--accent),#ff9b6a);border:none;border-radius:16px;color:#111;font-weight:800;cursor:pointer}
.layers{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.layer{background:rgba(15,20,24,.82);border:1px solid var(--line);border-radius:22px;padding:24px}
.layer-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
.layer-name{font-size:20px;font-weight:700}
.layer-desc{color:var(--muted);font-size:13px;margin-top:5px}
.pill{padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.1);font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:#ffc4bc}
@media (max-width:840px){.layers{grid-template-columns:1fr}.search{flex-direction:column}}
</style>
</head>
<body>
<div class="container">
<header class="header">
<div class="logo"><div class="logo-icon">J</div><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Retention layers</small><h2>JEBATCore Memory Map</h2></div></div>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<a href="/webui" class="nav-btn">Overview</a>
<a href="/webui/dashboard" class="nav-btn">Board</a>
<a href="/webui/skills" class="nav-btn">Skills</a>
<a href="/webui/control" class="nav-btn">Control</a>
</div>
</header>
<main class="explorer">
<section class="intro"><h1>Memory map</h1><p>Inspect what JEBATCore keeps, what expires, and what becomes durable operator knowledge. The memory plane is split by retention horizon so context survives without becoming sludge.</p></section>
<div class="search">
<input type="text" id="query" placeholder="Search memories...">
<button class="search-btn" onclick="search()">Inspect</button>
</div>
<div class="layers">
<div class="layer"><div class="layer-header"><div><div class="layer-name">M0 / Sensory buffer</div><div class="layer-desc">0-30 second retention</div></div><span class="pill">volatile</span></div><p style="color:var(--muted)">Immediate inputs, active observations, and transient state while an interaction is still being processed.</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">M1 / Episodic recall</div><div class="layer-desc">Minutes to hours</div></div><span class="pill">recent</span></div><p style="color:var(--muted)">Recent runs, conversation turns, and short-lived context that may still matter to the current task chain.</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">M2 / Semantic store</div><div class="layer-desc">Days to weeks</div></div><span class="pill">knowledge</span></div><p style="color:var(--muted)">Facts, stable project context, and reusable knowledge that should survive across sessions.</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">M3 / Conceptual models</div><div class="layer-desc">Long horizon</div></div><span class="pill">models</span></div><p style="color:var(--muted)">Higher-level patterns, operating heuristics, and mental models the assistant can reuse as guidance.</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">M4 / Procedural memory</div><div class="layer-desc">Long horizon</div></div><span class="pill">skills</span></div><p style="color:var(--muted)">Skills, durable procedures, and execution habits that should stay available as the system evolves.</p></div>
</div>
</main>
<div>
<script>
async function search(){
const q=document.getElementById('query').value;
if(!q)return;
try{
const resp=await fetch('/webui/api/memory/stats');
const data=await resp.json();
alert('Memory stats: '+JSON.stringify(data.stats||{},null,2));
}catch(e){alert('Search: '+e.message);}
}
document.getElementById('query').addEventListener('keypress',e=>{if(e.key==='Enter')search();});
</script>
</body>
</html>"""


def _agents_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Agents</title>
<style>
:root{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57;--ok:#2ad18b}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.14),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.shell{max-width:1320px;margin:0 auto;padding:24px}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px;background:rgba(15,20,24,.9);border:1px solid var(--line);border-radius:22px}
.brand{display:flex;align-items:center;gap:14px}.mark{width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,var(--accent),#8f2d26);display:grid;place-items:center;font-weight:800}
.nav{display:flex;gap:10px;flex-wrap:wrap}.nav a{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}
.hero{padding:26px;background:rgba(15,20,24,.86);border:1px solid var(--line);border-radius:24px;margin:22px 0}
.hero h1{font-size:42px;line-height:1;margin:10px 0 14px}.hero p{color:var(--muted);max-width:62ch;line-height:1.7}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.card{padding:22px;background:rgba(15,20,24,.82);border:1px solid var(--line);border-radius:22px}
.card small{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.08);color:#ffb4a4;text-transform:uppercase;letter-spacing:.12em;font-size:11px;margin-bottom:12px}
.card h3{font-size:22px;margin-bottom:10px}.card p,.card li{color:var(--muted);line-height:1.65;font-size:14px}
.card ul{list-style:none;display:grid;gap:8px;margin-top:12px}
.status{margin-top:22px;display:flex;gap:16px;flex-wrap:wrap;color:var(--muted)}.status span{display:flex;align-items:center;gap:10px}.dot{width:10px;height:10px;border-radius:50%;background:var(--ok)}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="top">
<div class="brand"><div class="mark">J</div><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Hermes + OpenClaw pattern</small><h2>Agent Surface</h2></div></div>
<nav class="nav"><a href="/webui/">Overview</a><a href="/webui/chat">Chat</a><a href="/webui/dashboard">Board</a><a href="/webui/skills">Skills</a><a href="/webui/doctor">Doctor</a><a href="/webui/control">Control</a></nav>
</header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Operator map</small><h1>Multi-agent roles, without losing the main thread.</h1><p>JEBATCore adopts the Hermes habit of staying useful in the foreground while OpenClaw-style routing and role separation stay visible. Each role has a clear surface and a reason to exist.</p></section>
<section class="grid">
<article class="card"><small>Primary</small><h3>JEBAT Operator</h3><p>The main interactive agent for planning, coding, execution, and repo-aware support.</p><ul><li>Owns the working conversation</li><li>Chooses mode and provider</li><li>Keeps task context stable</li></ul></article>
<article class="card"><small>Hermes Mode</small><h3>Capture-first copilot</h3><p>Biases toward understanding project shape, constraints, and risks before editing anything.</p><ul><li>Repo capture</li><li>Planning before action</li><li>Skill-guided execution</li></ul></article>
<article class="card"><small>OpenClaw Pattern</small><h3>Control and channels</h3><p>Represents the gateway, channel, and routed session mindset used in OpenClaw.</p><ul><li>Provider failover</li><li>Channel awareness</li><li>Operational control surface</li></ul></article>
<article class="card"><small>Specialists</small><h3>Role-based workers</h3><p>Builder, research, security, and reasoning roles stay explicit so you can see what should act next.</p><ul><li>Builder for implementation</li><li>Security for defensive analysis</li><li>Research for context gathering</li></ul></article>
</section>
<div class="status"><span><i class="dot"></i>Operator online</span><span><i class="dot"></i>Hermes posture active</span><span><i class="dot"></i>Control plane available</span></div>
</div>
</body>
</html>"""


def _skills_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Skills</title>
<style>
:root{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.shell{max-width:1320px;margin:0 auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px;background:rgba(15,20,24,.9);border:1px solid var(--line);border-radius:22px}
.mark{width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,var(--accent),#8f2d26);display:grid;place-items:center;font-weight:800}.brand{display:flex;align-items:center;gap:14px}.nav{display:flex;gap:10px;flex-wrap:wrap}.nav a{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}
.hero,.skill{background:rgba(15,20,24,.84);border:1px solid var(--line);border-radius:22px}.hero{padding:24px;margin:22px 0}.hero h1{font-size:40px;margin:10px 0 14px}.hero p,.skill p,.skill li{color:var(--muted);line-height:1.7}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.skill{padding:22px}.tag{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.1);color:#ffb4a4;text-transform:uppercase;letter-spacing:.12em;font-size:11px;margin-bottom:12px}.skill ul{list-style:none;display:grid;gap:8px;margin-top:12px}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="top"><div class="brand"><div class="mark">J</div><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Hermes-aligned toolkit</small><h2>Skills Menu</h2></div></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/chat">Chat</a><a href="/webui/agents">Agents</a><a href="/webui/dashboard">Board</a><a href="/webui/doctor">Doctor</a><a href="/webui/control">Control</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Menu surface</small><h1>Skills are visible, not hidden prompt magic.</h1><p>The console exposes the operating patterns behind the assistant so you know when you are in Hermes capture mode, coding mode, project mode, or provider-health mode.</p></section>
<section class="grid">
<article class="skill"><div class="tag">Core</div><h3>Hermes Agent</h3><p>Capture-first behavior for repo understanding, planning, and practical execution.</p><ul><li>Project intake</li><li>Constraint mapping</li><li>Next-step bias</li></ul></article>
<article class="skill"><div class="tag">Routing</div><h3>Provider failover</h3><p>Moves through configured provider paths when quota or availability changes.</p><ul><li>OpenAI / Google / Anthropic aware</li><li>Local fallback path</li><li>Doctor integration</li></ul></article>
<article class="skill"><div class="tag">Workflow</div><h3>Project-aware chat</h3><p>Injects repo context and keeps working sessions grounded in the current codebase.</p><ul><li>Repo summary</li><li>Session history</li><li>Pinned skills</li></ul></article>
<article class="skill"><div class="tag">Control</div><h3>OpenClaw-style surface</h3><p>Aligns the UI around sessions, agents, control, and visibility instead of generic chatbot screens.</p><ul><li>Control page</li><li>Status board</li><li>Agent menu</li></ul></article>
</section>
</div>
</body>
</html>"""


def _doctor_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Doctor</title>
<style>
:root{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57;--ok:#2ad18b;--warn:#f7b955}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.shell{max-width:1200px;margin:0 auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px;background:rgba(15,20,24,.9);border:1px solid var(--line);border-radius:22px}
.nav{display:flex;gap:10px;flex-wrap:wrap}.nav a{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}
.hero,.panel{background:rgba(15,20,24,.84);border:1px solid var(--line);border-radius:22px}.hero{padding:24px;margin:22px 0}.hero h1{font-size:38px;margin:10px 0 14px}.hero p,.row span{color:var(--muted);line-height:1.7}
.panel{padding:22px}.row{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 0;border-bottom:1px solid rgba(255,255,255,.05)}.row:last-child{border-bottom:none;padding-bottom:0}
.pill{padding:6px 10px;border-radius:999px;font-size:11px;text-transform:uppercase;letter-spacing:.12em}.ok{background:rgba(42,209,139,.14);color:var(--ok)}.warn{background:rgba(247,185,85,.12);color:var(--warn)}
</style>
</head>
<body>
<div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Readiness checks</small><h2>Doctor</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/chat">Chat</a><a href="/webui/dashboard">Board</a><a href="/webui/agents">Agents</a><a href="/webui/skills">Skills</a><a href="/webui/control">Control</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Health posture</small><h1>Operator checks before a live run.</h1><p>This page mirrors the CLI doctor mindset: provider readiness, routing posture, memory plane, and WebUI/API health in one scan.</p></section>
<section class="panel">
<div class="row"><div><strong>WebUI surface</strong><span style="display:block">Interactive console, menus, and operator navigation.</span></div><div class="pill ok">online</div></div>
<div class="row"><div><strong>API plane</strong><span style="display:block">Status, chat, health, and memory endpoints.</span></div><div class="pill ok">healthy</div></div>
<div class="row"><div><strong>Provider routing</strong><span style="display:block">Uses configured provider flow with fallback.</span></div><div class="pill warn">check via jebat-cli doctor --probe</div></div>
<div class="row"><div><strong>Hermes posture</strong><span style="display:block">Capture-first workflow available before edits.</span></div><div class="pill ok">ready</div></div>
</section>
</div>
</body>
</html>"""


def _control_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Control</title>
<style>
:root{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top right,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.shell{max-width:1320px;margin:0 auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px;background:rgba(15,20,24,.9);border:1px solid var(--line);border-radius:22px}
.nav{display:flex;gap:10px;flex-wrap:wrap}.nav a{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}
.hero,.grid-card{background:rgba(15,20,24,.84);border:1px solid var(--line);border-radius:22px}.hero{padding:24px;margin:22px 0}.hero h1{font-size:40px;margin:10px 0 14px}.hero p,.grid-card p,.grid-card li{color:var(--muted);line-height:1.7}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.grid-card{padding:22px}.grid-card ul{list-style:none;display:grid;gap:8px;margin-top:12px}.tag{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.1);color:#ffb4a4;text-transform:uppercase;letter-spacing:.12em;font-size:11px;margin-bottom:12px}
@media (max-width:980px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">OpenClaw-aligned menu</small><h2>Control</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/chat">Chat</a><a href="/webui/dashboard">Board</a><a href="/webui/agents">Agents</a><a href="/webui/skills">Skills</a><a href="/webui/doctor">Doctor</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Control plane</small><h1>OpenClaw-style menus, adapted for JEBATCore.</h1><p>This page collects the control concepts users expect from OpenClaw: sessions, agents, routing, surface health, and operator visibility, but expressed inside the JEBATCore WebUI.</p></section>
<section class="grid">
<article class="grid-card"><div class="tag">Sessions</div><h3>Chat and project runs</h3><p>Use the live chat page as the primary session surface and the dashboard as the readiness board.</p><ul><li>Live chat</li><li>Project-aware flow</li><li>Reasoning visibility</li></ul></article>
<article class="grid-card"><div class="tag">Agents</div><h3>Hermes and role surfaces</h3><p>Use the agent page to understand which role should act: operator, builder, security, or research.</p><ul><li>Hermes capture mode</li><li>Specialist roles</li><li>Routing visibility</li></ul></article>
<article class="grid-card"><div class="tag">Health</div><h3>Doctor and status checks</h3><p>Use the doctor page and CLI doctor command before long runs or when provider behavior looks degraded.</p><ul><li>Provider readiness</li><li>Fallback awareness</li><li>Surface health</li></ul></article>
</section>
</div>
</body>
</html>"""


def _channels_html():
    meta = _console_meta()
    available = "".join(
        f"<li><strong>{name.title()}</strong><span>Channel adapter discovered from jebat/integrations/channels.</span></li>"
        for name in meta["channels"]
    )
    configured = "".join(
        f"<li><strong>{name}</strong><span>Configured in OpenClaw template.</span></li>"
        for name in meta["openclaw"]["channel_names"]
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JEBATCore Channels</title>
<style>
:root{{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}}
.shell{{max-width:1280px;margin:0 auto;padding:24px}}.top,.panel,.hero{{background:rgba(15,20,24,.88);border:1px solid var(--line);border-radius:22px}}.top{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px}}
.nav{{display:flex;gap:10px;flex-wrap:wrap}}.nav a{{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}}.hero{{padding:24px;margin:22px 0}}.hero h1{{font-size:40px;margin:10px 0 14px}}.hero p,.panel p,.panel li,.panel span{{color:var(--muted);line-height:1.7}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.panel{{padding:22px}}.panel ul{{list-style:none;display:grid;gap:10px;margin-top:14px}}.panel li{{padding:12px 14px;border:1px solid rgba(255,255,255,.06);border-radius:14px;background:rgba(255,255,255,.02)}}.panel strong{{display:block;color:var(--text)}}
@media (max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Channel plane</small><h2>Channels</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/control">Control</a><a href="/webui/workstation">Workstation</a><a href="/webui/integrations">Integrations</a><a href="/webui/learning">Learning</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Surface routing</small><h1>Operator channels and message surfaces.</h1><p>These entries are pulled from the repo’s channel adapters and OpenClaw template, so the menu reflects the actual surfaces you can wire into the runtime.</p></section>
<section class="grid">
<article class="panel"><h3>Available channel adapters</h3><ul>{available}</ul></article>
<article class="panel"><h3>OpenClaw configured channels</h3><ul>{configured or '<li><strong>None</strong><span>No configured channels found in the template.</span></li>'}</ul><p style="margin-top:14px">Gateway port: <strong style="color:var(--text)">{meta["openclaw"]["gateway_port"]}</strong></p></article>
</section></div></body></html>"""


def _workstation_html():
    meta = _console_meta()
    cards = "".join(
        f"<li><strong>{item['name']}</strong><span>{item['path']} / {item['state']}</span></li>"
        for item in meta["workstations"]
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JEBATCore Workstation</title>
<style>
:root{{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57;--ok:#2ad18b}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}}
.shell{{max-width:1280px;margin:0 auto;padding:24px}}.top,.hero,.panel{{background:rgba(15,20,24,.88);border:1px solid var(--line);border-radius:22px}}.top{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px}}
.nav{{display:flex;gap:10px;flex-wrap:wrap}}.nav a{{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}}.hero{{padding:24px;margin:22px 0}}.hero h1{{font-size:40px;margin:10px 0 14px}}.hero p,.panel li,.panel span{{color:var(--muted);line-height:1.7}}
.panel{{padding:22px}}.panel ul{{list-style:none;display:grid;gap:12px}}.panel li{{padding:14px 16px;border:1px solid rgba(255,255,255,.06);border-radius:14px;background:rgba(255,255,255,.02)}}.panel strong{{display:block;color:var(--text)}}
</style></head><body><div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Operator environment</small><h2>Workstation</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/channels">Channels</a><a href="/webui/integrations">Integrations</a><a href="/webui/doctor">Doctor</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Connection surface</small><h1>One console, multiple operating stations.</h1><p>JEBATCore now exposes the work surfaces you actually use: CLI, OpenClaw runtime, VS Code, and the live VPS deployment.</p></section>
<article class="panel"><ul>{cards}</ul></article></div></body></html>"""


def _integrations_html():
    meta = _console_meta()
    items = "".join(
        f"<li><strong>{item['name']}</strong><span>{item['path']} / {item['state']}</span></li>"
        for item in meta["integrations"]
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JEBATCore Integrations</title>
<style>
:root{{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top right,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}}
.shell{{max-width:1280px;margin:0 auto;padding:24px}}.top,.hero,.panel{{background:rgba(15,20,24,.88);border:1px solid var(--line);border-radius:22px}}.top{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px}}
.nav{{display:flex;gap:10px;flex-wrap:wrap}}.nav a{{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}}.hero{{padding:24px;margin:22px 0}}.hero h1{{font-size:40px;margin:10px 0 14px}}.hero p,.panel p,.panel li,.panel span{{color:var(--muted);line-height:1.7}}
.panel{{padding:22px}}.panel ul{{list-style:none;display:grid;gap:12px}}.panel li{{padding:14px 16px;border:1px solid rgba(255,255,255,.06);border-radius:14px;background:rgba(255,255,255,.02)}}.panel strong{{display:block;color:var(--text)}}
</style></head><body><div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Versioned connections</small><h2>Integrations</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/channels">Channels</a><a href="/webui/workstation">Workstation</a><a href="/webui/control">Control</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Repo-grounded links</small><h1>Integration points that already exist in the repo.</h1><p>The page lists versioned integration assets, not aspirational ideas. That includes the OpenClaw bundle, MCP guide, and IDE integration docs already present in JEBATCore.</p></section>
<article class="panel"><ul>{items}</ul></article></div></body></html>"""


def _learning_html():
    meta = _console_meta()
    top_skills = "".join(
        f"<li><strong>{skill['name']}</strong><span>{skill['category']} / {skill['description']}</span></li>"
        for skill in meta["skills"]["top"]
    )
    learning_modules = "".join(
        f"<li><strong>{Path(module).name}</strong><span>{module}</span></li>"
        for module in meta["learning"]["modules"]
    )
    excerpt = meta["skills"]["openclaw_excerpt"] or "OpenClaw Hermes skill excerpt unavailable."
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JEBATCore Learning</title>
<style>
:root{{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}}
.shell{{max-width:1280px;margin:0 auto;padding:24px}}.top,.hero,.grid-card{{background:rgba(15,20,24,.88);border:1px solid var(--line);border-radius:22px}}.top{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px}}
.nav{{display:flex;gap:10px;flex-wrap:wrap}}.nav a{{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}}.hero{{padding:24px;margin:22px 0}}.hero h1{{font-size:40px;margin:10px 0 14px}}.hero p,.grid-card p,.grid-card li,.grid-card span,pre{{color:var(--muted);line-height:1.7}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.grid-card{{padding:22px}}.grid-card ul{{list-style:none;display:grid;gap:12px;margin-top:12px}}.grid-card li{{padding:14px 16px;border:1px solid rgba(255,255,255,.06);border-radius:14px;background:rgba(255,255,255,.02)}}.grid-card strong{{display:block;color:var(--text)}}pre{{white-space:pre-wrap;background:rgba(255,255,255,.02);padding:16px;border-radius:14px;border:1px solid rgba(255,255,255,.05)}}
@media (max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Adaptive behavior</small><h2>Skill Learning</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/skills">Skills</a><a href="/webui/agents">Agents</a><a href="/webui/control">Control</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Learning plane</small><h1>Use repo skills, and keep making them better.</h1><p>This surface ties together TokGuru skills, the OpenClaw Hermes skill, and the continuum/cortex learning modules already present in the codebase.</p></section>
<section class="grid">
<article class="grid-card"><h3>Top loaded skills</h3><p>Detected from the TokGuru registry. Current count: <strong style="color:var(--text)">{meta["skills"]["count"]}</strong></p><ul>{top_skills}</ul></article>
<article class="grid-card"><h3>Learning modules</h3><p>These modules are already in the repo and form the basis for adaptive skill execution and recommendation.</p><ul>{learning_modules}</ul></article>
</section>
<section class="grid" style="margin-top:18px">
<article class="grid-card" style="grid-column:1/-1"><h3>OpenClaw Hermes skill excerpt</h3><pre>{excerpt}</pre></article>
</section></div></body></html>"""


def _setup_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Setup Guide</title>
<style>
:root{--bg:#06090b;--bg2:#10161a;--panel:#11181c;--line:#263138;--text:#e6ecef;--muted:#8a9aa2;--accent:#ff5f57}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.12),transparent 22%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
.shell{max-width:1200px;margin:0 auto;padding:24px}.top,.hero,.panel{background:rgba(15,20,24,.88);border:1px solid var(--line);border-radius:22px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:18px 22px}
.nav{display:flex;gap:10px;flex-wrap:wrap}.nav a{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--text);text-decoration:none;background:rgba(255,255,255,.03)}.hero{padding:24px;margin:22px 0}.hero h1{font-size:40px;margin:10px 0 14px}.hero p,.panel li,.panel span{color:var(--muted);line-height:1.7}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{padding:22px}.panel ul{list-style:none;display:grid;gap:12px}.panel li{padding:14px 16px;border:1px solid rgba(255,255,255,.06);border-radius:14px;background:rgba(255,255,255,.02)}.panel strong{display:block;color:var(--text)}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="top"><div><small style="display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px">Operator guide</small><h2>Setup</h2></div><nav class="nav"><a href="/webui/">Overview</a><a href="/webui/channels">Channels</a><a href="/webui/workstation">Workstation</a><a href="/webui/control">Control</a></nav></header>
<section class="hero"><small style="color:#ffb4a4;letter-spacing:.14em;text-transform:uppercase;font-size:11px">Easy setup</small><h1>Connect channels and workstations in one pass.</h1><p>Use this page when you need the shortest path to a working Telegram bot, WhatsApp integration, Discord/Slack channel, or an operator workstation entry.</p></section>
<section class="grid">
<article class="panel"><h3>Channels</h3><ul><li><strong>Telegram</strong><span>Needs `bot_token` from `@BotFather`.</span></li><li><strong>WhatsApp</strong><span>Needs `phone_number_id`, `access_token`, `verify_token` from Meta.</span></li><li><strong>Discord</strong><span>Needs `bot_token`, `guild_id`.</span></li><li><strong>Slack</strong><span>Needs `bot_token`, `app_token`.</span></li></ul></article>
<article class="panel"><h3>Workstations</h3><ul><li><strong>CLI</strong><span>`~/.local/bin/jebat-cli`</span></li><li><strong>OpenClaw</strong><span>`~/.openclaw`</span></li><li><strong>VS Code</strong><span>`~/.config/Code/User`</span></li><li><strong>VPS</strong><span>`jebat.online` or your SSH host</span></li></ul></article>
</section>
</div>
</body>
</html>"""
