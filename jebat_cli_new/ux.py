"""
JEBAT — OpenClaude-style terminal UX.
Clean, minimal, focused on the conversation.
"""

from __future__ import annotations

import sys
from typing import Optional


class TerminalUX:
    @staticmethod
    def banner(provider: str = "ollama", model: str = "qwen2.5-coder:7b"):
        """Print the JEBAT banner."""
        print()
        print("  JEBAT  ⚔️  unified coding agent")
        print(f"  provider: {provider}  model: {model}")
        print()

    @staticmethod
    def tool_header(name: str, args_summary: str = ""):
        """Show tool execution header."""
        print()
        print(f"  ◆ {name}", end="")
        if args_summary:
            print(f"({args_summary})", end="")
        print()
        print()

    @staticmethod
    def tool_result(name: str, result: str, success: bool = True):
        """Show tool execution result."""
        if success:
            print(f"  ✓ {name} done")
        else:
            print(f"  ✗ {name} failed: {result[:100]}")

    @staticmethod
    def answer_header():
        """Show answer header."""
        print()
        print("  ═══")
        print()

    @staticmethod
    def info(msg: str):
        """Show info message."""
        print(f"  ℹ {msg}")

    @staticmethod
    def warn(msg: str):
        """Show warning message."""
        print(f"  ⚠ {msg}")

    @staticmethod
    def err(msg: str):
        """Show error message."""
        print(f"  ✗ {msg}")

    @staticmethod
    def stream_prefix(provider: str = "ollama", model: str = ""):
        """Show streaming prefix."""
        print(f"\n  [{provider}:{model}] ", end="", flush=True)

    @staticmethod
    def thinking(msg: str):
        """Show thinking message."""
        print(f"  ⟳ {msg}", end="", flush=True)

    @staticmethod
    def thinking_done():
        """Clear thinking line."""
        print(f"\r{' ' * 60}\r", end="", flush=True)

    @staticmethod
    def progress(msg: str):
        """Show progress message."""
        print(f"  • {msg}")


def streaming_print(text: str, provider: Optional[str] = None, model: Optional[str] = None):
    """Print with streaming effect."""
    TerminalUX.stream_prefix(provider or "ollama", model or "qwen2.5-coder:7b")
    try:
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
        print()
    except KeyboardInterrupt:
        print("\n  [stream interrupted]")
