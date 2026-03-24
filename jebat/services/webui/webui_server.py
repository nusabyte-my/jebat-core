"""
JEBAT WebUI - Simplified Version

A reliable web interface for JEBAT AI Assistant.
"""

import asyncio
import json
import logging
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
        top_skills = [summarize_skill(skill) for skill in all_skills[:6]]
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


# HTML templates (simplified for reliability)
def _home_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBATCore Operations</title>
<style>
:root{--bg:#070b0d;--bg2:#0d1316;--panel:rgba(17,23,27,.88);--panel-soft:rgba(15,20,24,.72);--line:#243037;--line-strong:#3a4950;--text:#e7ecef;--muted:#8a9aa3;--accent:#ff5f57;--accent-2:#ff8d6b;--ok:#2ad18b;--warn:#f7b955}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at top left,rgba(255,95,87,.16),transparent 26%),radial-gradient(circle at right,rgba(247,185,85,.1),transparent 18%),linear-gradient(180deg,var(--bg),var(--bg2));color:var(--text);min-height:100vh}
a{text-decoration:none;color:inherit}
.shell{max-width:1320px;margin:0 auto;padding:24px}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:18px 22px;background:var(--panel);border:1px solid var(--line);border-radius:22px;backdrop-filter:blur(18px);position:sticky;top:18px;z-index:20}
.brand{display:flex;gap:16px;align-items:center}
.brand-mark{width:52px;height:52px;border-radius:16px;background:linear-gradient(135deg,var(--accent),#9f2f2a);display:grid;place-items:center;font-weight:800;letter-spacing:.08em;box-shadow:0 0 40px rgba(255,95,87,.25)}
.brand-copy small{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.14em;font-size:11px}
.brand-copy strong{display:block;font-size:22px;letter-spacing:.06em}
.nav{display:flex;gap:10px;flex-wrap:wrap}
.nav a{padding:10px 14px;border:1px solid var(--line);border-radius:999px;color:var(--muted);transition:.2s ease}
.nav a:hover{border-color:var(--line-strong);color:var(--text);background:rgba(255,255,255,.03)}
.hero{display:grid;grid-template-columns:1.25fr .95fr;gap:22px;margin:24px 0}
.hero-main,.hero-side,.card,.brief,.metric{background:var(--panel);border:1px solid var(--line);border-radius:26px;backdrop-filter:blur(14px)}
.hero-main{padding:34px;position:relative;overflow:hidden}
.hero-main:before{content:"";position:absolute;inset:auto -10% -30% auto;width:340px;height:340px;background:radial-gradient(circle,rgba(255,95,87,.18),transparent 62%)}
.eyebrow{display:inline-flex;align-items:center;gap:10px;padding:8px 12px;background:rgba(255,95,87,.08);border:1px solid rgba(255,95,87,.22);border-radius:999px;color:#ffc8c3;font-size:12px;text-transform:uppercase;letter-spacing:.14em}
.hero h1{font-size:clamp(42px,6vw,72px);line-height:.94;max-width:9ch;margin:20px 0 18px}
.hero p{max-width:52ch;color:var(--muted);font-size:17px;line-height:1.7}
.cta{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}
.btn{padding:14px 18px;border-radius:14px;font-weight:700;letter-spacing:.02em}
.btn-primary{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#111}
.btn-secondary{border:1px solid var(--line-strong);background:rgba(255,255,255,.03)}
.hero-side{padding:24px;display:grid;gap:14px}
.metric{padding:18px 18px 16px;border-radius:18px;background:var(--panel-soft)}
.metric label{display:block;color:var(--muted);font-size:11px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px}
.metric strong{display:block;font-size:28px;margin-bottom:6px}
.metric span{color:var(--muted);font-size:13px;line-height:1.5}
.board{display:grid;grid-template-columns:1.15fr .85fr;gap:22px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.card{padding:22px;min-height:220px;position:relative;overflow:hidden}
.card:after{content:"";position:absolute;inset:auto -20px -30px auto;width:140px;height:140px;background:radial-gradient(circle,rgba(255,95,87,.12),transparent 68%)}
.card h3,.brief h3{font-size:18px;margin-bottom:10px}
.card p,.brief p,.brief li{color:var(--muted);line-height:1.65;font-size:14px}
.chip{display:inline-flex;padding:6px 10px;border:1px solid var(--line-strong);border-radius:999px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#ffc8c3;background:rgba(255,95,87,.06);margin-bottom:14px}
.brief{padding:24px}
.brief ul{list-style:none;display:grid;gap:12px;margin-top:14px}
.brief li{padding:12px 14px;border:1px solid var(--line);border-radius:14px;background:rgba(255,255,255,.02)}
.footer{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:18px 22px;margin-top:24px;background:var(--panel);border:1px solid var(--line);border-radius:22px;color:var(--muted)}
.status{display:flex;gap:18px;flex-wrap:wrap}
.status span{display:inline-flex;align-items:center;gap:10px}
.dot{width:10px;height:10px;border-radius:50%;background:var(--ok);box-shadow:0 0 18px rgba(42,209,139,.45)}
@media (max-width:980px){.hero,.board{grid-template-columns:1fr}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
<div class="brand">
<div class="brand-mark">J</div>
<div class="brand-copy"><small>Red Team Operations Console</small><strong>JEBATCore</strong></div>
</div>
<nav class="nav">
<a href="/webui/">Overview</a>
<a href="/webui/chat">Chat</a>
<a href="/webui/dashboard">Board</a>
<a href="/webui/memory">Memory</a>
<a href="/webui/agents">Agents</a>
<a href="/webui/skills">Skills</a>
<a href="/webui/doctor">Doctor</a>
<a href="/webui/control">Control</a>
<a href="/webui/channels">Channels</a>
<a href="/webui/workstation">Workstation</a>
<a href="/webui/integrations">Integrations</a>
<a href="/webui/learning">Learning</a>
</nav>
</header>
<section class="hero">
<article class="hero-main">
<div class="eyebrow">Live operator surface</div>
<h1>Run a sharper offensive workflow without losing control.</h1>
<p>JEBATCore gives you one surface for reasoning, memory, routing, and task execution. The interface is tuned like an operations room: quick reads, low noise, and the right next move always visible.</p>
<div class="cta">
<a class="btn btn-primary" href="/webui/chat">Open Live Session</a>
<a class="btn btn-secondary" href="/webui/dashboard">Inspect Systems</a>
<a class="btn btn-secondary" href="/webui/memory">Review Memory</a>
</div>
</article>
<aside class="hero-side">
<div class="metric"><label>Mission State</label><strong>Green</strong><span>WebUI, API, memory plane, and decision flow online.</span></div>
<div class="metric"><label>Thinking Modes</label><strong>6 active</strong><span>Fast, deliberate, deep, strategic, creative, and critical routing.</span></div>
<div class="metric"><label>Operator Pattern</label><strong>Capture first</strong><span>Context, risks, constraints, then action. No blind execution.</span></div>
</aside>
</section>
<section class="board">
<div class="grid">
<article class="card"><div class="chip">Session</div><h3>Live reasoning with visible confidence</h3><p>Chat runs as an operator console, not a novelty chatbot. Mode selection, response confidence, and reasoning traces stay exposed so you can verify the model instead of trusting vibes.</p></article>
<article class="card"><div class="chip">Memory</div><h3>Layered recall for durable context</h3><p>Short-term signals, episodic events, semantic facts, conceptual models, and procedures stay separated so the agent can remember aggressively without flattening everything into noise.</p></article>
<article class="card"><div class="chip">Routing</div><h3>Multi-provider fallback without dead air</h3><p>When a model is exhausted or unavailable, JEBATCore selects the next available provider path and keeps the session moving with minimal operator friction.</p></article>
<article class="card"><div class="chip">Ops</div><h3>One board for health, drift, and readiness</h3><p>The dashboard and doctor flow are aligned. You can see whether the surface is ready before you start a deep run, instead of discovering provider failure halfway through a task.</p></article>
</div>
<aside class="brief">
<h3>Operator Brief</h3>
<p>The interface is intentionally biased toward red-team cadence: concise status, visible tool readiness, fast movement into chat, and enough structure to support multi-step work without clutter.</p>
<ul>
<li>Use <strong>/webui/chat</strong> for active tasks and mode switching.</li>
<li>Use <strong>/webui/dashboard</strong> to confirm health before longer sessions.</li>
<li>Use <strong>/webui/memory</strong> to inspect what the system is retaining.</li>
</ul>
</aside>
</section>
<footer class="footer">
<div class="status">
<span><i class="dot"></i>Ultra-Think online</span>
<span><i class="dot"></i>Memory online</span>
<span><i class="dot"></i>Routing online</span>
</div>
<div>JEBATCore / Operations Surface</div>
</footer>
</div>
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
