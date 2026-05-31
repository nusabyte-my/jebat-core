"""Interactive REPL loop with Rich UI.

Provides the core chat loop with:
  - Input prompt (Rich-powered)
  - Message streaming (placeholder for LLM integration)
  - Session persistence
  - /help, /exit, /history commands
"""

import sys
from typing import Callable

from .repl_session import ReplSession


class ReplLoop:
    """Main REPL loop — reads input, calls handler, persists, repeats."""

    def __init__(
        self,
        db_path: str | None = None,
        session_name: str | None = None,
        readonly: bool = False,
    ) -> None:
        self._readonly = readonly
        self._session = ReplSession(db_path=db_path)
        self._session.create_or_load(session_name)
        self._running = False
        self._on_message: Callable[
            [str], str
        ] | None = None  # hook for LLM integration

    @property
    def session(self) -> ReplSession:
        return self._session

    @property
    def session_id(self) -> str:
        return self._session.session_id

    def set_handler(self, handler: Callable[[str], str]) -> None:
        """Set the message handler (called with user input, returns response)."""
        self._on_message = handler

    def run(self) -> None:
        """Start the interactive REPL."""
        self._running = True
        print(f"JEBAT REPL — session: {self._session.name}")
        print("Type /help for commands, /exit to quit.\n")

        while self._running:
            try:
                user_input = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye.")
                break

            if not user_input:
                continue

            # Handle built-in commands
            if user_input.startswith("/"):
                self._handle_command(user_input)
                continue

            # Persist user message
            if not self._readonly:
                self._session.add_message("user", user_input)

            # Get response
            if self._on_message:
                response = self._on_message(user_input)
            else:
                response = f"[echo] {user_input}"

            print(response)

            # Persist assistant response
            if not self._readonly:
                self._session.add_message("assistant", response)

    def _handle_command(self, cmd: str) -> None:
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command == "/exit" or command == "/quit":
            self._running = False
            print("Goodbye.")
        elif command == "/help":
            print("Commands:")
            print("  /help    — show this help")
            print("  /history — show session history")
            print("  /clear   — clear screen")
            print("  /exit    — quit REPL")
        elif command == "/history":
            msgs = self._session.load_history(limit=20)
            for m in msgs:
                role = m["role"]
                content = m["content"]
                if len(content) > 80:
                    content = content[:77] + "..."
                print(f"  [{role}] {content}")
        elif command == "/clear":
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
        else:
            print(f"Unknown command: {command}. Type /help for available commands.")