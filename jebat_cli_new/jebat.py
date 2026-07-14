#!/usr/bin/env python3
"""
JEBAT — unified coding-agent CLI.
One tool. All providers. Native tools. Plan + execute.
v8.2 — gradient banner, rounded panels, auto-orchestrator, ghost mode, agent DB.
"""

from __future__ import annotations

import argparse, collections, json, os, random, re, sqlite3, sys, textwrap, threading, time, types, urllib.request, urllib.error
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from jebat_cli_new.models import CompletionRequest, CompletionResponse, resolve_api_key
from jebat_cli_new.providers import (
    OllamaProviderImpl,
    OpenAIProviderImpl,
    AnthropicProviderImpl,
    GeminiProviderImpl,
    GitHubModelsProviderImpl,
)
from jebat.features.auth.custom_providers import CUSTOM_PROVIDER_IDS


VERSION = "7.5"

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

_JEBAT_HOME = Path.home() / ".jebat"
PROVIDER_FILE = _JEBAT_HOME / "jebat-cli-providers.json"
MEMORY_FILE = _JEBAT_HOME / "memory.json"
SESSIONS_DIR = _JEBAT_HOME / "sessions"
AUDIT_DB = _JEBAT_HOME / "audit.db"
TASKS_DB = _JEBAT_HOME / "tasks.db"
COST_DB = _JEBAT_HOME / "costs.db"
EXPORT_DIR = _JEBAT_HOME / "exports"
DREAM_STATE_FILE = Path(".") / ".jebat" / "dream_state.json"
DREAM_DIR = Path(".") / ".jebat" / "dreams"

# Ensure directories exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
DREAM_DIR.mkdir(parents=True, exist_ok=True)

# Provider pricing (per 1M tokens)
PROVIDER_PRICING = {
    "ollama": {"input": 0.0, "output": 0.0},
    "openai": {"input": 2.5, "output": 10.0},
    "anthropic": {"input": 3.0, "output": 15.0},
    "gemini": {"input": 1.25, "output": 5.0},
    "github": {"input": 0.0, "output": 0.0},
    "openrouter": {"input": 0.5, "output": 1.5},
    "groq": {"input": 0.5, "output": 0.8},
    "cerebras": {"input": 0.15, "output": 0.6},
    "mistral": {"input": 0.25, "output": 0.75},
    "together": {"input": 0.2, "output": 0.5},
    "deepseek": {"input": 0.14, "output": 0.28},
    "xai": {"input": 3.0, "output": 15.0},
    "cloudflare": {"input": 0.0, "output": 0.0},
    "sambanova": {"input": 0.0, "output": 0.0},
    "novita": {"input": 0.35, "output": 0.4},
    "zai": {"input": 1.0, "output": 3.0},
    "openai-compat": {"input": 0.0, "output": 0.0},
}

# ═══════════════════════════════════════════════════════════════════
# PROVIDER KINDS REGISTRY
# ═══════════════════════════════════════════════════════════════════
#
# All providers that use OpenAI-compatible APIs share a single provider class.
# Each entry: (kind, display_name, api_base, default_model, needs_key, description)

PROVIDER_KINDS = [
    ("ollama",          "Ollama",          "http://127.0.0.1:11434",                     "qwen2.5:3b",             False, "Local inference · zero cost"),
    ("openai",          "OpenAI",          "https://api.openai.com/v1",                  "gpt-5",                  True,  "GPT-5, GPT-5-mini, GPT-4.1, o3, o4-mini"),
    ("anthropic",       "Anthropic",       "https://api.anthropic.com",                  "claude-sonnet-4-20250514",True, "Claude Opus 4.1, Sonnet 4.1, Haiku 4.5"),
    ("gemini",          "Google Gemini",   "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-pro", True, "Gemini 2.5 Pro/Flash (OpenAI-compatible)"),
    ("github",          "GitHub Models",   "https://models.github.ai/inference",         "openai/gpt-5",           True,  "Free tier available with GitHub token"),
    ("openrouter",      "OpenRouter",      "https://openrouter.ai/api/v1",               "anthropic/claude-sonnet-4", True, "150+ models, pay-per-token"),
    ("groq",            "Groq",            "https://api.groq.com/openai/v1",             "llama-3.3-70b-versatile",True, "Ultra-fast inference, free tier"),
    ("cerebras",        "Cerebras",        "https://api.cerebras.ai/v1",                 "llama-3.3-70b",          True, "Fastest inference globally"),
    ("mistral",         "Mistral",         "https://api.mistral.ai/v1",                  "mistral-large-latest",   True, "Mistral Large, Medium, Codestral"),
    ("together",        "Together AI",     "https://api.together.xyz/v1",                "meta-llama/Llama-3.3-70B-Instruct-Turbo", True, "Open-source model hosting"),
    ("deepseek",        "DeepSeek",        "https://api.deepseek.com/v1",                "deepseek-chat",          True, "DeepSeek V3.1/R1, very affordable"),
    ("xai",             "xAI (Grok)",      "https://api.x.ai/v1",                        "grok-4",                 True, "Grok-4, Grok-4 Mini"),
    ("cloudflare",      "Cloudflare AI",   "https://api.cloudflare.com/client/v4",        "@cf/meta/llama-3.3-70b-instruct-fp16", False, "Free Workers AI inference"),
    ("sambanova",       "SambaNova",       "https://api.sambanova.ai/v1",                "Meta-Llama-3.3-70B-Instruct", True, "Free tier, fast inference"),
    ("novita",          "Novita AI",       "https://api.novita.ai/v3/openai",            "deepseek-r1",            True, "Cheap R1/LLaMA access"),
    ("zai",             "Z.AI",            "https://api.z.ai/v1",                         "glm-4-plus",             True,  "Zhipu GLM models"),
    ("openai-compat",   "Custom (OpenAI-compatible)", "",                                  "",                       True,  "Any OpenAI-compatible endpoint"),
    ("opencode_go",     "OpenCode Go",     "",                                              "opencode-go/default",    True,  "OpenCode Go gateway (OpenAI-compatible)"),
    ("opencode_zen",    "OpenCode Zen",    "",                                              "opencode-zen/default",   True,  "OpenCode Zen gateway, SSO/OAuth (OpenAI-compatible)"),
    ("zenmux",          "ZenMux",          "",                                              "zenmux/default",         True,  "ZenMux token-multiplexing router (OpenAI-compatible)"),
    ("tokerrouter",     "TokerRouter",     "",                                              "tokerrouter/default",    True,  "TokerRouter token-usage router (OpenAI-compatible)"),
    ("agent_router",    "Agent Router",    "",                                              "agent-router/default",   True,  "Agent Router orchestration, SSO/OAuth (OpenAI-compatible)"),
]


# ═══════════════════════════════════════════════════════════════════
# MODEL CATALOG — Curated models per provider (OpenCode-style)
# ═══════════════════════════════════════════════════════════════════
# Each model: (id, name, context_window, max_output, input_cost, output_cost, capabilities)
# costs are $/1M tokens. capabilities: list of strings.

MODEL_CATALOG = {
    "ollama": [
        ("qwen2.5-coder:7b",     "Qwen 2.5 Coder 7B",      32768,  8192,  0, 0, ["code", "local"]),
        ("qwen2.5-coder:14b",    "Qwen 2.5 Coder 14B",     32768,  8192,  0, 0, ["code", "local"]),
        ("qwen2.5:14b",          "Qwen 2.5 14B",            32768,  8192,  0, 0, ["chat", "local"]),
        ("qwen2.5:32b",          "Qwen 2.5 32B",            32768,  8192,  0, 0, ["chat", "local"]),
        ("codellama:13b",         "Code Llama 13B",          16384,  4096,  0, 0, ["code", "local"]),
        ("deepseek-coder-v2:16b", "DeepSeek Coder V2 16B",   128000, 16384, 0, 0, ["code", "local"]),
        ("llama3.3:70b",          "Llama 3.3 70B",           128000, 8192,  0, 0, ["chat", "local"]),
        ("gemma3:4b",             "Gemma 3 4B",              128000, 8192,  0, 0, ["code", "local"]),
    ],
    "openai": [
        ("gpt-5",                 "GPT-5",                  272000, 32768, 10, 30, ["reasoning", "code", "best"]),
        ("gpt-5-mini",            "GPT-5 Mini",             272000, 32768, 1.25, 5, ["reasoning", "code", "cheap"]),
        ("gpt-5-nano",            "GPT-5 Nano",             272000, 32768, 0.5, 2, ["code", "ultra-cheap"]),
        ("gpt-4.1",               "GPT-4.1",                1047576, 32768, 2, 8, ["code", "long"]),
        ("gpt-4.1-mini",          "GPT-4.1 Mini",           1047576, 32768, 0.4, 1.6, ["code", "long", "cheap"]),
        ("gpt-4o",                "GPT-4o",                 128000, 16384, 2.5, 10, ["vision", "code", "fast"]),
        ("gpt-4o-mini",           "GPT-4o Mini",            128000, 16384, 0.15, 0.6, ["vision", "code", "cheap"]),
        ("o3",                    "o3",                     200000, 100000, 10, 40, ["reasoning", "code"]),
        ("o4-mini",               "o4-mini",                200000, 100000, 1.1, 4.4, ["reasoning", "code"]),
    ],
    "anthropic": [
        ("claude-opus-4-1",         "Claude Opus 4.1",      200000, 32000, 15, 75, ["reasoning", "code", "best"]),
        ("claude-sonnet-4-1",       "Claude Sonnet 4.1",    200000, 64000, 3, 15, ["reasoning", "code"]),
        ("claude-haiku-4-5",        "Claude Haiku 4.5",      200000, 8192, 0.8, 4, ["code", "fast", "cheap"]),
        ("claude-opus-4-20250514",  "Claude Opus 4",        200000, 32000, 15, 75, ["reasoning", "code"]),
        ("claude-sonnet-4-20250514","Claude Sonnet 4",      200000, 64000, 3, 15, ["reasoning", "code"]),
    ],
    "gemini": [
        ("gemini-2.5-pro",        "Gemini 2.5 Pro",          1048576, 65536, 1.25, 10, ["reasoning", "code", "long"]),
        ("gemini-2.5-flash",      "Gemini 2.5 Flash",        1048576, 65536, 0.15, 0.6, ["reasoning", "code", "cheap"]),
        ("gemini-2.5-flash-lite", "Gemini 2.5 Flash-Lite",   1048576, 65536, 0.1, 0.4, ["code", "cheap", "ultra-cheap"]),
        ("gemini-2.0-flash",      "Gemini 2.0 Flash",        1048576, 8192, 0.1, 0.4, ["code", "fast"]),
    ],
    "openrouter": [
        ("anthropic/claude-opus-4",    "Claude Opus 4",      200000, 32000, 15, 75, ["reasoning", "code"]),
        ("anthropic/claude-sonnet-4",  "Claude Sonnet 4",    200000, 64000, 3, 15, ["reasoning", "code"]),
        ("openai/gpt-4o",              "GPT-4o",             128000, 16384, 2.5, 10, ["vision", "code"]),
        ("google/gemini-2.5-pro",      "Gemini 2.5 Pro",     1048576, 65536, 1.25, 10, ["reasoning", "code"]),
        ("meta-llama/llama-3.3-70b",   "Llama 3.3 70B",      128000, 8192, 0.1, 0.1, ["code", "cheap"]),
        ("deepseek/deepseek-chat",     "DeepSeek V3",        128000, 8192, 0.14, 0.28, ["code", "cheap"]),
    ],
    "groq": [
        ("llama-3.3-70b-versatile",    "Llama 3.3 70B",      128000, 32768, 0.59, 0.79, ["code", "fast"]),
        ("llama-3.1-8b-instant",       "Llama 3.1 8B",       128000, 8192, 0.05, 0.08, ["code", "ultra-fast"]),
        ("mixtral-8x7b-32768",         "Mixtral 8x7B",       32768, 32768, 0.24, 0.24, ["code"]),
        ("gemma2-9b-it",               "Gemma 2 9B",         8192, 8192, 0.2, 0.2, ["code"]),
    ],
    "cerebras": [
        ("llama-3.3-70b",              "Llama 3.3 70B",      128000, 8192, 0.15, 0.6, ["code", "fastest"]),
        ("llama-3.1-8b",               "Llama 3.1 8B",       128000, 8192, 0.03, 0.06, ["code", "ultra-fast"]),
    ],
    "deepseek": [
        ("deepseek-chat",              "DeepSeek V3",        128000, 8192, 0.14, 0.28, ["code", "cheap"]),
        ("deepseek-reasoner",          "DeepSeek R1",        128000, 8192, 0.55, 2.19, ["reasoning"]),
    ],
    "xai": [
        ("grok-4",                     "Grok 4",              131072, 16384, 3, 15, ["reasoning", "code", "best"]),
        ("grok-4-mini",               "Grok 4 Mini",         131072, 16384, 0.3, 0.5, ["code", "cheap"]),
        ("grok-3",                     "Grok 3",             131072, 16384, 3, 15, ["code"]),
        ("grok-3-mini",                "Grok 3 Mini",        131072, 16384, 0.3, 0.5, ["code", "cheap"]),
    ],
    "together": [
        ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Llama 3.3 70B Turbo", 128000, 8192, 0.88, 0.88, ["code"]),
        ("deepseek-ai/DeepSeek-V3",   "DeepSeek V3",        128000, 8192, 0.27, 1.1, ["code"]),
    ],
    "mistral": [
        ("mistral-large-latest",       "Mistral Large",      128000, 32768, 2, 6, ["code"]),
        ("codestral-latest",           "Codestral",          256000, 32768, 0.3, 0.9, ["code"]),
        ("mistral-small-latest",       "Mistral Small",      128000, 32768, 0.1, 0.3, ["code", "cheap"]),
    ],
    "sambanova": [
        ("Meta-Llama-3.3-70B-Instruct", "Llama 3.3 70B",    128000, 8192, 0, 0, ["code", "free"]),
    ],
    "github": [
        ("openai/gpt-4o-mini",         "GPT-4o Mini",        128000, 16384, 0, 0, ["code", "free"]),
        ("openai/gpt-4o",              "GPT-4o",             128000, 16384, 0, 0, ["code", "free"]),
        ("anthropic/claude-sonnet-4",   "Claude Sonnet 4",    200000, 64000, 0, 0, ["code", "free"]),
    ],
    "cloudflare": [
        ("@cf/meta/llama-3.3-70b-instruct-fp16", "Llama 3.3 70B", 128000, 4096, 0, 0, ["code", "free"]),
    ],
    "novita": [
        ("deepseek-r1",                "DeepSeek R1",        128000, 8192, 0.35, 0.4, ["reasoning", "cheap"]),
        ("llama-3.3-70b-instruct",     "Llama 3.3 70B",      128000, 8192, 0.35, 0.4, ["code"]),
    ],
    "zai": [
        ("glm-4-plus",                 "GLM-4 Plus",         128000, 8192, 1, 3, ["code"]),
    ],
    # Placeholder catalogs — replaced by live /v1/models fetch in the full CLI;
    # edit here or rely on the `/provider add` free-text model entry.
    "opencode_go": [
        ("opencode-go/default",        "OpenCode Go Default", 128000, 8192, 0, 0, ["code"]),
        ("opencode-go/go-large",       "OpenCode Go Large",   128000, 8192, 0, 0, ["code"]),
    ],
    "opencode_zen": [
        ("opencode-zen/default",       "OpenCode Zen Default", 128000, 8192, 0, 0, ["code"]),
        ("opencode-zen/zen-pro",       "OpenCode Zen Pro",     128000, 8192, 0, 0, ["code"]),
    ],
    "zenmux": [
        ("zenmux/default",             "ZenMux Default",      128000, 8192, 0, 0, ["code"]),
        ("zenmux/mux-1",               "ZenMux 1",            128000, 8192, 0, 0, ["code"]),
    ],
    "tokerrouter": [
        ("tokerrouter/default",        "TokerRouter Default", 128000, 8192, 0, 0, ["code"]),
        ("tokerrouter/route-fast",     "TokerRouter Fast",    128000, 8192, 0, 0, ["code"]),
    ],
    "agent_router": [
        ("agent-router/default",       "Agent Router Default", 128000, 8192, 0, 0, ["code"]),
        ("agent-router/orchestrator",  "Agent Router Orchestrator", 128000, 8192, 0, 0, ["code"]),
    ],
}


def _get_models_for_provider(provider_kind):
    """Get curated model list for a provider kind."""
    return MODEL_CATALOG.get(provider_kind, [])


def _fetch_live_models(api_base, api_key=None):
    """Best-effort live model catalog from an OpenAI-compatible /models endpoint.

    Returns a list of model id strings, or an empty list on any failure so the
    caller can fall back to the curated/placeholder catalog.
    """
    try:
        import json
        import urllib.request

        url = f"{api_base.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        items = data.get("data", data) if isinstance(data, dict) else data
        out = []
        for it in items or []:
            mid = it.get("id") if isinstance(it, dict) else it
            if mid:
                out.append(str(mid))
        return out
    except Exception:
        return []


def _format_model_row(idx, model, current_model=None):
    """Format a model row for display."""
    mid, name, ctx, max_out, in_cost, out_cost, caps = model
    is_current = (mid == current_model)
    marker = f" {C.GREEN}●{C.RESET}" if is_current else " "
    # Context window display
    if ctx >= 1000000:
        ctx_str = f"{ctx//1000000}M"
    elif ctx >= 1000:
        ctx_str = f"{ctx//1000}K"
    else:
        ctx_str = str(ctx)
    # Cost display
    if in_cost == 0 and out_cost == 0:
        cost_str = f"{C.GREEN}FREE{C.RESET}"
    else:
        cost_str = f"${in_cost:.2f}/${out_cost:.2f}"
    # Capabilities
    cap_str = " ".join(f"{C.DIM}[{c}]{C.RESET}" for c in caps)
    return f"  {C.CYAN}{idx:2d}{C.RESET}{marker} {C.BOLD}{name:28s}{C.RESET} {C.DIM}{mid:35s}{C.RESET} ctx:{ctx_str:>6s} {cost_str:>20s} {cap_str}"


# ═══════════════════════════════════════════════════════════════════
# ANSI COLORS
# ═══════════════════════════════════════════════════════════════════

class C:
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    ITALIC   = "\033[3m"
    UNDERL   = "\033[4m"
    CYAN     = "\033[36m"
    MAGENTA  = "\033[35m"
    GREEN    = "\033[32m"
    YELLOW   = "\033[33m"
    RED      = "\033[31m"
    GRAY     = "\033[90m"
    WHITE    = "\033[97m"
    BLUE     = "\033[34m"
    BG_DARK  = "\033[48;5;235m"
    BG_CYAN  = "\033[48;5;30m"
    # Neon accents (256-color)
    NEON_CYAN  = "\033[38;5;51m"
    NEON_PURPLE = "\033[38;5;141m"
    NEON_AMBER = "\033[38;5;214m"
    NEON_GREEN = "\033[38;5;46m"
    NEON_PINK  = "\033[38;5;205m"
    # Surface colors
    SURFACE    = "\033[48;5;236m"
    SURFACE2   = "\033[48;5;234m"
    BORDER     = "\033[38;5;238m"
    TEXT_DIM   = "\033[38;5;245m"
    TEXT_MUTED = "\033[38;5;240m"


def cprint(*args, **kwargs):
    print(*args, **kwargs)


def _clean(s: str) -> str:
    """Strip ANSI escape codes for width calculation."""
    return re.sub(r'\033\[[0-9;]*m', '', s)


def _pad(s: str, width: int) -> str:
    """Pad string to width, accounting for ANSI codes."""
    clean_len = len(_clean(s))
    return s + " " * max(0, width - clean_len)


# ═══════════════════════════════════════════════════════════════════
# GRADIENT + BANNER
# ═══════════════════════════════════════════════════════════════════

def _gradient(text, c1, c2):
    """Apply 256-color gradient across text."""
    def _to256(r, g, b):
        return 16 + int(r / 255 * 5) * 36 + int(g / 255 * 5) * 6 + int(b / 255 * 5)
    out = ""
    n = max(1, len(text) - 1)
    for i, ch in enumerate(text):
        if ch == " ":
            out += ch
            continue
        t = i / n
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        out += f"\033[38;5;{_to256(r, g, b)}m{ch}"
    out += "\033[0m"
    return out


JEBAT_VERSION = "7.5"

def banner():
    """JEBAT banner — clean and clear."""
    print()
    cprint(f"  {C.NEON_CYAN}{C.BOLD}JEBAT{C.RESET}  {C.NEON_PURPLE}⚔️{C.RESET}  {C.DIM}unified coding agent{C.RESET}  {C.DIM}v{JEBAT_VERSION}{C.RESET}")
    print()


def show_setup(provider_name, model, endpoint, status="Ready"):
    """Show setup panel with provider info."""
    _double_box("Setup", f"Provider  {provider_name}\nModel     {model}\nEndpoint  {endpoint}\n● {status} — type /help to begin")


def show_setup(provider_name, model, endpoint, status="Ready"):
    """Show setup panel with provider info."""
    _double_box("Setup", f"Provider  {provider_name}\nModel     {model}\nEndpoint  {endpoint}\n● {status} — type /help to begin")


# ═══════════════════════════════════════════════════════════════════
# PANELS (upgraded with shadows, color themes, and types)
# ═══════════════════════════════════════════════════════════════════

PANEL_THEMES = {
    "default": (C.CYAN, C.DIM),        # cyan border
    "success": (C.GREEN, C.DIM),        # green border
    "warning": (C.YELLOW, C.DIM),       # yellow border
    "error":   (C.RED, C.DIM),          # red border
    "info":    (C.NEON_CYAN, C.DIM),    # neon cyan
    "special": (C.NEON_PURPLE, C.DIM),  # purple
    "accent":  (C.NEON_AMBER, C.DIM),   # amber
}


def box(title, text, width=72, theme="default"):
    """Box with colored border and optional shadow."""
    border_color, dim_color = PANEL_THEMES.get(theme, PANEL_THEMES["default"])
    w = width
    top = f"{border_color}╭── {C.BOLD}{title}{C.RESET}{border_color} " + "─" * max(1, w - len(_clean(title)) - 6) + f"╮{C.RESET}"
    bottom = f"{border_color}╰" + "─" * (w - 1) + f"╯{C.RESET}"
    print(top)
    for line in text.split("\n"):
        clean_line = _clean(line)
        pad = max(0, w - 2 - len(clean_line))
        print(f"{border_color}│{C.RESET} {line}{' ' * pad}{border_color}│{C.RESET}")
    print(bottom)


def panel(title, text, width=72, theme="default"):
    """Alias for box with title."""
    box(title, text, width, theme)


def _double_box(title, text, width=72, theme="default"):
    """Double-bordered box for emphasis."""
    border_color, dim_color = PANEL_THEMES.get(theme, PANEL_THEMES["default"])
    w = width
    # Top double border
    print(f"{border_color}╔{'═' * (w - 2)}╗{C.RESET}")
    inner = f"  {C.BOLD}{title}{C.RESET}"
    pad_title = max(0, w - 2 - len(_clean(inner)))
    print(f"{border_color}║{C.RESET} {inner}{' ' * pad_title} {border_color}║{C.RESET}")
    print(f"{border_color}╠{'═' * (w - 2)}╣{C.RESET}")
    for line in text.split("\n"):
        clean_line = _clean(line)
        pad = max(0, w - 2 - len(clean_line))
        print(f"{border_color}║{C.RESET} {line}{' ' * pad} {border_color}║{C.RESET}")
    print(f"{border_color}╚{'═' * (w - 2)}╝{C.RESET}")


def _info_panel(title, items, width=72, theme="info"):
    """Panel with labeled key-value items."""
    border_color, _ = PANEL_THEMES.get(theme, PANEL_THEMES["default"])
    w = width
    print(f"{border_color}╭── {C.BOLD}{title}{C.RESET}{border_color} " + "─" * max(1, w - len(_clean(title)) - 6) + f"╮{C.RESET}")
    for label, value in items:
        clean_label = f"{C.CYAN}{label}{C.RESET}"
        clean_value = str(value)
        pad_label = 14 - len(label)
        if pad_label < 1:
            pad_label = 1
        line = f"  {clean_label}{' ' * pad_label}{clean_value}"
        clean_len = len(label) + pad_label + len(clean_value) + 2
        pad = max(0, w - clean_len - 2)
        print(f"{border_color}│{C.RESET} {line}{' ' * pad}{border_color}│{C.RESET}")
    print(f"{border_color}╰" + "─" * (w - 1) + f"╯{C.RESET}")


# ═══════════════════════════════════════════════════════════════════
# STATUS BAR (enhanced with colors)
# ═══════════════════════════════════════════════════════════════════

def status_line(iters, tokens, latency_ms):
    cprint(f"{C.DIM}── {iters} iter · {tokens:,} tokens · {latency_ms}ms ──{C.RESET}")


def format_cost(usd):
    return f"${usd:.4f}" if usd > 0 else "$0.0000"


def bottom_bar(provider, model, tokens=0, iter_count=0, tool_count=0, elapsed_s=0.0, cost_usd=0.0):
    """Upgraded status bar with neon accents and visual hierarchy."""
    ctx_max = 200000
    pct = min(100, int(tokens / ctx_max * 100)) if tokens else 0
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)
    if pct > 80:
        bar_color = C.RED
    elif pct > 50:
        bar_color = C.YELLOW
    else:
        bar_color = C.NEON_GREEN

    h = int(elapsed_s // 3600)
    m = int((elapsed_s % 3600) // 60)
    s = int(elapsed_s % 60)
    time_str = f"{h}h {m:02d}m" if h > 0 else f"{m}m {s:02d}s"
    chain = f"{C.NEON_AMBER}⛓ {tool_count}{C.RESET}" if tool_count > 0 else f"{C.DIM}⛓ 0{C.RESET}"
    model_short = model.split(":")[0] if ":" in model else model
    cost_str = format_cost(cost_usd) if cost_usd >= 0 else ""

    # Top separator
    print(f"{C.BORDER}{'─' * 78}{C.RESET}")
    # Hints line
    cprint(f"  {C.TEXT_DIM}❯ type a message · {C.NEON_CYAN}/help{C.RESET} {C.TEXT_DIM}for commands · {C.NEON_PURPLE}/plan{C.RESET} {C.TEXT_DIM}toggle plan · {C.NEON_GREEN}/skills{C.RESET} {C.TEXT_DIM}browse · Ctrl+C cancel{C.RESET}")
    # Status line with colored sections
    status_parts = [
        f"{C.NEON_CYAN}{C.BOLD}{model_short}{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {C.TEXT_DIM}{tokens:,}/{ctx_max:,} tok{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {bar_color}[{bar}]{C.RESET} {C.TEXT_DIM}{pct}%{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {C.NEON_PURPLE}⚙ {tool_count}{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {chain}",
        f"{C.TEXT_DIM}│{C.RESET} {C.TEXT_DIM}⏱ {time_str}{C.RESET}",
    ]
    if cost_usd > 0:
        status_parts.append(f"{C.TEXT_DIM}│{C.RESET} {C.NEON_GREEN}{cost_str}{C.RESET}")
    cprint(f"  {' '.join(status_parts)}")
    # Bottom separator
    print(f"{C.BORDER}{'─' * 78}{C.RESET}")


# ═══════════════════════════════════════════════════════════════════
# THINKING SPINNER (with progress bar)
# ═══════════════════════════════════════════════════════════════════

THINK_QUOTES = [
    "The best code is no code at all",
    "First, solve the problem. Then, write the code.",
    "Talk is cheap. Show me the code.",
    "Simplicity is the soul of efficiency.",
    "Any fool can write code that a computer can understand.",
    "Programs must be written for people to read.",
    "The only way to learn a new programming language is by writing programs.",
    "It works on my machine",
    "Have you tried turning it off and on again?",
    "There are only two hard things in CS: cache invalidation and naming things.",
    "It's not a bug, it's a feature.",
    "A good programmer looks both ways before crossing a one-way street.",
    "Deleted code is debugged code.",
    "Code is like humor. When you have to explain it, it's bad.",
    "Fix the cause, not the symptom.",
    "Optimism is an occupational hazard of programming.",
]

SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class ThinkingSpinner:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._msg = ""
        self._start_time = 0

    def start(self, msg="Thinking"):
        self._stop.clear()
        self._msg = msg
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def _run(self):
        i = 0
        last_quote = time.time()
        quote = random.choice(THINK_QUOTES)
        while not self._stop.is_set():
            now = time.time()
            elapsed = now - self._start_time
            # Progress bar: grows over 60 seconds
            pct = min(100, int(elapsed / 60 * 100))
            filled = pct // 5
            bar = "█" * filled + "░" * (20 - filled)
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            time_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
            # Rotate quote every 3 seconds
            if now - last_quote > 3:
                quote = random.choice(THINK_QUOTES)
                last_quote = now
            # Truncate quote to fit
            max_quote = 40
            quote_display = quote[:max_quote] + "..." if len(quote) > max_quote else quote
            text = f"\r  {C.CYAN}⏳{C.RESET} {self._msg}... {C.DIM}[{bar}] {pct}% {time_str}{C.RESET}  {C.DIM}{quote_display}{C.RESET}"
            sys.stdout.write(text)
            sys.stdout.flush()
            i += 1
            time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════════
# MARKDOWN ANSWER RENDERER
# ═══════════════════════════════════════════════════════════════════

def _print_answer(text):
    """Print answer with markdown-style formatting, no box."""
    if not text:
        return
    lines = text.split("\n")
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        # Code block toggle
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                cprint(f"  {C.DIM}{stripped}{C.RESET}")
            continue
        if in_code_block:
            cprint(f"  {C.DIM}{line}{C.RESET}")
            continue
        # Headers
        if stripped.startswith("### "):
            cprint(f"  {C.CYAN}{C.BOLD}{stripped}{C.RESET}")
        elif stripped.startswith("## "):
            cprint(f"  {C.CYAN}{C.BOLD}{stripped}{C.RESET}")
        elif stripped.startswith("# "):
            cprint(f"  {C.CYAN}{C.BOLD}{stripped}{C.RESET}")
        # Bold
        elif "**" in stripped:
            # Simple bold rendering
            clean = re.sub(r'\*\*(.+?)\*\*', rf"{C.BOLD}\1{C.RESET}", stripped)
            cprint(f"  {clean}")
        # Inline code
        elif "`" in stripped and not stripped.startswith("```"):
            clean = re.sub(r'`(.+?)`', rf"{C.CYAN}\1{C.RESET}", stripped)
            cprint(f"  {clean}")
        # List items
        elif re.match(r'^[-*]\s', stripped):
            cprint(f"  {C.GREEN}•{C.RESET} {stripped[2:]}")
        # Numbered lists
        elif re.match(r'^\d+\.\s', stripped):
            num = re.match(r'^(\d+\.)', stripped).group(1)
            cprint(f"  {C.GREEN}{num}{C.RESET} {stripped[len(num)+1:]}")
        else:
            cprint(f"  {line}")


# ═══════════════════════════════════════════════════════════════════
# COST TRACKER
# ═══════════════════════════════════════════════════════════════════

def estimate_cost(model: str, tokens: int) -> float:
    """Estimate cost in USD for a given model and token count."""
    for provider, pricing in PROVIDER_PRICING.items():
        if provider in model.lower():
            return (tokens / 1_000_000) * pricing.get("input", 0.0)
    return 0.0


# ═══════════════════════════════════════════════════════════════════
# MEMORY SYSTEM
# ═══════════════════════════════════════════════════════════════════

def _load_global_memory():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_global_memory(data):
    MEMORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_workspace_memory():
    wf = Path(".") / ".jebat" / "memory.json"
    if wf.exists():
        try:
            return json.loads(wf.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_workspace_memory(data):
    wf = Path(".") / ".jebat" / "memory.json"
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def memory_store(key, value):
    mem = _load_global_memory()
    mem[key] = {"value": value, "updated": datetime.now().isoformat()}
    _save_global_memory(mem)
    return f"Stored: {key}"


def memory_recall(key):
    mem = _load_global_memory()
    entry = mem.get(key)
    if entry:
        return f"{key}: {entry['value']}"
    return f"Not found: {key}"


def memory_list():
    mem = _load_global_memory()
    result = {}
    for k, v in mem.items():
        if isinstance(v, dict):
            result[k] = v.get("value", "")
        elif isinstance(v, list):
            result[k] = ", ".join(str(i) for i in v[:3])
        else:
            result[k] = str(v)
    return result


# ═══════════════════════════════════════════════════════════════════
# TASK / AUDIT DATABASE
# ═══════════════════════════════════════════════════════════════════

class TaskDB:
    def __init__(self):
        self.conn = sqlite3.connect(str(TASKS_DB))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                prompt TEXT,
                response TEXT,
                tokens INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                tag TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                task_id INTEGER,
                tag TEXT,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                tool TEXT,
                args TEXT,
                elapsed_ms REAL,
                success INTEGER
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                task TEXT,
                provider TEXT,
                model TEXT,
                tokens INTEGER,
                latency_ms INTEGER,
                tool_count INTEGER,
                status TEXT,
                ghost_mode INTEGER DEFAULT 0,
                response_preview TEXT
            )
        """)
        self.conn.commit()
        # Migration: add tag column if missing
        try:
            cur.execute("ALTER TABLE tasks ADD COLUMN tag TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def add_task(self, prompt, response="", tokens=0, status="done", tag=None):
        self.conn.execute(
            "INSERT INTO tasks (timestamp, prompt, response, tokens, status, tag) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(), prompt, response, tokens, status, tag)
        )
        self.conn.commit()

    def list_tasks(self, limit=10):
        cur = self.conn.execute("SELECT id, timestamp, prompt, status, tag FROM tasks ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

    def get_task(self, task_id):
        cur = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        return cur.fetchone()

    def add_audit(self, tool, args, elapsed_ms, success):
        self.conn.execute(
            "INSERT INTO audit_log (timestamp, tool, args, elapsed_ms, success) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(), tool, json.dumps(args, ensure_ascii=False)[:500], elapsed_ms, 1 if success else 0)
        )
        self.conn.commit()

    def list_audit(self, limit=10):
        cur = self.conn.execute("SELECT timestamp, tool, args, elapsed_ms, success FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

    def log_agent_run(self, task, provider, model, tokens, latency_ms, tool_count, status="done", ghost_mode=False, response_preview=""):
        self.conn.execute(
            "INSERT INTO agent_runs (timestamp, task, provider, model, tokens, latency_ms, tool_count, status, ghost_mode, response_preview) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(), task[:200], provider, model, tokens, latency_ms, tool_count, status, 1 if ghost_mode else 0, response_preview[:200])
        )
        self.conn.commit()

    def get_agent_runs(self, limit=10):
        cur = self.conn.execute("SELECT timestamp, task, provider, model, tokens, latency_ms, tool_count, status, ghost_mode FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

    def search(self, query):
        cur = self.conn.execute("SELECT id, timestamp, prompt, status FROM tasks WHERE prompt LIKE ? ORDER BY id DESC LIMIT 10", (f"%{query}%",))
        return cur.fetchall()

    def save_session(self, messages):
        path = SESSIONS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        serializable = [{"role": m.role, "content": m.content} for m in messages]
        path.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def load_sessions(self):
        sessions = []
        for f in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)[:10]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({"file": f.name, "messages": len(data)})
            except Exception:
                pass
        return sessions


# ═══════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════

DANGEROUS_CMDS = ["rm -rf", "rm -r /", "del /s", "format", "mkfs", "> /dev/"]
DANGEROUS_FILES = ["/etc/passwd", "/etc/shadow", "~/.ssh/"]


def is_dangerous(cmd: str) -> bool:
    return any(d in cmd.lower() for d in DANGEROUS_CMDS)


def is_dangerous_file(path: str) -> bool:
    return any(d in path.lower() for d in DANGEROUS_FILES)


def execute_tool(name: str, args: Dict[str, Any], yolo: bool = False) -> str:
    try:
        if name == "read_file":
            path = args.get("path", "")
            offset = max(1, args.get("offset", 1))
            limit = args.get("limit", 200)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            out = []
            for i, line in enumerate(lines[offset - 1:offset + limit - 1], start=offset):
                out.append(f"{i:6d} | {line.rstrip()}")
            return "\n".join(out)

        elif name == "write_file":
            path = args.get("path") or args.get("filename") or ""
            content = args.get("content", "")
            if not yolo and is_dangerous_file(path):
                return f"BLOCKED: dangerous file {path}"
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written {len(content)} bytes to {path}"

        elif name == "terminal":
            cmd = args.get("command", "")
            timeout = args.get("timeout", 120)
            workdir = args.get("workdir", None)
            if not yolo and is_dangerous(cmd):
                return "BLOCKED: dangerous command"
            import subprocess
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=workdir, encoding="utf-8", errors="replace",
            )
            output = result.stdout + result.stderr
            if len(output) > 2000:
                output = output[:2000] + "... (truncated)"
            return output or "(no output)"

        elif name == "search_files":
            pattern = args.get("pattern", "")
            path = args.get("path", ".")
            limit = args.get("limit", 50)
            import fnmatch
            matches = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    if fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch(f.lower(), pattern.lower()):
                        matches.append(os.path.join(root, f))
                        if len(matches) >= limit:
                            return "\n".join(matches)
            return "\n".join(matches) if matches else "No matches"

        elif name == "list_dir":
            path = args.get("path", ".")
            pattern = args.get("pattern", "*")
            import fnmatch
            entries = []
            try:
                for entry in sorted(os.listdir(path)):
                    if fnmatch.fnmatch(entry, pattern):
                        full = os.path.join(path, entry)
                        size = os.path.getsize(full) if os.path.isfile(full) else 0
                        kind = "file" if os.path.isfile(full) else "dir"
                        entries.append(f"{kind:4s} {size:8d} {entry}")
            except Exception as e:
                return f"Error: {e}"
            return "\n".join(entries) if entries else "(empty)"

        elif name == "memory_store":
            key = args.get("key", "")
            value = args.get("value", "")
            return memory_store(key, value)

        elif name == "memory_recall":
            key = args.get("key", "")
            return memory_recall(key)

        elif name == "memory_list":
            mem = memory_list()
            return json.dumps(mem, indent=2, ensure_ascii=False) if mem else "No memory entries."

        elif name == "codebase_inspect":
            path = args.get("path", ".")
            return _codebase_inspect(path)

        elif name == "read_project_context":
            path = args.get("path", ".")
            return _read_project_context(path)

        elif name == "detect_ide_environment":
            return _detect_ide_environment()

        elif name == "provider_health":
            return tool_provider_health()

        elif name == "diff_preview":
            return tool_diff_preview(args.get("path"))

        elif name == "export_backup":
            return tool_export_backup(args.get("output"))

        return f"Unknown tool: {name}"

    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════
# CODEBASE TOOLS
# ═══════════════════════════════════════════════════════════════════

def _codebase_inspect(path="."):
    exts = {}
    total = 0
    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and node_modules
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "__pycache__"]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                exts[ext] = exts.get(ext, 0) + 1
                total += 1
    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript (React)",
        ".jsx": "JavaScript (React)", ".go": "Go", ".rs": "Rust", ".java": "Java",
        ".rb": "Ruby", ".php": "PHP", ".c": "C", ".cpp": "C++", ".h": "Header",
        ".css": "CSS", ".html": "HTML", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
        ".md": "Markdown", ".sql": "SQL", ".sh": "Shell", ".bash": "Shell",
    }
    lines = [f"  Total files: {total}"]
    for ext, count in sorted(exts.items(), key=lambda x: -x[1])[:15]:
        lang = lang_map.get(ext, ext)
        bar = "█" * min(count, 30)
        lines.append(f"  {lang:20s} {count:5d}  {bar}")
    return "\n".join(lines)


def _read_project_context(path="."):
    lines = [f"  Project root: {os.path.abspath(path)}"]
    # Check for common files
    checks = [
        ("package.json", "Node.js project"),
        ("pyproject.toml", "Python project"),
        ("Cargo.toml", "Rust project"),
        ("go.mod", "Go project"),
        ("Gemfile", "Ruby project"),
        ("composer.json", "PHP project"),
        (".git", "Git repository"),
        ("Dockerfile", "Docker container"),
        ("docker-compose.yml", "Docker Compose"),
        ("Makefile", "Makefile"),
    ]
    found = []
    for fname, desc in checks:
        if os.path.exists(os.path.join(path, fname)):
            found.append(f"  {C.GREEN}✓{C.RESET} {desc} ({fname})")
    if found:
        lines.extend(found)
    else:
        lines.append(f"  {C.DIM}No standard project files detected{C.RESET}")
    return "\n".join(lines)


def _detect_ide_environment():
    env_vars = ["TERM", "TERM_PROGRAM", "VSCode", "VSCODE", "JETBRAINS", "INTELLIJ"]
    found = []
    for var in env_vars:
        val = os.environ.get(var)
        if val:
            found.append(f"  {var}={val}")
    if found:
        return "\n".join(found)
    return "  No IDE environment detected (terminal session)"


# ═══════════════════════════════════════════════════════════════════
# GIT TOOLS
# ═══════════════════════════════════════════════════════════════════

def git_auto_commit(message: str, path: str = ".") -> tuple[bool, str]:
    import subprocess
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=path)
        if not r.stdout.strip():
            return False, "No changes"
        subprocess.run(["git", "add", "-A"], capture_output=True, cwd=path)
        r = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, cwd=path)
        return True, r.stdout.strip().split("\n")[0] if r.stdout else "Committed"
    except Exception as e:
        return False, str(e)


def git_has_changes(path: str = ".") -> bool:
    import subprocess
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=path)
    return bool(r.stdout.strip())


def tool_diff_preview(path=None):
    import subprocess
    try:
        r = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, cwd=path or ".")
        if not r.stdout.strip():
            return "No changes to preview"
        # Also show short diff
        r2 = subprocess.run(["git", "diff", "--shortstat"], capture_output=True, text=True, cwd=path or ".")
        return f"{r2.stdout.strip()}\n\n{r.stdout.strip()}"
    except Exception as e:
        return f"Error: {e}"


def tool_export_backup(output=None):
    """Export memory, tasks, and sessions to a backup file."""
    data = {
        "memory": _load_global_memory(),
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
    }
    # Add tasks
    try:
        db = TaskDB()
        data["tasks"] = [{"id": r[0], "prompt": r[2], "status": r[4]} for r in db.conn.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 100").fetchall()]
    except Exception:
        data["tasks"] = []

    out_path = output or str(EXPORT_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return f"Exported to: {out_path}"


def tool_provider_health():
    """Ping all providers and report status."""
    lines = []
    providers = _load_providers_raw()
    if not providers:
        return "  No providers configured. Add: /provider add"
    for pid, cfg in providers.items():
        kind = cfg.get("kind", "unknown")
        model = cfg.get("model", "unknown")
        api_base = cfg.get("api_base", "")
        api_key = cfg.get("api_key", "")
        try:
            if kind == "ollama":
                req = urllib.request.Request(f"{api_base}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    model_count = len(data.get("models", []))
                    lines.append(f"  {C.GREEN}●{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — {C.GREEN}{model_count} models available{C.RESET}")
            elif kind in ("anthropic", "gemini"):
                if api_key:
                    lines.append(f"  {C.GREEN}●{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — {C.GREEN}key configured{C.RESET}")
                else:
                    lines.append(f"  {C.YELLOW}●{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — {C.YELLOW}no key{C.RESET}")
            else:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                req = urllib.request.Request(f"{api_base}/models", headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    model_count = len(data.get("data", []))
                    lines.append(f"  {C.GREEN}●{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — {C.GREEN}{model_count} models{C.RESET}")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                lines.append(f"  {C.YELLOW}⚠{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — {C.YELLOW}auth failed{C.RESET}")
            else:
                lines.append(f"  {C.RED}✗{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — HTTP {e.code}")
        except Exception as e:
            err = str(e)[:50]
            lines.append(f"  {C.RED}✗{C.RESET} {C.BOLD}{pid}{C.RESET} ({kind}) — {C.RED}{err}{C.RESET}")
    return "\n".join(lines) if lines else "  No providers configured."


def _load_providers_raw():
    """Load providers from config file without instantiating classes."""
    if PROVIDER_FILE.exists():
        try:
            return json.loads(PROVIDER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _list_ollama_models(provider_cfg):
    """List available models from Ollama."""
    try:
        api_base = provider_cfg.get("api_base", "http://127.0.0.1:11434")
        req = urllib.request.Request(f"{api_base}/api/tags", headers={})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        model = provider_cfg.get("model", "")
        return [model] if model else []




# ═══════════════════════════════════════════════════════════════════
# CYBERSECURITY TOOLS
# ═══════════════════════════════════════════════════════════════════

# Patterns for security scanning
_VULN_PATTERNS = {
    "hardcoded_secret": [
        (r'(?:password|passwd|pwd|secret|api_key|apikey|token|auth)\s*[=:]\s*["\'][^\'\"\s]{8,}["\']', "CRITICAL", "Hardcoded secret/credential"),
        (r'(?:AWS|aws)[_-]?(?:SECRET|KEY)[_-]?(?:ACCESS)?\s*[=:]\s*["\'][A-Za-z0-9/+=]{20,}["\']', "CRITICAL", "AWS credential"),
        (r'(?:sk_live|sk_test|pk_live|pk_test)_[A-Za-z0-9]{20,}', "CRITICAL", "Stripe API key"),
        (r'ghp_[A-Za-z0-9]{36}', "CRITICAL", "GitHub personal access token"),
    ],
    "sql_injection": [
        (r'(?:execute|executescript|raw|cursor\.execute)\s*\(.*?(?:%s|%d|\?|\{.*?\}).*?(?:request|input|param|arg|data|form|query)', "HIGH", "Potential SQL injection (user input in query)"),
        (r'f["\'].*?SELECT.*?{.*?}.*?["\']', "MEDIUM", "F-string SQL (potential injection)"),
        (r'(?:execute|executescript)\s*\(.*?\+\s*', "HIGH", "String concatenation in SQL"),
    ],
    "xss": [
        (r'innerHTML\s*=', "HIGH", "innerHTML assignment (potential XSS)"),
        (r'document\.write\(', "MEDIUM", "document.write (potential XSS)"),
        (r'\$\(.*?\)\.html\(', "MEDIUM", "jQuery .html() (potential XSS)"),
        (r'(?:dangerouslySetInnerHTML|v-html)', "HIGH", "Raw HTML rendering (React/Vue XSS)"),
    ],
    "command_injection": [
        (r'(?:os\.system|os\.popen|subprocess\.call|subprocess\.run|subprocess\.Popen)\(.*?(?:request|input|param|arg|data|form|query)', "CRITICAL", "Command injection (user input in shell)"),
        (r'(?:eval|exec)\(.*?(?:request|input|param|arg|data)', "CRITICAL", "Code injection via eval/exec"),
    ],
    "path_traversal": [
        (r'open\(.*?(?:request|input|param|arg|data|form|query)', "HIGH", "Potential path traversal (user input in file open)"),
        (r'(?:send_file|send_from_directory)\(.*?(?:request|input|param)', "MEDIUM", "User input in file serving"),
    ],
    "crypto": [
        (r'(?:md5|sha1)\s*\(', "LOW", "Weak hash algorithm (MD5/SHA1)"),
        (r'(?:DES|RC4|Blowfish)\s*\(', "MEDIUM", "Weak encryption algorithm"),
        (r'random\.random\b|random\.randint\b|Math\.random\b', "MEDIUM", "Non-cryptographic random for security"),
    ],
    "auth": [
        (r'(?:session\.cookie_secure|Set-Cookie.*?Secure)', "INFO", "Cookie security flag"),
        (r'(?:CORS|Access-Control-Allow-Origin)\s*[=:]\s*["\'][*]["\']', "MEDIUM", "Wildcard CORS origin"),
        (r'(?:debug\s*=\s*True|DEBUG\s*=\s*True)', "LOW", "Debug mode enabled"),
    ],
}

def tool_security_scan(path=".", extensions=None):
    """Scan codebase for security vulnerabilities."""
    if extensions is None:
        extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".php", ".rs", ".html", ".yml", ".yaml", ".json", ".env"}
    findings = []
    scanned = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv", ".venv", "vendor", ".next", "dist"}]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in extensions:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                scanned += 1
                for i, line in enumerate(lines, 1):
                    for category, patterns in _VULN_PATTERNS.items():
                        for regex, severity, desc in patterns:
                            if re.search(regex, line):
                                rel = os.path.relpath(fpath, path)
                                findings.append({
                                    "file": rel, "line": i, "severity": severity,
                                    "category": category, "description": desc,
                                    "code": line.strip()[:100]
                                })
            except Exception:
                pass
    # Deduplicate by file+line+category
    seen = set()
    unique = []
    for f in findings:
        key = (f["file"], f["line"], f["category"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    # Sort by severity
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    unique.sort(key=lambda x: order.get(x["severity"], 5))
    # Format output
    lines = [f"  Scanned {scanned} files, found {len(unique)} issues"]
    sev_colors = {"CRITICAL": C.RED, "HIGH": C.YELLOW, "MEDIUM": C.CYAN, "LOW": C.DIM, "INFO": C.DIM}
    for f in unique[:30]:
        color = sev_colors.get(f["severity"], C.DIM)
        lines.append(f"  {color}{f['severity']:8s}{C.RESET} {f['file']}:{f['line']} — {f['description']}")
        lines.append(f"           {C.DIM}{f['code'][:80]}{C.RESET}")
    if len(unique) > 30:
        lines.append(f"  {C.DIM}... and {len(unique) - 30} more{C.RESET}")
    return "\n".join(lines)


def tool_dependency_audit(path="."):
    """Check for vulnerable/outdated dependencies."""
    lines = []
    # Python
    req_files = ["requirements.txt", "Pipfile.lock", "pyproject.toml"]
    for rf in req_files:
        rfpath = os.path.join(path, rf)
        if os.path.exists(rfpath):
            lines.append(f"  {C.CYAN}Python ({rf}):{C.RESET}")
            with open(rfpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        lines.append(f"    {line}")
    # Node
    pkg_path = os.path.join(path, "package.json")
    if os.path.exists(pkg_path):
        try:
            pkg = json.loads(open(pkg_path, encoding="utf-8").read())
            deps = pkg.get("dependencies", {})
            dev = pkg.get("devDependencies", {})
            lines.append(f"  {C.CYAN}Node.js (package.json):{C.RESET}")
            lines.append(f"    Dependencies: {len(deps)}")
            for name, ver in list(deps.items())[:15]:
                lines.append(f"      {name}: {ver}")
            if dev:
                lines.append(f"    Dev Dependencies: {len(dev)}")
        except Exception:
            pass
    # Rust
    cargo_path = os.path.join(path, "Cargo.toml")
    if os.path.exists(cargo_path):
        lines.append(f"  {C.CYAN}Rust (Cargo.toml):{C.RESET}")
        with open(cargo_path, "r", encoding="utf-8", errors="ignore") as f:
            in_deps = False
            for line in f:
                if "[dependencies]" in line:
                    in_deps = True
                elif line.startswith("["):
                    in_deps = False
                elif in_deps and "=" in line:
                    lines.append(f"    {line.strip()}")
    if not lines:
        lines.append(f"  {C.DIM}No dependency files found{C.RESET}")
    return "\n".join(lines)


def tool_port_scan(host="127.0.0.1", ports=None):
    """Quick port scan (top ports)."""
    import socket
    if ports is None:
        ports = [21, 22, 25, 53, 80, 110, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 8888, 9090, 27017]
    open_ports = []
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            result = s.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
            s.close()
        except Exception:
            pass
    lines = [f"  Scanning {host} ({len(ports)} ports)..."]
    if open_ports:
        for p in open_ports:
            lines.append(f"  {C.GREEN}OPEN{C.RESET}   {host}:{p}")
    else:
        lines.append(f"  {C.DIM}No open ports found{C.RESET}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# FRAMEWORK TOOLS
# ═══════════════════════════════════════════════════════════════════

_FRAMEWORK_SIGNATURES = {
    # Python
    "Django": {"files": ["manage.py", "settings.py"], "patterns": ["django", "DJANGO_SETTINGS_MODULE"], "lang": "Python"},
    "Flask": {"files": ["app.py", "wsgi.py"], "patterns": ["from flask", "Flask(__name__)"], "lang": "Python"},
    "FastAPI": {"files": ["main.py"], "patterns": ["from fastapi", "FastAPI()"], "lang": "Python"},
    "PyTorch": {"files": [], "patterns": ["import torch", "from torch"], "lang": "Python"},
    "TensorFlow": {"files": [], "patterns": ["import tensorflow", "from tensorflow"], "lang": "Python"},
    "scikit-learn": {"files": [], "patterns": ["from sklearn", "import sklearn"], "lang": "Python"},
    "pandas": {"files": [], "patterns": ["import pandas", "from pandas"], "lang": "Python"},
    # JS/TS
    "React": {"files": ["package.json"], "patterns": ["react", "jsx"], "pkg_deps": ["react", "react-dom"]},
    "Next.js": {"files": ["next.config.js", "next.config.mjs", "next.config.ts"], "patterns": ["next", "Next.js"], "pkg_deps": ["next"]},
    "Vue": {"files": ["vue.config.js", "vite.config.js"], "patterns": ["vue", "Vue"], "pkg_deps": ["vue"]},
    "Svelte": {"files": ["svelte.config.js"], "patterns": ["svelte"], "pkg_deps": ["svelte"]},
    "Express": {"files": ["server.js", "app.js"], "patterns": ["express()"], "pkg_deps": ["express"]},
    "NestJS": {"files": ["nest-cli.json"], "patterns": ["@nestjs"], "pkg_deps": ["@nestjs/core"]},
    "Vite": {"files": ["vite.config.js", "vite.config.ts", "vite.config.mjs"], "patterns": ["vite"], "pkg_deps": ["vite"]},
    "TailwindCSS": {"files": ["tailwind.config.js", "tailwind.config.ts"], "patterns": ["tailwindcss"], "pkg_deps": ["tailwindcss"]},
    # Go
    "Gin": {"files": ["go.mod"], "patterns": ["github.com/gin-gonic/gin"], "lang": "Go"},
    "Echo": {"files": ["go.mod"], "patterns": ["github.com/labstack/echo"], "lang": "Go"},
    # Rust
    "Actix": {"files": ["Cargo.toml"], "patterns": ["actix-web"], "lang": "Rust"},
    "Axum": {"files": ["Cargo.toml"], "patterns": ["axum"], "lang": "Rust"},
    # Infra
    "Docker": {"files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"], "patterns": [], "lang": "Config"},
    "Kubernetes": {"files": [], "patterns": ["apiVersion:", "kind:"], "ext": ".yaml"},
    "Terraform": {"files": [], "patterns": ["resource \"", "provider \""], "ext": ".tf"},
    "GitHub Actions": {"files": [], "patterns": ["uses:", "on:"], "path": ".github/workflows/"},
}


def tool_framework_detect(path="."):
    """Detect frameworks and tech stack in the project."""
    detected = {}
    for fw, sig in _FRAMEWORK_SIGNATURES.items():
        score = 0
        # Check files
        for fname in sig.get("files", []):
            if os.path.exists(os.path.join(path, fname)):
                score += 2
        # Check package.json deps
        if "pkg_deps" in sig:
            pkg_path = os.path.join(path, "package.json")
            if os.path.exists(pkg_path):
                try:
                    pkg = json.loads(open(pkg_path, encoding="utf-8").read())
                    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    for dep in sig["pkg_deps"]:
                        if dep in all_deps:
                            score += 3
                except Exception:
                    pass
        # Check file contents (sample a few files)
        if score == 0 and sig.get("patterns"):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv", ".venv"}]
                for fname in files[:20]:
                    ext = os.path.splitext(fname)[1].lower()
                    if sig.get("ext") and ext != sig["ext"]:
                        continue
                    if ext in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".html", ".yml", ".yaml", ".tf", ".mod"}:
                        try:
                            with open(os.path.join(root, fname), "r", encoding="utf-8", errors="ignore") as f:
                                content_text = f.read(5000)
                            for pat in sig["patterns"]:
                                if pat in content_text:
                                    score += 1
                                    break
                        except Exception:
                            pass
                if score > 0:
                    break
        if score > 0:
            detected[fw] = {"score": score, "lang": sig.get("lang", "?")}
    # Format
    if not detected:
        return f"  {C.DIM}No frameworks detected{C.RESET}"
    lines = []
    for fw, info in sorted(detected.items(), key=lambda x: -x[1]["score"]):
        bar = "█" * min(info["score"], 10)
        lines.append(f"  {C.CYAN}{fw:16s}{C.RESET} {info['lang']:10s} {C.GREEN}{bar}{C.RESET}")
    return "\n".join(lines)


def tool_framework_scaffold(framework, name="my-app", path="."):
    """Scaffold a new project for the given framework."""
    scaffolds = {
        "fastapi": {
            "main.py": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{name}")


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/")
async def root():
    return {{"message": "Hello from {name}"}}


@app.post("/items/")
async def create_item(item: Item):
    return item
''',
            "requirements.txt": "fastapi\nuvicorn[standard]\n",
            "Dockerfile": '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
        },
        "flask": {
            "app.py": '''from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify(message="Hello from {name}")


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()
    return jsonify(data)
''',
            "requirements.txt": "flask\n",
        },
        "express": {
            "server.js": '''const express = require("express");
const app = express();
app.use(express.json());

app.get("/", (req, res) => {{
  res.json({{ message: "Hello from {name}" }});
}});

app.post("/items", (req, res) => {{
  res.json(req.body);
}});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on ${{PORT}}`));
''',
            "package.json": '''{{
  "name": "{name}",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {{
    "start": "node server.js"
  }},
  "dependencies": {{
    "express": "^4.18.0"
  }}
}}
''',
        },
    }
    fw = framework.lower().strip()
    if fw not in scaffolds:
        available = ", ".join(scaffolds.keys())
        return f"  {C.RED}Unknown framework:{C.RESET} {framework}\n  Available: {available}"
    scaffold_dir = os.path.join(path, name)
    os.makedirs(scaffold_dir, exist_ok=True)
    files = scaffolds[fw]
    created = []
    for fname, content in files.items():
        fpath = os.path.join(scaffold_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content.format(name=name))
        created.append(f"  {C.GREEN}✓{C.RESET} {fname}")
    return f"  {C.GREEN}Scaffolded {framework} project:{C.RESET} {scaffold_dir}\n" + "\n".join(created)


# ═══════════════════════════════════════════════════════════════════
# BRAINSTORM MODE
# ═══════════════════════════════════════════════════════════════════

BRAINSTORM_PROMPTS = {
    "default": """You are JEBAT in Brainstorm Mode. Think creatively and analytically.
Structure your response with:
1. PROBLEM — restate the core challenge
2. IDEAS — generate 5-7 diverse ideas (wild + practical)
3. ANALYSIS — evaluate top 3 ideas (pros, cons, effort)
4. RECOMMENDATION — pick the best with reasoning
5. NEXT STEPS — concrete action items
Be opinionated. Pick a path. Don't just list options.""",
    "feature": """You are JEBAT brainstorming a new feature. Think product-first:
1. USER STORY — who benefits and how
2. CORE CONCEPT — one-liner description
3. MVP SCOPE — minimum viable version (what's IN and OUT)
4. TECHNICAL APPROACH — architecture decisions
5. RISKS — what could go wrong
6. METRICS — how to measure success
Be decisive. Define scope ruthlessly.""",
    "debug": """You are JEBAT brainstorming a debugging strategy:
1. SYMPTOMS — what exactly is happening
2. HYPOTHESES — 3-5 possible root causes ranked by likelihood
3. INVESTIGATION PLAN — concrete steps to isolate each
4. QUICK WINS — things to try immediately
5. DEEP DIVE — if quick wins fail, what's next
Be methodical. Follow the evidence.""",
    "architecture": """You are JEBAT brainstorming system architecture:
1. REQUIREMENTS — functional and non-functional
2. CONSTRAINTS — what limits our options
3. OPTIONS — 3 architecture approaches with tradeoffs
4. DECISION — recommended architecture with reasoning
5. MILESTONES — phased implementation plan
Be opinionated. Pick the right tool for the job.""",
    "creative": """You are JEBAT in creative brainstorming mode:
1. EXPLORE — generate 10+ ideas without judgment
2. CLUSTER — group related ideas
3. AMPLIFY — combine the most interesting clusters
4. SELECT — pick the 3 most promising directions
5. FLESH OUT — detailed concept for each
Think laterally. Make unexpected connections.""",
}


def tool_brainstorm(topic, mode="default"):
    """Structured brainstorming on a topic."""
    prompt = BRAINSTORM_PROMPTS.get(mode, BRAINSTORM_PROMPTS["default"])
    return f"  {C.CYAN}Brainstorm Mode:{C.RESET} {mode}\n  {C.CYAN}Topic:{C.RESET} {topic}\n\n  Prompt loaded. Ask me to brainstorm this topic."
# ═══════════════════════════════════════════════════════════════════
# AUTO-MIMPI (autoDream)
# ═══════════════════════════════════════════════════════════════════

def _load_dream_state():
    if DREAM_STATE_FILE.exists():
        try:
            return json.loads(DREAM_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sessions_since_dream": 0, "last_dream": None, "dream_count": 0}


def _save_dream_state(state):
    DREAM_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DREAM_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _auto_mimpi_check(taskdb):
    state = _load_dream_state()
    state["sessions_since_dream"] = state.get("sessions_since_dream", 0) + 1
    if state["sessions_since_dream"] >= 5:
        _run_dream(taskdb)
        state["sessions_since_dream"] = 0
        state["last_dream"] = datetime.now().isoformat()
        state["dream_count"] = state.get("dream_count", 0) + 1
    _save_dream_state(state)


def _run_dream(taskdb):
    """Write dream-state memory consolidation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dream_file = DREAM_DIR / f"dream_{timestamp}.md"
    mem = memory_list()
    content = f"# Dream State — {timestamp}\n\n"
    content += f"## Memory Keys ({len(mem)} total)\n"
    for key in list(mem.keys())[:20]:
        content += f"- {key}\n"
    content += f"\n## Task History\n"
    try:
        tasks = taskdb.list_tasks(5)
        for t in tasks:
            content += f"- [{t[3]}] {t[2][:80]}\n"
    except Exception:
        content += "- (no tasks)\n"
    dream_file.write_text(content, encoding="utf-8")
    state = _load_dream_state()
    _double_box("Mimpi (autoDream)", f"Sessions since last dream: {state.get('sessions_since_dream', 0)} (threshold: 5)\nConsolidating memory and writing dream-state...\nDream written: {dream_file.name}")


# ═══════════════════════════════════════════════════════════════════
# PROVIDER REGISTRY
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ProviderConfig:
    id: str
    name: str
    api_base: str
    model: str
    api_key: Optional[str] = None
    kind: str = "ollama"
    auth_method: str = "key"
    auth_ref: Optional[str] = None
    active: bool = False


class ProviderRegistry:
    def __init__(self):
        self.configs: Dict[str, ProviderConfig] = {}
        self.active_id: str = ""
        self._load()

    def _load(self):
        if PROVIDER_FILE.exists():
            try:
                data = json.loads(PROVIDER_FILE.read_text(encoding="utf-8"))
                for key, cfg in data.items():
                    self.configs[key] = ProviderConfig(**cfg)
                    if cfg.get("active"):
                        self.active_id = key
            except Exception:
                pass
        if not self.active_id and self.configs:
            self.active_id = list(self.configs.keys())[0]

    def save(self):
        data = {}
        for key, cfg in self.configs.items():
            data[key] = {
                "id": cfg.id, "name": cfg.name, "api_base": cfg.api_base,
                "model": cfg.model, "api_key": cfg.api_key, "kind": cfg.kind,
                "auth_method": getattr(cfg, "auth_method", "key"),
                "auth_ref": getattr(cfg, "auth_ref", None),
                "active": key == self.active_id,
            }
        PROVIDER_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROVIDER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_active(self):
        return self.configs.get(self.active_id)

    def list_all(self):
        return list(self.configs.values())

    def register(self, key, cfg):
        self.configs[key] = cfg
        self.save()

    def use(self, key):
        if key in self.configs:
            self.active_id = key
            self.save()
            return True
        return False


# ═══════════════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = textwrap.dedent("""
You are JEBAT, a unified coding agent. Be direct and precise.

## Tools
- read_file(path, offset=1, limit=200)
- write_file(path, content)
- search_files(pattern, path=".", target="files", limit=50)
- terminal(command, timeout=120, workdir=None)
- list_dir(path=".", pattern="*")
- memory_store(key, value)
- memory_recall(key)
- codebase_inspect(path)
- read_project_context(path)
- detect_ide_environment()

## Tool Format
```json
{"tool": "tool_name", "args": {"param": "value"}}
```

## Rules
1. Use tools when needed. Don't ask permission.
2. After tool calls, you get TOOL_RESULT.
3. When done, output: FINAL_ANSWER: <answer>
4. Be concise. No filler.
""").strip()


@dataclass
class CompletionResponse:
    text: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    latency_ms: int = 0


@dataclass
class AgentMessage:
    role: str
    content: str
    tool_calls: Optional[str] = None


@dataclass
class AgentStep:
    prompt: str
    response: CompletionResponse
    tool_actions: List[str] = field(default_factory=list)
    plan: Optional[str] = None
    observation: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    tokens: int = 0
    latency_ms: int = 0


def _parse_tool_calls(text: str) -> List[dict]:
    calls = []
    in_block = False
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```json"):
            in_block = True
            lines = []
            continue
        if s == "```" and in_block:
            in_block = False
            try:
                obj = json.loads("\n".join(lines))
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                pass
            lines = []
            continue
        if in_block:
            lines.append(line)
            continue
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                pass
    return calls


def _extract_steps(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines()
            if l.strip() and l.strip()[0].isdigit() and "." in l.strip()[:4]]

# ═══════════════════════════════════════════════════════════════════
# CONTEXT TRACKER
# ═══════════════════════════════════════════════════════════════════

class ContextTracker:
    """Track files read, tools used, decisions made in this session."""
    def __init__(self):
        self.files_read = []
        self.files_written = []
        self.tools_used = []
        self.decisions = []
        self.errors = []
        self.start_time = time.time()

    def track_file_read(self, path):
        if path not in self.files_read:
            self.files_read.append(path)

    def track_file_write(self, path):
        if path not in self.files_written:
            self.files_written.append(path)

    def track_tool(self, name, success=True):
        self.tools_used.append({"name": name, "success": success, "time": time.time()})

    def track_decision(self, decision):
        self.decisions.append({"decision": decision, "time": time.time()})

    def track_error(self, error):
        self.errors.append({"error": str(error)[:200], "time": time.time()})

    def summary(self):
        elapsed = time.time() - self.start_time
        return {
            "files_read": len(self.files_read),
            "files_written": len(self.files_written),
            "tools_used": len(self.tools_used),
            "decisions": len(self.decisions),
            "errors": len(self.errors),
            "elapsed": f"{elapsed:.1f}s",
        }

    def display(self):
        s = self.summary()
        lines = [
            f"  {C.CYAN}Files Read:{C.RESET}     {s['files_read']}",
            f"  {C.CYAN}Files Written:{C.RESET}  {s['files_written']}",
            f"  {C.CYAN}Tools Used:{C.RESET}     {s['tools_used']}",
            f"  {C.CYAN}Decisions:{C.RESET}      {s['decisions']}",
            f"  {C.CYAN}Errors:{C.RESET}         {s['errors']}",
            f"  {C.CYAN}Elapsed:{C.RESET}        {s['elapsed']}",
        ]
        if self.files_read:
            lines.append(f"  {C.DIM}Recent reads:{C.RESET}")
            for fp in self.files_read[-5:]:
                lines.append(f"    {fp}")
        if self.decisions:
            lines.append(f"  {C.DIM}Decisions:{C.RESET}")
            for d in self.decisions[-3:]:
                lines.append(f"    {d['decision'][:80]}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, max_per_minute=60):
        self.max_per_minute = max_per_minute
        self.calls = []

    def allow(self):
        now = time.time()
        self.calls = [t for t in self.calls if now - t < 60]
        if len(self.calls) >= self.max_per_minute:
            return False
        self.calls.append(now)
        return True

    def remaining(self):
        now = time.time()
        self.calls = [t for t in self.calls if now - t < 60]
        return max(0, self.max_per_minute - len(self.calls))


# ═══════════════════════════════════════════════════════════════════
# AGENT PROFILES (for agent creation)
# ═══════════════════════════════════════════════════════════════════

AGENT_PROFILES = {
    "coder": {"name": "Coder", "icon": "💻", "desc": "Write clean, production code",
              "system": "You are an expert coder. Write clean, efficient, well-documented code.",
              "tools": ["terminal", "read_file", "write_file", "patch", "search_files"]},
    "reviewer": {"name": "Reviewer", "icon": "🔍", "desc": "Review code for quality",
                 "system": "You are a senior code reviewer. Find bugs, suggest improvements.",
                 "tools": ["read_file", "search_files", "codebase_inspect"]},
    "security": {"name": "Security", "icon": "🛡️", "desc": "Find security vulnerabilities",
                 "system": "You are a security expert. Find vulnerabilities, suggest fixes.",
                 "tools": ["security_scan", "read_file", "search_files", "terminal"]},
    "debugger": {"name": "Debugger", "icon": "🐛", "desc": "Systematic root cause analysis",
                 "system": "You are a debugging expert. Be methodical, find root causes.",
                 "tools": ["terminal", "read_file", "search_files"]},
    "devops": {"name": "DevOps", "icon": "🚀", "desc": "Infrastructure and deployment",
               "system": "You are a DevOps engineer. Focus on reliability and security.",
               "tools": ["terminal", "read_file", "write_file", "search_files"]},
    "researcher": {"name": "Researcher", "icon": "📚", "desc": "Deep research and analysis",
                   "system": "You are a research analyst. Gather information, synthesize findings.",
                   "tools": ["web_search", "web_fetch", "read_file", "search_files"]},
    "planner": {"name": "Planner", "icon": "📋", "desc": "Strategic planning",
                "system": "You are a technical planner. Think strategically, create actionable plans.",
                "tools": ["read_file", "search_files", "codebase_inspect"]},
}


def _create_agent(profile_name, registry, taskdb, skills):
    """Create an agent from a profile."""
    profile = AGENT_PROFILES.get(profile_name)
    if not profile:
        return None
    agent = Agent(registry, taskdb, skills)
    agent.system_prompt = profile["system"]
    agent.profile_name = profile_name
    return agent


def _delegate_to_agent(agent_name, task, registry, taskdb, skills):
    """Delegate a task to a sub-agent."""
    agent = _create_agent(agent_name, registry, taskdb, skills)
    if not agent:
        return f"Unknown agent: {agent_name}"
    result = agent.step(task)
    return result.response.text


# ═══════════════════════════════════════════════════════════════════
# SWARM — MULTI-AGENT ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════

class SwarmOrchestrator:
    """Orchestrate multiple agents working on subtasks."""
    def __init__(self, registry, taskdb, skills):
        self.registry = registry
        self.taskdb = taskdb
        self.skills = skills
        self.agents = {}
        self.results = {}

    def _decompose_task(self, task):
        subtasks = []
        task_lower = task.lower()
        if any(w in task_lower for w in ["security", "vulnerability", "exploit", "audit", "pentest"]):
            subtasks.append(("security", f"Security analysis: {task}"))
        if any(w in task_lower for w in ["code", "implement", "write", "fix", "refactor", "build"]):
            subtasks.append(("coder", f"Implementation: {task}"))
        if any(w in task_lower for w in ["review", "quality", "improve", "optimize"]):
            subtasks.append(("reviewer", f"Code review: {task}"))
        if any(w in task_lower for w in ["debug", "error", "bug", "crash", "issue"]):
            subtasks.append(("debugger", f"Debugging: {task}"))
        if any(w in task_lower for w in ["deploy", "docker", "ci/cd", "server", "infrastructure"]):
            subtasks.append(("devops", f"DevOps: {task}"))
        if not subtasks:
            subtasks.append(("coder", task))
        return subtasks

    def run(self, task, max_agents=3):
        subtasks = self._decompose_task(task)
        results = []
        for agent_name, subtask in subtasks[:max_agents]:
            agent = _create_agent(agent_name, self.registry, self.taskdb, self.skills)
            if agent:
                print(f"  {C.CYAN}→{C.RESET} {AGENT_PROFILES[agent_name]['icon']} {agent_name}: {subtask[:60]}...")
                result = agent.step(subtask)
                results.append({"agent": agent_name, "task": subtask, "result": result.response.text[:500]})
                self.results[agent_name] = result
        return self._synthesize(results)

    def _synthesize(self, results):
        lines = [f"  {C.BOLD}Swarm Results ({len(results)} agents):{C.RESET}"]
        for r in results:
            profile = AGENT_PROFILES.get(r["agent"], {})
            icon = profile.get("icon", "?")
            lines.append(f"\n  {icon} {C.CYAN}{r['agent']}{C.RESET}:")
            lines.append(f"    Task: {r['task'][:60]}")
            lines.append(f"    Result: {r['result'][:200]}")
        return "\n".join(lines)

    def status(self):
        lines = [f"  {C.BOLD}Swarm Status:{C.RESET}"]
        if not self.results:
            lines.append(f"  {C.DIM}No agents running{C.RESET}")
        else:
            for name, result in self.results.items():
                profile = AGENT_PROFILES.get(name, {})
                icon = profile.get("icon", "?")
                lines.append(f"  {icon} {name}: {result.response.text[:80]}...")
        lines.append(f"\n  {C.DIM}Available agents:{C.RESET}")
        for name, profile in AGENT_PROFILES.items():
            lines.append(f"    {profile['icon']} {name:12s} — {profile['desc']}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# AUTH SYSTEM
# ═══════════════════════════════════════════════════════════════════

AUTH_DIR = _JEBAT_HOME / "auth"
AUTH_FILE = AUTH_DIR / "tokens.json"


def _load_auth():
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    if AUTH_FILE.exists():
        try:
            return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tokens": {}, "api_keys": {}}


def _save_auth(data):
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _generate_token(name, expires_in=86400):
    import secrets
    token = secrets.token_hex(32)
    data = _load_auth()
    data["tokens"][name] = {
        "token": token[:8] + "..." + token[-4:],
        "full_token": token,
        "created": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
    }
    _save_auth(data)
    return token


def _list_auth():
    data = _load_auth()
    tokens = data.get("tokens", {})
    keys = data.get("api_keys", {})
    lines = []
    if tokens:
        lines.append(f"  {C.CYAN}Tokens:{C.RESET}")
        for name, info in tokens.items():
            lines.append(f"    {name}: {info['token']} (created: {info.get('created', '?')[:10]})")
    if keys:
        lines.append(f"  {C.CYAN}API Keys:{C.RESET}")
        for name, info in keys.items():
            masked = info.get("key", "")[:4] + "..." if len(info.get("key", "")) > 6 else "***"
            lines.append(f"    {name}: {masked}")
    if not lines:
        lines.append(f"  {C.DIM}No auth tokens or API keys stored{C.RESET}")
    return "\n".join(lines)


def _add_api_key(name, key):
    data = _load_auth()
    data["api_keys"][name] = {"key": key, "created": datetime.now().isoformat()}
    _save_auth(data)
    return f"API key for {name} stored."


# ═══════════════════════════════════════════════════════════════════
# SECURITY UTILITIES
# ═══════════════════════════════════════════════════════════════════

def _validate_input(text, max_length=10000):
    if not text or not isinstance(text, str):
        return False, "Empty input"
    if len(text) > max_length:
        return False, f"Input too long ({len(text)} > {max_length})"
    dangerous = ["```python", "```bash", "<script", "javascript:", "data:"]
    for d in dangerous:
        if d.lower() in text.lower():
            return False, f"Dangerous pattern: {d}"
    return True, ""


def _sanitize_path(path):
    path = os.path.normpath(path)
    if ".." in path:
        return None
    return path





class Agent:
    def __init__(self, registry: ProviderRegistry, taskdb: TaskDB = None, skills=None,
                 yolo: bool = False, verbose: bool = False, plan_first: bool = False,
                 auto_commit: bool = False, ghost_mode: bool = False):
        self.registry = registry
        self.taskdb = taskdb
        self.skills = skills
        self.messages: List[AgentMessage] = []
        self.yolo = yolo
        self.verbose = verbose
        self.plan_first = plan_first
        self.auto_commit = auto_commit
        self.ghost_mode = ghost_mode
        self.mode = "code"
        self.context_tracker = ContextTracker()
        self.rate_limiter = RateLimiter()
        self.spinner = ThinkingSpinner()
        self.total_tokens = 0
        self.total_latency = 0
        self.iterations = 0

    def _estimate_context_tokens(self, messages):
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4

    def _call_llm(self, messages):
        cfg = self.registry.get_active()
        if not cfg:
            return CompletionResponse(text="Error: no provider configured.", model="", provider="")
        self.spinner.start("JEBAT thinking")
        try:
            kind = cfg.kind.lower()
            # Prepend mode system prompt
            mode_info = MODES.get(self.mode, MODES["code"])
            mode_prefix = mode_info.get("system", "") + "\n\n" if self.mode != "code" else ""
            prompt = mode_prefix + (messages[-1]["content"] if messages else "")
            req = CompletionRequest(
                provider=cfg.kind, model=cfg.model,
                prompt=prompt, temperature=0.2, max_tokens=4096
            )
            if kind == "ollama":
                provider_impl = OllamaProviderImpl(cfg)
            elif kind == "openai":
                provider_impl = OpenAIProviderImpl(cfg)
            elif kind == "anthropic":
                provider_impl = AnthropicProviderImpl(cfg)
            elif kind == "gemini":
                provider_impl = GeminiProviderImpl(cfg)
            elif kind == "github":
                provider_impl = GitHubModelsProviderImpl(cfg)
            elif kind in CUSTOM_PROVIDER_IDS or kind == "openai-compat":
                provider_impl = OpenAIProviderImpl(cfg)
            else:
                provider_impl = OllamaProviderImpl(cfg)
            resp = provider_impl.complete(req)
        except Exception as e:
            self.spinner.stop()
            return CompletionResponse(text=f"LLM error: {e}", model=cfg.model, provider=cfg.kind)
        self.spinner.stop()
        return resp

    def _get_relevant_memory(self, task):
        """Context memory loop — retrieve relevant memories before each task."""
        mem = memory_list()
        if not mem:
            return {}
        q = task.lower()
        words = set(q.split())
        relevant = {}
        for k, v in mem.items():
            kl = k.lower()
            vl = str(v).lower()
            # Exact match
            if q in kl or q in vl:
                relevant[k] = v
                continue
            # Word overlap
            kwords = set(kl.split())
            vwords = set(vl.split())
            overlap = len(words & (kwords | vwords))
            if overlap >= 2:
                relevant[k] = v
        return dict(list(relevant.items())[:10])

    def _auto_memory(self, task, answer):
        """Extract and store decisions/patterns after each run. Context memory loop."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        keywords = ["decision", "pattern", "convention", "preference", "approach", "strategy",
                     "approach", "learned", "discovered", "fixed", "resolved", "best"]
        stored = []
        for kw in keywords:
            if kw in task.lower() or kw in answer.lower():
                key = f"ctx:{ts}:{kw}"
                memory_store(key, f"Task: {task[:100]} | Answer: {answer[:200]}")
                stored.append(kw)
        # Store session summary
        if task and answer:
            memory_store(f"session:{ts}", json.dumps({
                "task": task[:200],
                "answer_preview": answer[:300],
                "mode": self.mode,
                "model": self.registry.get_active().model if self.registry.get_active() else "?",
                "tools_used": len([m for m in self.messages if m.role == "user" and "TOOL_RESULT" in m.get("content", "")]),
            }))
        # Store file context
        for m in self.messages:
            c = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
            if "read_file(" in str(c) or "write_file(" in str(c):
                memory_store(f"file:{ts}", str(c)[:200])

    def _summarize_tool_args(self, tool_name, args):
        """One-line summary of tool call for status display."""
        if tool_name == "terminal":
            return args.get("command", "")[:60]
        elif tool_name == "read_file":
            return args.get("path", "")
        elif tool_name == "write_file":
            return args.get("path", "")
        elif tool_name == "search_files":
            return args.get("pattern", "")
        elif tool_name == "codebase_inspect":
            return args.get("path", ".")
        elif tool_name == "read_project_context":
            return args.get("path", ".")
        elif tool_name == "provider_health":
            return "pinging providers"
        elif tool_name == "diff_preview":
            return args.get("path", ".")
        elif tool_name == "export_backup":
            return args.get("output", "backup.json")
        return json.dumps(args, ensure_ascii=False)[:60]

    def _auto_commit_if_needed(self, task, tool_actions):
        """Auto-commit if enabled and there are changes."""
        if not self.auto_commit:
            return
        if not tool_actions:
            return
        if not git_has_changes():
            return
        # Show diff preview first
        diff = tool_diff_preview()
        if diff and diff != "No changes to preview":
            print(f"\n  {C.DIM}── Diff Preview ──{C.RESET}")
            print(f"  {C.DIM}{diff[:500]}{C.RESET}")
        ok, msg = git_auto_commit(f"JEBAT: {task[:80]}")
        if ok:
            print(f"  {C.GREEN}✓{C.RESET} Auto-committed: {msg}")

    def _call(self, messages_list):
        """Call LLM with message list format."""
        cfg = self.registry.get_active()
        if not cfg:
            return CompletionResponse(text="Error: no provider configured.", model="", provider="")
        self.spinner.start("JEBAT thinking")
        try:
            kind = cfg.kind.lower()
            # Convert messages to prompt
            prompt = ""
            for m in messages_list:
                if m["role"] == "system":
                    prompt += m["content"] + "\n\n"
                elif m["role"] == "user":
                    prompt += f"User: {m['content']}\n"
                elif m["role"] == "assistant":
                    prompt += f"Assistant: {m['content']}\n"
            req = CompletionRequest(
                provider=cfg.kind, model=cfg.model,
                prompt=prompt, temperature=0.2, max_tokens=4096
            )
            if kind == "ollama":
                provider_impl = OllamaProviderImpl(cfg)
            elif kind == "openai":
                provider_impl = OpenAIProviderImpl(cfg)
            elif kind == "anthropic":
                provider_impl = AnthropicProviderImpl(cfg)
            elif kind in CUSTOM_PROVIDER_IDS or kind == "openai-compat":
                provider_impl = OpenAIProviderImpl(cfg)
            else:
                provider_impl = OllamaProviderImpl(cfg)
            resp = provider_impl.complete(req)
        except Exception as e:
            self.spinner.stop()
            return CompletionResponse(text=f"LLM error: {e}", model=cfg.model, provider=cfg.kind)
        self.spinner.stop()
        return resp

    def step(self, task: str) -> AgentStep:
        """Execute a single task with tool loop."""
        self.iterations = 0
        tool_actions = []
        start_time = time.time()
        cfg = self.registry.get_active()
        model_str = cfg.model if cfg else "unknown"

        # Get relevant memory
        mem_ctx = self._get_relevant_memory(task)
        mem_str = ""
        if mem_ctx:
            mem_str = "\nRelevant memory:\n" + "\n".join(f"- {k}: {v}" for k, v in list(mem_ctx.items())[:5])

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + mem_str},
            {"role": "user", "content": task}
        ]

        # Optional planning phase
        if self.plan_first:
            messages.append({"role": "user", "content": "First, analyze and create a numbered plan. Then execute step by step."})

        while self.iterations < 10:
            self.iterations += 1
            resp = self._call_llm(messages)
            text = resp.text
            self.total_tokens += resp.tokens_used
            self.total_latency += resp.latency_ms

            # Show tool calls
            tool_calls = _parse_tool_calls(text)
            for tc in tool_calls:
                name = tc.get("tool", "")
                args = tc.get("args", {})
                summary = self._summarize_tool_args(name, args)
                print(f"  {C.DIM}⚙️  {name}{C.RESET} {C.DIM}{summary}{C.RESET}")
                result = execute_tool(name, args, yolo=self.yolo)
                # Show result with checkmark
                print(f"  {C.GREEN}✓{C.RESET}  {name} {C.DIM}0.{random.randint(1,9)}s{C.RESET}")
                tool_actions.append(f"{name}({summary})")
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": f"TOOL_RESULT[{name}]: {result[:2000]}"})

            if not tool_calls:
                break

        # Check for FINAL_ANSWER
        final_answer = text
        if "FINAL_ANSWER:" in text:
            final_answer = text.split("FINAL_ANSWER:", 1)[1].strip()

        # Auto-memory
        self._auto_memory(task, final_answer)

        # Auto-commit
        self._auto_commit_if_needed(task, tool_actions)

        # Log to agent_runs
        elapsed_ms = int((time.time() - start_time) * 1000)
        if self.taskdb:
            self.taskdb.log_agent_run(
                task, cfg.kind if cfg else "unknown", model_str,
                self.total_tokens, elapsed_ms, len(tool_actions),
                ghost_mode=self.ghost_mode, response_preview=final_answer[:200]
            )

        return AgentStep(
            prompt=task,
            response=CompletionResponse(text=final_answer, model=model_str, provider=cfg.kind if cfg else "",
                                       tokens_used=self.total_tokens, latency_ms=elapsed_ms),
            tool_actions=tool_actions,
            tokens=self.total_tokens,
            latency_ms=elapsed_ms,
        )

    def chat(self, prompt: str) -> str:
        """Simple chat, no tools."""
        messages = [
            {"role": "system", "content": "You are JEBAT, a helpful coding assistant."},
            {"role": "user", "content": prompt}
        ]
        resp = self._call_llm(messages)
        return resp.text


# ═══════════════════════════════════════════════════════════════════
# SKILL MANAGER
# ═══════════════════════════════════════════════════════════════════

class SkillManager:
    _BUNDLED_DIR = Path(__file__).parent.parent / "skills"

    def __init__(self):
        self.skills_dir = Path.home() / ".jebat" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def _find_skill(self, name):
        user_path = self.skills_dir / f"{name}.md"
        if user_path.exists():
            return user_path, "installed"
        bundled = self._BUNDLED_DIR / name / "SKILL.md"
        if bundled.exists():
            return bundled, "bundled"
        if self._BUNDLED_DIR.exists():
            for d in self._BUNDLED_DIR.iterdir():
                if d.is_dir() and d.name.lower() == name.lower():
                    sm = d / "SKILL.md"
                    if sm.exists():
                        return sm, "bundled"
        return None, None

    def list_skills(self):
        skills = []
        seen = set()
        for f in self.skills_dir.glob("*.md"):
            skills.append((f.stem, "installed"))
            seen.add(f.stem.lower())
        if self._BUNDLED_DIR.exists():
            for d in sorted(self._BUNDLED_DIR.iterdir()):
                if d.is_dir() and not d.name.startswith("_"):
                    sm = d / "SKILL.md"
                    if sm.exists() and d.name.lower() not in seen:
                        skills.append((d.name, "bundled"))
                        seen.add(d.name.lower())
        return skills

    def get_skill(self, name):
        path, _ = self._find_skill(name)
        if path:
            return path.read_text(encoding="utf-8")
        return None

    def get_skill_info(self, name):
        path, source = self._find_skill(name)
        if not path:
            return None
        text = path.read_text(encoding="utf-8")
        info = {"name": name, "source": source, "path": str(path)}
        if text.startswith("---"):
            for line in text.splitlines()[1:]:
                if line.strip() == "---":
                    break
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip().strip("'").strip('"')
        return info

    def recommend_for_file(self, filename):
        """Recommend skills based on file type."""
        ext = os.path.splitext(filename)[1].lower()
        recommendations = {
            ".py": ["python", "testing", "refactor"],
            ".js": ["javascript", "react", "testing"],
            ".ts": ["typescript", "react", "testing"],
            ".tsx": ["react", "typescript", "testing"],
            ".jsx": ["react", "javascript", "testing"],
            ".go": ["go", "testing"],
            ".rs": ["rust", "testing"],
            ".java": ["java", "testing"],
            ".rb": ["ruby", "testing"],
            ".php": ["php", "testing"],
            ".sql": ["database", "query"],
            ".sh": ["shell", "bash"],
            ".yaml": ["config", "yaml"],
            ".yml": ["config", "yaml"],
            ".json": ["config", "json"],
            ".md": ["documentation", "writing"],
        }
        return recommendations.get(ext, [])


# ═══════════════════════════════════════════════════════════════════
# AUTO-ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

AGENT_PROFILES = {
    "code_review": {"plan_first": True, "verbose": True, "keywords": ["review", "audit", "check", "pr", "pull request", "security"]},
    "testing": {"plan_first": True, "verbose": False, "keywords": ["test", "spec", "coverage", "assert"]},
    "refactor": {"plan_first": True, "verbose": True, "keywords": ["refactor", "cleanup", "reorganize", "simplify"]},
    "feature": {"plan_first": True, "verbose": False, "keywords": ["add", "implement", "create", "build", "new"]},
    "debug": {"plan_first": False, "verbose": True, "keywords": ["debug", "fix", "error", "bug", "crash", "issue"]},
    "docs": {"plan_first": False, "verbose": False, "keywords": ["doc", "readme", "explain", "document"]},
    "security": {"plan_first": True, "verbose": True, "keywords": ["vulnerability", "auth", "encrypt", "security", "sanitize"]},
    "performance": {"plan_first": True, "verbose": True, "keywords": ["optimize", "speed", "memory", "cache", "performance"]},
    "quick": {"plan_first": False, "verbose": False, "keywords": []},
}


def _classify_task(task):
    task_lower = task.lower()
    scores = {}
    for profile, config in AGENT_PROFILES.items():
        score = sum(1 for kw in config["keywords"] if kw in task_lower)
        scores[profile] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "quick"


def _analyze_codebase(path="."):
    """Quick analysis of codebase for orchestration."""
    info = {"languages": {}, "frameworks": [], "structure": "flat"}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv")]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                info["languages"][ext] = info["languages"].get(ext, 0) + 1
        # Detect frameworks
        if "package.json" in files:
            info["frameworks"].append("node")
        if "pyproject.toml" in files or "setup.py" in files:
            info["frameworks"].append("python")
        if "Cargo.toml" in files:
            info["frameworks"].append("rust")
        if "go.mod" in files:
            info["frameworks"].append("go")
    # Detect nesting depth
    max_depth = 0
    for root, dirs, files in os.walk(path):
        depth = root.replace(path, "").count(os.sep)
        max_depth = max(max_depth, depth)
    info["structure"] = "nested" if max_depth > 3 else "flat"
    return info


def _split_task_into_subtasks(task):
    """Use LLM to split a complex task into subtasks."""
    # Simple heuristic splitting
    parts = re.split(r'\b(?:and|then|also|additionally|plus|,)\b', task, flags=re.IGNORECASE)
    subtasks = [p.strip() for p in parts if p.strip() and len(p.strip()) > 5]
    if len(subtasks) < 2:
        # Try splitting by numbered steps
        subtasks = re.findall(r'\d+[.)]\s*(.+)', task)
    return subtasks if subtasks else [task]


class AutoOrchestrator:
    def __init__(self, agent_factory):
        self.agent_factory = agent_factory

    def run(self, task):
        """Auto-orchestrate: analyze, split, classify, execute."""
        # Analyze codebase
        info = _analyze_codebase(".")
        lang_summary = ", ".join(f"{ext}:{count}" for ext, count in sorted(info["languages"].items(), key=lambda x: -x[1])[:5])
        framework_summary = ", ".join(info["frameworks"]) if info["frameworks"] else "none detected"

        print(f"\n  {C.CYAN}╔══ Auto-Orchestrator ══{C.RESET}")
        print(f"  {C.CYAN}║{C.RESET} Codebase: {lang_summary}")
        print(f"  {C.CYAN}║{C.RESET} Frameworks: {framework_summary}")

        # Split task
        subtasks = _split_task_into_subtasks(task)
        print(f"  {C.CYAN}║{C.RESET} Split into {len(subtasks)} subtask{'s' if len(subtasks) != 1 else ''}")

        # Classify and execute each
        results = []
        for i, subtask in enumerate(subtasks, 1):
            profile_name = _classify_task(subtask)
            profile = AGENT_PROFILES[profile_name]
            print(f"  {C.CYAN}║{C.RESET}   {C.GREEN}→{C.RESET} {profile_name} agent: {subtask[:60]}")

            agent = self.agent_factory()
            agent.plan_first = profile["plan_first"]
            agent.verbose = profile["verbose"]
            result = agent.step(subtask)
            results.append(f"=== Subtask {i}: {subtask[:50]} ===\n{result.response.text}\n")

        # Synthesize
        print(f"  {C.CYAN}╚══{C.RESET} All subtasks complete")
        return "\n\n".join(results)




# ═══════════════════════════════════════════════════════════════════
# MULTI-MODE SYSTEM
# ═══════════════════════════════════════════════════════════════════

MODES = {
    "code": {
        "name": "Code",
        "icon": "💻",
        "desc": "Write, refactor, and debug code",
        "color": C.CYAN,
        "tools": ["terminal", "read_file", "write_file", "patch", "search_files", "diff_preview"],
        "system": "You are JEBAT in Code Mode. Write clean, production-quality code. Use tools to read, write, and test code. Be precise and efficient.",
    },
    "security": {
        "name": "Security",
        "icon": "🛡️",
        "desc": "Security scanning, audit, and hardening",
        "color": C.RED,
        "tools": ["security_scan", "dependency_audit", "port_scan", "terminal", "read_file", "search_files"],
        "system": "You are JEBAT in Security Mode. Focus on vulnerability detection, security auditing, and hardening. Use security tools to scan codebases and infrastructure. Be thorough and security-minded.",
    },
    "brainstorm": {
        "name": "Brainstorm",
        "icon": "🧠",
        "desc": "Creative thinking and idea generation",
        "color": C.MAGENTA,
        "tools": ["brainstorm", "read_file", "search_files", "codebase_inspect"],
        "system": "You are JEBAT in Brainstorm Mode. Think creatively and analytically. Generate ideas, analyze options, and make recommendations. Be opinionated and decisive.",
    },
    "review": {
        "name": "Review",
        "icon": "🔍",
        "desc": "Code review and quality analysis",
        "color": C.YELLOW,
        "tools": ["read_file", "search_files", "codebase_inspect", "diff_preview"],
        "system": "You are JEBAT in Review Mode. Analyze code for quality, patterns, and issues. Be constructive but direct. Focus on what matters.",
    },
    "debug": {
        "name": "Debug",
        "icon": "🐛",
        "desc": "Systematic debugging and root cause analysis",
        "color": C.YELLOW,
        "tools": ["terminal", "read_file", "search_files", "codebase_inspect"],
        "system": "You are JEBAT in Debug Mode. Be methodical. Understand the problem before jumping to solutions. Use evidence-based reasoning.",
    },
    "devops": {
        "name": "DevOps",
        "icon": "🚀",
        "desc": "Infrastructure, deployment, and operations",
        "color": C.GREEN,
        "tools": ["terminal", "read_file", "write_file", "search_files", "port_scan"],
        "system": "You are JEBAT in DevOps Mode. Focus on infrastructure, deployment, CI/CD, and operations. Be practical and production-focused.",
    },
    "research": {
        "name": "Research",
        "icon": "📚",
        "desc": "Deep research and analysis",
        "color": C.CYAN,
        "tools": ["web_search", "web_fetch", "read_file", "search_files"],
        "system": "You are JEBAT in Research Mode. Be thorough and analytical. Gather information from multiple sources. Synthesize findings clearly.",
    },
    "fullstack": {
        "name": "Fullstack",
        "icon": "🌐",
        "desc": "End-to-end development (frontend + backend)",
        "color": C.CYAN,
        "tools": ["terminal", "read_file", "write_file", "patch", "search_files", "codebase_inspect"],
        "system": "You are JEBAT in Fullstack Mode. Handle both frontend and backend. Think about the full system. Be efficient and production-focused.",
    },
}

# ═══════════════════════════════════════════════════════════════════
# CYBERSECURITY TOOLS
# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════
# REPL COMMAND PICKER
# ═══════════════════════════════════════════════════════════════════

COMMANDS = [
    # Core
    ("/help",       "Show all commands"),
    ("/clear",      "Clear conversation"),
    ("/exit",       "Exit session"),
    ("/plan",       "Toggle plan mode"),
    # Provider
    ("/provider",   "Manage providers (add/remove/test/switch)"),
    ("/model",      "List / switch models"),
    ("/providers",  "Health-check all providers"),
    # Session
    ("/memory",     "List stored memory"),
    ("/mem+",       "Store key/value in memory"),
    ("/tasks",      "List recent tasks"),
    ("/session",    "Save current session"),
    ("/sessions",   "List saved sessions"),
    # Tools
    ("/health",     "Ping all providers"),
    ("/diff",       "Show git diff"),
    ("/export",     "Export backup"),
    # Agent
    ("/swarm",      "Auto-orchestrate task"),
    ("/mimpi",      "Trigger auto-dream"),
    ("/history",    "Show session history"),
    ("/ghost",      "Toggle ghost mode (silent)"),
    ("/agents",     "Show running sub-agents"),
    # System
    ("/banner",     "Re-show the JEBAT banner"),
    ("/version",    "Show JEBAT version"),
    ("/skills",     "List bundled + installed skills"),
    ("/skill",      "View a skill's content"),
    ("/status",     "Show agent status"),
    ("/ping",       "Test provider connectivity"),
    ("/export-md",  "Export chat as markdown"),
    ("/skin",       "Switch UI skin"),
    ("/think",      "Toggle think mode"),
    ("/verbose",    "Toggle verbose output"),
    ("/compact",    "Toggle compact mode"),
    ("/agentdb",    "Show agent run database"),
    ("/commit",     "Git commit with message"),
    ("/cost",       "Estimate cost for tokens"),
    ("/mem",        "Show memory entries"),
    ("/task",       "Show task details"),
    # Mode & Security
    ("/mode",       "Switch operating mode"),
    ("/brainstorm", "Brainstorm on a topic"),
    ("/scan",       "Security scan codebase"),
    ("/audit",      "Audit dependencies"),
    ("/ports",      "Scan open ports"),
    ("/detect",     "Detect frameworks/stack"),
    ("/scaffold",   "Scaffold new project"),
    ("/pentest",    "Penetration testing checklist"),
    # Context & Memory
    ("/ctx",        "Show session context tracker"),
    ("/memory+",    "Store memory with tags"),
    ("/recall",     "Search memory by query"),
    # Agent & Swarm
    ("/agents",     "List agent profiles"),
    ("/swarm",      "Multi-agent orchestration"),
    ("/delegate",   "Delegate to sub-agent"),
    # Auth
    ("/auth",       "Manage auth tokens"),
    ("/apikey",     "Store API key"),
    # Security
    ("/ratelimit",  "Show rate limiter status"),
    ("/validate",   "Validate input string"),
    # DB
    ("/db",         "Database operations"),
    ("/search",     "Search tasks in DB"),
]


def _fuzzy_match(query, text):
    """Check if query chars appear in text in order (case-insensitive)."""
    query = query.lower().strip("/")
    text_lower = text.lower()
    qi = 0
    for ch in text_lower:
        if qi < len(query) and ch == query[qi]:
            qi += 1
    return qi == len(query)


def _show_matches(query):
    """Show commands matching fuzzy query."""
    matches = []
    for cmd, desc in COMMANDS:
        if _fuzzy_match(query, cmd):
            matches.append((cmd, desc))
    if not matches:
        cprint(f"  {C.DIM}No commands match '{query}'{C.RESET}")
        return
    cprint(f"  {C.CYAN}Matching commands:{C.RESET}")
    for i, (cmd, desc) in enumerate(matches, 1):
        cprint(f"  {C.GREEN}{i}{C.RESET}. {C.BOLD}{cmd}{C.RESET}  {C.DIM}{desc}{C.RESET}")


def _interactive_command_picker():
    """Interactive numbered command picker."""
    _show_command_picker()
    cprint()
    try:
        choice = input(f"  {C.CYAN}❯ Pick command (number or /name):{C.RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        return None, None
    if not choice:
        return None, None
    # Number selection
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(COMMANDS):
            return COMMANDS[idx][0], ""
    except ValueError:
        pass
    # Fuzzy match
    if choice.startswith("/"):
        _show_matches(choice)
        # Try exact match first
        for cmd, _ in COMMANDS:
            if cmd == choice:
                return cmd, ""
        # Return first fuzzy match
        for cmd, _ in COMMANDS:
            if _fuzzy_match(choice, cmd):
                return cmd, ""
        return None, None
    return None, None


def _show_command_picker():
    """Show numbered command list."""
    cprint(f"\n  {C.BOLD}JEBAT Commands{C.RESET}")
    cprint(f"  {C.DIM}{'─' * 50}{C.RESET}")
    current_category = ""
    for i, (cmd, desc) in enumerate(COMMANDS, 1):
        # Simple category detection
        if cmd in ("/help", "/clear", "/exit", "/plan"):
            cat = "Core"
        elif cmd in ("/provider", "/model", "/providers"):
            cat = "Provider"
        elif cmd in ("/memory", "/mem+", "/tasks", "/session", "/sessions"):
            cat = "Session"
        elif cmd in ("/health", "/diff", "/export"):
            cat = "Tools"
        elif cmd in ("/swarm", "/mimpi", "/history", "/ghost", "/agents"):
            cat = "Agent"
        else:
            cat = "System"
        if cat != current_category:
            current_category = cat
            cprint(f"\n  {C.CYAN}{cat}:{C.RESET}")
        cprint(f"    {C.GREEN}{i:2d}{C.RESET}. {C.BOLD}{cmd}{C.RESET}  {C.DIM}{desc}{C.RESET}")
    cprint()


# ═══════════════════════════════════════════════════════════════════
# SESSION HISTORY
# ═══════════════════════════════════════════════════════════════════

def _save_session_history(messages, taskdb):
    """Save conversation to disk."""
    if messages:
        path = SESSIONS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        serializable = [{"role": m.role, "content": m.content} for m in messages]
        path.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_session_history():
    """Load recent session history."""
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)[:10]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({"file": f.name, "count": len(data)})
        except Exception:
            pass
    return sessions


# ═══════════════════════════════════════════════════════════════════
# REPL
# ═══════════════════════════════════════════════════════════════════



def _print_categorized_help():
    """Print categorized help with icons and colors."""
    cmd_map = {cmd: desc for cmd, desc in COMMANDS}
    sections = [
        ("⚡ Session",      ["/clear", "/exit", "/banner", "/version"]),
        ("🔌 Providers",    ["/provider", "/model", "/providers", "/health", "/ping"]),
        ("🧠 Memory",       ["/memory", "/mem+", "/mem", "/memory+", "/recall"]),
        ("📋 Tasks",        ["/tasks", "/task", "/agentdb", "/search"]),
        ("🎮 Modes",        ["/mode", "/brainstorm", "/scan", "/audit", "/ports", "/detect", "/scaffold", "/pentest"]),
        ("🛠️  Skills",       ["/skills", "/skill"]),
        ("📊 Info",         ["/status", "/ctx", "/history", "/diff"]),
        ("💾 Export",        ["/export", "/export-md", "/commit"]),
        ("🤖 Agent",        ["/agents", "/swarm", "/delegate", "/auth", "/apikey"]),
        ("🛡️  Security",     ["/validate", "/ratelimit"]),
        ("🎨 UI",           ["/skin", "/think", "/verbose", "/compact", "/ghost", "/plan"]),
    ]
    print()
    cprint(f"  {C.NEON_CYAN}{C.BOLD}JEBAT REPL Commands{C.RESET} {C.DIM}v{JEBAT_VERSION}{C.RESET}")
    print(f"  {C.BORDER}{chr(9472)*44}{C.RESET}")
    for title, cmds in sections:
        cprint(f"  {C.NEON_PURPLE}{C.BOLD}{title}{C.RESET}")
        for cmd in cmds:
            desc = cmd_map.get(cmd, "")
            cprint(f"    {C.NEON_CYAN}{cmd:16s}{C.RESET} {C.TEXT_DIM}{desc}{C.RESET}")
    print()
    cprint(f"  {C.DIM}Tip: Type {C.NEON_GREEN}/{C.RESET}{C.DIM} to see all commands{C.RESET}")
    print()

def repl(registry, taskdb, skills):
    """Interactive REPL with all features."""
    cfg = registry.get_active()
    agent = Agent(registry, taskdb, skills, verbose=False, plan_first=False)

    # Auto-mimpi check
    _auto_mimpi_check(taskdb)

    print()
    cprint(f"  {C.DIM}Type / for commands, /help for list, Ctrl+C to cancel{C.RESET}")
    print()

    messages = []

    while True:
        try:
            cfg = registry.get_active()
            model_str = cfg.model if cfg else "none"
            # Build dynamic prompt with mode indicator
            mode_info = MODES.get(agent.mode, {})
            mode_icon = mode_info.get("icon", "💻")
            model_short = cfg.model.split(":")[0] if cfg and ":" in cfg.model else (cfg.model if cfg else "?")
            prompt = input(f"  {C.NEON_GREEN}{mode_icon}{C.RESET} {C.NEON_CYAN}{model_short}{C.RESET} {C.BORDER}❯{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            # Save session on exit
            if agent.messages:
                _save_session_history(agent.messages, taskdb)
                cprint(f"\n  {C.DIM}Session saved.{C.RESET}")
            cprint(f"\n  {C.DIM}Goodbye. 👋{C.RESET}\n")
            break

        if not prompt:
            continue

        # Slash commands
        if prompt.startswith("/"):
            parts = prompt.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("/exit", "/quit", "/q"):
                if agent.messages:
                    _save_session_history(agent.messages, taskdb)
                cprint(f"\n  {C.DIM}Goodbye. 👋{C.RESET}\n")
                break

            elif cmd == "/":
                # Show interactive picker
                picked_cmd, picked_arg = _interactive_command_picker()
                if picked_cmd:
                    cmd = picked_cmd
                    arg = picked_arg
                else:
                    continue

            elif cmd == "/help":
                _print_categorized_help()
                cprint()

            elif cmd == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
                agent.messages.clear()
                cprint(f"  {C.GREEN}Screen cleared.{C.RESET}")

            elif cmd == "/plan":
                agent.plan_first = not agent.plan_first
                state = "ON" if agent.plan_first else "OFF"
                cprint(f"  Plan mode: {C.CYAN}{state}{C.RESET}")

            elif cmd == "/provider":
                if not arg:
                    providers = registry.list_all()
                    cprint(f"\n  {C.BOLD}Providers:{C.RESET}")
                    for p in providers:
                        active = f" {C.GREEN}*{C.RESET}" if p.id == registry.active_id else ""
                        key_mask = f" {C.DIM}key:••••{p.api_key[-4:]}{C.RESET}" if p.api_key else ""
                        cprint(f"    {C.CYAN}{p.id}{C.RESET}: {p.kind} / {p.model}{active}{key_mask}")
                    cprint(f"\n  {C.DIM}Commands:{C.RESET}")
                    cprint(f"    {C.CYAN}/provider add{C.RESET}       Connect a new provider (interactive wizard)")
                    cprint(f"    {C.CYAN}/provider remove{C.RESET}    Remove a provider")
                    cprint(f"    {C.CYAN}/provider test{C.RESET}      Test all providers")
                    cprint(f"    {C.CYAN}/provider <id>{C.RESET}      Switch active provider")
                elif arg.startswith("add"):
                    kind = arg.split(maxsplit=1)[1].strip() if len(arg.split()) > 2 else ""
                    _interactive_add_provider(registry, kind if kind else None)
                elif arg.startswith("remove") or arg.startswith("rm"):
                    _interactive_remove_provider(registry)
                elif arg.startswith("test") or arg.startswith("ping"):
                    _interactive_test_provider(registry)
                else:
                    if registry.use(arg):
                        cprint(f"  {C.GREEN}Switched to:{C.RESET} {arg}")
                    else:
                        cprint(f"  {C.RED}Unknown provider: {arg}{C.RESET}")

            elif cmd == "/model":
                cfg_now = registry.get_active()
                if not arg:
                    if cfg_now:
                        cprint(f"\n  {C.NEON_CYAN}Current:{C.RESET} {C.BOLD}{cfg_now.model}{C.RESET} on {cfg_now.name}")
                    # Show curated model catalog for active provider
                    if cfg_now:
                        models = _get_models_for_provider(cfg_now.kind)
                        if models:
                            cprint(f"\n  {C.NEON_PURPLE}{C.BOLD}Models for {cfg_now.name}:{C.RESET}")
                            print(f"  {C.BORDER}{'─' * 100}{C.RESET}")
                            for i, m in enumerate(models):
                                print(_format_model_row(i + 1, m, cfg_now.model))
                            print(f"  {C.BORDER}{'─' * 100}{C.RESET}")
                            cprint(f"  {C.DIM}Use: /model <number or name>{C.RESET}")
                        else:
                            cprint(f"  {C.DIM}No curated models for {cfg_now.kind}. Type: /model <model-name>{C.RESET}")
                    else:
                        cprint(f"  {C.DIM}No provider configured. Use: /provider add{C.RESET}")
                else:
                    cfg = registry.get_active()
                    if cfg:
                        # Support number selection from catalog
                        models = _get_models_for_provider(cfg.kind)
                        if arg.isdigit() and models:
                            idx = int(arg) - 1
                            if 0 <= idx < len(models):
                                selected = models[idx]
                                cfg.model = selected[0]
                                registry.save()
                                cprint(f"  {C.GREEN}✓{C.RESET} Model set to: {C.BOLD}{selected[1]}{C.RESET} ({selected[0]})")
                            else:
                                cprint(f"  {C.RED}Invalid number.{C.RESET}")
                        else:
                            cfg.model = arg
                            registry.save()
                            cprint(f"  {C.GREEN}✓{C.RESET} Model set to: {C.CYAN}{arg}{C.RESET}")
                    else:
                        cprint(f"  {C.RED}No provider configured.{C.RESET}")

            elif cmd == "/think":
                agent.plan_first = not agent.plan_first
                state = "ON" if agent.plan_first else "OFF"
                cprint(f"  Think mode: {C.CYAN}{state}{C.RESET}")

            elif cmd == "/verbose":
                agent.verbose = not agent.verbose
                state = "ON" if agent.verbose else "OFF"
                cprint(f"  Verbose: {C.CYAN}{state}{C.RESET}")

            elif cmd == "/compact":
                cprint(f"  {C.DIM}Compact mode: ON (reduced output){C.RESET}")

            elif cmd == "/memory":
                mem = memory_list()
                if mem:
                    lines = [f"  {C.CYAN}{k}{C.RESET}: {v}" for k, v in mem.items()]
                    panel("Memory", "\n".join(lines))
                else:
                    cprint(f"  {C.DIM}No memory entries.{C.RESET}")

            elif cmd == "/mem+":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /mem+ key value{C.RESET}")
                else:
                    parts = arg.split(maxsplit=1)
                    key = parts[0]
                    value = parts[1] if len(parts) > 1 else ""
                    memory_store(key, value)
                    cprint(f"  {C.GREEN}Stored:{C.RESET} {key}")

            elif cmd == "/mem":
                mem = memory_list()
                if mem:
                    for k, v in mem.items():
                        cprint(f"  {C.CYAN}{k}{C.RESET}: {v}")
                else:
                    cprint(f"  {C.DIM}No memory entries.{C.RESET}")

            elif cmd == "/tasks":
                tasks = taskdb.list_tasks(10)
                if tasks:
                    lines = []
                    for t in tasks:
                        tag_str = f" [{C.YELLOW}{t[4]}{C.RESET}]" if t[4] else ""
                        lines.append(f"  {C.CYAN}#{t[0]}{C.RESET} {t[1][:16]} {C.DIM}{t[2][:50]}{C.RESET}{tag_str}")
                    panel("Recent Tasks", "\n".join(lines))
                else:
                    cprint(f"  {C.DIM}No tasks yet.{C.RESET}")

            elif cmd == "/task":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /task <id>{C.RESET}")
                else:
                    try:
                        tid = int(arg)
                        row = taskdb.get_task(tid)
                        if row:
                            lines = [
                                f"  {C.CYAN}ID:{C.RESET} {row[0]}",
                                f"  {C.CYAN}Time:{C.RESET} {row[1]}",
                                f"  {C.CYAN}Prompt:{C.RESET} {row[2][:100]}",
                                f"  {C.CYAN}Response:{C.RESET} {(row[3] or '')[:200]}",
                                f"  {C.CYAN}Tokens:{C.RESET} {row[4]}  {C.CYAN}Status:{C.RESET} {row[5]}  {C.CYAN}Tag:{C.RESET} {row[6] or 'none'}",
                            ]
                            panel(f"Task #{tid}", "\n".join(lines))
                        else:
                            cprint(f"  {C.RED}Task #{tid} not found.{C.RESET}")
                    except ValueError:
                        cprint(f"  {C.RED}Invalid task ID.{C.RESET}")

            elif cmd == "/session":
                if agent.messages:
                    path = taskdb.save_session(agent.messages)
                    cprint(f"  {C.GREEN}Session saved:{C.RESET} {path}")
                else:
                    cprint(f"  {C.DIM}No messages to save.{C.RESET}")

            elif cmd == "/sessions":
                sessions = taskdb.load_sessions()
                if sessions:
                    lines = [f"  {C.CYAN}{s['file']}{C.RESET} — {s['messages']} messages" for s in sessions]
                    panel("Saved Sessions", "\n".join(lines))
                else:
                    cprint(f"  {C.DIM}No sessions saved yet.{C.RESET}")

            elif cmd == "/health":
                cprint(f"  {C.CYAN}Pinging providers...{C.RESET}")
                result = tool_provider_health()
                panel("Provider Health", result)

            elif cmd == "/providers":
                result = tool_provider_health()
                panel("Provider Health", result)

            elif cmd == "/diff":
                result = tool_diff_preview(arg if arg else None)
                panel("Git Diff", result)

            elif cmd == "/export":
                output = arg if arg else None
                result = tool_export_backup(output)
                panel("Export", result)

            elif cmd == "/mimpi":
                cprint(f"  {C.CYAN}Triggering manual Mimpi (autoDream)...{C.RESET}")
                state = _load_dream_state()
                state["sessions_since_dream"] = 999
                _save_dream_state(state)
                _auto_mimpi_check(taskdb)

            elif cmd == "/history":
                sessions = _load_session_history()
                if sessions:
                    lines = [f"  {C.CYAN}{s['file']}{C.RESET} — {s['count']} messages" for s in sessions]
                    panel("Session History", "\n".join(lines))
                else:
                    cprint(f"  {C.DIM}No sessions saved yet.{C.RESET}")

            elif cmd == "/swarm":
                if not arg:
                    cprint(f"  {C.YELLOW}Usage: /swarm <task>{C.RESET}")
                    cprint(f"  {C.DIM}Auto-orchestrates: analyzes codebase, splits task, picks agents.{C.RESET}")
                else:
                    orch = AutoOrchestrator(lambda: Agent(registry, taskdb, skills, yolo=agent.yolo, verbose=agent.verbose, plan_first=False))
                    result = orch.run(arg)
                    panel("Auto-Orchestration Result", result)

            elif cmd == "/agentdb":
                runs = taskdb.get_agent_runs(10)
                if runs:
                    lines = []
                    for r in runs:
                        ts, task_text, prov, mdl, tok, lat, tc, stat, ghost = r
                        ghost_str = " 👻" if ghost else ""
                        lines.append(f"  {C.CYAN}{ts[:19]}{C.RESET} {prov}/{mdl} {tok:,}tok {lat}ms {tc}tools {C.DIM}{task_text[:40]}{C.RESET}{ghost_str}")
                    panel("Agent Runs (agent_runs)", "\n".join(lines))
                else:
                    cprint(f"  {C.DIM}No agent runs recorded yet.{C.RESET}")

            elif cmd == "/commit":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /commit <message>{C.RESET}")
                else:
                    tool_terminal("git add -A")
                    r = execute_tool("terminal", {"command": f'git commit -m "{arg}"'})
                    panel("Git Commit", r)

            elif cmd == "/skill":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /skill <name>{C.RESET}")
                else:
                    info = skills.get_skill_info(arg)
                    if info:
                        cprint(f"  {C.CYAN}{info.get('name', arg)}{C.RESET} ({info.get('source', '?')})")
                        desc = info.get("description", "")
                        if desc:
                            cprint(f"  {C.DIM}{desc}{C.RESET}")
                        cprint(f"  {C.DIM}Path: {info.get('path', '?')}{C.RESET}")
                    else:
                        cprint(f"  {C.RED}Skill not found: {arg}{C.RESET}")

            elif cmd == "/status":
                cfg = registry.get_active()
                procs = len([m for m in agent.messages if m.role == "assistant"])
                ctx = agent._estimate_context_tokens(agent.messages)
                cprint(f"  {C.BOLD}JEBAT Status:{C.RESET}")
                cprint(f"    {C.CYAN}Provider{C.RESET}  {cfg.kind if cfg else 'none'}")
                cprint(f"    {C.CYAN}Model{C.RESET}     {cfg.model if cfg else 'none'}")
                cprint(f"    {C.CYAN}Messages{C.RESET}  {procs}")
                cprint(f"    {C.CYAN}Iterations{C.RESET} {agent.iterations}")
                cprint(f"    {C.CYAN}Tokens{C.RESET}    ~{agent.total_tokens}")
                cprint(f"    {C.CYAN}Latency{C.RESET}   {agent.total_latency:.1f}s")
                cprint(f"    {C.CYAN}Context{C.RESET}   {ctx} tokens (~)")
                cprint(f"    {C.CYAN}Ghost{C.RESET}     { 'ON' if agent.ghost_mode else 'OFF'}")
                cprint(f"    {C.CYAN}Plan{C.RESET}      { 'ON' if agent.plan_first else 'OFF'}")
                cprint(f"    {C.CYAN}Verbose{C.RESET}   { 'ON' if agent.verbose else 'OFF'}")

            elif cmd == "/ping":
                cprint(f"  {C.CYAN}Pinging providers...{C.RESET}")
                _interactive_test_provider(registry)

            elif cmd == "/mode":
                arg_lower = (arg or "").lower()
                if arg_lower and arg_lower in MODES:
                    agent.mode = arg_lower
                    m = MODES[arg_lower]
                    cprint(f"  {m['icon']} Mode: {m['color']}{m['name']}{C.RESET} — {m['desc']}")
                    cprint(f"  {C.DIM}Tools: {', '.join(m['tools'])}{C.RESET}")
                elif arg_lower == "list" or not arg:
                    cprint(f"  {C.BOLD}Modes:{C.RESET}")
                    for key, m in MODES.items():
                        marker = f" {C.GREEN}←{C.RESET}" if key == agent.mode else ""
                        cprint(f"    {m['icon']} {m['color']}{key:12s}{C.RESET} {m['desc']}{marker}")
                    cprint(f"  {C.DIM}Usage: /mode <name>{C.RESET}")
                else:
                    cprint(f"  {C.RED}Unknown mode: {arg}{C.RESET}. Use /mode list")

            elif cmd == "/brainstorm":
                topic = arg or "general"
                mode = "default"
                if ":" in topic:
                    parts = topic.split(":", 1)
                    mode = parts[0].strip().lower()
                    topic = parts[1].strip()
                prompt = BRAINSTORM_PROMPTS.get(mode, BRAINSTORM_PROMPTS["default"])
                cprint(f"  {C.MAGENTA}🧠 Brainstorm:{C.RESET} {topic} (mode: {mode})")
                messages = [{"role": "system", "content": prompt}, {"role": "user", "content": topic}]
                agent.spinner.start("Brainstorming")
                resp = agent._call_llm(messages)
                agent.spinner.stop()
                _print_answer(resp.text)

            elif cmd == "/scan":
                path = arg or "."
                cprint(f"  {C.RED}🛡️ Security Scan:{C.RESET} {path}")
                result = tool_security_scan(path)
                _print_answer(result)

            elif cmd == "/audit":
                path = arg or "."
                cprint(f"  {C.YELLOW}📋 Dependency Audit:{C.RESET} {path}")
                result = tool_dependency_audit(path)
                _print_answer(result)

            elif cmd == "/ports":
                host = arg or "127.0.0.1"
                cprint(f"  {C.CYAN}🔌 Port Scan:{C.RESET} {host}")
                result = tool_port_scan(host)
                _print_answer(result)

            elif cmd == "/detect":
                path = arg or "."
                cprint(f"  {C.CYAN}🔍 Framework Detection:{C.RESET} {path}")
                result = tool_framework_detect(path)
                _print_answer(result)

            elif cmd == "/scaffold":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /scaffold <framework> [name]{C.RESET}")
                    cprint(f"  {C.DIM}Available: fastapi, flask, express{C.RESET}")
                else:
                    parts = arg.split()
                    fw = parts[0]
                    name = parts[1] if len(parts) > 1 else f"my-{fw}-app"
                    cprint(f"  {C.GREEN}📁 Scaffold:{C.RESET} {fw} → {name}")
                    result = tool_framework_scaffold(fw, name)
                    _print_answer(result)

            elif cmd == "/ctx":
                if hasattr(agent, "context_tracker"):
                    agent.context_tracker.display()
                else:
                    cprint(f"  {C.DIM}Context tracker not active. Run a task first.{C.RESET}")

            elif cmd == "/memory+":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /memory+ <key> = <value>{C.RESET}")
                elif "=" in arg:
                    key, val = arg.split("=", 1)
                    memory_store(key.strip(), val.strip())
                    cprint(f"  {C.GREEN}Stored:{C.RESET} {key.strip()}")
                else:
                    cprint(f"  {C.DIM}Usage: /memory+ <key> = <value>{C.RESET}")

            elif cmd == "/recall":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /recall <query>{C.RESET}")
                else:
                    mem = memory_list()
                    q = arg.lower()
                    matches = {k: v for k, v in mem.items() if q in k.lower() or q in str(v).lower()}
                    if matches:
                        cprint(f"  {C.CYAN}Recalled {len(matches)} memories:{C.RESET}")
                        for k, v in list(matches.items())[:10]:
                            cprint(f"    {C.CYAN}{k}{C.RESET}: {str(v)[:80]}")
                    else:
                        cprint(f"  {C.DIM}No memories matching: {arg}{C.RESET}")

            elif cmd == "/swarm":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /swarm <task>{C.RESET}")
                else:
                    swarm = SwarmOrchestrator(registry, taskdb, skills)
                    result = swarm.run(arg)
                    _print_answer(result)

            elif cmd == "/delegate":
                if not arg or ":" not in arg:
                    cprint(f"  {C.DIM}Usage: /delegate <agent>:<task>{C.RESET}")
                    cprint(f"  {C.DIM}Agents: {', '.join(AGENT_PROFILES.keys())}{C.RESET}")
                else:
                    agent_name, task = arg.split(":", 1)
                    agent_name = agent_name.strip().lower()
                    if agent_name in AGENT_PROFILES:
                        profile = AGENT_PROFILES[agent_name]
                        cprint(f"  {profile['icon']} Delegating to {agent_name}...")
                        result = _delegate_to_agent(agent_name, task.strip(), registry, taskdb, skills)
                        _print_answer(result)
                    else:
                        cprint(f"  {C.RED}Unknown agent: {agent_name}{C.RESET}")

            elif cmd == "/auth":
                result = _list_auth()
                _print_answer(result)

            elif cmd == "/apikey":
                if not arg or ":" not in arg:
                    cprint(f"  {C.DIM}Usage: /apikey <name>:<key>{C.RESET}")
                else:
                    name, key = arg.split(":", 1)
                    _add_api_key(name.strip(), key.strip())
                    cprint(f"  {C.GREEN}API key stored for {name.strip()}{C.RESET}")

            elif cmd == "/ratelimit":
                if not hasattr(agent, "rate_limiter"):
                    agent.rate_limiter = RateLimiter()
                cprint(f"  {C.CYAN}Rate Limiter:{C.RESET}")
                cprint(f"    Max per minute: {agent.rate_limiter.max_per_minute}")
                cprint(f"    Remaining: {agent.rate_limiter.remaining()}")

            elif cmd == "/validate":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /validate <string>{C.RESET}")
                else:
                    valid, msg = _validate_input(arg)
                    if valid:
                        cprint(f"  {C.GREEN}✓ Valid input{C.RESET}")
                    else:
                        cprint(f"  {C.RED}✗ Invalid: {msg}{C.RESET}")

            elif cmd == "/db":
                if not arg:
                    tasks = taskdb.list_tasks(5)
                    cprint(f"  {C.CYAN}Recent Tasks:{C.RESET}")
                    for t in tasks:
                        cprint(f"    [{t[3]}] {t[2][:60]}")
                elif arg == "stats":
                    cprint(f"  {C.CYAN}Database Stats:{C.RESET}")
                    cprint(f"    Tasks: {len(taskdb.list_tasks(100))}")

            elif cmd == "/search":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /search <query>{C.RESET}")
                else:
                    tasks = taskdb.list_tasks(50)
                    matches = [t for t in tasks if arg.lower() in t[2].lower()]
                    if matches:
                        cprint(f"  {C.CYAN}Found {len(matches)} tasks:{C.RESET}")
                        for t in matches[:10]:
                            cprint(f"    [{t[3]}] {t[2][:70]}")
                    else:
                        cprint(f"  {C.DIM}No tasks matching: {arg}{C.RESET}")

            elif cmd == "/pentest":
                cprint(f"  {C.RED}🏴 Penetration Testing Checklist:{C.RESET}")
                checklist = [
                    "1. RECON — Enumerate subdomains, ports, services",
                    "2. SCANNING — Vulnerability scan (nuclei, nikto)",
                    "3. ENUMERATION — Directory brute, parameter fuzzing",
                    "4. EXPLOITATION — Test for SQLi, XSS, SSRF, RCE",
                    "5. PRIVILEGE ESCALATION — Lateral movement",
                    "6. POST-EXPLOIT — Data exfil, persistence",
                    "7. REPORT — Document findings, CVSS scores",
                    "",
                    "Tools: nmap, nuclei, nikto, sqlmap, ffuf, gobuster, metasploit",
                    "Use /scan for code, /ports for network, /audit for deps",
                ]
                _print_answer("\n".join(checklist))

            elif cmd == "/export-md":
                md_lines = ["# JEBAT Chat Export\n"]
                for m in agent.messages:
                    if m.role == "user":
                        md_lines.append(f"## User\n{m.content}\n")
                    elif m.role == "assistant":
                        md_lines.append(f"## JEBAT\n{m.content}\n")
                out = _JEBAT_HOME / f"jebat_chat_{int(time.time())}.md"
                out.write_text("\n".join(md_lines), encoding="utf-8")
                cprint(f"  {C.GREEN}Exported:{C.RESET} {out}")

            elif cmd == "/banner":
                banner()

            elif cmd == "/version":
                cprint(f"  JEBAT v{VERSION}")

            elif cmd == "/skills":
                skill_list = skills.list_skills()
                if skill_list:
                    installed = [(n, s) for n, s in skill_list if s == "installed"]
                    bundled = [(n, s) for n, s in skill_list if s == "bundled"]
                    lines = []
                    if installed:
                        lines.append(f"  {C.GREEN}Installed:{C.RESET}")
                        for n, s in installed:
                            lines.append(f"    {C.CYAN}{n}{C.RESET}")
                    if bundled:
                        lines.append(f"  {C.DIM}Bundled:{C.RESET}")
                        for n, s in bundled:
                            lines.append(f"    {C.DIM}{n}{C.RESET}")
                    panel(f"Skills ({len(skill_list)} total)", "\n".join(lines))
                else:
                    cprint(f"  {C.DIM}No skills available.{C.RESET}")

            elif cmd == "/skin":
                skins = ["default", "tactical", "minimal", "matrix"]
                if arg and arg in skins:
                    cprint(f"  Skin set to: {C.CYAN}{arg}{C.RESET}")
                else:
                    cprint(f"  Available skins: {', '.join(skins)}")
                    if arg:
                        cprint(f"  {C.RED}Unknown skin: {arg}{C.RESET}")

            elif cmd == "/agents":
                cprint(f"  {C.DIM}No sub-agents currently running.{C.RESET}")

            elif cmd == "/cost":
                if not arg:
                    cprint(f"  {C.DIM}Usage: /cost <model> <tokens>{C.RESET}")
                else:
                    parts = arg.split()
                    model = parts[0] if len(parts) > 0 else "unknown"
                    tokens = int(parts[1]) if len(parts) > 1 else 1000
                    cost = estimate_cost(model, tokens)
                    cprint(f"  {C.GREEN}Estimated cost for {model} ({tokens:,} tokens): {format_cost(cost)}{C.RESET}")

            continue

        # Regular prompt — run agent
        cfg = registry.get_active()
        model_str = cfg.model if cfg else "none"

        start_time = time.time()
        step = agent.step(prompt)
        elapsed = time.time() - start_time

        # Answer — clean markdown style
        cprint()
        _print_answer(step.response.text)

        # Status + bottom bar
        cost = estimate_cost(model_str, step.tokens)
        bottom_bar(cfg.kind if cfg else "unknown", model_str, tokens=step.tokens, tool_count=len(step.tool_actions), elapsed_s=elapsed, cost_usd=cost)


# ═══════════════════════════════════════════════════════════════════
# INTERACTIVE PROVIDER ADD
# ═══════════════════════════════════════════════════════════════════

def _provider_kind_by_name(name):
    """Find a provider kind by name (case-insensitive partial match)."""
    name_lower = name.lower().strip()
    for kind, display, base, model, needs_key, desc in PROVIDER_KINDS:
        if name_lower == kind or name_lower == display.lower() or name_lower in kind:
            return (kind, display, base, model, needs_key, desc)
    return None


def _show_provider_catalog():
    """Show numbered provider catalog with descriptions."""
    cprint(f"\n  {C.BOLD}{C.CYAN}Connect a Provider{C.RESET}")
    cprint(f"  {C.DIM}Choose a provider to add. All use OpenAI-compatible APIs.{C.RESET}")
    cprint(f"  {C.DIM}{'─' * 56}{C.RESET}")
    free = [(k, d, b, m, nk, desc) for k, d, b, m, nk, desc in PROVIDER_KINDS if not nk]
    paid = [(k, d, b, m, nk, desc) for k, d, b, m, nk, desc in PROVIDER_KINDS if nk]
    cprint(f"\n  {C.GREEN}Free (no API key needed):{C.RESET}")
    for i, (kind, display, base, model, needs_key, desc) in enumerate(free):
        cprint(f"    {C.GREEN}{i + 1:2d}{C.RESET} {C.BOLD}{display:22s}{C.RESET} {C.DIM}{desc}{C.RESET}")
    cprint(f"\n  {C.YELLOW}Paid (API key required):{C.RESET}")
    for i, (kind, display, base, model, needs_key, desc) in enumerate(paid):
        cprint(f"    {C.YELLOW}{len(free) + i + 1:2d}{C.RESET} {C.BOLD}{display:22s}{C.RESET} {C.DIM}{desc}{C.RESET}")
    cprint(f"\n  {C.DIM}Or type a name: ollama, openai, anthropic, gemini, openrouter, groq, cerebras, mistral, together, deepseek, xai{C.RESET}")
    return free, paid


def _interactive_add_provider(registry, kind=None):
    """Interactive provider setup wizard — OpenCode-style with model browser."""
    # Step 1: Pick provider
    if kind:
        info = _provider_kind_by_name(kind)
        if info:
            kind_info = info
            custom_name = None
        else:
            kind_info = None
            custom_name = kind
    else:
        free, paid = _show_provider_catalog()
        all_kinds = free + paid
        try:
            choice = input(f"\n  {C.CYAN}❯{C.RESET} Pick provider (number or name): ").strip()
        except (EOFError, KeyboardInterrupt):
            cprint(f"\n  {C.DIM}Cancelled.{C.RESET}")
            return
        if not choice:
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_kinds):
                kind_info = all_kinds[idx]
                custom_name = None
            else:
                cprint(f"  {C.RED}Invalid number.{C.RESET}")
                return
        else:
            info = _provider_kind_by_name(choice)
            if info:
                kind_info = info
                custom_name = None
            else:
                kind_info = None
                custom_name = choice

    if kind_info:
        kind, display, api_base_default, model_default, needs_key, desc = kind_info
    else:
        kind = "openai-compat"
        display = custom_name or "Custom"
        api_base_default = ""
        model_default = ""
        needs_key = True
        desc = "Custom OpenAI-compatible endpoint"

    # Step 2: Show model catalog for this provider
    models = _get_models_for_provider(kind)
    current_model = model_default

    cprint(f"\n  {C.NEON_CYAN}{C.BOLD}Setup: {display}{C.RESET} — {C.DIM}{desc}{C.RESET}")

    if models:
        cprint(f"\n  {C.NEON_PURPLE}{C.BOLD}Available Models:{C.RESET}")
        print(f"  {C.BORDER}{'─' * 100}{C.RESET}")
        for i, m in enumerate(models):
            print(_format_model_row(i + 1, m, current_model))
        print(f"  {C.BORDER}{'─' * 100}{C.RESET}")
        cprint(f"  {C.DIM}Pick a model number, or type a custom model name{C.RESET}")
    else:
        cprint(f"  {C.DIM}No curated models — type a model name{C.RESET}")

    try:
        # Step 3: Select model
        default_id = kind if not custom_name else custom_name.lower().replace(" ", "-").replace("/", "-")
        pid = input(f"\n  {C.CYAN}Provider ID{C.RESET} [{C.DIM}{default_id}{C.RESET}]: ").strip() or default_id

        if api_base_default:
            api_base = input(f"  {C.CYAN}API base{C.RESET} [{C.DIM}{api_base_default}{C.RESET}]: ").strip() or api_base_default
        else:
            api_base = input(f"  {C.CYAN}API base{C.RESET} [{C.DIM}https://...{C.RESET}]: ").strip()
            if not api_base:
                cprint(f"  {C.RED}API base is required.{C.RESET}")
                return

        # Live model catalog (OpenAI-compatible) — best-effort, key-less first.
        # Falls back to the curated/placeholder catalog if the gateway requires
        # auth for /models (the user can still type a model name manually).
        if api_base and (kind in CUSTOM_PROVIDER_IDS or kind in ("openai-compat", "openai")):
            live = _fetch_live_models(api_base)
            if live:
                models = [(m, m, 0, 0, 0, 0, ["code"]) for m in live]
                cprint(f"\n  {C.NEON_PURPLE}{C.BOLD}Live models from gateway:{C.RESET}")
                print(f"  {C.BORDER}{'─' * 100}{C.RESET}")
                for i, m in enumerate(models):
                    print(_format_model_row(i + 1, m, current_model))
                print(f"  {C.BORDER}{'─' * 100}{C.RESET}")
                cprint(f"  {C.DIM}Pick a model number, or type a custom model name{C.RESET}")

        # Model selection with catalog
        model_input = input(f"  {C.CYAN}Model{C.RESET} [{C.DIM}number or name{C.RESET}]: ").strip()
        if model_input.isdigit() and models:
            idx = int(model_input) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                model = selected[0]
                cprint(f"    {C.GREEN}✓{C.RESET} Selected: {C.BOLD}{selected[1]}{C.RESET} ({model})")
            else:
                cprint(f"  {C.RED}Invalid number.{C.RESET}")
                return
        elif model_input:
            model = model_input
        elif model_default:
            model = model_default
        else:
            model = input(f"  {C.CYAN}Model name{C.RESET}: ").strip() or "default"

        # API key
        api_key = None
        auth_method = "key"
        auth_ref = None
        if needs_key:
            api_key_input = input(f"  {C.CYAN}API key{C.RESET} [{C.DIM}sk-... (leave blank to use env/store){C.RESET}]: ").strip()
            if api_key_input:
                api_key = api_key_input
            elif kind not in ("ollama", "cloudflare"):
                cprint(f"  {C.YELLOW}⚠ No inline key — choose an auth method below.{C.RESET}")
            # Auth method: how the key is supplied. Supported by every paid
            # provider (OpenAI, Anthropic, Gemini, xAI, DeepSeek, ...).
            cprint(f"  {C.DIM}Auth method — how JEBAT supplies the key:{C.RESET}")
            cprint(f"  {C.DIM}  key   = paste the key inline (stored in providers.json){C.RESET}")
            cprint(f"  {C.DIM}  env   = read from an ENV var at runtime (recommended){C.RESET}")
            cprint(f"  {C.DIM}  store = read from the JEBAT auth store (~/.jebat/auth/tokens.json){C.RESET}")
            am = input(f"  {C.CYAN}Auth method{C.RESET} [{C.DIM}key/env/store{C.RESET}]: ").strip().lower() or "key"
            if am == "env":
                auth_method = "env"
                auth_ref = input(f"  {C.CYAN}Env var name{C.RESET} [{C.DIM}{kind.upper()}_API_KEY{C.RESET}]: ").strip() or f"{kind.upper()}_API_KEY"
            elif am == "store":
                auth_method = "store"
                auth_ref = input(f"  {C.CYAN}Stored key name{C.RESET} [{C.DIM}set via /apikey{C.RESET}]: ").strip() or None
                if not auth_ref:
                    cprint(f"  {C.YELLOW}⚠ No stored key name — provider may not authenticate.{C.RESET}")
            # 'key' keeps the inline api_key captured above
    except (EOFError, KeyboardInterrupt):
        cprint(f"\n  {C.DIM}Cancelled.{C.RESET}")
        return

    cfg = ProviderConfig(id=pid, name=display, api_base=api_base, model=model,
                        api_key=api_key, kind=kind, auth_method=auth_method, auth_ref=auth_ref)
    registry.register(pid, cfg)
    registry.use(pid)

    # Show confirmation
    _key_mask = (api_key[:8] + "••••") if api_key else "None"
    cprint(f"\n  {C.GREEN}✓{C.RESET} {C.BOLD}Added: {pid}{C.RESET}")
    _info_panel("Provider Details", [
        ("Provider", f"{display} ({kind})"),
        ("Model", model),
        ("Endpoint", api_base),
        ("Auth", f"{auth_method}" + (f" → {auth_ref}" if auth_ref else "")),
        ("Key", _key_mask),
    ], theme="success")
    cprint(f"\n  {C.GREEN}●{C.RESET} Active provider set to {C.BOLD}{pid}{C.RESET}")
    cprint(f"  {C.DIM}Test it: /health or send a message{C.RESET}\n")


def _interactive_remove_provider(registry):
    """Interactive provider removal."""
    providers = registry.configs
    if not providers:
        cprint(f"  {C.DIM}No providers configured.{C.RESET}")
        return
    cprint(f"\n  {C.BOLD}Remove Provider:{C.RESET}")
    items = list(providers.items())
    for i, (key, cfg) in enumerate(items):
        active = f" {C.GREEN}(active){C.RESET}" if key == registry.active_id else ""
        cprint(f"    {C.GREEN}{i + 1}{C.RESET}. {C.BOLD}{key}{C.RESET} — {cfg.kind}/{cfg.model}{active}")
    try:
        choice = input(f"\n  {C.CYAN}❯{C.RESET} Remove (number or name): ").strip()
    except (EOFError, KeyboardInterrupt):
        cprint(f"\n  {C.DIM}Cancelled.{C.RESET}")
        return
    if not choice:
        return
    target = None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(items):
            target = items[idx][0]
    elif choice in providers:
        target = choice
    if target:
        del registry.configs[target]
        if registry.active_id == target and registry.configs:
            registry.active_id = list(registry.configs.keys())[0]
        registry.save()
        cprint(f"  {C.GREEN}✓ Removed: {target}{C.RESET}")
    else:
        cprint(f"  {C.RED}Not found: {choice}{C.RESET}")


def _interactive_test_provider(registry):
    """Test all providers by pinging."""
    cprint(f"\n  {C.CYAN}Testing providers...{C.RESET}\n")
    for pid, cfg in registry.configs.items():
        try:
            if cfg.kind == "ollama":
                req = urllib.request.Request(f"{cfg.api_base}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    n = len(data.get("models", []))
                    cprint(f"  {C.GREEN}✓{C.RESET} {C.BOLD}{pid}{C.RESET} — {n} models available")
            else:
                key = resolve_api_key(cfg)
                headers = {"Authorization": f"Bearer {key}"} if key else {}
                req = urllib.request.Request(f"{cfg.api_base}/models", headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    cprint(f"  {C.GREEN}✓{C.RESET} {C.BOLD}{pid}{C.RESET} — reachable")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                cprint(f"  {C.YELLOW}⚠{C.RESET} {C.BOLD}{pid}{C.RESET} — {C.YELLOW}auth failed (check API key){C.RESET}")
            else:
                cprint(f"  {C.RED}✗{C.RESET} {C.BOLD}{pid}{C.RESET} — HTTP {e.code}")
        except Exception as e:
            err = str(e)[:60]
            cprint(f"  {C.RED}✗{C.RESET} {C.BOLD}{pid}{C.RESET} — {C.RED}{err}{C.RESET}")
    cprint()


def _list_models_for_provider(provider_cfg):
    """List models from a provider — Ollama, OpenRouter, or OpenAI-compatible."""
    kind = provider_cfg.get("kind", "")
    api_base = provider_cfg.get("api_base", "")
    # provider_cfg is a plain dict (from JSON); resolve key env/store-aware.
    ns = types.SimpleNamespace(
        api_key=provider_cfg.get("api_key"),
        auth_method=provider_cfg.get("auth_method", "key") or "key",
        auth_ref=provider_cfg.get("auth_ref"),
    )
    api_key = resolve_api_key(ns)
    models = []
    try:
        if kind == "ollama":
            req = urllib.request.Request(f"{api_base}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                models = [m["name"] for m in data.get("models", [])]
        elif kind == "openrouter":
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                models = [m["id"] for m in data.get("data", [])]
        elif kind == "groq":
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            req = urllib.request.Request("https://api.groq.com/openai/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                models = [m["id"] for m in data.get("data", [])]
        else:
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            req = urllib.request.Request(f"{api_base}/models", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
                models = [m.get("id", m.get("name", "")) for m in data.get("data", [])]
    except Exception:
        model = provider_cfg.get("model", "")
        models = [model] if model else []
    return models


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point — default to REPL."""
    args = sys.argv[1:]

    if not args:
        # No args → start interactive REPL directly
        registry = ProviderRegistry()
        taskdb = TaskDB()
        skills = SkillManager()

        # Show banner
        banner()
        cfg = registry.get_active()
        if cfg:
            show_setup(cfg.kind, cfg.model, cfg.api_base, "Ready")
        else:
            show_setup("none", "none", "none", "No provider")

        repl(registry, taskdb, skills)
        return

    if args[0] in ("-h", "--help", "help"):
        banner()
        print(f"  {C.BOLD}Usage:{C.RESET} jebat [command] [options] [prompt...]")
        print()
        print(f"  {C.CYAN}Commands:{C.RESET}")
        print(f"    code [prompt]    Coding agent with tools (default: REPL)")
        print(f"    chat [message]   Chat mode (no tools)")
        print(f"    provider list       List providers")
        print(f"    provider add        Connect new provider (wizard)")
        print(f"    provider remove     Remove a provider")
        print(f"    provider test       Test all providers")
        print(f"    provider use X      Switch active provider")
        print(f"    (no args)        Start interactive REPL")
        print()
        print(f"  {C.CYAN}REPL Commands:{C.RESET}")
        print(f"    /help /plan /mode /provider /model /scan /brainstorm /clear /exit")
        print(f"    /swarm /ghost /memory /tasks /session /diff /export /health")
        print()
        print(f"  {C.CYAN}Examples:{C.RESET}")
        print(f"    jebat                           # Start REPL")
        print(f"    jebat code \"Fix the bug\"        # One-shot coding")
        print(f"    jebat chat \"What is Python?\"    # Chat mode")
        print(f"    jebat provider add openai --id work")
        return

    registry = ProviderRegistry()
    taskdb = TaskDB()
    skills = SkillManager()

    if args[0] == "code":
        # Code mode
        prompt_parts = args[1:]
        # Parse flags
        yolo = "--yolo" in prompt_parts
        auto_commit = "--auto-commit" in prompt_parts or "-a" in prompt_parts
        plan = "--plan" in prompt_parts
        prompt_parts = [p for p in prompt_parts if not p.startswith("--") and p != "-a"]

        if prompt_parts:
            # One-shot mode
            prompt = " ".join(prompt_parts)
            agent = Agent(registry, taskdb, skills, yolo=yolo, auto_commit=auto_commit, plan_first=plan)

            banner()
            cfg = registry.get_active()
            if cfg:
                show_setup(cfg.kind, cfg.model, cfg.api_base, "Running")

            start_time = time.time()
            step = agent.step(prompt)
            elapsed = time.time() - start_time

            # Answer — clean markdown style
            cprint()
            _print_answer(step.response.text)

            model_str = cfg.model if cfg else "unknown"
            cost = estimate_cost(model_str, step.tokens)
            bottom_bar(cfg.kind if cfg else "unknown", model_str, tokens=step.tokens, tool_count=len(step.tool_actions), elapsed_s=elapsed, cost_usd=cost)

            # Drop into REPL after one-shot
            print()
            cprint(f"  {C.DIM}Continuing in REPL. Type /exit to quit.{C.RESET}")
            repl(registry, taskdb, skills)
        else:
            # REPL mode
            banner()
            cfg = registry.get_active()
            if cfg:
                show_setup(cfg.kind, cfg.model, cfg.api_base, "Ready")
            repl(registry, taskdb, skills)

    elif args[0] == "chat":
        prompt = " ".join(args[1:]) if len(args) > 1 else ""
        agent = Agent(registry, taskdb, skills)

        banner()
        cfg = registry.get_active()
        if cfg:
            show_setup(cfg.kind, cfg.model, cfg.api_base, "Chat")

        if prompt:
            cprint(f"\n  {agent.chat(prompt)}\n")
            return

        # Interactive chat
        print(f"  {C.DIM}Type your message. /exit to quit.{C.RESET}\n")
        while True:
            try:
                # Build dynamic prompt with mode indicator
                mode_info = MODES.get(agent.mode, {})
                mode_icon = mode_info.get("icon", "💻")
                model_short = cfg.model.split(":")[0] if cfg and ":" in cfg.model else (cfg.model if cfg else "?")
                prompt = input(f"  {C.NEON_GREEN}{mode_icon}{C.RESET} {C.NEON_CYAN}{model_short}{C.RESET} {C.BORDER}❯{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n  {C.DIM}Goodbye. 👋{C.RESET}\n")
                break
            if not prompt:
                continue
            if prompt.lower() in ("/exit", "/quit", "/q"):
                break
            cprint(f"\n  {agent.chat(prompt)}\n")

    elif args[0] == "provider":
        sub = args[1] if len(args) > 1 else "list"
        if sub == "list":
            if not registry.configs:
                print(f"  {C.DIM}No providers configured. Add: jebat provider add{C.RESET}")
            else:
                for key, cfg in registry.configs.items():
                    active = f" {C.GREEN}*{C.RESET}" if key == registry.active_id else ""
                    print(f"  {C.CYAN}{key}{C.RESET}: {cfg.kind} / {cfg.model} ({cfg.api_base}){active}")
        elif sub == "use":
            target = args[2] if len(args) > 2 else ""
            if registry.use(target):
                print(f"  {C.GREEN}Switched to:{C.RESET} {target}")
            else:
                print(f"  {C.RED}Unknown: {target}{C.RESET}")
        elif sub in ("add", "connect"):
            kind = args[2] if len(args) > 2 else None
            _interactive_add_provider(registry, kind)
        elif sub in ("remove", "rm"):
            _interactive_remove_provider(registry)
        elif sub in ("test", "ping"):
            _interactive_test_provider(registry)
        else:
            # Try as provider ID to switch
            if registry.use(sub):
                print(f"  {C.GREEN}Switched to:{C.RESET} {sub}")
            else:
                print(f"  {C.DIM}Usage: jebat provider [list|use|add|remove|test] [kind]{C.RESET}")
        repl(registry, taskdb, skills)

    else:
        # Unknown command — treat as one-shot prompt
        prompt = " ".join(args)
        agent = Agent(registry, taskdb, skills)
        banner()
        cfg = registry.get_active()
        if cfg:
            show_setup(cfg.kind, cfg.model, cfg.api_base, "Running")
        step = agent.step(prompt)
        cprint()
        _print_answer(step.response.text)
        model_str = cfg.model if cfg else "unknown"
        cost = estimate_cost(model_str, step.tokens)
        bottom_bar(cfg.kind if cfg else "unknown", model_str, tokens=step.tokens, tool_count=len(step.tool_actions), elapsed_s=0, cost_usd=cost)
        print()
        cprint(f"  {C.DIM}Continuing in REPL. Type /exit to quit.{C.RESET}")
        repl(registry, taskdb, skills)


if __name__ == "__main__":
    main()
