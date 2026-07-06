"""JEBAT Agent Loop — iterative tool-calling agent with LLM integration.

The agent loop handles:
1. Sending user messages to the LLM
2. Detecting tool calls in the response (API-level or ReAct text pattern)
3. Executing tool calls via the tool registry
4. Feeding tool results back to the LLM
5. Repeating until the LLM produces a final text response or max iterations

Supports two tool-calling patterns:
- API-level: OpenAI/Anthropic structured tool_calls in the response
- ReAct: Other providers use text patterns like "Action: tool_name\nAction Input: {...}"
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from jebat.llm import (
    JebatLLMConfig,
    generate_chat_reply,
    resolve_llm_config,
    build_chat_system_prompt,
    apply_chat_preset,
    estimate_tokens,
)
from jebat.llm.chat_runtime import (
    CHAT_PRESETS,
    normalize_chat_preset,
    list_chat_presets,
    apply_runtime_overrides,
    ChatGenerationMetadata,
)
from jebat.tools import TOOL_REGISTRY, call_tool, classify_tool_call


# ── Project Context Auto-Load ────────────────────────────────────────────

_PROJECT_CONTEXT_FILES = [
    "AGENTS.md",
    "MEMORY.md",
    "DESIGN.md",
    "CLAUDE.md",
    ".cursorrules",
    "CODEX_PROFILE.md",
    "JEBAT.md",
]

_PROJECT_MARKER_FILES = [
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "Makefile",
    "README.md",
]


def _build_project_context_section(project_path: str | None = None) -> str:
    """Scan the project directory for context files and build a system prompt section.

    Reads AGENTS.md, MEMORY.md, DESIGN.md, and other marker files from the
    project root (cwd by default) and assembles a compact prefix that tells
    the agent what project it's operating in and what conventions to follow.

    Returns empty string if no context files are found.
    """
    import os

    root = Path(project_path) if project_path else Path.cwd()
    root = root.resolve()

    sections: list[str] = []
    found_any = False

    # 1. Scan for explicit context files (AGENTS.md etc.)
    for filename in _PROJECT_CONTEXT_FILES:
        filepath = root / filename
        if not filepath.is_file():
            # Also check one level up (monorepo root)
            alt = root.parent / filename
            if alt.is_file() and alt.parent != root:
                filepath = alt
            else:
                continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Truncate very large files to prevent token overflow
        max_chars = 8000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[... truncated at {max_chars} chars, {len(content)} total]"

        sections.append(f"=== {filename} ===\n{content}")
        found_any = True

    # 2. If no explicit context files, note the project type from markers
    if not found_any:
        markers_found = []
        for marker in _PROJECT_MARKER_FILES:
            if (root / marker).is_file():
                markers_found.append(marker)
        if markers_found:
            sections.append(f"Project root: {root}")
            sections.append(f"Project markers: {', '.join(markers_found)}")
            sections.append("No AGENTS.md, MEMORY.md, or DESIGN.md found. Use file_tree and file_read to explore the repo.")
            found_any = True

    if not found_any:
        return ""

    header = f"# Project Context (auto-loaded from {root})\n"
    return header + "\n\n".join(sections)

from pathlib import Path  # used by _build_project_context_section


# ── Data structures ──────────────────────────────────────────────────────

@dataclass
class ToolCallStep:
    """A single tool call within an agent iteration."""
    tool_name: str
    params: dict[str, Any]
    result: Any
    duration_ms: int = 0
    safety_tier: str = "auto"
    approved: bool = True
    error: str | None = None


@dataclass
class AgentResult:
    """Result from a complete agent loop run."""
    final_response: str
    tool_calls_made: list[ToolCallStep] = field(default_factory=list)
    iterations_used: int = 0
    tokens_used: dict[str, int] = field(default_factory=dict)
    provider_used: str = ""
    llm_config_used: JebatLLMConfig | None = None
    metadata: ChatGenerationMetadata | None = None
    raw_llm_responses: list[str] = field(default_factory=list)
    error: str | None = None
    session_id: str | None = None


# ── ReAct pattern detection ─────────────────────────────────────────────

_REACT_ACTION_RE = re.compile(
    r"Action:\s*(\w+)\s*\n\s*Action Input:\s*(\{.*?\}|\[.*?\]|\".*?\"|'.*?')",
    re.IGNORECASE | re.DOTALL,
)

_REACT_THOUGHT_RE = re.compile(
    r"Thought:\s*(.*?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL,
)

_REACT_OBSERVATION_RE = re.compile(
    r"Observation:\s*(.*?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL,
)


def _extract_react_tool_calls(text: str) -> list[tuple[str, dict[str, Any]]]:
    """Extract tool calls from ReAct-style text patterns.

    Returns list of (tool_name, params_dict) tuples.
    """
    calls: list[tuple[str, dict[str, Any]]] = []
    for match in _REACT_ACTION_RE.finditer(text):
        tool_name = match.group(1).strip()
        raw_params = match.group(2).strip()
        # Parse params
        try:
            if raw_params.startswith("{"):
                params = json.loads(raw_params)
            elif raw_params.startswith('"') or raw_params.startswith("'"):
                # Single string param → wrap in dict
                params = {"query": raw_params[1:-1]}
            elif raw_params.startswith("["):
                # Array → wrap
                params = {"items": json.loads(raw_params)}
            else:
                params = {"input": raw_params}
        except json.JSONDecodeError:
            params = {"raw_input": raw_params}

        calls.append((tool_name, params))
    return calls


def _extract_api_tool_calls(response_data: Any) -> list[tuple[str, dict[str, Any]]]:
    """Extract tool calls from API-level structured tool_calls.

    Handles OpenAI/Anthropic response shapes with tool_calls arrays.
    """
    calls: list[tuple[str, dict[str, Any]]] = []
    if isinstance(response_data, dict):
        tool_calls_list = response_data.get("tool_calls", [])
        for tc in tool_calls_list:
            name = tc.get("name", tc.get("function", {}).get("name", ""))
            args_str = tc.get("arguments", tc.get("function", {}).get("arguments", "{}"))
            try:
                params = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                params = {"raw_arguments": args_str}
            if name:
                calls.append((name, params))
    return calls


def _format_tool_result_for_llm(tool_name: str, result: Any, error: str | None) -> str:
    """Format a tool execution result for inclusion in the next LLM prompt."""
    if error:
        return f"Tool {tool_name} error: {error}"
    if isinstance(result, dict):
        # Truncate large results
        text = json.dumps(result, default=str, ensure_ascii=False)
        if len(text) > 4000:
            text = text[:4000] + "... (truncated)"
        return f"Tool {tool_name} result: {text}"
    return f"Tool {tool_name} result: {str(result)[:4000]}"


def _build_tool_system_prompt_appendix(max_tools: int = 0) -> str:
    """Build a system prompt section describing available tools.

    When max_tools > 0, only the most commonly used tools are listed with
    brief descriptions (no parameter details) to save context space for
    local/small models. When 0, all tools are listed with full parameters.

    Only includes tools that are currently registered in TOOL_REGISTRY.
    """
    if not TOOL_REGISTRY:
        return ""

    # Tools most likely needed by a coding agent — listed first with brief descriptions
    CORE_TOOLS = [
        "file_read", "file_write", "file_patch", "file_search", "file_tree",
        "terminal", "execute_code",
        "git_status", "git_diff", "git_log", "git_commit", "git_stash", "git_branch",
        "delegate_task",
        "search_web",
        "clarify",
    ]

    tool_descriptions = []

    if max_tools > 0:
        # Brief mode: only list core tools, no parameter details
        tool_descriptions.append("  Most useful tools (use these first):")
        for name in CORE_TOOLS:
            tdef = TOOL_REGISTRY.get(name)
            if tdef:
                desc = (tdef.description or "No description")[:80]
                tool_descriptions.append(f"    {name}: {desc}")
        tool_descriptions.append("")
        tool_descriptions.append(f"  All {len(TOOL_REGISTRY)} tools are available — use any tool by its registered name.")
        tool_descriptions.append("")
    else:
        # Full mode: all tools with parameter details
        for name, tool_def in sorted(TOOL_REGISTRY.items()):
            desc = tool_def.description or "No description"
            props = tool_def.schema.get("properties", {})
            required = tool_def.schema.get("required", [])
            param_summary = ""
            if props:
                param_parts = []
                for pname, pinfo in props.items():
                    ptype = pinfo.get("type", "any")
                    req_marker = "*" if pname in required else ""
                    param_parts.append(f"{pname}{req_marker}: {ptype}")
                param_summary = "(" + ", ".join(param_parts) + ")"

            tool_descriptions.append(f"  - {name}{param_summary}: {desc}")

    return (
        "\n\nAvailable tools:\n"
        + "\n".join(tool_descriptions)
        + "\n\n## Tool Use Format\n"
        + "To call a tool, use EXACTLY this format (one tool per response):\n"
        + "Action: tool_name\n"
        + 'Action Input: {"param1": "value1"}\n'
        + "\nExample:\n"
        + 'Action: file_tree\n'
        + 'Action Input: {"path": "."}\n'
        + "\nAfter you send a tool call, you will receive:\n"
        + "Observation: <tool result>\n\n"
        + "Then either call another tool or provide your FINAL answer.\n"
        + "Your final answer should be plain text without Action: or Observation: prefixes.\n"
        + "Do NOT include the Observation: text in your own response."
    )


# ── Safety tier enforcement ──────────────────────────────────────────────

class SafetyMode:
    """Controls how tool safety tiers are enforced."""
    AUTO = "auto"        # auto-tier tools execute, confirm/dangerous require approval
    CONFIRM = "confirm"  # all tools execute without confirmation prompts
    DANGEROUS = "dangerous"  # all tools including dangerous execute without prompts


def _should_approve_tool(
    tool_name: str,
    params: dict[str, Any],
    safety_mode: str,
    interactive_confirm: Any | None = None,
) -> bool:
    """Decide whether a tool call should be approved based on safety mode.

    Args:
        tool_name: The tool being called.
        params: Parameters for the tool call.
        safety_mode: Current safety mode (auto/confirm/dangerous).
        interactive_confirm: Optional callable(prompt_text) -> bool for user prompts.

    Returns:
        True if the tool call is approved, False if rejected.
    """
    effective_tier = classify_tool_call(tool_name, params)

    if safety_mode == SafetyMode.DANGEROUS:
        return True
    if safety_mode == SafetyMode.CONFIRM:
        return True
    if effective_tier == "auto":
        return True

    # Need interactive confirmation for confirm/dangerous tiers in auto mode
    if interactive_confirm:
        detail = params.get("command") or params.get("path") or json.dumps(params, default=str)[:80]
        prompt_text = f"[{effective_tier.upper()}] {tool_name}: {detail}\nProceed? [Y/n]: "
        return interactive_confirm(prompt_text)

    # In non-interactive mode, reject confirm/dangerous
    return False


# ── Agent Loop ────────────────────────────────────────────────────────────

MAX_ITERATIONS = 10
DEFAULT_MAX_CONTEXT_TOKENS = 80_000  # Truncate conversation history beyond this


class _LoopCancelled(Exception):
    """Raised when user cancels the agent loop via Ctrl+C."""
    pass


# ── Context Window Management ─────────────────────────────────────────────

def _compact_conversation_history(
    messages: list[dict[str, str]],
    max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
) -> list[dict[str, str]]:
    """Truncate conversation history to fit within a token budget.

    Keeps the system message (if any) and the most recent N messages,
    dropping oldest messages first. Uses a rough 4-chars-per-token estimate.
    """
    if not messages:
        return []

    # Rough token estimate: ~4 chars per token
    def msg_tokens(msg: dict[str, str]) -> int:
        return len(msg.get("content", "")) // 4 + 1

    total = sum(msg_tokens(m) for m in messages)
    if total <= max_tokens:
        return messages

    # Keep the first message (usually system or initial user prompt)
    # and trim from the middle
    result = [messages[0]]
    remaining_budget = max_tokens - msg_tokens(messages[0])

    # Add messages from newest to oldest until budget exhausted
    for msg in reversed(messages[1:]):
        t = msg_tokens(msg)
        if t <= remaining_budget:
            result.append(msg)
            remaining_budget -= t
        else:
            break

    # Reverse back to chronological order (first message stays first)
    return [result[0]] + list(reversed(result[1:]))


# ── Retry Helper ──────────────────────────────────────────────────────────

async def _retry_with_backoff(
    fn,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
) -> Any:
    """Call an async function with exponential backoff on transient errors.

    Retries on common transient failures: timeouts, rate limits, connection errors.
    Does NOT retry on authentication errors or validation errors.
    """
    import asyncio
    import random

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            err_str = str(exc).lower()

            # Don't retry on auth/validation errors
            if any(kw in err_str for kw in ["auth", "invalid api", "unauthorized", "forbidden"]):
                raise

            # Transient errors worth retrying
            is_transient = any(kw in err_str for kw in [
                "timeout", "rate limit", "too many requests",
                "connection", "network", "502", "503", "504",
                "service unavailable", "bad gateway",
            ])

            if not is_transient and attempt < max_retries:
                # For unknown errors, retry once more just in case
                pass
            elif not is_transient:
                raise

            if attempt >= max_retries:
                break

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.25)
            await asyncio.sleep(delay + jitter)

    raise last_exc


class AgentLoop:
    """Iterative tool-calling agent loop with LLM integration.

    The loop:
    1. Takes user message + conversation history
    2. Sends to LLM with system prompt + tool descriptions
    3. Checks response for tool calls (API-level or ReAct text)
    4. Executes approved tool calls
    5. Feeds results back as "Observation" context
    6. Repeats until final text response or max iterations

    Attributes:
        config: The LLM configuration to use.
        safety_mode: Current safety enforcement mode.
        max_iterations: Maximum number of think-act-observe cycles.
        interactive_confirm: Optional callable for user approval prompts.
    """

    def __init__(
        self,
        config: JebatLLMConfig | None = None,
        *,
        provider_override: str | None = None,
        model_override: str | None = None,
        preset: str | None = None,
        safety_mode: str = SafetyMode.AUTO,
        max_iterations: int = MAX_ITERATIONS,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        interactive_confirm: Any | None = None,
        session_id: str | None = None,
        system_prompt: str | None = None,
    ):
        self.config = config or resolve_llm_config(
            provider_override=provider_override,
            model_override=model_override,
        )
        if preset:
            self.config = apply_chat_preset(self.config, preset=preset)
        self.safety_mode = safety_mode
        self.max_iterations = max_iterations
        self.max_context_tokens = max_context_tokens
        self.interactive_confirm = interactive_confirm
        self.session_id = session_id
        self._custom_system_prompt = system_prompt
        self._session_manager = None  # Lazy init

        # Accumulated tool call history for this run
        self._tool_steps: list[ToolCallStep] = []
        self._tool_observations: list[str] = []

        # Lazy tool module import flag
        self._tools_imported = False

    def _get_session_manager(self):
        """Lazily initialise the SessionManager for SQLite persistence."""
        if self._session_manager is None:
            from jebat.features.session import SessionManager
            self._session_manager = SessionManager()
        return self._session_manager

    def _ensure_tools_imported(self) -> None:
        """Lazily import tool feature modules so they register in TOOL_REGISTRY.

        Avoids circular imports by deferring until first tool call is needed.
        """
        if self._tools_imported:
            return
        self._tools_imported = True

        # Import each tool feature module — they use @register_tool decorator
        # which populates TOOL_REGISTRY on import
        _tool_modules = [
            "jebat.features.terminal.terminal_exec",
            "jebat.features.fileops.file_ops",
            "jebat.features.vision.vision",
            "jebat.features.search.web_search",
            "jebat.features.browser.browser",
            "jebat.tools.memory_tools",
            "jebat.tools.todo_tools",
            "jebat.tools.clarify_tools",
            "jebat.tools.image_gen_tools",
            "jebat.tools.skill_tools",
            "jebat.tools.session_search_tools",
            "jebat.tools.execute_code",
            "jebat.features.social_media.social_media",
            "jebat.features.git.git_tools",
            "jebat.features.shell.shell_tools",
            "jebat.features.undo.undo",
            "jebat.features.sandbox.sandbox",
            "jebat.features.cost_tracking.cost_tracking",
            "jebat.features.plugins.plugins",
            "jebat.features.telemetry.telemetry",
        ]
        for mod_name in _tool_modules:
            try:
                __import__(mod_name)
            except ImportError:
                pass  # Module may not be available (e.g. playwright not installed)

    async def run(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        mode: str | None = None,
        stream_callback: Callable[[str], Awaitable[None]] | None = None,
    ) -> AgentResult:
        """Run the agent loop: send message, detect tool calls, execute, repeat.

        Args:
            user_message: The user's input text.
            conversation_history: Previous messages in the session.
            mode: LLM reasoning mode (fast/deliberate/deep/strategic/creative/critical).
            stream_callback: If provided, final response tokens are streamed via this callback.

        Returns:
            AgentResult with final_response, tool_calls, iteration count, etc.
        """
        self._tool_steps = []
        self._tool_observations = []
        iterations = 0
        all_responses: list[str] = []
        total_tokens: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        # Build the augmented system prompt with tool descriptions
        if self._custom_system_prompt:
            base_system_prompt = self._custom_system_prompt
        else:
            base_system_prompt = build_chat_system_prompt(mode=mode)

        # Inject project context (AGENTS.md, MEMORY.md, DESIGN.md, etc.)
        project_context = _build_project_context_section()
        if project_context:
            base_system_prompt = project_context + "\n\n" + base_system_prompt

        # Inject wiki RAG context (relevant wiki pages via FTS5 keyword search)
        try:
            from jebat.features.wiki.wiki_rag import inject_wiki_rag
            wiki_context = inject_wiki_rag(user_message, max_pages=3)
            if wiki_context:
                base_system_prompt = wiki_context + "\n" + base_system_prompt
        except Exception:
            pass  # Wiki not available — skip gracefully

        self._ensure_tools_imported()
        # Local/small models get a brief tool listing to save context space
        provider = self.config.provider if hasattr(self.config, 'provider') else ''
        max_tools = 15 if provider in ('ollama', 'llamacpp', 'local') else 0
        tool_appendix = _build_tool_system_prompt_appendix(max_tools=max_tools)
        full_system_prompt = base_system_prompt + tool_appendix

        # Working prompt — starts with user message, gets augmented with observations
        current_prompt = user_message
        working_history = list(conversation_history or [])

        # ── Session persistence ──────────────────────────────────────
        sm = self._get_session_manager()
        if not self.session_id:
            # Auto-create a new session; title from the first few words
            title = user_message.strip()[:80]
            if len(user_message) > 80:
                title += "..."
            self.session_id = sm.create_session(title=title)
        else:
            # Resume existing session — load its history and prepend
            existing = sm.load_history(self.session_id, limit=50)
            for msg in existing:
                working_history.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        # Save user message to DB
        sm.add_message(self.session_id, "user", user_message)

        while iterations < self.max_iterations:
            iterations += 1

            # ── Context compaction: trim conversation history ─────────
            if len(working_history) > 10:
                # Rough check — will estimate tokens more carefully
                working_history = _compact_conversation_history(
                    working_history,
                    max_tokens=self.max_context_tokens,
                )

            # ── Call LLM with retry on transient errors ───────────────
            try:
                result = await _retry_with_backoff(
                    lambda: generate_chat_reply(
                        prompt=current_prompt,
                        mode=mode,
                        conversation_messages=working_history,
                        provider_override=self.config.provider,
                        model_override=self.config.model,
                        temperature_override=self.config.temperature,
                        return_metadata=True,
                        system_prompt_override=full_system_prompt,
                    ),
                    max_retries=3,
                    base_delay=2.0,
                )
            except _LoopCancelled:
                sm.add_message(self.session_id, "assistant", "Agent loop cancelled by user.")
                return AgentResult(
                    final_response="Agent loop cancelled by user.",
                    tool_calls_made=self._tool_steps,
                    iterations_used=iterations,
                    tokens_used=total_tokens,
                    provider_used=self.config.provider,
                    error="Cancelled by user (Ctrl+C)",
                    session_id=self.session_id,
                )
            except Exception as exc:
                # LLM call failed after retries — return what we have
                error_msg = f"LLM error: {exc}" + (
                    "\n\n" + "\n".join(self._tool_observations) if self._tool_observations else ""
                )
                sm.add_message(self.session_id, "assistant", error_msg)
                return AgentResult(
                    final_response=error_msg,
                    tool_calls_made=self._tool_steps,
                    iterations_used=iterations,
                    tokens_used=total_tokens,
                    provider_used=self.config.provider,
                    error=str(exc),
                    session_id=self.session_id,
                )

            # Unpack result
            if len(result) == 4:
                response_text, used_provider, used_config, metadata = result
            else:
                response_text, used_provider, used_config = result[:3]
                metadata = None

            all_responses.append(response_text)

            # Accumulate token usage
            if metadata and metadata.usage:
                total_tokens["prompt_tokens"] += metadata.usage.get("prompt_tokens", 0)
                total_tokens["completion_tokens"] += metadata.usage.get("completion_tokens", 0)
                total_tokens["total_tokens"] += metadata.usage.get("total_tokens", 0)

            # Detect tool calls — ReAct pattern first (works with any provider)
            tool_calls = _extract_react_tool_calls(response_text)

            # Also check for API-level tool calls if the response contains structured data
            # (This would come from providers that support native tool calling)
            # For now, we primarily rely on ReAct text patterns since generate_chat_reply
            # returns plain text. API-level tool calls would need a different response shape.

            if not tool_calls:
                # No tool calls detected — this is the final response
                # If it contains a "Final Answer:" prefix, strip it
                final = response_text
                final_answer_match = re.match(
                    r"Final Answer:\s*(.*)", response_text, re.IGNORECASE | re.DOTALL
                )
                if final_answer_match:
                    final = final_answer_match.group(1).strip()

                # Persist final response
                sm.add_message(self.session_id, "assistant", final)

                # Stream final response if callback is set
                if stream_callback:
                    for c in final:
                        await stream_callback(c)

                return AgentResult(
                    final_response=final,
                    tool_calls_made=self._tool_steps,
                    iterations_used=iterations,
                    tokens_used=total_tokens,
                    provider_used=used_provider,
                    llm_config_used=used_config,
                    metadata=metadata,
                    raw_llm_responses=all_responses,
                    session_id=self.session_id,
                )

            # Execute tool calls
            observation_parts = []
            consecutive_failures = 0
            for tool_name, params in tool_calls:
                step = await self._execute_tool_call(tool_name, params)
                self._tool_steps.append(step)

                result_text = _format_tool_result_for_llm(tool_name, step.result, step.error)
                observation_parts.append(f"Observation: {result_text}")
                self._tool_observations.append(result_text)

                if step.error:
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0

            # Break if model is stuck in a hallucination loop (5+ consecutive tool failures)
            if consecutive_failures >= 5:
                error_msg = (
                    f"Agent loop halted: {consecutive_failures} consecutive tool failures. "
                    f"The model appears stuck outputting invalid tool calls.\n"
                    f"Last tool: {tool_calls[-1][0] if tool_calls else 'none'}\n"
                    f"Tip: The local model may need a system prompt adjustment or a larger model."
                )
                sm.add_message(self.session_id, "assistant", error_msg)
                return AgentResult(
                    final_response=error_msg,
                    tool_calls_made=self._tool_steps,
                    iterations_used=iterations,
                    tokens_used=total_tokens,
                    provider_used=used_provider,
                    error="Consecutive tool failures exceeded threshold",
                    session_id=self.session_id,
                )

            # Break if exact same tool call is repeated 3+ times across iterations
            call_signature = json.dumps([(n, p) for n, p in tool_calls], sort_keys=True)
            if not hasattr(self, '_recent_call_sigs'):
                self._recent_call_sigs = []
            self._recent_call_sigs.append(call_signature)
            if len(self._recent_call_sigs) >= 3 and len(set(self._recent_call_sigs[-3:])) == 1:
                error_msg = (
                    f"Agent loop halted: same tool call repeated 3 times.\n"
                    f"Repeated call: {call_signature[:200]}\n"
                    f"Tip: The model is stuck in a loop. Try a different prompt or a larger model."
                )
                sm.add_message(self.session_id, "assistant", error_msg)
                return AgentResult(
                    final_response=error_msg,
                    tool_calls_made=self._tool_steps,
                    iterations_used=iterations,
                    tokens_used=total_tokens,
                    provider_used=used_provider,
                    error="Repeated tool call loop detected",
                    session_id=self.session_id,
                )

            # Feed observations back to the LLM as the next prompt
            # Include the LLM's thinking + the observations
            observation_block = "\n".join(observation_parts)
            current_prompt = observation_block

            # Add the previous LLM response + observations to history for context
            working_history.append({"role": "assistant", "content": response_text})
            working_history.append({"role": "user", "content": observation_block})

            # Persist to session DB
            sm.add_message(self.session_id, "assistant", response_text,
                           tool_calls=[{"name": n, "params": p} for n, p in tool_calls],
                           tokens=metadata.usage.get("total_tokens", 0) if metadata and metadata.usage else 0)
            sm.add_message(self.session_id, "user", observation_block)

        # Max iterations reached — return last response with tool observations appended
        last_response = all_responses[-1] if all_responses else "Agent loop reached max iterations."
        if self._tool_observations:
            last_response += "\n\n[Tool observations:\n" + "\n".join(self._tool_observations) + "]"

        # Persist maxed-out response
        sm.add_message(self.session_id, "assistant", last_response)

        # Stream fallback response
        if stream_callback:
            for c in last_response:
                await stream_callback(c)

        return AgentResult(
            final_response=last_response,
            tool_calls_made=self._tool_steps,
            iterations_used=iterations,
            tokens_used=total_tokens,
            provider_used=self.config.provider,
            llm_config_used=self.config,
            raw_llm_responses=all_responses,
            session_id=self.session_id,
        )

    async def _execute_tool_call(self, tool_name: str, params: dict[str, Any]) -> ToolCallStep:
        """Execute a single tool call with safety checks.

        Returns a ToolCallStep with the result or error.
        """
        import time
        start = time.time()

        # Check if tool exists
        if tool_name not in TOOL_REGISTRY:
            return ToolCallStep(
                tool_name=tool_name,
                params=params,
                result=None,
                duration_ms=int((time.time() - start) * 1000),
                error=f"Tool '{tool_name}' not found in registry",
            )

        # Safety approval
        approved = _should_approve_tool(
            tool_name, params, self.safety_mode, self.interactive_confirm
        )
        if not approved:
            return ToolCallStep(
                tool_name=tool_name,
                params=params,
                result={"status": "cancelled"},
                duration_ms=int((time.time() - start) * 1000),
                safety_tier=classify_tool_call(tool_name, params),
                approved=False,
                error="User cancelled",
            )

        # Execute the tool (with retry on transient errors)
        try:
            result = await _retry_with_backoff(
                lambda: call_tool(tool_name, **params),
                max_retries=2,
                base_delay=1.0,
            )
            duration_ms = int((time.time() - start) * 1000)
            return ToolCallStep(
                tool_name=tool_name,
                params=params,
                result=result,
                duration_ms=duration_ms,
                safety_tier=classify_tool_call(tool_name, params),
                approved=True,
            )
        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            return ToolCallStep(
                tool_name=tool_name,
                params=params,
                result=None,
                duration_ms=duration_ms,
                safety_tier=classify_tool_call(tool_name, params),
                approved=True,
                error=str(exc),
            )