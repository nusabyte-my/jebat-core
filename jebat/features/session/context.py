"""JEBAT Context Manager — manages LLM context window for token budget.

Prioritizes content by importance:
  1. System prompt (always included)
  2. Wiki context (most relevant pages)
  3. Memory entries (prioritized by relevance)
  4. Conversation history (most recent, compressed if needed)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jebat.llm.token_usage import estimate_tokens


# ── Rough Token Counter ──────────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """Count tokens with the configured tokenizer or a conservative fallback."""
    return estimate_tokens(text)


def compress_text(text: str, target_tokens: int) -> str:
    """Crude compression: truncate to approximate token target.

    A proper implementation would use an LLM summarization call,
    but this is fine for initial context trimming.
    """
    max_chars = target_tokens * 4
    if len(text) <= max_chars:
        return text

    # Keep first 20% and last 80% of the budget
    head_budget = int(max_chars * 0.2)
    tail_budget = max_chars - head_budget
    head = text[:head_budget]
    tail = text[-tail_budget:]
    return f"{head}\n\n[... {count_tokens(text) - target_tokens} tokens compressed ...]\n\n{tail}"


# ── Context Assembly ─────────────────────────────────────────────────────

@dataclass
class ContextMessage:
    role: str
    content: str


class ContextManager:
    """Assembles the LLM context from all sources, respecting token budget."""

    def __init__(self, max_tokens: int = 32000):
        self.max_tokens = max_tokens
        self.warning_threshold = int(max_tokens * 0.70)

    def build_messages(
        self,
        system_prompt: str,
        history: list[dict[str, Any]] | None = None,
        wiki_pages: list[str] | None = None,
        memory_entries: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Build the ordered message list for the LLM call.

        Returns list of {"role": ..., "content": ...} dicts.
        """
        messages: list[dict[str, str]] = []
        tokens_used = 0

        # 1. System prompt (always included)
        messages.append({"role": "system", "content": system_prompt})
        tokens_used += count_tokens(system_prompt)

        # 2. Wiki pages (only if under warning threshold)
        for page in (wiki_pages or []):
            page_tokens = count_tokens(page)
            if tokens_used + page_tokens < self.warning_threshold:
                messages.append({"role": "system", "content": f"[Wiki] {page}"})
                tokens_used += page_tokens

        # 3. Memory entries (top 5, only if under warning threshold)
        for entry in (memory_entries or [])[:5]:
            entry_tokens = count_tokens(entry)
            if tokens_used + entry_tokens < self.warning_threshold:
                messages.append({"role": "system", "content": f"[Memory] {entry}"})
                tokens_used += entry_tokens

        # 4. Conversation history (most recent first, compress if needed)
        remaining = self.max_tokens - tokens_used
        if history:
            for msg in reversed(history):
                msg_tokens = count_tokens(msg.get("content", ""))
                if msg_tokens > remaining:
                    # Compress this message to fit remaining budget
                    compressed = self._compress_message(msg, remaining)
                    messages.insert(-len(wiki_pages or []) - len((memory_entries or [])[:5]) - 1, compressed)
                    break
                messages.append(msg)
                tokens_used += msg_tokens
                remaining -= msg_tokens

        return messages

    def _compress_message(self, msg: dict[str, str], budget: int) -> dict[str, str]:
        """Compress a single message to fit the token budget."""
        content = msg.get("content", "")
        if len(content) < 100 or budget < 10:
            return msg
        return {
            "role": msg.get("role", "user"),
            "content": compress_text(content, budget),
        }
