"""Minimal authenticated A2A 1.0 adapter for deployed Agentix solutions."""
from __future__ import annotations

import asyncio
import hmac
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field


class A2APart(BaseModel):
    text: str


class A2AMessage(BaseModel):
    role: str = "user"
    parts: list[A2APart]


class A2ARequest(BaseModel):
    message: A2AMessage
    configuration: Dict[str, Any] = Field(default_factory=dict)


def create_a2a_router(solution: str, *, token: Optional[str] = None) -> APIRouter:
    """Opt-in adapter. Token is required for non-loopback deployment."""
    token = token if token is not None else os.environ.get("JEBAT_A2A_TOKEN", "")
    if not token:
        raise RuntimeError("A2A adapter requires JEBAT_A2A_TOKEN or explicit token")
    router = APIRouter(prefix="/a2a")
    tasks: Dict[str, Dict[str, Any]] = {}
    lock = threading.Lock()

    def authorize(authorization: Optional[str]):
        expected = f"Bearer {token}"
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="invalid A2A bearer token")

    def get_state(task_id: str) -> Dict[str, Any]:
        with lock:
            if task_id not in tasks:
                raise HTTPException(status_code=404, detail="task not found")
            return dict(tasks[task_id])

    @router.get("/.well-known/agent-card.json")
    async def agent_card():
        return {
            "name": f"JEBAT Agentix: {solution}", "version": "1.0.0",
            "protocolVersions": ["1.0.0"], "capabilities": {"streaming": False},
            "skills": [{"id": solution, "name": solution, "description": "Deployed Agentix solution"}],
        }

    @router.post("/tasks")
    async def send_message(request: A2ARequest, authorization: Optional[str] = Header(None)):
        authorize(authorization)
        text = "\n".join(part.text for part in request.message.parts).strip()
        if not text:
            raise HTTPException(status_code=400, detail="message contains no text")
        task_id = str(uuid.uuid4())
        with lock:
            tasks[task_id] = {"id": task_id, "status": {"state": "submitted", "timestamp": time.time()}, "artifacts": []}
        async def execute():
            from jebat_cli_new.agentix import _resolve_solution, _run_solution
            try:
                answer, info = await asyncio.to_thread(_run_solution, _resolve_solution(solution), text)
                with lock:
                    tasks[task_id]["status"] = {"state": "completed", "timestamp": time.time()}
                    tasks[task_id]["artifacts"] = [{"parts": [{"text": answer}]}]
                    tasks[task_id]["metadata"] = {"run_id": info.get("run_id"), "provider": info.get("provider"), "model": info.get("model")}
            except Exception as exc:
                with lock:
                    tasks[task_id]["status"] = {"state": "failed", "timestamp": time.time(), "message": str(exc)}
        asyncio.create_task(execute())
        return get_state(task_id)

    @router.get("/tasks/{task_id}")
    async def get_task(task_id: str, authorization: Optional[str] = Header(None)):
        authorize(authorization)
        return get_state(task_id)

    @router.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str, authorization: Optional[str] = Header(None)):
        authorize(authorization)
        with lock:
            state = get_state(task_id)
            if state["status"]["state"] in {"completed", "failed", "canceled"}:
                return state
            tasks[task_id]["status"] = {"state": "canceled", "timestamp": time.time()}
            return dict(tasks[task_id])

    return router
