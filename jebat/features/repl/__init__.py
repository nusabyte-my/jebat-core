"""JEBAT Interactive REPL — streaming chat with session persistence."""

from __future__ import annotations


async def run_repl(session_id: str | None = None, ephemeral: bool = False) -> None:
    """Run the interactive chat REPL loop.

    Args:
        session_id: Resume an existing session, or None for new.
        ephemeral: If True, don't persist messages to SQLite.
    """
    # Will be built out in Stage 2
    from jebat.features.repl.repl import ReplLoop
    loop = ReplLoop(session_id=session_id, ephemeral=ephemeral)
    await loop.run()