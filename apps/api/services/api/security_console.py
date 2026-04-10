from __future__ import annotations

import json
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from apps.api.features.security_console.service import get_security_console_service
from apps.api.features.security_console.models import (
    CommandRun,
    CopilotChatRequest,
    CopilotChatResponse,
    CreateFindingRequest,
    CreateRunRequest,
    CreateSessionRequest,
    CreateTargetRequest,
    ExecuteCommandRequest,
    Finding,
    SecurityConsoleSnapshot,
    SecuritySession,
    Target,
)

router = APIRouter(prefix="/api/v1/security", tags=["Security Console"])
service = get_security_console_service()
session_connections: dict[str, set[WebSocket]] = defaultdict(set)


def _session_payload(session_id: str) -> dict[str, object]:
    session = service.get_session(session_id)
    if session is None:
        raise KeyError(f"unknown session: {session_id}")
    return {
        "type": "session_state",
        "session": session.model_dump(mode="json"),
        "runs": [run.model_dump(mode="json") for run in service.list_runs(session_id)],
        "findings": [finding.model_dump(mode="json") for finding in service.list_findings(session_id)],
    }


async def _broadcast_session_state(session_id: str) -> None:
    if session_id not in session_connections or not session_connections[session_id]:
        return
    payload = json.dumps(_session_payload(session_id))
    stale: list[WebSocket] = []
    for websocket in session_connections[session_id]:
        try:
            await websocket.send_text(payload)
        except Exception:
            stale.append(websocket)
    for websocket in stale:
        session_connections[session_id].discard(websocket)


@router.get("/snapshot", response_model=SecurityConsoleSnapshot)
async def get_snapshot() -> SecurityConsoleSnapshot:
    return service.snapshot()


@router.get("/summary")
async def get_summary() -> dict[str, object]:
    return service.summary()


@router.get("/targets", response_model=list[Target])
async def list_targets() -> list[Target]:
    return service.list_targets()


@router.post("/targets", response_model=Target, status_code=status.HTTP_201_CREATED)
async def create_target(request: CreateTargetRequest) -> Target:
    return service.create_target(request)


@router.get("/sessions", response_model=list[SecuritySession])
async def list_sessions(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    query: str | None = None,
) -> list[SecuritySession]:
    return service.list_sessions(status=status_filter, query=query)


@router.post("/sessions", response_model=SecuritySession, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest) -> SecuritySession:
    try:
        return service.create_session(request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_model=SecuritySession)
async def get_session(session_id: str) -> SecuritySession:
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return session


@router.websocket("/sessions/{session_id}/ws")
async def session_ws(websocket: WebSocket, session_id: str) -> None:
    if service.get_session(session_id) is None:
        await websocket.close(code=1008, reason="session not found")
        return
    await websocket.accept()
    session_connections[session_id].add(websocket)
    try:
        await websocket.send_json(_session_payload(session_id))
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong", "session_id": session_id})
    except WebSocketDisconnect:
        session_connections[session_id].discard(websocket)
    except Exception:
        session_connections[session_id].discard(websocket)
        await websocket.close()


@router.get("/sessions/{session_id}/findings", response_model=list[Finding])
async def list_findings(
    session_id: str,
    severity: str | None = None,
    source_tool: Annotated[str | None, Query(alias="tool")] = None,
    query: str | None = None,
) -> list[Finding]:
    try:
        return service.list_findings(session_id, severity=severity, source_tool=source_tool, query=query)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/runs", response_model=list[CommandRun])
async def list_runs(
    session_id: str,
    tool: str | None = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[CommandRun]:
    try:
        return service.list_runs(session_id, tool=tool, status=status_filter)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/findings", response_model=list[Finding])
async def list_all_findings(
    severity: str | None = None,
    source_tool: Annotated[str | None, Query(alias="tool")] = None,
    query: str | None = None,
) -> list[Finding]:
    return service.list_all_findings(severity=severity, source_tool=source_tool, query=query)


@router.post(
    "/sessions/{session_id}/findings",
    response_model=Finding,
    status_code=status.HTTP_201_CREATED,
)
async def create_finding(session_id: str, request: CreateFindingRequest) -> Finding:
    try:
        finding = service.create_finding(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await _broadcast_session_state(session_id)
    return finding


@router.post("/sessions/{session_id}/runs", status_code=status.HTTP_201_CREATED)
async def create_run(session_id: str, request: CreateRunRequest) -> dict[str, object]:
    try:
        run = service.create_run(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await _broadcast_session_state(session_id)
    return {"run": run, "runs": service.list_runs(session_id)}


@router.post("/sessions/{session_id}/execute", status_code=status.HTTP_201_CREATED)
async def execute_command(session_id: str, request: ExecuteCommandRequest) -> dict[str, object]:
    try:
        run = service.execute_command(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await _broadcast_session_state(session_id)
    return {
        "run": run,
        "runs": service.list_runs(session_id),
        "findings": service.list_findings(session_id),
    }


@router.post("/sessions/{session_id}/copilot/chat", response_model=CopilotChatResponse)
async def security_copilot_chat(
    session_id: str,
    request: CopilotChatRequest,
) -> CopilotChatResponse:
    try:
        response = await service.chat(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await _broadcast_session_state(session_id)
    return response
