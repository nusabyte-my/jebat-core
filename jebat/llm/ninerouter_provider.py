"""9Router Provider — FREE AI via 9router.com local proxy.

9Router (https://github.com/decolua/9router) is an OpenAI-compatible proxy
that auto-fallbacks across tiers:
  Tier 1: Subscription (Claude Code, Copilot) → Tier 2: Cheap (GLM, MiniMax)
  → Tier 3: FREE (Kiro, OpenCode Free, Vertex credits)

It also compresses tool_result tokens via RTK (20-40% savings).

Usage:
  1. Install 9router: npm install -g 9router && 9router
  2. Dashboard at http://localhost:20128 — connect free providers
  3. Set JEBAT provider: JEBAT_LLM_PROVIDER=ninerouter
  4. Set model with routing prefix: JEBAT_LLM_MODEL=kr/claude-sonnet-4.5

Routing prefixes:
  kr/   → Kiro AI (free Claude unlimited)
  oc/   → OpenCode Free (no auth)
  glm/  → GLM ($0.6/1M tokens)
  mm/   → MiniMax ($0.2/1M tokens)
  sub/  → Your subscription accounts
  vtx/  → Vertex AI ($300 free credits)

Env vars:
  JEBAT_LLM_PROVIDER=ninerouter
  JEBAT_LLM_MODEL=kr/claude-sonnet-4.5
  NINEROUTER_HOST=http://localhost:20128  (default)
  NINEROUTER_API_KEY= (copy from 9router dashboard)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from .config import JebatLLMConfig
from .token_usage import TokenUsage, usage_from_texts


# ── Defaults ──────────────────────────────────────────────────────────────

NINEROUTER_DEFAULT_HOST = "http://localhost:20128"
NINEROUTER_DEFAULT_API_KEY = "ninerouter"  # 9router accepts any key by default


def _input_for_usage(prompt: str, system_prompt: str | None = None) -> str:
    return "\n\n".join(part for part in [system_prompt or "", prompt] if part)


# ── Provider ──────────────────────────────────────────────────────────────

@dataclass(slots=True)
class NineRouterProvider:
    """OpenAI-compatible provider that routes through 9Router proxy.

    9Router exposes /v1/chat/completions (OpenAI format) and /v1/messages
    (Anthropic format). We use chat/completions for maximum compatibility.
    """
    api_key: str
    model: str
    host: str
    temperature: float
    max_tokens: int

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return (await self.generate_with_metadata(prompt=prompt, system_prompt=system_prompt)).text

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> tuple[str, TokenUsage]:  # Returns (text, usage) as ProviderGeneration-like
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are JEBAT, a Malaysian AI warrior."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        base_url = self.host.rstrip("/") + "/v1/chat/completions"

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jebat.local",
                    "X-Title": "JEBAT CLI Agent",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        text = ""
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                text = content.strip()

        if not text:
            # 9Router may return errors in specific format
            error = data.get("error", {})
            if error:
                raise RuntimeError(f"9Router error: {error.get('message', error)}")
            raise RuntimeError("9Router response did not contain text output")

        return ProviderGeneration(
            text=text,
            usage=usage_from_texts(
                _input_for_usage(prompt, system_prompt),
                text,
                model=self.model,
                provider="ninerouter",
                raw_usage=data.get("usage", {}),
            ),
        )

    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ):
        """Stream tokens from 9Router — yields text chunks."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are JEBAT."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        base_url = self.host.rstrip("/") + "/v1/chat/completions"

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jebat.local",
                    "X-Title": "JEBAT CLI Agent",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue


# ── Integration ───────────────────────────────────────────────────────────

def build_ninerouter_provider(config: JebatLLMConfig) -> NineRouterProvider:
    """Build NineRouterProvider from config + env vars."""
    api_key = os.getenv("NINEROUTER_API_KEY", NINEROUTER_DEFAULT_API_KEY)
    host = os.getenv("NINEROUTER_HOST", NINEROUTER_DEFAULT_HOST)
    return NineRouterProvider(
        api_key=api_key,
        model=config.model,  # e.g. "kr/claude-sonnet-4.5"
        host=host,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


# ── Quick setup helper ────────────────────────────────────────────────────

NINEROUTER_QUICK_SETUP = """
9Router Quick Setup for JEBAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install 9Router:
   npm install -g 9router
   9router

2. Open dashboard: http://localhost:20128

3. Connect a FREE provider (no signup needed):
   Dashboard → Providers → Kiro AI (free Claude unlimited)

4. Configure JEBAT:
   export JEBAT_LLM_PROVIDER=ninerouter
   export JEBAT_LLM_MODEL=kr/claude-sonnet-4.5
   export NINEROUTER_HOST=http://localhost:20128
   export NINEROUTER_API_KEY=<from dashboard>

5. Run JEBAT:
   jebat chat-repl

Model routing prefixes:
  kr/     → Kiro AI (free Claude)
  oc/     → OpenCode Free
  glm/    → GLM ($0.6/1M)
  mm/     → MiniMax ($0.2/1M)
  sub/    → Your subscriptions
  vtx/    → Vertex AI ($300 credits)

RTK (Reduce Token Kind) auto-compresses tool outputs → 20-40% savings.
"""


def print_ninerouter_setup():
    """Print quick setup guide."""
    print(NINEROUTER_QUICK_SETUP)


# ── Supported free models ─────────────────────────────────────────────────

FREE_MODELS: dict[str, dict[str, str]] = {
    "kr/claude-sonnet-4.5": {"tier": "free", "provider": "Kiro AI", "notes": "Free Claude unlimited"},
    "kr/claude-opus-4": {"tier": "free", "provider": "Kiro AI", "notes": "Free Claude Opus"},
    "oc/claude-sonnet-4.5": {"tier": "free", "provider": "OpenCode", "notes": "No auth required"},
    "glm-4-flash": {"tier": "cheap", "provider": "GLM", "notes": "$0.6/1M tokens"},
    "mm/MiniMax-Text-01": {"tier": "cheap", "provider": "MiniMax", "notes": "$0.2/1M tokens"},
    "vtx/gemini-2.5-pro": {"tier": "free-credits", "provider": "Vertex AI", "notes": "$300 free credits"},
}


def list_free_models() -> list[dict[str, str]]:
    """List free/cheap models available via 9Router."""
    result = []
    for model_id, info in FREE_MODELS.items():
        result.append({
            "model": model_id,
            "tier": info["tier"],
            "provider": info["provider"],
            "notes": info["notes"],
        })
    return result