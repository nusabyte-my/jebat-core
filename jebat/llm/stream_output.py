"""JEBAT Streaming Output Module — character-by-character terminal output via Rich.

For CLI agent commands (chat, chat-repl, agent), this provides immediate
visual feedback instead of waiting for the full response to appear.
Tokens are printed as they arrive from the LLM, just like Claude Code and Hermes.
"""

from __future__ import annotations

import sys
import asyncio
from typing import Any, AsyncIterator

from rich.console import Console
from rich.live import Live
from rich.text import Text


# ── Streaming Printer ────────────────────────────────────────────────────────

class StreamPrinter:
    """Prints LLM tokens to terminal as they arrive, character-by-character.

    Usage:
        printer = StreamPrinter()
        await printer.stream(async_generator)
        # or
        printer.print_final(full_text)
    """

    def __init__(self, console: Console | None = None, show_cursor: bool = True):
        self.console = console or Console()
        self.show_cursor = show_cursor
        self._buffer = Text()
        self._live = Live(
            self._buffer,
            console=self.console,
            refresh_per_second=15,
            transient=False,
            vertical_overflow="visible",
        )

    async def stream(self, token_generator: AsyncIterator[str]) -> str:
        """Stream tokens from an async generator and print them live.

        Args:
            token_generator: Async generator that yields text chunks.

        Returns:
            The full accumulated text after streaming completes.
        """
        full_text = ""
        self._buffer = Text("")
        self._live = Live(
            self._buffer,
            console=self.console,
            refresh_per_second=15,
            transient=False,
            vertical_overflow="visible",
        )
        self._live.start()

        try:
            async for chunk in token_generator:
                if isinstance(chunk, str):
                    full_text += chunk
                    self._buffer.append(chunk)
                    self._live.update(self._buffer)
                # Small delay to let Rich render — not too slow
                await asyncio.sleep(0.001)
        except Exception as e:
            # On error, just print what we have so far
            self.console.print(f"\n[Stream interrupted: {e}]", style="yellow")
        finally:
            self._live.stop()

        return full_text

    def print_final(self, text: str) -> None:
        """Print a complete (non-streaming) response in one shot.

        This is the fallback when streaming isn't available.
        """
        self.console.print(text)


# ── Integration with generate_with_failover ──────────────────────────────────

async def generate_streaming_with_failover(
    config: Any,
    prompt: str,
    system_prompt: str | None = None,
    printer: StreamPrinter | None = None,
) -> tuple[str, str]:
    """Generate a streaming response with 3-tier fallback.

    This mirrors generate_with_failover but uses streaming when the provider
    supports it. Falls back to non-streaming for providers that don't.

    Args:
        config: JebatLLMConfig with provider, model, fallback chain.
        prompt: User prompt text.
        system_prompt: Optional system prompt.
        printer: StreamPrinter instance for live output. If None, collects silently.

    Returns:
        (response_text, provider_used) tuple.
    """
    from jebat.llm import generate_with_failover

    # Try streaming with the primary provider first
    provider = config.provider
    model = config.model

    # Check if the primary provider supports streaming
    try:
        from jebat.llm.ninerouter_provider import build_ninerouter_provider
        ninerouter = build_ninerouter_provider(config)

        if printer:
            full_text = await printer.stream(ninerouter.generate_streaming(prompt, system_prompt))
        else:
            # Collect without printing (silent mode)
            full_text = ""
            async for chunk in ninerouter.generate_streaming(prompt, system_prompt):
                full_text += chunk

        return full_text, "ninerouter"
    except Exception:
        # Streaming failed — fall back to standard non-streaming generation
        pass

    # Fallback to standard generation (already handles 3-tier failover)
    response, used_provider = await generate_with_failover(
        config=config,
        prompt=prompt,
        system_prompt=system_prompt,
    )

    if printer:
        printer.print_final(response)

    return response, used_provider