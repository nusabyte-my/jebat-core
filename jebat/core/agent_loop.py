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
    """Format a tool execution result for inclusion in the next LLM prompt.

    Token-optimized: truncates aggressively, strips boilerplate.
    """
    if error:
        return f"Error({tool_name}): {error[:200]}"
    if isinstance(result, dict):
        text = json.dumps(result, default=str, ensure_ascii=False)
        if len(text) > 2000:
            text = text[:2000] + "…"
        return f"[{tool_name}] {text}"
    return f"[{tool_name}] {str(result)[:2000]}"


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

# Token budget allocation (percentages of total budget)
TOKEN_BUDGET = {
    "system_prompt": 0.25,      # 25% for system prompt + project context
    "memory_context": 0.10,     # 10% for memory recall
    "working_memory": 0.10,     # 10% for working memory buffer
    "cross_session": 0.05,      # 5% for cross-session context
    "history": 0.50,            # 50% for conversation history
}


class _LoopCancelled(Exception):
    """Raised when user cancels the agent loop via Ctrl+C."""
    pass


# ── Context Window Management ─────────────────────────────────────────────

def _compact_conversation_history(
    messages: list[dict[str, str]],
    max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
) -> list[dict[str, str]]:
    """Truncate conversation history to fit within a token budget.

    Importance-aware: keeps system messages + recent messages, drops oldest first.
    Uses a rough 4-chars-per-token estimate.
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


def _summarize_evicted_context(messages: list[dict[str, str]], max_chars: int = 800) -> str:
    """Create a compact summary of evicted messages for context continuity.

    Extracts key points from dropped messages so the agent retains awareness.
    """
    if not messages:
        return ""

    summary_parts = []
    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "unknown")
        if not content or role == "system":
            continue
        # Take first sentence or first 150 chars
        first_sentence = content.split(".")[0].strip() if "." in content else content[:150]
        if first_sentence:
            summary_parts.append(f"{'U' if role == 'user' else 'A'}: {first_sentence[:150]}")

    if not summary_parts:
        return ""

    summary = "[Prior context] " + " | ".join(summary_parts[:6])
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "…"
    return summary


def _adaptive_compact(
    messages: list[dict[str, str]],
    max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    recalled_memory_contents: list[str] | None = None,
) -> list[dict[str, str]]:
    """Importance-aware context compaction.

    Scores each message by importance, keeps the most valuable messages
    within the token budget, then re-sorts chronologically.

    Importance factors:
      - System messages: highest priority (never dropped)
      - Messages with tool calls (Action:/Observation:): high priority
      - Messages referenced in recalled memories: boosted
      - Recent messages: higher priority than older ones
      - User messages with questions: higher priority than statements
    """
    if not messages:
        return []

    def msg_tokens(msg: dict[str, str]) -> int:
        return len(msg.get("content", "")) // 4 + 1

    total = sum(msg_tokens(m) for m in messages)
    if total <= max_tokens:
        return messages

    # Build a set of memory-referenced content for fast lookup
    memory_keywords: set[str] = set()
    if recalled_memory_contents:
        for mem in recalled_memory_contents:
            # Extract key phrases (first 50 chars of each memory)
            if mem:
                memory_keywords.add(mem[:50].lower())

    scored: list[tuple[float, int, dict[str, str]]] = []
    for idx, msg in enumerate(messages):
        content = msg.get("content", "")
        role = msg.get("role", "unknown")
        importance = 0.5  # base

        # System messages are critical
        if role == "system":
            importance = 1.0
        # Tool call results are important for context
        elif "Action:" in content or "Observation:" in content:
            importance = 0.8
        # Final answers are important
        elif "Final Answer:" in content:
            importance = 0.9
        # User questions are important
        elif role == "user" and "?" in content:
            importance = 0.7
        # Recency boost: newer messages score higher
        recency = idx / max(len(messages), 1)
        importance += recency * 0.2

        # Memory reference boost
        content_lower = content[:50].lower()
        if any(kw in content_lower for kw in memory_keywords):
            importance += 0.15

        scored.append((importance, idx, msg))

    # Sort by importance descending, greedily pick messages within budget
    scored.sort(key=lambda x: x[0], reverse=True)
    selected: list[tuple[int, dict[str, str]]] = []
    remaining = max_tokens
    for importance, idx, msg in scored:
        t = msg_tokens(msg)
        if t <= remaining:
            selected.append((idx, msg))
            remaining -= t

    # Re-sort chronologically
    selected.sort(key=lambda x: x[0])
    return [msg for _, msg in selected]


# ── Working Memory Buffer ─────────────────────────────────────────────────

@dataclass
class WorkingMemory:
    """Structured working memory that persists across agent iterations.

    Maintains current goals, discovered facts, and active constraints
    so the agent doesn't have to re-derive context each iteration.
    """
    goals: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    _max_items: int = 8

    def add_goal(self, goal: str) -> None:
        if len(self.goals) < self._max_items and goal not in self.goals:
            self.goals.append(goal)

    def add_fact(self, fact: str) -> None:
        if len(self.facts) < self._max_items and fact not in self.facts:
            self.facts.append(fact)

    def add_constraint(self, constraint: str) -> None:
        if len(self.constraints) < self._max_items and constraint not in self.constraints:
            self.constraints.append(constraint)

    def update_from_llm(self, text: str) -> None:
        """Parse LLM output for structured state updates.

        Looks for lines like:
          GOAL: implement feature X
          FACT: project uses TypeScript
          CONSTRAINT: do not modify database schema
        """
        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("GOAL:"):
                self.add_goal(line[5:].strip())
            elif line.upper().startswith("FACT:"):
                self.add_fact(line[5:].strip())
            elif line.upper().startswith("CONSTRAINT:"):
                self.add_constraint(line[11:].strip())

    def to_prompt_section(self) -> str:
        """Render working memory as a compact prompt section."""
        parts = []
        if self.goals:
            parts.append("Active goals: " + "; ".join(self.goals[:5]))
        if self.facts:
            parts.append("Known facts: " + "; ".join(self.facts[:5]))
        if self.constraints:
            parts.append("Constraints: " + "; ".join(self.constraints[:5]))
        if not parts:
            return ""
        return "[Working Memory]\n" + "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "goals": self.goals,
            "facts": self.facts,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkingMemory":
        wm = cls()
        wm.goals = data.get("goals", [])
        wm.facts = data.get("facts", [])
        wm.constraints = data.get("constraints", [])
        return wm


# ── Memory Integration ───────────────────────────────────────────────────

async def _recall_memories_for_query(query: str, limit: int = 5) -> list[str]:
    """Retrieve relevant memories from the EnhancedMemorySystem.

    Returns list of memory content strings, or empty list if unavailable.
    Token-efficient: only returns top-N most relevant.
    """
    try:
        from jebat.features.memory import EnhancedMemorySystem
        memory = EnhancedMemorySystem()
        traces = await memory.retrieve(query, limit=limit)
        return [t.content[:300] for t in traces if t.content]
    except Exception:
        return []


async def _encode_run_memories(
    user_message: str,
    final_response: str,
    tool_steps: list[ToolCallStep],
    session_id: str | None = None,
) -> None:
    """Encode key outcomes from an agent run as episodic memories.

    Extracts:
      - User intent + agent outcome (episodic)
      - Key decisions made (semantic)
      - Files created/modified (procedural)
      - Errors encountered (episodic, high importance)
      - Significant tool results (procedural)
    """
    try:
        from jebat.features.memory import EnhancedMemorySystem, MemoryType
        memory = EnhancedMemorySystem()

        tags = {"agent_run"}
        if session_id:
            tags.add(f"session:{session_id}")

        # ── 1. User intent + final outcome ─────────────────────────
        outcome_text = f"User asked: {user_message[:200]}. Agent responded: {final_response[:300]}"
        tool_names = [s.tool_name for s in tool_steps if not s.error]
        if tool_names:
            tags.update(set(tool_names[:3]))

        await memory.encode(
            content=outcome_text,
            memory_type=MemoryType.EPISODIC,
            tags=tags,
            importance=0.5,
            context={"session_id": session_id or "", "tool_count": len(tool_steps)},
        )

        # ── 2. Extract decisions from LLM responses ────────────────
        for step in tool_steps:
            if not step.error and step.tool_name in ("file_patch", "file_write", "terminal"):
                result_str = str(step.result) if step.result else ""
                # Look for decision patterns
                if any(kw in result_str.lower() for kw in ("decided", "chose", "selected", "implemented", "added")):
                    await memory.encode(
                        content=f"Decision: {result_str[:300]}",
                        memory_type=MemoryType.SEMANTIC,
                        tags={"decision", step.tool_name},
                        importance=0.7,
                        context={"session_id": session_id or ""},
                    )

        # ── 3. Track files created/modified ────────────────────────
        files_modified: list[str] = []
        for step in tool_steps:
            if step.tool_name in ("file_write", "file_patch") and not step.error:
                result_str = str(step.result) if step.result else ""
                # Extract file paths from result
                import re
                path_matches = re.findall(r'[/\w.-]+\.\w+', result_str)
                files_modified.extend(path_matches[:3])

        if files_modified:
            await memory.encode(
                content=f"Files modified in session: {', '.join(set(files_modified)[:5])}",
                memory_type=MemoryType.PROCEDURAL,
                tags={"files_modified", "session_summary"},
                importance=0.6,
                context={"session_id": session_id or "", "files": files_modified[:10]},
            )

        # ── 4. Encode errors (high importance for learning) ────────
        errors = [s for s in tool_steps if s.error]
        if errors:
            error_summary = "; ".join(f"{s.tool_name}: {s.error[:80]}" for s in errors[:3])
            await memory.encode(
                content=f"Errors encountered: {error_summary}",
                memory_type=MemoryType.EPISODIC,
                tags={"error", "learning_opportunity"},
                importance=0.8,  # Errors are important to remember
                context={"session_id": session_id or "", "error_count": len(errors)},
            )

        # ── 5. Significant tool results ────────────────────────────
        significant_tools = {"file_write", "file_patch", "git_commit", "terminal", "delegate_task"}
        for step in tool_steps:
            if step.tool_name in significant_tools and not step.error:
                result_str = str(step.result)[:200] if step.result else ""
                if result_str:
                    await memory.encode(
                        content=f"Tool {step.tool_name}: {result_str}",
                        memory_type=MemoryType.PROCEDURAL,
                        tags={step.tool_name, "tool_result"},
                        importance=0.4,
                    )
    except Exception:
        pass  # Memory encoding is best-effort


# ── Cross-Session Context ────────────────────────────────────────────────

def _load_cross_session_context(query: str, max_chars: int = 1500) -> str:
    """Load recent session summaries for context continuity.

    Searches across past sessions for relevant context related to the current query.
    Returns compact context string, or empty if unavailable.
    """
    try:
        from jebat.features.session import SessionManager
        sm = SessionManager()

        # Search past messages for relevant context
        results = sm.search_messages(query, limit=5)
        if not results:
            return ""

        parts = []
        for r in results:
            snippet = r.get("snippet", "")
            title = r.get("title", "")
            if snippet:
                parts.append(f"[{title}] {snippet[:200]}")

        context = "Past sessions: " + " | ".join(parts)
        if len(context) > max_chars:
            context = context[:max_chars] + "…"
        return context
    except Exception:
        return ""


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

        # Working memory buffer
        self._working_memory = WorkingMemory()

        # Cost tracker (lazy init)
        self._cost_tracker = None

        # Lazy tool module import flag
        self._tools_imported = False

    def _get_session_manager(self):
        """Lazily initialise the SessionManager for SQLite persistence."""
        if self._session_manager is None:
            from jebat.features.session import SessionManager
            self._session_manager = SessionManager()
        return self._session_manager

    def _get_cost_tracker(self):
        """Lazily initialise the CostTracker for budget enforcement."""
        if self._cost_tracker is None:
            try:
                from jebat.features.cost_tracking.cost_tracking import record_usage
                self._cost_tracker = record_usage
            except Exception:
                pass
        return self._cost_tracker

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
            "jebat.features.pentest.pentest_tools",
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
        self._working_memory = WorkingMemory()
        iterations = 0
        all_responses: list[str] = []
        total_tokens: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        # ── Build system prompt with memory + context ─────────────────
        if self._custom_system_prompt:
            base_system_prompt = self._custom_system_prompt
        else:
            base_system_prompt = build_chat_system_prompt(mode=mode)

        # Inject project context (AGENTS.md, MEMORY.md, DESIGN.md, etc.)
        project_context = _build_project_context_section()
        if project_context:
            base_system_prompt = project_context + "\n\n" + base_system_prompt

        # Gather wiki + memory context for ContextManager
        wiki_pages: list[str] = []
        memory_entries: list[str] = []

        try:
            from jebat.features.wiki.wiki_rag import inject_wiki_rag
            wiki_context = inject_wiki_rag(user_message, max_pages=3)
            if wiki_context:
                wiki_pages.append(wiki_context)
        except Exception:
            pass

        memory_context = await _recall_memories_for_query(user_message, limit=5)
        if memory_context:
            memory_entries = memory_context

        cross_session = _load_cross_session_context(user_message)
        if cross_session:
            memory_entries.append(cross_session)

        self._ensure_tools_imported()
        # Local/small models get a brief tool listing to save context space
        provider = self.config.provider if hasattr(self.config, 'provider') else ''
        max_tools = 15 if provider in ('ollama', 'llamacpp', 'local') else 0
        tool_appendix = _build_tool_system_prompt_appendix(max_tools=max_tools)
        full_system_prompt = base_system_prompt + tool_appendix

        # ── ContextManager: assemble messages respecting token budget ──
        from jebat.features.session.context import ContextManager
        ctx = ContextManager(max_tokens=self.max_context_tokens)
        working_history = list(conversation_history or [])

        # ── Session persistence ──────────────────────────────────────
        sm = self._get_session_manager()
        if not self.session_id:
            title = user_message.strip()[:80]
            if len(user_message) > 80:
                title += "..."
            self.session_id = sm.create_session(title=title)
        else:
            existing = sm.load_history(self.session_id, limit=50)
            for msg in existing:
                working_history.append({
                    "role": msg.role,
                    "content": msg.content,
                })
            # Load persisted working memory for this session
            wm_state = sm.load_working_memory(self.session_id)
            if wm_state:
                for g in wm_state.get("goals", []):
                    self._working_memory.add_goal(g)
                for f in wm_state.get("facts", []):
                    self._working_memory.add_fact(f)
                for c in wm_state.get("constraints", []):
                    self._working_memory.add_constraint(c)
        sm.add_message(self.session_id, "user", user_message)

        # Use ContextManager to build token-aware messages list
        messages = ctx.build_messages(
            system_prompt=full_system_prompt,
            history=working_history,
            wiki_pages=wiki_pages if wiki_pages else None,
            memory_entries=memory_entries if memory_entries else None,
        )
        # Extract the system prompt (first message) and rebuild history
        system_msg = messages[0]["content"] if messages else full_system_prompt
        # The rest are wiki/memory + conversation history
        history_from_ctx = [m for m in messages[1:] if m["role"] != "system"]

        while iterations < self.max_iterations:
            iterations += 1

            # ── Inject working memory into system prompt ──────────────
            wm_section = self._working_memory.to_prompt_section()
            prompt_with_wm = system_msg
            if wm_section:
                prompt_with_wm += f"\n\n{wm_section}"

            # Adaptive compaction: importance-aware context trimming
            current_prompt = history_from_ctx[-1]["content"] if history_from_ctx else user_message
            history_for_llm = history_from_ctx[:-1] if len(history_from_ctx) > 1 else []
            if history_for_llm:
                history_for_llm = _adaptive_compact(
                    history_for_llm,
                    max_tokens=int(self.max_context_tokens * 0.5),
                    recalled_memory_contents=memory_context if memory_context else None,
                )

            # ── Call LLM with retry on transient errors ───────────────
            try:
                result = await _retry_with_backoff(
                    lambda: generate_chat_reply(
                        prompt=current_prompt,
                        mode=mode,
                        conversation_messages=history_for_llm,
                        provider_override=self.config.provider,
                        model_override=self.config.model,
                        temperature_override=self.config.temperature,
                        return_metadata=True,
                        system_prompt_override=prompt_with_wm,
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

                # Track cost per iteration
                cost_fn = self._get_cost_tracker()
                if cost_fn:
                    try:
                        cost_fn(
                            provider=used_provider,
                            model=self.config.model or "unknown",
                            input_tokens=metadata.usage.get("prompt_tokens", 0),
                            output_tokens=metadata.usage.get("completion_tokens", 0),
                            operation="agent",
                            session_id=self.session_id or "unknown",
                        )
                    except Exception:
                        pass

            # Update working memory from LLM output
            self._working_memory.update_from_llm(response_text)

            # Detect tool calls — ReAct pattern first (works with any provider)
            tool_calls = _extract_react_tool_calls(response_text)

            if not tool_calls:
                # No tool calls detected — this is the final response
                final = response_text
                final_answer_match = re.match(
                    r"Final Answer:\s*(.*)", response_text, re.IGNORECASE | re.DOTALL
                )
                if final_answer_match:
                    final = final_answer_match.group(1).strip()

                # Persist final response
                sm.add_message(self.session_id, "assistant", final)

                # Save working memory state for this session
                sm.save_working_memory(
                    self.session_id,
                    goals=self._working_memory.goals,
                    facts=self._working_memory.facts,
                    constraints=self._working_memory.constraints,
                )

                # Encode memories from this run (best-effort, async)
                try:
                    await _encode_run_memories(
                        user_message, final, self._tool_steps, self.session_id
                    )
                except Exception:
                    pass

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
