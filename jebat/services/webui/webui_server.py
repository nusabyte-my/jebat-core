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


@webui_router.post("/webui/api/chat")
async def chat(message: ChatMessage):
    """Process chat message with Ultra-Think"""
    try:
        from jebat.ultra_think import ThinkingMode, create_ultra_think

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
        from jebat.ultra_think import ThinkingMode, create_ultra_think

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
        from jebat.memory_system.core.memory_manager import MemoryManager

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
                    from jebat.ultra_think import ThinkingMode, create_ultra_think

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


# HTML templates (simplified for reliability)
def _home_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBAT - AI Assistant</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);color:#f8fafc;min-height:100vh}
.container{max-width:1400px;margin:0 auto;padding:20px}
.header{background:rgba(30,41,59,0.8);border-bottom:1px solid #334155;padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{width:40px;height:40px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:bold}
.nav-btn{padding:8px 16px;background:#334155;border:none;border-radius:6px;color:#f8fafc;cursor:pointer;text-decoration:none;transition:all 0.3s}
.nav-btn:hover{background:#6366f1}
.hero{text-align:center;padding:60px 20px;background:rgba(99,102,241,0.1);border-radius:20px;margin:40px auto;border:1px solid #334155}
.hero h2{font-size:42px;margin-bottom:20px;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:18px;color:#64748b;max-width:600px;margin:0 auto 30px}
.btn{padding:15px 30px;border-radius:10px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:8px;margin:5px}
.btn-primary{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border:none}
.btn-secondary{background:#334155;color:#f8fafc;border:1px solid #64748b}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;margin-top:40px}
.feature-card{background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:15px;padding:30px;transition:all 0.3s}
.feature-card:hover{transform:translateY(-5px);border-color:#6366f1}
.feature-icon{width:60px;height:60px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:20px}
.status-bar{background:rgba(30,41,59,0.8);border-top:1px solid #334155;padding:20px 0;margin-top:60px}
.status-content{display:flex;justify-content:space-between;align-items:center}
.status-item{display:flex;align-items:center;gap:8px}
.status-dot{width:10px;height:10px;border-radius:50%;background:#10b981;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
</style>
</head>
<body>
<header class="header">
<div class="logo"><div class="logo-icon">J</div><div><h2>JEBAT</h2><p style="color:#64748b;font-size:13px">AI with Eternal Memory</p></div></div>
<nav style="display:flex;gap:10px">
<a href="/webui" class="nav-btn">🏠 Home</a>
<a href="/webui/chat" class="nav-btn">💬 Chat</a>
<a href="/webui/dashboard" class="nav-btn">📊 Dashboard</a>
<a href="/webui/memory" class="nav-btn">🧠 Memory</a>
</nav>
</header>
<main class="container">
<div class="hero">
<h2>🗡️ Welcome to JEBAT</h2>
<p>Your personal AI assistant with eternal memory, ultra-reasoning, and continuous learning.</p>
<div>
<a href="/webui/chat" class="btn btn-primary">💬 Start Chatting</a>
<a href="/webui/dashboard" class="btn btn-secondary">📊 Dashboard</a>
<a href="/webui/memory" class="btn btn-secondary">🧠 Memory</a>
</div>
</div>
<div class="features">
<div class="feature-card"><div class="feature-icon">💬</div><h3>Intelligent Chat</h3><p style="color:#64748b;margin-top:10px">Deep conversations with Ultra-Think powered reasoning.</p></div>
<div class="feature-card"><div class="feature-icon">🧠</div><h3>Eternal Memory</h3><p style="color:#64748b;margin-top:10px">5-layer memory (M0-M4) with heat scoring.</p></div>
<div class="feature-card"><div class="feature-icon">🔄</div><h3>Ultra-Loop</h3><p style="color:#64748b;margin-top:10px">Continuous processing: Perception→Cognition→Memory→Action→Learning.</p></div>
<div class="feature-card"><div class="feature-icon">🤔</div><h3>Deep Reasoning</h3><p style="color:#64748b;margin-top:10px">6 thinking modes for every problem type.</p></div>
<div class="feature-card"><div class="feature-icon">📊</div><h3>Dashboard</h3><p style="color:#64748b;margin-top:10px">Real-time system health monitoring.</p></div>
<div class="feature-card"><div class="feature-icon">🔌</div><h3>Multi-Channel</h3><p style="color:#64748b;margin-top:10px">WebSocket, WhatsApp, Telegram, Discord & more.</p></div>
</div>
</main>
<footer class="status-bar"><div class="container status-content">
<div class="status-item"><div class="status-dot"></div><span>Ultra-Loop: Operational</span></div>
<div class="status-item"><div class="status-dot"></div><span>Ultra-Think: Operational</span></div>
<div class="status-item"><div class="status-dot"></div><span>Memory: Operational</span></div>
<div style="color:#64748b">🗡️ JEBAT v1.0.0</div>
</div></footer>
</body>
</html>"""


def _chat_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEBAT Chat</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);color:#f8fafc;height:100vh;display:flex;flex-direction:column}
.header{background:rgba(30,41,59,0.8);border-bottom:1px solid #334155;padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{width:40px;height:40px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:bold}
.nav-btn{padding:8px 16px;background:#334155;border:none;border-radius:6px;color:#f8fafc;cursor:pointer;text-decoration:none}
.chat-container{flex:1;display:flex;overflow:hidden}
.sidebar{width:280px;background:rgba(30,41,59,0.5);border-right:1px solid #334155;padding:20px;overflow-y:auto}
.mode-select{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.mode-btn{padding:8px 12px;background:#334155;border:1px solid transparent;border-radius:6px;color:#f8fafc;cursor:pointer;font-size:13px}
.mode-btn:hover{border-color:#6366f1}
.mode-btn.active{background:#6366f1;border-color:#6366f1}
.chat-main{flex:1;display:flex;flex-direction:column}
.messages{flex:1;overflow-y:auto;padding:20px}
.message{margin-bottom:20px;display:flex;gap:15px}
.message.user{flex-direction:row-reverse}
.avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-weight:bold;flex-shrink:0}
.content{max-width:70%}
.bubble{background:#334155;padding:15px 20px;border-radius:15px;margin-bottom:8px}
.user .bubble{background:#6366f1}
.meta{display:flex;gap:15px;font-size:12px;color:#64748b}
.steps{background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:10px;padding:15px;margin-top:10px}
.steps h4{font-size:14px;margin-bottom:10px;color:#6366f1}
.step{display:flex;align-items:flex-start;gap:10px;margin-bottom:8px;font-size:13px}
.step-num{width:20px;height:20px;background:#6366f1;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;flex-shrink:0}
.input-area{background:rgba(30,41,59,0.8);border-top:1px solid #334155;padding:20px}
.input-container{display:flex;gap:10px}
.input-container input{flex:1;padding:15px 20px;background:#334155;border:1px solid transparent;border-radius:10px;color:#f8fafc;font-size:15px}
.input-container input:focus{outline:none;border-color:#6366f1}
.send-btn{padding:15px 30px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;color:white;font-weight:600;cursor:pointer}
.send-btn:disabled{opacity:0.5}
.typing{display:none;padding:15px 20px;background:#334155;border-radius:15px;width:fit-content}
.typing.show{display:block}
.dots{display:flex;gap:5px}
.dot{width:8px;height:8px;background:#64748b;border-radius:50%;animation:typing 1.4s infinite}
.dot:nth-child(2){animation-delay:0.2s}
.dot:nth-child(3){animation-delay:0.4s}
@keyframes typing{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-10px)}}
</style>
</head>
<body>
<header class="header">
<div class="logo"><div class="logo-icon">J</div><h2>JEBAT Chat</h2></div>
<a href="/webui" class="nav-btn">← Back</a>
</header>
<div class="chat-container">
<aside class="sidebar">
<label style="color:#64748b;font-size:14px;display:block;margin-bottom:10px">THINKING MODE</label>
<div class="mode-select">
<button class="mode-btn" data-mode="fast">⚡ Fast</button>
<button class="mode-btn active" data-mode="deliberate">🤔 Deliberate</button>
<button class="mode-btn" data-mode="deep">🧠 Deep</button>
<button class="mode-btn" data-mode="strategic">📈 Strategic</button>
<button class="mode-btn" data-mode="creative">🎨 Creative</button>
<button class="mode-btn" data-mode="critical">🔍 Critical</button>
</div>
<div style="margin-top:30px">
<label style="color:#64748b;font-size:14px;display:block;margin-bottom:10px">INFO</label>
<p style="color:#64748b;font-size:13px;line-height:1.6">JEBAT uses Ultra-Think to analyze messages with chain-of-thought reasoning.</p>
</div>
</aside>
<main class="chat-main">
<div class="messages" id="messages">
<div class="message">
<div class="avatar">J</div>
<div class="content">
<div class="bubble">Hello! I'm JEBAT. How can I help you today?</div>
<div class="meta"><span>Just now</span></div>
</div>
</div>
</div>
<div class="typing" id="typing"><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>
<div class="input-area">
<div class="input-container">
<input type="text" id="input" placeholder="Type your message..." autocomplete="off">
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
stepsHtml='<div class="steps"><h4>🧠 Reasoning</h4>'+meta.reasoning.map((s,i)=>'<div class="step"><div class="step-num">'+(i+1)+'</div><div>'+s+'</div></div>').join('')+'</div>';
}
div.innerHTML='<div class="avatar">'+(role==='user'?'U':'J')+'</div><div class="content"><div class="bubble">'+content+'</div>'+stepsHtml+'<div class="meta">'+metaHtml+'</div></div>';
document.getElementById('messages').appendChild(div);
document.getElementById('messages').scrollTop=div.scrollHeight;
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
<title>JEBAT Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);color:#f8fafc;min-height:100vh}
.container{max-width:1400px;margin:0 auto;padding:20px}
.header{background:rgba(30,41,59,0.8);border-bottom:1px solid #334155;padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{width:40px;height:40px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:bold}
.nav-btn{padding:8px 16px;background:#334155;border:none;border-radius:6px;color:#f8fafc;cursor:pointer;text-decoration:none}
.dashboard{padding:40px 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}
.stat{background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:15px;padding:25px}
.stat h3{color:#64748b;font-size:14px;margin-bottom:10px}
.stat-value{font-size:36px;font-weight:700;margin-bottom:5px}
.stat-label{color:#64748b;font-size:13px}
.components{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.component{background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:15px;padding:25px}
.comp-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
.badge{padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600;background:rgba(16,185,129,0.2);color:#10b981}
</style>
</head>
<body>
<header class="header">
<div class="logo"><div class="logo-icon">J</div><h2>JEBAT Dashboard</h2></div>
<a href="/webui" class="nav-btn">← Back</a>
</header>
<main class="dashboard">
<div class="container">
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
<title>JEBAT Memory</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);color:#f8fafc;min-height:100vh}
.container{max-width:1400px;margin:0 auto;padding:20px}
.header{background:rgba(30,41,59,0.8);border-bottom:1px solid #334155;padding:15px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{width:40px;height:40px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:bold}
.nav-btn{padding:8px 16px;background:#334155;border:none;border-radius:6px;color:#f8fafc;cursor:pointer;text-decoration:none}
.explorer{padding:40px 0}
.search{display:flex;gap:10px;margin-bottom:30px}
.search input{flex:1;padding:15px 20px;background:#334155;border:1px solid transparent;border-radius:10px;color:#f8fafc;font-size:15px}
.search input:focus{outline:none;border-color:#6366f1}
.search-btn{padding:15px 30px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:10px;color:white;font-weight:600;cursor:pointer}
.layers{display:grid;gap:20px}
.layer{background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:15px;padding:25px}
.layer-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
.layer-name{font-size:20px;font-weight:600}
.layer-desc{color:#64748b;font-size:13px;margin-top:5px}
</style>
</head>
<body>
<header class="header">
<div class="logo"><div class="logo-icon">J</div><h2>Memory Explorer</h2></div>
<a href="/webui" class="nav-btn">← Back</a>
</header>
<main class="explorer">
<div class="container">
<div class="search">
<input type="text" id="query" placeholder="Search memories...">
<button class="search-btn" onclick="search()">🔍 Search</button>
</div>
<div class="layers">
<div class="layer"><div class="layer-header"><div><div class="layer-name">🔴 M0 - Sensory Memory</div><div class="layer-desc">0-30 seconds buffer</div></div></div><p style="color:#64748b">Immediate sensory information processing</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">🟠 M1 - Episodic Memory</div><div class="layer-desc">Minutes to hours</div></div></div><p style="color:#64748b">Recent conversations and events</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">🟡 M2 - Semantic Memory</div><div class="layer-desc">Days to weeks</div></div></div><p style="color:#64748b">Facts and conceptual knowledge</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">🟢 M3 - Conceptual Memory</div><div class="layer-desc">Permanent</div></div></div><p style="color:#64748b">Deep understanding and mental models</p></div>
<div class="layer"><div class="layer-header"><div><div class="layer-name">🔵 M4 - Procedural Memory</div><div class="layer-desc">Permanent</div></div></div><p style="color:#64748b">Skills and automated processes</p></div>
</div>
</div>
</main>
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
