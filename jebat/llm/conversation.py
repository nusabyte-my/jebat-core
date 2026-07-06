from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .token_usage import estimate_tokens


@dataclass(slots=True)
class PreparedPrompt:
    prompt: str
    profile: str
    summary: str = ""
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def prepare_chat_prompt(
    prompt: str,
    *,
    mode: str | None = None,
    model: str = "",
    provider: str = "",
    conversation_messages: list[dict[str, str]] | None = None,
) -> PreparedPrompt:
    profile = select_prompt_profile(prompt, mode=mode)
    messages = [dict(item) for item in (conversation_messages or []) if isinstance(item, dict)]
    keep_recent = 2 if profile == "lean" else 4
    summary_chars = 420 if profile == "lean" else 760

    if not messages:
        wrapped_prompt = _wrap_prompt(prompt, profile=profile)
        return PreparedPrompt(
            prompt=wrapped_prompt,
            profile=profile,
            metadata={
                "history_summary_turns": 0,
                "recent_turns": 0,
                "estimated_prompt_tokens": estimate_tokens(wrapped_prompt, model=model, provider=provider),
            },
        )

    recent_turns = messages[-keep_recent:]
    if recent_turns and recent_turns[-1].get("role") == "user" and recent_turns[-1].get("content", "") == prompt:
        recent_turns = recent_turns[:-1]
    older_turns = messages[: max(0, len(messages) - (len(recent_turns) + 1))]
    summary = summarize_history(older_turns, max_chars=summary_chars)

    parts: list[str] = []
    if summary:
        parts.append("[Conversation State]\n" + summary)
    if recent_turns:
        parts.append("[Recent Turns]\n" + "\n".join(_format_turn(turn, max_chars=220) for turn in recent_turns))
    wrapped_prompt = _wrap_prompt(prompt, profile=profile)
    if wrapped_prompt != prompt or parts:
        parts.append("[Current User Request]\n" + wrapped_prompt)
        final_prompt = "\n\n".join(parts)
    else:
        final_prompt = prompt

    return PreparedPrompt(
        prompt=final_prompt,
        profile=profile,
        summary=summary,
        recent_turns=[
            {
                "role": str(turn.get("role", "user")),
                "content": _normalize_text(str(turn.get("content", "")), max_chars=220),
            }
            for turn in recent_turns
            if str(turn.get("content", "")).strip()
        ],
        metadata={
            "history_summary_turns": len(older_turns),
            "recent_turns": len(recent_turns),
            "estimated_prompt_tokens": estimate_tokens(final_prompt, model=model, provider=provider),
        },
    )


def select_prompt_profile(prompt: str, mode: str | None = None) -> str:
    mode_name = (mode or "").strip().lower()
    if mode_name in {"deep", "strategic", "critical"}:
        return "deep"

    text = prompt.lower()
    deep_markers = (
        "review",
        "audit",
        "security",
        "compare",
        "analyze",
        "architecture",
        "tradeoff",
        "migration",
        "rollout",
        "design",
        "plan",
        "strategy",
    )
    if any(marker in text for marker in deep_markers):
        return "deep"
    return "lean"


def summarize_history(messages: list[dict[str, str]], *, max_chars: int = 600, max_items: int = 8) -> str:
    if not messages:
        return ""

    lines: list[str] = []
    for item in messages[-max_items:]:
        role = str(item.get("role", "user")).strip() or "user"
        content = _normalize_text(str(item.get("content", "")), max_chars=140)
        if not content:
            continue
        lines.append(f"- {role}: {content}")

    summary = "\n".join(lines)
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 3].rstrip() + "..."


def _wrap_prompt(prompt: str, *, profile: str) -> str:
    if profile == "lean":
        return prompt

    return (
        "[Execution Profile]\n"
        "- Provide evidence-backed reasoning.\n"
        "- Surface tradeoffs and risks.\n"
        "- Keep the answer structured and concise.\n\n"
        + prompt
    )


def _format_turn(turn: dict[str, str], *, max_chars: int) -> str:
    role = str(turn.get("role", "user")).strip() or "user"
    content = _normalize_text(str(turn.get("content", "")), max_chars=max_chars)
    return f"{role}: {content}"


def _normalize_text(text: str, *, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."
