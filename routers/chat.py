"""Chat endpoint with LLM provider failover and SSE streaming."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from jebat.llm.config import load_llm_config
from jebat.llm.providers import ProviderGeneration, generate_with_failover, generate_stream_with_failover
from jebat.llm.token_usage import usage_from_texts

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000, description="User message")
    system_prompt: str = Field(default="", description="Optional system prompt")
    session_id: str = Field(default="default", description="Session identifier for history")
    temperature: Optional[float] = Field(default=None, ge=0, le=2, description="Override temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000, description="Override max tokens")
    stream: bool = Field(default=False, description="Enable SSE streaming (ignored by /stream endpoint)")


class ChatResponse(BaseModel):
    response: str
    provider: str
    session_id: str
    usage: Dict[str, Any] = Field(default_factory=dict)


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message and receive a complete LLM response with automatic provider failover."""
    config = load_llm_config()
    if req.temperature is not None:
        config = replace(config, temperature=req.temperature)
    if req.max_tokens is not None:
        config = replace(config, max_tokens=req.max_tokens)

    response, provider = await generate_with_failover(
        config,
        prompt=req.message,
        system_prompt=req.system_prompt,
        return_metadata=True,
    )
    if isinstance(response, ProviderGeneration):
        text = response.text
        usage = response.usage.to_dict()
    else:
        text = str(response)
        usage = usage_from_texts(
            f"{req.system_prompt}\n{req.message}",
            text,
            model=config.model,
            provider=provider,
        ).to_dict()

    return ChatResponse(
        response=text,
        provider=provider,
        session_id=req.session_id,
        usage={
            **usage,
            "provider": provider,
            "model": config.model,
            "input_token_budget": max(0, config.context_window - config.max_tokens),
        },
    )


def _sse_format(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


@router.post("/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Stream LLM response token-by-token via Server-Sent Events (SSE).

    Events:
        - `metadata` — sent first, contains provider and model info
        - `token` — individual text chunks as they arrive
        - `done` — final event with provider name
        - `error` — emitted if all providers fail
    """
    config = load_llm_config()
    if req.temperature is not None:
        config = replace(config, temperature=req.temperature)
    if req.max_tokens is not None:
        config = replace(config, max_tokens=req.max_tokens)

    async def event_generator():
        try:
            async for chunk in generate_stream_with_failover(
                config,
                prompt=req.message,
                system_prompt=req.system_prompt,
            ):
                yield _sse_format(chunk)
        except Exception as exc:
            yield _sse_format({"type": "error", "message": str(exc)})
        yield "data: [DONE]\n\n"


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
        },
    )
