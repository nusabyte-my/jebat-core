"""
JEBAT — OMP-style Terminal UX.
Minimalist, high-taste terminal cards, box-drawing, and status chips.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional, Union

from jebat_cli_new.theme import (
    C,
    cprint,
    box,
    panel,
    thought_card,
    StreamingMarkdown,
    render_diff,
    ThinkingSpinner,
    bottom_bar,
    _print_answer,
    USE_COLOR,
)

# Backward-compatible color aliases
DIM = C.DIM
CYAN = C.CYAN
GREEN = C.GREEN
YELLOW = C.YELLOW
RED = C.RED
MAGENTA = C.MAGENTA
BOLD = C.BOLD
ITALIC = C.ITALIC
RESET = C.RESET


class TerminalUX:
    """OMP-inspired minimalist terminal UX with cards and box borders."""

    WIDTH = 75

    @classmethod
    def banner(cls, provider: str = "llamacpp", model: str = "jebat-llm.gguf", version: str = "8.2.1"):
        """Render sovereign header bar."""
        print()
        print(f"{C.DIM}┌─ {C.CYAN}{C.BOLD}JEBAT ⚔️  Sovereign Agent{C.RESET} {C.DIM}v{version} " + "─" * (cls.WIDTH - 35) + f"┐{C.RESET}")
        print(f"{C.DIM}│{C.RESET}  provider: {C.GREEN}{provider}{C.RESET} │ model: {C.CYAN}{model}{C.RESET} │ mode: {C.MAGENTA}ReAct-MultiTurn{C.RESET}")
        print(f"{C.DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{C.RESET}")
        print()

    @classmethod
    def thought_card(cls, thought: str, elapsed_s: Optional[float] = None, collapsed: bool = False):
        """Render an OMP-style reasoning scratchpad card."""
        thought_card(thought, elapsed_s=elapsed_s, collapsed=collapsed)

    @classmethod
    def tool_card(
        cls,
        tool_name: str,
        arguments: Union[Dict[str, Any], str],
        result_summary: str,
        latency_ms: Optional[float] = None,
        is_error: bool = False,
    ):
        """Render a tool execution card with arguments and execution summary."""
        args_str = json.dumps(arguments, ensure_ascii=False) if isinstance(arguments, dict) else str(arguments)
        if len(args_str) > cls.WIDTH - 12:
            args_str = args_str[: cls.WIDTH - 15] + "..."

        header = f"⚙️  Tool: {tool_name}"
        pad = cls.WIDTH - len(header) - 5
        print(f"{C.DIM}┌─ {C.CYAN}{header}{C.RESET}{C.DIM} " + "─" * max(2, pad) + f"┐{C.RESET}")
        print(f"{C.DIM}│{C.RESET}  args: {C.DIM}{args_str}{C.RESET}")
        print(f"{C.DIM}├" + "─" * (cls.WIDTH - 2) + f"┤{C.RESET}")

        status_icon = f"{C.RED}✗ Failed{C.RESET}" if is_error else f"{C.GREEN}✔ Success{C.RESET}"
        timing = f" {C.DIM}({latency_ms:.1f}ms){C.RESET}" if latency_ms is not None else ""

        # Clean single line summary
        summary = result_summary.strip().splitlines()[0] if result_summary else "Done"
        if len(summary) > cls.WIDTH - 25:
            summary = summary[: cls.WIDTH - 28] + "..."
        print(f"{C.DIM}│{C.RESET}  {status_icon}: {summary}{timing}")
        print(f"{C.DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{C.RESET}")

    @classmethod
    def response_card(cls, text: str, latency_ms: Optional[float] = None, tokens_used: int = 0):
        """Render response card."""
        timing_str = f" {C.DIM}({latency_ms:.0f}ms │ {tokens_used:,} tok){C.RESET}" if latency_ms else ""
        header = f"💬 Response{timing_str}"
        pad = cls.WIDTH - len(header) - 5
        print()
        print(f"{C.DIM}┌─ {C.GREEN}{header}{C.RESET}{C.DIM} " + "─" * max(2, pad) + f"┐{C.RESET}")
        for line in text.strip().splitlines():
            print(f"{C.DIM}│{C.RESET}  {line}")
        print(f"{C.DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{C.RESET}")
        print()

    @classmethod
    def live_stream_box(cls):
        """Open live streaming card in terminal."""
        pad = cls.WIDTH - 16
        print()
        print(f"{C.DIM}┌─ {C.GREEN}💬 Live Stream{C.RESET}{C.DIM} " + "─" * max(2, pad) + f"┐{C.RESET}")
        sys.stdout.write(f"{C.DIM}│{C.RESET}  ")
        sys.stdout.flush()

    @classmethod
    def live_stream_token(cls, token: str):
        """Stream a token directly into the terminal with border alignment."""
        if "\n" in token:
            parts = token.split("\n")
            for i, part in enumerate(parts):
                if i > 0:
                    sys.stdout.write(f"\n{C.DIM}│{C.RESET}  ")
                sys.stdout.write(part)
        else:
            sys.stdout.write(token)
        sys.stdout.flush()

    @classmethod
    def live_stream_end(cls, latency_ms: Optional[float] = None, tokens_used: int = 0):
        """Close live streaming card."""
        print()
        print(f"{C.DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{C.RESET}")
        if latency_ms is not None:
            print(f"  {C.DIM}Stream completed in {latency_ms:.0f}ms ({tokens_used:,} tokens){C.RESET}\n")

    @classmethod
    def context_gauge(cls, used_tokens: int, max_tokens: int = 16384) -> str:
        """Render a sleek OMP-style context usage gauge."""
        pct = min(100, int((used_tokens / max(1, max_tokens)) * 100))
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        color = C.GREEN if pct < 60 else (C.YELLOW if pct < 85 else C.RED)
        return f"{color}[{bar}] {pct}% ({used_tokens:,}/{max_tokens:,}){C.RESET}"

    @classmethod
    def prompt_prefix(cls, provider: str, model: str) -> str:
        """Return clean OMP prompt line."""
        return f"{C.DIM}[{provider}:{model}]{C.RESET} {C.CYAN}{C.BOLD}❯{C.RESET} "

    @classmethod
    def info(cls, msg: str):
        print(f"  {C.CYAN}ℹ{C.RESET} {msg}")

    @classmethod
    def warn(cls, msg: str):
        print(f"  {C.YELLOW}⚠{C.RESET} {msg}")

    @classmethod
    def err(cls, msg: str):
        print(f"  {C.RED}✗{C.RESET} {msg}")

    @classmethod
    def thinking(cls, msg: str):
        print(f"  {C.DIM}⟳ {msg}...{C.RESET}", end="", flush=True)

    @classmethod
    def thinking_done(cls):
        print(f"\r{' ' * 60}\r", end="", flush=True)


def streaming_print(text: str, provider: Optional[str] = None, model: Optional[str] = None):
    """Print with clean syntax coloring."""
    TerminalUX.response_card(text)
