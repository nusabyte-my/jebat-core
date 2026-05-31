"""JEBAT Token Saver — RTK-style cache-aware cost governor.

Caveman-simple approach: track what's cached, don't re-count it,
and bill the user honestly. No fluff, no stochastic parsing.

Three levers:
  1. Cache tracking — log cache_creation + cache_read tokens separately
  2. Tokenizer-based counting — use tiktoken when available, fallback conservatively
  3. Rolling conversation compression — RTK-style: "we had a 30-turn convo, here's 3 lines"

This is the Juru Cermat (Savings Clerk) — watches every token.
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAVER_DATA_DIR = os.path.expanduser("~/.jebat/token_saver")
os.makedirs(SAVER_DATA_DIR, exist_ok=True)

# ── Tokenizer helpers ──────────────────────────────────────────────────────

def count_tokens(text: str, *, model: str = "", provider: str = "") -> int:
    """Count tokens using tiktoken if available, with a tight fallback.
    
    The fallback is 5 chars = 1 token (more conservative than 4:1, 
    avoids overestimating context capacity — RTK style).
    """
    if not text or not text.strip():
        return 0
    
    # Try tiktoken first
    try:
        import tiktoken
        try:
            if model:
                enc = tiktoken.encoding_for_model(model)
                return len(enc.encode(text))
        except KeyError:
            pass
        # Fallback encoder
        try:
            enc = tiktoken.get_encoding("o200k_base")
            return len(enc.encode(text))
        except Exception:
            pass
    except ImportError:
        pass
    
    # Conservative fallback: 5 chars ≈ 1 token
    return max(1, len(text.strip()) // 5)

def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str = "") -> float:
    """Estimate USD cost from token counts.
    
    Falls back to a generic $3/M input, $15/M output (claude-sonnet-4-ish)
    when model is unknown.
    """
    pricing = {
        # OpenAI
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "o1": (15.00, 60.00),
        "o1-mini": (3.00, 12.00),
        # Anthropic
        "claude-sonnet-4": (3.00, 15.00),
        "claude-sonnet-4-5": (3.00, 15.00),
        "claude-opus-4": (15.00, 75.00),
        "claude-haiku-3.5": (0.80, 4.00),
        # Google
        "gemini-2.5-pro": (1.25, 10.00),
        "gemini-2.5-flash": (0.15, 0.60),
        # Free models — cost is zero
        "kr/claude-sonnet-4.5": (0.0, 0.0),
        "kr/claude-opus-4": (0.0, 0.0),
        "oc/claude-sonnet-4.5": (0.0, 0.0),
        "vtx/gemini-2.5-pro": (0.0, 0.0),
        "llama3": (0.0, 0.0),
        "mistral": (0.0, 0.0),
    }
    input_rate, output_rate = pricing.get(model, (3.00, 15.00))
    return (prompt_tokens / 1_000_000 * input_rate) + (completion_tokens / 1_000_000 * output_rate)


# ── Cache-aware attestation ────────────────────────────────────────────────

def save_cache_attestation(
    session_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int,
    model: str,
    provider: str = "",
    operation: str = "chat",
) -> dict[str, Any]:
    """Log a token usage event with cache breakdown.
    
    RTK-style: we separate fresh vs cached tokens so you know what
    you actually burned vs what was served from prompt caching.
    """
    fresh_prompt = max(0, prompt_tokens - cached_tokens)
    cost = estimate_cost(prompt_tokens, completion_tokens, model)
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id or datetime.now().strftime("%Y%m%d"),
        "model": model,
        "provider": provider or "unknown",
        "operation": operation,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_tokens": cached_tokens,
        "fresh_prompt_tokens": fresh_prompt,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost_usd": round(cost, 6),
    }
    
    # Append to daily JSON log
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(SAVER_DATA_DIR, f"{date_str}.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    
    return record


def get_daily_log(date_str: str | None = None) -> list[dict[str, Any]]:
    """Read all token saver records for a given day."""
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(SAVER_DATA_DIR, f"{date_str}.jsonl")
    if not os.path.exists(log_path):
        return []
    records: list[dict[str, Any]] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def summarize_savings(days: int = 7) -> dict[str, Any]:
    """Summarize token usage and cache savings.
    
    Returns:
        dict with total/fresh/cached/completion token counts + cost
    """
    total_prompt = total_completion = total_cached = total_fresh = total_cost = 0
    record_count = 0
    
    for i in range(days):
        from datetime import timedelta
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for rec in get_daily_log(date):
            total_prompt += rec.get("prompt_tokens", 0)
            total_completion += rec.get("completion_tokens", 0)
            total_cached += rec.get("cached_tokens", 0)
            total_fresh += rec.get("fresh_prompt_tokens", 0)
            total_cost += rec.get("cost_usd", 0)
            record_count += 1
    
    cache_hit_rate = (total_cached / total_prompt * 100) if total_prompt > 0 else 0.0
    cash_saved = estimate_cost(total_cached, 0, "")
    
    return {
        "records": record_count,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
        "cached_tokens": total_cached,
        "fresh_tokens": total_fresh,
        "cache_hit_rate_pct": round(cache_hit_rate, 1),
        "total_cost_usd": round(total_cost, 4),
        "estimated_cache_savings_usd": round(cash_saved, 4),
    }


# ── RTK-style rolling compression ──────────────────────────────────────────

def compress_conversation(
    messages: list[dict[str, str]],
    *,
    max_prompt_tokens: int = 2000,
    max_recent_turns: int = 3,
    summary_chars: int = 350,
) -> list[dict[str, str]]:
    """Aggressively compress conversation history — caveman style.
    
    Rules:
    - Keep the first message (system prompt)
    - Keep the last N turns verbatim
    - Summarize everything in between to a single terse line
    - Drop any message that doesn't fit the budget
    """
    if not messages:
        return []
    
    # Estimate tokens for each message
    def msg_tokens(m: dict[str, str]) -> int:
        return count_tokens(m.get("content", ""))
    
    # Guard: first message (system)
    result = [messages[0]]
    remaining = max_prompt_tokens - msg_tokens(messages[0])
    
    if remaining <= 0:
        return result  # System prompt alone is over budget — return just it
    
    if len(messages) <= max_recent_turns + 1:
        # Small enough — keep as-is if within budget
        total = sum(msg_tokens(m) for m in messages[1:])
        if total <= remaining:
            return list(messages)
    
    # Keep the last N turns verbatim
    recent_turns = messages[-max_recent_turns:] if len(messages) > 1 else []
    recent_tokens = sum(msg_tokens(m) for m in recent_turns)
    
    # Everything between first message and recent turns gets summarized
    middle = messages[1:-max_recent_turns] if len(messages) > max_recent_turns + 1 else []
    
    # Summarize middle messages into one terse line
    if middle:
        roles_seen: set[str] = set()
        summary_parts: list[str] = []
        for m in middle:
            short = (m.get("content", "") or "")[:summary_chars].replace("\n", " ").strip()
            if short:
                role = m.get("role", "user")
                if role not in roles_seen:
                    summary_parts.append(f"[{role}]")
                    roles_seen.add(role)
                summary_parts.append(short[:60])
        
        if summary_parts:
            summary_line = f"[Conversation compressed — {len(middle)} turns] " + " | ".join(summary_parts[:5])
            if len(summary_line) > summary_chars:
                summary_line = summary_line[:summary_chars - 3] + "..."
            
            compressed_tokens = count_tokens(summary_line)
            if compressed_tokens + recent_tokens <= remaining:
                result.append({"role": "system", "content": summary_line})
                remaining -= compressed_tokens
    
    # Add recent turns (newest first to fit budget)
    for msg in reversed(recent_turns):
        t = msg_tokens(msg)
        if t <= remaining:
            result.append(msg)
            remaining -= t
        else:
            # Truncate the content of the last message to fit
            content = msg.get("content", "")
            if content:
                content = content[:max(80, remaining * 5)]
                result.append({**msg, "content": content})
            break
    
    return result