"""
JEBAT Subagent Delegation System — CLI-level child agent spawning and management.

This module provides the DelegationManager for spawning isolated subagent processes
that run independently with their own conversation context, filtered toolsets, and
timeout enforcement. It also registers a `delegate_task` tool (confirm tier) so the
parent agent can delegate work through the standard tool interface.

Architecture:
  - SubagentConfig: defines what a subagent should do and what it can use
  - SubagentResult: condensed summary returned to the parent (not full conversation)
  - DelegationManager: orchestrates spawn_subagent / spawn_parallel with semaphores
  - delegate_task tool: registered via @register_tool for parent agent invocation

The subagent runs an isolated AgentLoop (from jebat.core.agent_loop) with a filtered
subset of TOOL_REGISTRY tools and a dedicated system prompt.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from jebat.config import load_config
from jebat.tools import TOOL_REGISTRY, ToolDef, register_tool

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────


@dataclass
class SubagentConfig:
    """Configuration for a single subagent task.

    Attributes:
        goal: What the subagent should accomplish (clear, specific instruction).
        context: Background information the subagent needs (project state, constraints).
        toolsets: List of tool name prefixes/categories the subagent may use.
                   Empty list means all registered tools are available.
        model: LLM model override for this subagent (empty = use default from config).
        provider: LLM provider override for this subagent (empty = use default from config).
        max_iterations: Maximum agent loop iterations before forced termination.
        timeout: Maximum wall-clock seconds before the subagent is killed.
    """

    goal: str
    context: str = ""
    toolsets: list[str] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    max_iterations: int = 10
    timeout: int = 120


@dataclass
class SubagentResult:
    """Condensed result from a subagent — summary, not full conversation.

    Attributes:
        summary: Human-readable result summary (what was accomplished, findings).
        success: Whether the subagent completed its goal satisfactorily.
        tool_calls_made: List of dicts with tool_name, params_summary for each call.
        tokens_used: Dict with prompt/completion/total token counts if available.
        error: Error message if the subagent failed or timed out (None on success).
    """

    summary: str
    success: bool
    tool_calls_made: list[dict[str, Any]] = field(default_factory=list)
    tokens_used: dict[str, int] = field(default_factory=dict)
    error: str | None = None


# ── Delegation Manager ───────────────────────────────────────────────────


class DelegationManager:
    """
    Manage subagent delegation — spawn isolated agent loops and return summaries.

    The DelegationManager creates isolated AgentLoop instances with filtered toolsets,
    dedicated system prompts, and timeout enforcement. It supports both single and
    parallel subagent spawning.
    """

    def __init__(self) -> None:
        self._config = load_config()
        self._active_subagents: dict[str, asyncio.Task] = {}

    # ── Public API ────────────────────────────────────────────────────────

    async def spawn_subagent(self, config: SubagentConfig) -> SubagentResult:
        """Spawn a single subagent with an isolated agent loop.

        Creates a filtered toolset, builds a subagent system prompt, runs an
        AgentLoop in isolation, and condenses the result into a SubagentResult.

        Args:
            config: SubagentConfig defining the task, tools, model, and limits.

        Returns:
            SubagentResult with summary, success flag, tool calls, tokens, and
            any error information.
        """
        subagent_id = str(uuid4())
        logger.info(
            "Spawning subagent %s: goal='%s' timeout=%s max_iter=%s",
            subagent_id,
            config.goal[:80],
            config.timeout,
            config.max_iterations,
        )

        allowed_tools = self._create_isolated_toolset(config.toolsets)
        system_prompt = self._build_subagent_system_prompt(
            goal=config.goal,
            context=config.context,
            allowed_tools=allowed_tools,
        )

        # Resolve model/provider — fall back to global config if not specified
        model = config.model or self._config.get("model.model", "gpt-4o")
        provider = config.provider or self._config.get("model.provider", "openai")

        try:
            result = await asyncio.wait_for(
                self._run_isolated_loop(
                    subagent_id=subagent_id,
                    system_prompt=system_prompt,
                    goal=config.goal,
                    allowed_tools=allowed_tools,
                    model=model,
                    provider=provider,
                    max_iterations=config.max_iterations,
                ),
                timeout=config.timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Subagent %s timed out after %ss", subagent_id, config.timeout)
            # Cancel the underlying task if still running
            task = self._active_subagents.pop(subagent_id, None)
            if task and not task.done():
                task.cancel()
            return SubagentResult(
                summary=f"Subagent timed out after {config.timeout}s. Goal: {config.goal[:120]}",
                success=False,
                error=f"TimeoutError: exceeded {config.timeout}s limit",
            )
        except Exception as exc:
            logger.exception("Subagent %s failed with exception", subagent_id)
            return SubagentResult(
                summary=f"Subagent failed: {exc}",
                success=False,
                error=str(exc),
            )
        finally:
            self._active_subagents.pop(subagent_id, None)

        return self._summarize_result(result)

    async def spawn_parallel(
        self,
        configs: list[SubagentConfig],
        max_concurrent: int = 3,
    ) -> list[SubagentResult]:
        """Spawn multiple subagents concurrently with a semaphore for throttling.

        Args:
            configs: List of SubagentConfig for each subagent to spawn.
            max_concurrent: Maximum number of subagents running simultaneously.
                            Defaults to 3 to avoid resource exhaustion.

        Returns:
            List of SubagentResult, one per config, in the same order as configs.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results: list[SubagentResult | None] = [None] * len(configs)

        async def _spawn_with_semaphore(index: int, cfg: SubagentConfig) -> None:
            async with semaphore:
                results[index] = await self.spawn_subagent(cfg)

        tasks = [
            asyncio.create_task(_spawn_with_semaphore(i, cfg))
            for i, cfg in enumerate(configs)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Replace any None slots (gather swallowed an exception) with error results
        final: list[SubagentResult] = []
        for i, r in enumerate(results):
            if r is None:
                final.append(
                    SubagentResult(
                        summary=f"Subagent {i} failed unexpectedly",
                        success=False,
                        error="Unknown error during parallel execution",
                    )
                )
            else:
                final.append(r)

        return final

    # ── Internal Methods ──────────────────────────────────────────────────

    def _create_isolated_toolset(self, toolset_names: list[str]) -> dict[str, ToolDef]:
        """Filter TOOL_REGISTRY to only allow the specified tool categories/names.

        If toolset_names is empty, all tools are available (full registry).
        If toolset_names contains specific tool names, only those tools are included.
        If toolset_names contains prefixes (e.g. 'file_' ), all tools starting with
        that prefix are included.

        The delegate_task tool is always excluded from subagent toolsets to prevent
        recursive delegation.
        """
        if not toolset_names:
            # All tools except delegate_task (prevent recursive delegation)
            return {
                name: td
                for name, td in TOOL_REGISTRY.items()
                if name != "delegate_task"
            }

        filtered: dict[str, ToolDef] = {}
        for name, td in TOOL_REGISTRY.items():
            # Skip delegate_task to prevent recursive subagent spawning
            if name == "delegate_task":
                continue
            # Exact match or prefix match
            for pattern in toolset_names:
                if name == pattern or name.startswith(pattern.rstrip("_") + "_"):
                    filtered[name] = td
                    break

        return filtered

    def _build_subagent_system_prompt(
        self,
        goal: str,
        context: str,
        allowed_tools: dict[str, ToolDef],
    ) -> str:
        """Build a dedicated system prompt for the subagent.

        The prompt frames the subagent as a focused, goal-oriented worker that:
        - Has a specific task to complete
        - Has limited tools available
        - Should return a concise summary when done
        - Should not ask questions or wait for user input
        """
        tool_descriptions = "\n".join(
            f"  - {name}: {td.description or '(no description)'}"
            for name, td in sorted(allowed_tools.items())
        )
        if not tool_descriptions:
            tool_descriptions = "  (no tools available)"

        prompt_parts = [
            "You are a JEBAT subagent — a focused worker executing a specific delegated task.",
            "",
            "## Your Goal",
            goal,
            "",
        ]

        if context:
            prompt_parts.extend([
                "## Context",
                context,
                "",
            ])

        prompt_parts.extend([
            "## Available Tools",
            tool_descriptions,
            "",
            "## Rules",
            "1. Complete the task independently — do not ask the user for clarification.",
            "2. Use only the tools listed above. Do not attempt to use tools not in the list.",
            "3. When finished, provide a concise summary of what you accomplished.",
            "4. If you cannot complete the task, explain why clearly and concisely.",
            "5. Be efficient — avoid unnecessary iterations or redundant tool calls.",
            "6. Never attempt to spawn further subagents (delegate_task is not available).",
            "",
            "## Output Format",
            "When done, output your final result as a clear summary section marked:",
            "### SUBAGENT RESULT",
            "Followed by a brief summary of findings, actions taken, and any recommendations.",
        ])

        return "\n".join(prompt_parts)

    async def _run_isolated_loop(
        self,
        subagent_id: str,
        system_prompt: str,
        goal: str,
        allowed_tools: dict[str, ToolDef],
        model: str,
        provider: str,
        max_iterations: int,
    ) -> dict[str, Any]:
        """Run an isolated AgentLoop for the subagent.

        This method attempts to import and use AgentLoop from jebat.core.agent_loop.
        If agent_loop is not yet available, it falls back to a direct LLM call
        pattern so the delegation system can still function.

        Returns a dict with keys: response, tool_calls, tokens, iterations, success.
        """
        # Track tool calls made during execution
        tool_calls_log: list[dict[str, Any]] = []
        tokens_accumulated: dict[str, int] = {"prompt": 0, "completion": 0, "total": 0}
        iterations_used = 0
        final_response = ""

        try:
            # Import AgentLoop — this module may not exist yet during early build
            from jebat.core.agent_loop import AgentLoop, AgentResult  # type: ignore[import-untyped]

            # Create isolated tool registry for the subagent
            isolated_registry = dict(allowed_tools)

            loop = AgentLoop(
                system_prompt=system_prompt,
                model=model,
                provider=provider,
                max_iterations=max_iterations,
                tool_registry=isolated_registry,
            )

            # Run the loop and capture the task as an asyncio.Task for cancellation
            task = asyncio.create_task(loop.run(goal))
            self._active_subagents[subagent_id] = task
            agent_result: AgentResult = await task

            # Extract data from AgentResult
            final_response = getattr(agent_result, "response", str(agent_result))
            tool_calls_log = getattr(agent_result, "tool_calls", [])
            tokens_accumulated = getattr(agent_result, "tokens_used", tokens_accumulated)
            iterations_used = getattr(agent_result, "iterations", max_iterations)
            success = getattr(agent_result, "success", True)

            return {
                "response": final_response,
                "tool_calls": tool_calls_log,
                "tokens": tokens_accumulated,
                "iterations": iterations_used,
                "success": success,
            }

        except ImportError:
            # AgentLoop not yet available — use direct LLM fallback
            logger.info(
                "AgentLoop not available, using direct LLM call for subagent %s",
                subagent_id,
            )
            return await self._fallback_direct_llm(
                subagent_id=subagent_id,
                system_prompt=system_prompt,
                goal=goal,
                model=model,
                provider=provider,
                allowed_tools=allowed_tools,
                max_iterations=max_iterations,
            )

    async def _fallback_direct_llm(
        self,
        subagent_id: str,
        system_prompt: str,
        goal: str,
        model: str,
        provider: str,
        allowed_tools: dict[str, ToolDef],
        max_iterations: int,
    ) -> dict[str, Any]:
        """Fallback execution using direct LLM calls when AgentLoop is unavailable.

        This provides a single-shot LLM call with the subagent prompt. It won't
        execute tool calls but will generate a response that can be summarized.
        """
        from jebat.llm import generate_with_failover, resolve_llm_config

        llm_config = resolve_llm_config(
            provider_override=provider,
            model_override=model,
        )

        # Build the user prompt combining goal and available tools
        tool_list = ", ".join(sorted(allowed_tools.keys())) or "(none)"
        user_prompt = f"Task: {goal}\n\nAvailable tools: {tool_list}\n\nComplete this task."

        try:
            generation = await generate_with_failover(
                prompt=user_prompt,
                system_prompt=system_prompt,
                config=llm_config,
            )

            tokens = {}
            if hasattr(generation, "usage") and generation.usage:
                usage = generation.usage
                tokens = {
                    "prompt": getattr(usage, "prompt_tokens", 0) or 0,
                    "completion": getattr(usage, "completion_tokens", 0) or 0,
                    "total": getattr(usage, "total_tokens", 0) or 0,
                }

            return {
                "response": generation.text if hasattr(generation, "text") else str(generation),
                "tool_calls": [],  # No tool execution in fallback mode
                "tokens": tokens,
                "iterations": 1,
                "success": True,
            }
        except Exception as exc:
            return {
                "response": f"LLM call failed: {exc}",
                "tool_calls": [],
                "tokens": {},
                "iterations": 0,
                "success": False,
            }

    def _summarize_result(self, loop_result: dict[str, Any]) -> SubagentResult:
        """Condense a loop result dict into a SubagentResult.

        Extracts the key information: summary from response, success flag,
        tool call records, token usage. Truncates long responses to keep
        the summary manageable for the parent agent.
        """
        response = loop_result.get("response", "")
        success = loop_result.get("success", True)
        tool_calls = loop_result.get("tool_calls", [])
        tokens = loop_result.get("tokens", {})
        iterations = loop_result.get("iterations", 0)
        error = loop_result.get("error")

        # Extract the SUBAGENT RESULT section if present, else truncate
        summary = self._extract_summary(response, max_chars=2000)

        # Normalize tool_calls to list of dicts
        normalized_calls: list[dict[str, Any]] = []
        for call in tool_calls:
            if isinstance(call, dict):
                normalized_calls.append({
                    "tool_name": call.get("tool_name", call.get("name", "unknown")),
                    "params_summary": str(call.get("params", call.get("arguments", {})))[:200],
                })
            elif isinstance(call, str):
                normalized_calls.append({"tool_name": call, "params_summary": ""})
            else:
                normalized_calls.append({
                    "tool_name": str(call),
                    "params_summary": "",
                })

        # Normalize token counts
        normalized_tokens: dict[str, int] = {
            "prompt": int(tokens.get("prompt", 0)),
            "completion": int(tokens.get("completion", 0)),
            "total": int(tokens.get("total", 0)),
        }

        # Add iteration count to summary context
        if iterations > 0:
            summary += f"\n[Iterations used: {iterations}]"

        return SubagentResult(
            summary=summary,
            success=success and not error,
            tool_calls_made=normalized_calls,
            tokens_used=normalized_tokens,
            error=error,
        )

    def _extract_summary(self, response: str, max_chars: int = 2000) -> str:
        """Extract the SUBAGENT RESULT section from a response, or truncate.

        If the response contains a '### SUBAGENT RESULT' marker, extract
        everything after it. Otherwise, truncate to max_chars with a note.
        """
        marker = "### SUBAGENT RESULT"
        if marker in response:
            idx = response.index(marker)
            summary = response[idx + len(marker):].strip()
        else:
            summary = response.strip()

        if len(summary) > max_chars:
            summary = summary[:max_chars] + "\n[...truncated]"

        return summary if summary else "Subagent completed with no output."


# ── delegate_task Tool Registration ──────────────────────────────────────


DELEGATE_TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "goal": {
            "type": "string",
            "description": "What the subagent should accomplish. Be specific and clear.",
        },
        "context": {
            "type": "string",
            "description": "Background information the subagent needs. Project state, constraints, prior findings.",
        },
        "toolsets": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tool name prefixes/categories the subagent may use. Empty = all tools. Examples: ['file_', 'terminal', 'search'].",
        },
        "model": {
            "type": "string",
            "description": "LLLM model override for this subagent. Empty = use default.",
        },
        "provider": {
            "type": "string",
            "description": "LLLM provider override for this subagent. Empty = use default.",
        },
        "max_iterations": {
            "type": "integer",
            "description": "Maximum agent loop iterations. Default: 10.",
            "default": 10,
            "minimum": 1,
            "maximum": 50,
        },
        "timeout": {
            "type": "integer",
            "description": "Maximum seconds before killing the subagent. Default: 120.",
            "default": 120,
            "minimum": 10,
            "maximum": 600,
        },
        "parallel_tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string"},
                    "context": {"type": "string"},
                    "toolsets": {"type": "array", "items": {"type": "string"}},
                },
            },
            "description": "Optional: list of additional tasks to run in parallel with the main goal. If provided, all tasks (main + parallel) run concurrently.",
        },
        "max_concurrent": {
            "type": "integer",
            "description": "Max parallel subagents when parallel_tasks is used. Default: 3.",
            "default": 3,
            "minimum": 1,
            "maximum": 10,
        },
    },
    "required": ["goal"],
}


@register_tool(
    "delegate_task",
    schema=DELEGATE_TOOL_SCHEMA,
    safety_tier="confirm",
    timeout=600,
    max_output=50_000,
    description="Spawn a subagent to handle a delegated task. Costs tokens and may have side effects — requires confirmation.",
)
async def delegate_task_handler(
    goal: str,
    context: str = "",
    toolsets: list[str] | None = None,
    model: str = "",
    provider: str = "",
    max_iterations: int = 10,
    timeout: int = 120,
    parallel_tasks: list[dict[str, Any]] | None = None,
    max_concurrent: int = 3,
) -> dict[str, Any]:
    """Handle delegate_task tool calls.

    Supports both single subagent spawn and parallel multi-subagent spawn.
    Returns a dict with results suitable for the parent agent to consume.
    """
    manager = DelegationManager()

    # Build the primary subagent config
    primary_config = SubagentConfig(
        goal=goal,
        context=context,
        toolsets=toolsets or [],
        model=model,
        provider=provider,
        max_iterations=max_iterations,
        timeout=timeout,
    )

    if parallel_tasks:
        # Run multiple subagents in parallel
        configs = [primary_config]
        for pt in parallel_tasks:
            configs.append(SubagentConfig(
                goal=pt.get("goal", ""),
                context=pt.get("context", ""),
                toolsets=pt.get("toolsets", []),
                model=model,
                provider=provider,
                max_iterations=max_iterations,
                timeout=timeout,
            ))

        results = await manager.spawn_parallel(configs, max_concurrent=max_concurrent)

        # Format parallel results
        formatted: list[dict[str, Any]] = []
        total_tokens = {"prompt": 0, "completion": 0, "total": 0}
        all_success = True

        for i, r in enumerate(results):
            label = "primary" if i == 0 else f"parallel_{i}"
            formatted.append({
                "task": label,
                "summary": r.summary,
                "success": r.success,
                "tool_calls": len(r.tool_calls_made),
                "tokens": r.tokens_used,
                "error": r.error,
            })
            if not r.success:
                all_success = False
            for key in total_tokens:
                total_tokens[key] += r.tokens_used.get(key, 0)

        return {
            "mode": "parallel",
            "total_tasks": len(results),
            "all_success": all_success,
            "total_tokens": total_tokens,
            "results": formatted,
        }

    else:
        # Single subagent spawn
        result = await manager.spawn_subagent(primary_config)

        return {
            "mode": "single",
            "summary": result.summary,
            "success": result.success,
            "tool_calls_made": [
                {"tool_name": tc.get("tool_name", ""), "params_summary": tc.get("params_summary", "")}
                for tc in result.tool_calls_made
            ],
            "tokens_used": result.tokens_used,
            "error": result.error,
        }


# ── Utility ──────────────────────────────────────────────────────────────


def list_available_toolsets() -> list[str]:
    """List the distinct tool name prefixes/categories in TOOL_REGISTRY.

    Useful for the parent agent to know what toolset names are valid when
    configuring a subagent.
    """
    prefixes: set[str] = set()
    for name in TOOL_REGISTRY:
        # Split on underscores to find category prefixes
        parts = name.split("_")
        if len(parts) > 1:
            prefixes.add(parts[0] + "_")
        prefixes.add(name)  # Exact name is always valid
    return sorted(prefixes)