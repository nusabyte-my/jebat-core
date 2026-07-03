"""
JEBAT — REPL with Pi-style terminal UX and streaming hooks.
"""

from __future__ import annotations

import sys
from typing import Optional


class TerminalUX:
    @staticmethod
    def banner(width: int = 60):
        print("=" * width)
        print("JEBAT ⚔️  unified coding agent".center(width))
        print("providers: ollama | openai | anthropic | gemini | github".center(width))
        print("=" * width)

    @staticmethod
    def info(msg: str):
        print(f"\n[info] {msg}")

    @staticmethod
    def warn(msg: str):
        print(f"\n[warn] {msg}")

    @staticmethod
    def err(msg: str):
        print(f"\n[error] {msg}")

    @staticmethod
    def stream_prefix(provider: str, model: str):
        print(f"\n[{provider}:{model}] → ", end="", flush=True)


def streaming_print(text: str, provider: Optional[str] = None, model: Optional[str] = None):
    TerminalUX.stream_prefix(provider or "ollama", model or "qwen2.5-coder:7b")
    try:
        for ch in text:
            sys.stdout.write(ch)
        sys.stdout.flush()
        print()
    except KeyboardInterrupt:
        print("\n[stream interrupted]")
