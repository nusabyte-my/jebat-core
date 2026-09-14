"""
JEBAT — OMP-style Terminal UX.
Minimalist, high-taste terminal cards, box-drawing, and status chips.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional, Union

# ─── ANSI Palette (Subtle Zinc / Cyan / Emerald) ───────────────────

USE_COLOR = os.environ.get("NO_COLOR") is None and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

if USE_COLOR:
    DIM = "\033[90m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    RESET = "\033[0m"
else:
    DIM = CYAN = GREEN = YELLOW = RED = MAGENTA = BOLD = ITALIC = RESET = ""


class TerminalUX:
    """OMP-inspired minimalist terminal UX with cards and box borders."""

    WIDTH = 75

    @classmethod
    def banner(cls, provider: str = "llamacpp", model: str = "jebat-llm.gguf", version: str = "8.2.1"):
        """Render sovereign header bar."""
        print()
        print(f"{DIM}┌─ {CYAN}{BOLD}JEBAT ⚔️  Sovereign Agent{RESET} {DIM}v{version} " + "─" * (cls.WIDTH - 35) + f"┐{RESET}")
        print(f"{DIM}│{RESET}  provider: {GREEN}{provider}{RESET} │ model: {CYAN}{model}{RESET} │ mode: {MAGENTA}ReAct-MultiTurn{RESET}")
        print(f"{DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{RESET}")
        print()

    @classmethod
    def thought_card(cls, thought: str, elapsed_s: Optional[float] = None):
        """Render an OMP-style reasoning scratchpad card."""
        if not thought or not thought.strip():
            return
        timing = f" ({elapsed_s:.1f}s)" if elapsed_s is not None else ""
        header = f"💭 Thought{timing}"
        pad = cls.WIDTH - len(header) - 5
        print(f"{DIM}┌─ {YELLOW}{header}{RESET}{DIM} " + "─" * max(2, pad) + f"┐{RESET}")
        for line in thought.strip().splitlines():
            # word wrap if line is too long
            while len(line) > cls.WIDTH - 6:
                print(f"{DIM}│{RESET}  {ITALIC}{DIM}{line[:cls.WIDTH - 6]}{RESET}")
                line = line[cls.WIDTH - 6:]
            print(f"{DIM}│{RESET}  {ITALIC}{DIM}{line}{RESET}")
        print(f"{DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{RESET}")

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
        print(f"{DIM}┌─ {CYAN}{header}{RESET}{DIM} " + "─" * max(2, pad) + f"┐{RESET}")
        print(f"{DIM}│{RESET}  args: {DIM}{args_str}{RESET}")
        print(f"{DIM}├" + "─" * (cls.WIDTH - 2) + f"┤{RESET}")

        status_icon = f"{RED}✗ Failed{RESET}" if is_error else f"{GREEN}✔ Success{RESET}"
        timing = f" {DIM}({latency_ms:.1f}ms){RESET}" if latency_ms is not None else ""

        # Clean single line summary
        summary = result_summary.strip().splitlines()[0] if result_summary else "Done"
        if len(summary) > cls.WIDTH - 25:
            summary = summary[: cls.WIDTH - 28] + "..."
        print(f"{DIM}│{RESET}  {status_icon}: {summary}{timing}")
        print(f"{DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{RESET}")

    @classmethod
    def response_card(cls, text: str, latency_ms: Optional[float] = None, tokens_used: int = 0):
        """Render response card."""
        timing_str = f" {DIM}({latency_ms:.0f}ms │ {tokens_used:,} tok){RESET}" if latency_ms else ""
        header = f"💬 Response{timing_str}"
        pad = cls.WIDTH - len(header) - 5
        print()
        print(f"{DIM}┌─ {GREEN}{header}{RESET}{DIM} " + "─" * max(2, pad) + f"┐{RESET}")
        for line in text.strip().splitlines():
            print(f"{DIM}│{RESET}  {line}")
        print(f"{DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{RESET}")
        print()

    @classmethod
    def live_stream_box(cls):
        """Open live streaming card in terminal."""
        pad = cls.WIDTH - 16
        print()
        print(f"{DIM}┌─ {GREEN}💬 Live Stream{RESET}{DIM} " + "─" * max(2, pad) + f"┐{RESET}")
        sys.stdout.write(f"{DIM}│{RESET}  ")
        sys.stdout.flush()

    @classmethod
    def live_stream_token(cls, token: str):
        """Stream a token directly into the terminal with border alignment."""
        if "\n" in token:
            parts = token.split("\n")
            for i, part in enumerate(parts):
                if i > 0:
                    sys.stdout.write(f"\n{DIM}│{RESET}  ")
                sys.stdout.write(part)
        else:
            sys.stdout.write(token)
        sys.stdout.flush()

    @classmethod
    def live_stream_end(cls, latency_ms: Optional[float] = None, tokens_used: int = 0):
        """Close live streaming card."""
        print()
        print(f"{DIM}└" + "─" * (cls.WIDTH - 2) + f"┘{RESET}")
        if latency_ms is not None:
            print(f"  {DIM}Stream completed in {latency_ms:.0f}ms ({tokens_used:,} tokens){RESET}\n")

    @classmethod
    def context_gauge(cls, used_tokens: int, max_tokens: int = 16384) -> str:
        """Render a sleek OMP-style context usage gauge."""
        pct = min(100, int((used_tokens / max(1, max_tokens)) * 100))
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        color = GREEN if pct < 60 else (YELLOW if pct < 85 else RED)
        return f"{color}[{bar}] {pct}% ({used_tokens:,}/{max_tokens:,}){RESET}"

    @classmethod
    def prompt_prefix(cls, provider: str, model: str) -> str:
        """Return clean OMP prompt line."""
        return f"{DIM}[{provider}:{model}]{RESET} {CYAN}{BOLD}❯{RESET} "

    @classmethod
    def info(cls, msg: str):
        print(f"  {CYAN}ℹ{RESET} {msg}")

    @classmethod
    def warn(cls, msg: str):
        print(f"  {YELLOW}⚠{RESET} {msg}")

    @classmethod
    def err(cls, msg: str):
        print(f"  {RED}✗{RESET} {msg}")

    @classmethod
    def thinking(cls, msg: str):
        print(f"  {DIM}⟳ {msg}...{RESET}", end="", flush=True)

    @classmethod
    def thinking_done(cls):
        print(f"\r{' ' * 60}\r", end="", flush=True)


def streaming_print(text: str, provider: Optional[str] = None, model: Optional[str] = None):
    """Print with clean syntax coloring."""
    TerminalUX.response_card(text)
