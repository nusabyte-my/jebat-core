"""JEBAT Interactive REPL — full streaming chat loop with agent tool-calling.

This is the primary user-facing interface. Features:
- Real LLM generation via AgentLoop (ReAct tool-calling)
- Streaming token-by-token display with Rich
- Tool call visualization (shows each step as it happens)
- Session persistence (SQLite + FTS5)
- Context window management
- Input history (prompt_toolkit)
- Safety mode switching (auto/confirm/dangerous)
- Slash commands for model switching, tool listing, etc.
- Multi-line input support
- Graceful Ctrl+C handling
"""

from __future__ import annotations

import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from jebat.config import load_config
from jebat.features.session import SessionManager
from jebat.features.session.context import ContextManager, count_tokens

# Try to import rich for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
    from rich.table import Table
    from rich.rule import Rule
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None  # type: ignore

# Try prompt_toolkit for input history
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


def _print(text: str, style: str = "") -> None:
    if RICH_AVAILABLE and console:
        console.print(text, style=style)
    else:
        print(text)


def _input_line(prompt: str = "> ") -> str:
    """Get a line of input, supporting history via prompt_toolkit."""
    if PROMPT_TOOLKIT_AVAILABLE and _is_interactive_tty():
        history_path = Path.home() / ".jebat" / "repl_history.txt"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        session = PromptSession(history=FileHistory(str(history_path)))
        try:
            return session.prompt(prompt, multiline=False)
        except KeyboardInterrupt:
            return ""
    else:
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""


def _is_interactive_tty() -> bool:
    """Return True if stdin is a real interactive terminal.
    
    On Windows, MSYS/git-bash terminals don't expose proper PTY
    semantics to prompt_toolkit. Detect this and fall back to input().
    """
    if not sys.stdin.isatty():
        return False
    # On Windows, check for MSYS/git-bash (TERM=cygwin/xterm but no ConPTY)
    if sys.platform == "win32":
        # MSYS2/git-bash sets TERM but lacks ConPTY — prompt_toolkit will
        # fail to read input. Check if we're in a real Windows console.
        # ConPTY is available on Win10 1809+, but git-bash goes through
        # MSYS PTY emulation which prompt_toolkit can't detect.
        msys_env = os.environ.get("MSYSTEM", "")
        if msys_env:
            # Inside MSYS2/git-bash — fall back to input()
            return False
    return True


def _confirm(prompt_text: str) -> bool:
    """Simple Y/n confirmation for safety prompts."""
    try:
        response = input(prompt_text).strip().lower()
        return response in ("y", "yes", "")
    except (EOFError, KeyboardInterrupt):
        return False


class ReplLoop:
    """The interactive chat REPL loop with real LLM + agent tool-calling."""

    def __init__(
        self,
        session_id: str | None = None,
        ephemeral: bool = False,
        system_prompt: str | None = None,
    ):
        self.config = load_config()
        self.session_mgr = SessionManager()
        self.context_mgr = ContextManager(
            max_tokens=int(self.config.get("model.max_tokens", 32000))
        )
        self.ephemeral = ephemeral
        self.system_prompt = system_prompt or (
            "You are JEBAT, a pragmatic engineering assistant. "
            "Be direct, use tools when appropriate, and keep responses actionable."
        )
        self.running = True
        self.safety_mode = "auto"  # auto / confirm / dangerous

        # Current model/provider overrides (can change mid-session)
        self._provider_override: str | None = None
        self._model_override: str | None = None
        self._preset: str | None = None
        self._mode: str | None = None  # fast/deliberate/deep/etc.

        # Session setup
        if session_id:
            existing = self.session_mgr.get_session(session_id)
            if existing:
                self.session_id = session_id
                self.session = existing
                _print(f"Resumed session {session_id}", "dim")
            else:
                _print(f"Session {session_id} not found, starting new.", "yellow")
                self.session_id = self.session_mgr.create_session()
                self.session = self.session_mgr.get_session(self.session_id)
        else:
            self.session_id = self.session_mgr.create_session()
            self.session = self.session_mgr.get_session(self.session_id)

    async def run(self) -> None:
        """Main REPL loop."""
        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

        provider = self._provider_override or self.config.get("model.provider", "openai")
        model = self._model_override or self.config.get("model.model", "gpt-4o")

        _print(f"\n  JEBAT REPL -- session {self.session_id}", "bold green")
        _print(f"  {datetime.now().strftime('%A, %d %B %Y %H:%M')}", "dim")
        if self.ephemeral:
            _print("  EPHEMERAL mode -- messages not saved", "yellow")
        _print(f"  Model: {provider}/{model}", "dim")
        _print(f"  Safety: {self.safety_mode}", "dim")
        _print("  Type /help for commands, /quit to exit\n", "dim")

        # Show history if resuming
        if not self.ephemeral:
            history = self.session_mgr.load_history(self.session_id, limit=5)
            if history:
                _print("--- Recent history ---", "dim")
                for msg in history[-3:]:
                    label = {"user": "You", "assistant": "JEBAT"}.get(msg.role, msg.role)
                    preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                    _print(f"  [{label}] {preview}", "dim")
                _print("---\n", "dim")

        while self.running:
            try:
                user_input = _input_line("\n> ")
                if not user_input:
                    continue

                # Process commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                # Save user message
                if not self.ephemeral:
                    self.session_mgr.add_message(
                        self.session_id, "user", user_input,
                        tokens=count_tokens(user_input),
                    )

                # Run the agent loop
                await self._run_agent(user_input)

            except EOFError:
                self.running = False
            except KeyboardInterrupt:
                if not self.running:
                    break
                print("\n  (Ctrl+C to quit, or type /quit)")

        # Restore signal handler
        signal.signal(signal.SIGINT, original_sigint)

        # Auto-title the session
        if not self.ephemeral and self.session_mgr.message_count(self.session_id) >= 2:
            first_msg = self.session_mgr.load_history(self.session_id, limit=1)
            if first_msg:
                title = first_msg[0].content[:60].strip()
                if title:
                    self.session_mgr.update_title(self.session_id, title)

        _print(f"\n  Session {self.session_id} saved. Bye!\n", "dim blue")

    async def _run_agent(self, user_input: str) -> None:
        """Run the AgentLoop for a user message, displaying steps as they happen."""
        from jebat.core.agent_loop import AgentLoop, SafetyMode

        # Build conversation history from session
        if not self.ephemeral:
            history = self.session_mgr.load_history(self.session_id, limit=20)
            messages = [{"role": m.role, "content": m.content} for m in history]
        else:
            messages = []

        # Show thinking indicator
        if RICH_AVAILABLE and console:
            with Live(Spinner("dots", text="JEBAT thinking..."), console=console, transient=True):
                pass  # Just shows spinner briefly, then we run the loop

        _print("  [thinking...]", "dim")

        # Map safety mode string to SafetyMode constant
        safety_map = {
            "auto": SafetyMode.AUTO,
            "confirm": SafetyMode.CONFIRM,
            "dangerous": SafetyMode.DANGEROUS,
        }
        safety = safety_map.get(self.safety_mode, SafetyMode.AUTO)

        # Create agent loop with current config
        loop = AgentLoop(
            provider_override=self._provider_override,
            model_override=self._model_override,
            preset=self._preset,
            safety_mode=safety,
            max_iterations=10,
            interactive_confirm=_confirm if self.safety_mode == "auto" else None,
        )

        # Run the loop
        start_time = time.time()
        result = await loop.run(
            user_message=user_input,
            conversation_history=messages,
            mode=self._mode,
        )
        elapsed = time.time() - start_time

        # Display tool calls made during the loop
        if result.tool_calls_made:
            _print(Rule("Tool Calls", style="dim"), style="dim") if RICH_AVAILABLE else _print("--- Tool Calls ---")
            for step in result.tool_calls_made:
                status_icon = "OK" if step.error is None else "ERR"
                if not step.approved:
                    status_icon = "SKIP"
                duration = f"{step.duration_ms}ms" if step.duration_ms else "?"
                detail = ""
                if step.params:
                    # Show key params briefly
                    for k, v in list(step.params.items())[:2]:
                        val_str = str(v)[:60]
                        detail += f" {k}={val_str}"
                line = f"  [{status_icon}] {step.tool_name}({detail.strip()}) -- {duration}"
                if step.error:
                    line += f"  error: {step.error[:80]}"
                style = "green" if status_icon == "OK" else ("yellow" if status_icon == "SKIP" else "red")
                _print(line, style)
            _print("")  # spacing

        # Display the final response
        await self._stream_response(result.final_response)

        # Save assistant message
        if not self.ephemeral:
            self.session_mgr.add_message(
                self.session_id, "assistant", result.final_response,
                tokens=count_tokens(result.final_response),
            )

        # Show footer stats
        stats_parts = []
        if result.provider_used:
            stats_parts.append(f"provider: {result.provider_used}")
        if result.iterations_used > 1:
            stats_parts.append(f"iterations: {result.iterations_used}")
        if result.tokens_used.get("total_tokens"):
            stats_parts.append(f"tokens: {result.tokens_used['total_tokens']}")
        stats_parts.append(f"time: {elapsed:.1f}s")
        if result.tool_calls_made:
            stats_parts.append(f"tools: {len(result.tool_calls_made)} calls")

        stats_line = "  " + " | ".join(stats_parts)
        _print(stats_line, "dim")

    async def _stream_response(self, text: str) -> None:
        """Display the final response text with Rich Markdown rendering."""
        if RICH_AVAILABLE and console:
            try:
                md = Markdown(text)
                console.print(md)
            except Exception:
                # Rich markdown can fail on malformed content
                console.print(text)
        else:
            print(f"\n{text}")

    async def _handle_command(self, cmd_raw: str) -> None:
        """Handle slash commands."""
        # Split into command and args
        parts = cmd_raw.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ("/quit", "/exit", "/q"):
            self.running = False

        elif cmd == "/help":
            _print("""
  Commands:
    /quit, /exit, /q    Exit the REPL
    /help               Show this help
    /clear              Clear screen
    /save               Force save current session
    /status             Show session stats
    /sandbox            Toggle sandbox mode (blocks dangerous tools)
    /ephemeral          Toggle ephemeral mode (no session save)
    /sys <text>         Set system prompt
    /model <provider/model>  Switch model (e.g. /model openai/gpt-4o)
    /provider <name>    Switch provider only (openai, anthropic, google, openrouter, ollama)
    /preset <name>      Switch chat preset (fast, deliberate, deep, strategic, creative, critical)
    /mode <name>        Set reasoning mode for next response
    /tools              List available tools
    /safety <tier>      Set safety tier (auto, confirm, dangerous)
    /reset              Clear conversation history for this session
    /context            Show context window usage
            """.strip())

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")

        elif cmd == "/save":
            if self.ephemeral:
                _print("  Cannot save in ephemeral mode", "yellow")
            else:
                _print(f"  Session {self.session_id} saved ({self.session_mgr.message_count(self.session_id)} messages)", "green")

        elif cmd == "/status":
            count = self.session_mgr.message_count(self.session_id)
            tokens = self.session_mgr.total_tokens(self.session_id)
            provider = self._provider_override or self.config.get("model.provider", "openai")
            model = self._model_override or self.config.get("model.model", "gpt-4o")
            _print(f"  Session:  {self.session_id}", "bold")
            _print(f"  Messages: {count}")
            _print(f"  Tokens:   {tokens}")
            _print(f"  Model:    {provider}/{model}")
            _print(f"  Safety:   {self.safety_mode}")
            _print(f"  Ephemeral: {self.ephemeral}")
            if self._preset:
                _print(f"  Preset:   {self._preset}")
            if self._mode:
                _print(f"  Mode:     {self._mode}")

        elif cmd == "/ephemeral":
            self.ephemeral = not self.ephemeral
            _print(f"  Ephemeral mode: {'ON' if self.ephemeral else 'OFF'}", "yellow")

        elif cmd == "/sys" and args:
            self.system_prompt = args
            _print(f"  System prompt updated ({len(self.system_prompt)} chars)", "green")

        elif cmd == "/model" and args:
            if "/" in args:
                prov, mod = args.split("/", 1)
                self._provider_override = prov.strip()
                self._model_override = mod.strip()
            else:
                self._model_override = args.strip()
            provider = self._provider_override or self.config.get("model.provider", "?")
            model = self._model_override or self.config.get("model.model", "?")
            _print(f"  Model switched to: {provider}/{model}", "green")

        elif cmd == "/provider" and args:
            self._provider_override = args.strip()
            model = self._model_override or self.config.get("model.model", "?")
            _print(f"  Provider switched to: {self._provider_override}/{model}", "green")

        elif cmd == "/preset" and args:
            self._preset = args.strip()
            _print(f"  Preset set to: {self._preset}", "green")

        elif cmd == "/mode" and args:
            self._mode = args.strip()
            _print(f"  Mode set to: {self._mode}", "green")

        elif cmd == "/safety" and args:
            tier = args.strip().lower()
            if tier in ("auto", "confirm", "dangerous"):
                self.safety_mode = tier
                _print(f"  Safety mode: {self.safety_mode}", "yellow")
                if tier == "dangerous":
                    _print("  WARNING: All tools execute without confirmation!", "bold red")
                elif tier == "confirm":
                    _print("  All tools execute without confirmation prompts.", "yellow")
            else:
                _print(f"  Unknown tier: {tier}. Use: auto, confirm, dangerous", "yellow")

        elif cmd == "/tools":
            from jebat.tools import TOOL_REGISTRY
            # Trigger lazy imports
            try:
                from jebat.core.agent_loop import AgentLoop
                loop = AgentLoop.__new__(AgentLoop)
                loop._tools_imported = False
                loop._ensure_tools_imported()
            except Exception:
                pass

            if not TOOL_REGISTRY:
                _print("  No tools registered.", "yellow")
                return

            if RICH_AVAILABLE and console:
                table = Table(title="Available Tools", show_lines=False)
                table.add_column("Tool", style="cyan")
                table.add_column("Tier", style="dim")
                table.add_column("Description", style="white")
                for name, tdef in sorted(TOOL_REGISTRY.items()):
                    tier = tdef.safety_tier or "auto"
                    desc = (tdef.description or "No description")[:60]
                    table.add_row(name, tier, desc)
                console.print(table)
            else:
                for name, tdef in sorted(TOOL_REGISTRY.items()):
                    tier = tdef.safety_tier or "auto"
                    desc = (tdef.description or "No description")[:60]
                    _print(f"  {name} [{tier}] -- {desc}")

        elif cmd == "/reset":
            if not self.ephemeral:
                # Clear session messages but keep the session
                self.session_mgr.clear_history(self.session_id)
                _print("  Conversation history cleared.", "green")
            else:
                _print("  Nothing to reset in ephemeral mode.", "yellow")

        elif cmd == "/context":
            if not self.ephemeral:
                history = self.session_mgr.load_history(self.session_id, limit=50)
                total_tokens = sum(count_tokens(m.content) for m in history)
                max_tokens = int(self.config.get("model.max_tokens", 32000))
                pct = (total_tokens / max_tokens * 100) if max_tokens else 0
                _print(f"  Context: {total_tokens}/{max_tokens} tokens ({pct:.1f}%)", "bold")
                _print(f"  Messages in context: {len(history)}")
                if pct > 80:
                    _print("  WARNING: Context window nearly full! Consider /reset.", "bold red")
            else:
                _print("  No context tracking in ephemeral mode.", "yellow")

        else:
            _print(f"  Unknown command: {cmd_raw}. Type /help for list.", "yellow")

    def _handle_sigint(self, sig, frame) -> None:  # type: ignore
        """Handle Ctrl+C gracefully."""
        print()
        self.running = False