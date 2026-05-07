"""
JEBAT LLM tool-calling core.

Provider-agnostic tool loop:
1. Inject available tool schemas into the system prompt.
2. Ask the LLM to either answer normally or return JSON:
   {"tool": "web_search", "arguments": {"query": "..."}}
3. Execute the tool.
4. Feed tool result back to the LLM for final answer.

This intentionally works with every provider, including local/Ollama models that do
not reliably support native function calling.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .config import JebatLLMConfig

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[str]]


@dataclass
class ToolCallResult:
    tool_name: str
    arguments: dict[str, Any]
    result: str = ""
    error: str = ""


class ToolRegistry:
    """Registry of executable tools available to an LLM."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def register_defaults(self) -> None:
        self.register(ToolDefinition(
            name="web_search",
            description="Search the web for current information or unknown facts.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5},
                },
                "required": ["query"],
            },
            handler=_web_search_handler,
        ))
        self.register(ToolDefinition(
            name="web_fetch",
            description="Fetch and read the text content of a specific URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "max_length": {"type": "integer", "description": "Maximum extracted text length", "default": 20000},
                },
                "required": ["url"],
            },
            handler=_web_fetch_handler,
        ))

    def prompt_block(self) -> str:
        if not self._tools:
            return ""
        lines = [
            "You may use tools when needed.",
            "If you need a tool, respond ONLY with valid JSON in this exact shape:",
            '{"tool": "tool_name", "arguments": {"param": "value"}}',
            "If no tool is needed, answer normally.",
            "",
            "Available tools:",
        ]
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
            lines.append(f"  schema: {json.dumps(tool.parameters, ensure_ascii=False)}")
        return "\n".join(lines)

    def to_openai_schema(self) -> list[dict[str, Any]]:
        """Return OpenAI/OpenRouter-compatible chat-completions tool schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def to_anthropic_schema(self) -> list[dict[str, Any]]:
        """Return Anthropic Messages API-compatible tool schemas."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in self._tools.values()
        ]

    def to_ollama_schema(self) -> list[dict[str, Any]]:
        """Return Ollama chat-compatible tool schemas."""
        return self.to_openai_schema()

    def to_google_schema(self) -> list[dict[str, Any]]:
        """Return Gemini function-calling compatible tool schemas.

        Gemini expects::

            [{"function_declarations": [{"name": ..., "description": ..., "parameters": {...}}]}]
        """
        declarations = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self._tools.values()
        ]
        return [{"function_declarations": declarations}]


async def _web_search_handler(**kwargs: Any) -> str:
    from ..skills.web_search import WebSearchSkill
    skill = WebSearchSkill()
    result = await skill.execute(
        query=str(kwargs.get("query", "")),
        limit=int(kwargs.get("limit", 5)),
    )
    if not result.success:
        return f"Search failed: {result.error}"
    if not result.results:
        return "No search results found."
    return "\n\n".join(
        f"Title: {item.get('title', '')}\nURL: {item.get('url', '')}\nSnippet: {item.get('snippet', '')}"
        for item in result.results
    )


async def _web_fetch_handler(**kwargs: Any) -> str:
    from ..skills.web_fetch import WebFetchSkill
    skill = WebFetchSkill()
    result = await skill.execute(
        url=str(kwargs.get("url", "")),
        max_length=int(kwargs.get("max_length", 20000)),
    )
    if not result.success:
        return f"Fetch failed: {result.error}"
    title = f"Title: {result.title}\n" if result.title else ""
    return f"{title}URL: {result.url}\n\n{result.text}"


def parse_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    """Extract a tool call JSON object from LLM text."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()
    match = re.search(r"\{\s*\"tool\"\s*:\s*\"[^\"]+\".*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    tool = data.get("tool")
    args = data.get("arguments", {})
    if isinstance(tool, str) and isinstance(args, dict):
        return tool, args
    return None


async def execute_tool_call(
    registry: ToolRegistry,
    tool_name: str,
    arguments: dict[str, Any],
) -> ToolCallResult:
    tool = registry.get(tool_name)
    if not tool:
        return ToolCallResult(tool_name, arguments, error=f"Unknown tool: {tool_name}")
    try:
        output = await tool.handler(**arguments)
        return ToolCallResult(tool_name, arguments, result=output)
    except Exception as exc:
        logger.exception("Tool call failed: %s", tool_name)
        return ToolCallResult(tool_name, arguments, error=str(exc))


async def generate_with_tools(
    config: JebatLLMConfig,
    prompt: str,
    system_prompt: str | None = None,
    tool_registry: ToolRegistry | None = None,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> tuple[str, str, list[ToolCallResult]]:
    """Generate response with optional tool execution loop.

    Prefers native function-calling for providers that support it
    (OpenRouter, Ollama, Anthropic).  Falls back to prompt-injection
    for all other providers (Google, OpenAI Responses API, local).

    Returns (final_text, provider_name, list_of_tool_results).
    """
    from .providers import (  # lazy to avoid httpx at import time
        generate_with_failover,
        generate_with_native_tools,
        supports_native_tools,
    )

    registry = tool_registry or ToolRegistry()
    if not registry.list_tools():
        text, provider = await generate_with_failover(config, prompt, system_prompt)
        return text, provider, []

    base_system = (system_prompt or "You are JEBAT.").strip()
    use_native = supports_native_tools(config.provider)

    # Choose the right schema format for native calling
    if use_native:
        provider_lower = config.provider.lower()
        if provider_lower == "anthropic":
            native_schema = registry.to_anthropic_schema()
        elif provider_lower == "google":
            native_schema = registry.to_google_schema()
        else:
            # OpenAI, OpenRouter, Ollama all use OpenAI-compatible format
            native_schema = registry.to_openai_schema()
    else:
        native_schema = None

    conversation_prompt = prompt
    tool_results: list[ToolCallResult] = []
    provider_used = config.provider

    for _ in range(max_rounds):
        if use_native and native_schema:
            # ── Native tool-calling path ────────────────────────────
            text, tool_calls, provider_used = await generate_with_native_tools(
                config, conversation_prompt, base_system, native_schema,
            )
            if tool_calls:
                # Provider returned structured tool calls
                for tc in tool_calls:
                    result = await execute_tool_call(registry, tc["name"], tc["arguments"])
                    tool_results.append(result)
                # Feed results back for next round
                tool_output_parts = []
                for tr in tool_results:
                    out = tr.result if tr.result else f"ERROR: {tr.error}"
                    tool_output_parts.append(f"Tool `{tr.tool_name}` returned:\n{out}")
                conversation_prompt = (
                    f"Original user request:\n{prompt}\n\n"
                    + "\n\n".join(tool_output_parts)
                    + "\n\nUse these tool results to answer the original request directly. "
                    "If another tool is absolutely required, call it."
                )
                continue
            # No tool calls — text is the final answer
            if text:
                return text, provider_used, tool_results
            # Empty text and no tool calls — fall through to prompt-injection
            use_native = False

        # ── Prompt-injection fallback path ──────────────────────────
        tool_system = f"{base_system}\n\n{registry.prompt_block()}"
        text, provider_used = await generate_with_failover(config, conversation_prompt, tool_system)
        call = parse_tool_call(text)
        if not call:
            return text, provider_used, tool_results

        tool_name, args = call
        result = await execute_tool_call(registry, tool_name, args)
        tool_results.append(result)
        tool_output = result.result if result.result else f"ERROR: {result.error}"
        conversation_prompt = (
            f"Original user request:\n{prompt}\n\n"
            f"Tool `{tool_name}` returned:\n{tool_output}\n\n"
            "Use this tool result to answer the original request directly. "
            "If another tool is absolutely required, return another tool JSON call."
        )

    # Max rounds exhausted — ask for final answer
    final_text, provider_used = await generate_with_failover(
        config,
        f"Original user request:\n{prompt}\n\nTool results:\n"
        + "\n\n".join(r.result or r.error for r in tool_results)
        + "\n\nProvide the final answer.",
        base_system,
    )
    return final_text, provider_used, tool_results


__all__ = [
    "ToolDefinition",
    "ToolCallResult",
    "ToolRegistry",
    "parse_tool_call",
    "execute_tool_call",
    "generate_with_tools",
]
