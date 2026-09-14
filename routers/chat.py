"""Chat endpoint with LLM provider failover and SSE streaming."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from typing import Any, Dict, List, Optional
from uuid import uuid4
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


class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: Optional[str] = "jebat-pro"
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class OpenAIChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]
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


@router.post("/completions", response_model=OpenAIChatResponse)
async def openai_chat_completion(request: OpenAIChatRequest) -> Any:
    """OpenAI-compatible chat completions endpoint (supports Zed, Cursor, OpenCode, SDKs)."""
    config = load_llm_config()
    if request.temperature is not None:
        config = replace(config, temperature=request.temperature)
    if request.max_tokens is not None:
        config = replace(config, max_tokens=request.max_tokens)
    if request.model and request.model not in {"default", "jebat-pro", ""}:
        config = replace(config, model=request.model)

    user_messages = [m for m in request.messages if m.role == "user"]
    prompt = user_messages[-1].content if user_messages else "Hello"

    system_messages = [m for m in request.messages if m.role == "system"]
    system_prompt = "\n".join(m.content for m in system_messages) if system_messages else ""

    if len(request.messages) > 1:
        history_lines = [
            f"{msg.role.upper()}: {msg.content}"
            for msg in request.messages[:-1]
            if msg.role != "system"
        ]
        if history_lines:
            prompt = "Previous conversation:\n" + "\n".join(history_lines) + f"\n\nLatest User Request: {prompt}"

    if request.stream:
        async def openai_stream_generator():
            cmpl_id = f"chatcmpl-{uuid4().hex[:12]}"
            created = int(time.time())
            try:
                async for chunk in generate_stream_with_failover(
                    config, prompt=prompt, system_prompt=system_prompt
                ):
                    if chunk.get("type") == "token" and chunk.get("text"):
                        token_payload = {
                            "id": cmpl_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": config.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": chunk["text"]},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        yield f"data: {json.dumps(token_payload)}\n\n"
            except Exception as exc:
                err_payload = {"error": str(exc)}
                yield f"data: {json.dumps(err_payload)}\n\n"

            stop_payload = {
                "id": cmpl_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": config.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"data: {json.dumps(stop_payload)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            openai_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    response, provider = await generate_with_failover(
        config,
        prompt=prompt,
        system_prompt=system_prompt,
        return_metadata=True,
    )
    if isinstance(response, ProviderGeneration):
        text = response.text
        usage = response.usage.to_dict()
    else:
        text = str(response)
        usage = usage_from_texts(f"{system_prompt}\n{prompt}", text, model=config.model, provider=provider).to_dict()

    return OpenAIChatResponse(
        id=f"chatcmpl-{uuid4().hex[:12]}",
        created=int(time.time()),
        model=config.model,
        choices=[
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    )


async def list_openai_models() -> Dict[str, Any]:
    """List OpenAI-compatible models."""
    config = load_llm_config()
    return {
        "object": "list",
        "data": [
            {"id": "jebat-pro", "object": "model", "owned_by": "jebat"},
            {"id": "jebat-llm.gguf", "object": "model", "owned_by": "llamacpp"},
            {"id": "qwen2.5-coder:7b", "object": "model", "owned_by": "ollama"},
            {"id": config.model, "object": "model", "owned_by": config.provider},
        ],
    }
