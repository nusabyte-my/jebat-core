"""
🗡️ JEBAT DevAssistant - Interactive CLI

Modern interactive command-line interface with:
- REPL-style interaction
- Rich UI with syntax highlighting
- Streaming responses
- Chat history
- Slash commands
- Auto-suggestions
- Real-time status indicators

Usage:
    jebat                          # Start interactive mode
    jebat "create a React app"     # Single command
    jebat -i                       # Force interactive mode
"""

import asyncio
import json
import os
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Rich UI imports
try:
    from rich.console import Console
    from rich.live import Live
    from rich.logging import RichHandler
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.spinner import Spinner
    from rich.style import Style
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Prompt toolkit for advanced input
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style as PromptStyle

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

    class Completer:  # type: ignore[no-redef]
        """Fallback base class when prompt-toolkit is unavailable."""

        pass

    class Completion:  # type: ignore[no-redef]
        """Fallback completion placeholder."""

        def __init__(self, *args, **kwargs):
            pass

    class KeyBindings:  # type: ignore[no-redef]
        """Fallback key bindings placeholder."""

        def add(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

from ..brain.dev_brain import DevBrain, TaskResult
from ..sandbox.dev_sandbox import DevSandbox

# ==================== Custom Completer ====================


class JebatCompleter(Completer):
    """Auto-completion for JEBAT commands."""

    COMMANDS = [
        "create",
        "modify",
        "review",
        "generate",
        "ui",
        "debug",
        "scaffold",
        "git",
        "test",
        "help",
        "exit",
        "quit",
    ]

    SLASH_COMMANDS = [
        "/help",
        "/agents",
        "/agent",
        "/clear",
        "/history",
        "/sessions",
        "/session",
        "/config",
        "/status",
        "/workspace",
        "/gateway",
        "/models",
        "/files",
        "/undo",
        "/settings",
    ]

    PROJECT_TYPES = ["python_package", "react_app", "nodejs_app"]
    FRAMEWORKS = ["react", "vue", "angular", "pytest", "jest", "unittest"]
    GIT_OPS = ["init", "add", "commit", "status", "log", "push", "pull", "branch"]

    def __init__(self):
        super().__init__()
        self.words = set()

    def add_word(self, word: str):
        """Add word to completion dictionary."""
        if len(word) > 2:
            self.words.add(word)

    def get_completions(self, document, complete_event):
        """Get completions based on current input."""
        text = document.text_before_cursor.lower()
        words = text.split()

        # Slash commands
        if text.startswith("/"):
            for cmd in self.SLASH_COMMANDS:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
            return

        # First word - commands
        if not words or (len(words) == 1 and not text.endswith(" ")):
            for cmd in self.COMMANDS:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
            return

        # Context-aware completions
        first_word = words[0] if words else ""

        if first_word == "scaffold" and len(words) <= 2:
            for pt in self.PROJECT_TYPES:
                if pt.startswith(words[-1]):
                    yield Completion(pt, start_position=-len(words[-1]))

        elif first_word == "ui" and "--framework" in text:
            for fw in self.FRAMEWORKS:
                if fw.startswith(words[-1]):
                    yield Completion(fw, start_position=-len(words[-1]))

        elif first_word == "git" and len(words) <= 2:
            for op in self.GIT_OPS:
                if op.startswith(words[-1]):
                    yield Completion(op, start_position=-len(words[-1]))

        elif first_word == "test" and "--framework" in text:
            for fw in self.FRAMEWORKS:
                if fw.startswith(words[-1]):
                    yield Completion(fw, start_position=-len(words[-1]))

        # General word completions
        for word in self.words:
            if word.startswith(words[-1]) and word != words[-1]:
                yield Completion(word, start_position=-len(words[-1]))


# ==================== Interactive CLI Class ====================


class InteractiveCLI:
    """
    Interactive CLI for JEBAT DevAssistant.

    Features:
    - REPL-style interaction
    - Rich formatting
    - Streaming responses
    - Chat history
    - Slash commands
    - Auto-completion
    """

    # Welcome banner
    BANNER = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🗡️  JEBAT DevAssistant  v1.0.0                         ║
║                                                           ║
║   Your Personal Development AI Assistant                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """

    AGENT_ROLES = {
        "jebat": {
            "label": "Primary",
            "description": "General operator with full task routing",
            "default_task": "generate",
        },
        "builder": {
            "label": "Build",
            "description": "Project creation and code generation",
            "default_task": "generate",
        },
        "reviewer": {
            "label": "Review",
            "description": "Code review and quality checks",
            "default_task": "review",
        },
        "debugger": {
            "label": "Debug",
            "description": "Error analysis and fixes",
            "default_task": "debug",
        },
        "designer": {
            "label": "UI",
            "description": "UI generation and frontend shaping",
            "default_task": "ui",
        },
        "operator": {
            "label": "Ops",
            "description": "Git, tests, and runtime operations",
            "default_task": "git",
        },
    }

    def __init__(self, use_rich: bool = True, use_prompt_toolkit: bool = True):
        """
        Initialize interactive CLI.

        Args:
            use_rich: Enable Rich UI formatting
            use_prompt_toolkit: Enable advanced input features
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.use_prompt_toolkit = use_prompt_toolkit and PROMPT_TOOLKIT_AVAILABLE

        # Initialize console
        self.console = Console() if self.use_rich else None

        # Initialize brain and sandbox
        self.brain = DevBrain()
        self.sandbox = DevSandbox()
        self.brain.initialize_skills(self.sandbox)

        # Chat history
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {
            "current_project": None,
            "last_command": None,
            "last_result": None,
        }
        self.active_agent = "jebat"
        self.session_dir = self._resolve_session_dir()
        self.session_name = self._default_session_name()
        self.gateway_state_path = Path.home() / ".jebat" / "gateway-state.json"
        self.gateway_config_path = Path.home() / ".jebat" / "jebat-gateway.json"

        # Completer
        self.completer = JebatCompleter() if self.use_prompt_toolkit else None

        # Key bindings
        self.bindings = self._create_key_bindings() if self.use_prompt_toolkit else None

        # Prompt style
        self.prompt_style = None
        if self.use_prompt_toolkit:
            self.prompt_style = PromptStyle.from_dict(
                {
                    "prompt": "fg:#00ff00 bold",
                    "input": "fg:#ffffff",
                    "completion-menu.completion": "bg:#008800 #ffffff",
                    "completion-menu.completion.current": "bg:#00ff00 #000000",
                }
            )

        # Stats
        self.stats = {
            "commands_executed": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "start_time": datetime.now(),
        }

        self._restore_latest_session()

    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings."""
        bindings = KeyBindings()

        @bindings.add("c-d")
        def _(event):
            """Exit on Ctrl+D."""
            event.app.exit(result="exit")

        @bindings.add("c-c")
        def _(event):
            """Cancel on Ctrl+C."""
            event.app.exit(result="")

        return bindings

    def print_banner(self):
        """Print welcome banner."""
        if self.use_rich:
            self.console.print(
                Panel(
                    Text(self.BANNER, style="bold cyan"),
                    border_style="green",
                    padding=(1, 2),
                )
            )
            self.console.print(
                f"[dim]Session:[/dim] [cyan]{self.session_name}[/cyan]  "
                f"[dim]Agent:[/dim] [green]{self.active_agent}[/green]"
            )
            self._print_help()
        else:
            print(self.BANNER)
            print(f"Session: {self.session_name} | Agent: {self.active_agent}")
            print("Type 'help' for commands, '/help' for slash commands\n")

    def _print_help(self):
        """Print help information."""
        if not self.use_rich:
            print("""
Commands:
  create     Create new projects/components
  modify     Modify existing code
  review     Review code for issues
  generate   Generate code
  ui         Generate UI with Stitch MCP
  debug      Debug issues
  scaffold   Scaffold a new project
  git        Git operations
  test       Run tests
  help       Show this help
  exit/quit  Exit JEBAT

Slash Commands:
  /help      Show detailed help
  /agents    Show available control agents
  /agent     Switch active agent
  /clear     Clear screen
  /history   Show command history
  /sessions  Show saved sessions
  /session   Save/load/create sessions
  /config    Show configuration
  /status    Show system status
  /workspace Show workspace and path details
  /gateway   Show gateway runtime state
  /models    Show available models
  /files     Show recent files
  /undo      Undo last action
  /settings  Open settings

Examples:
  create a React chat application
  scaffold myapp --type python_package
  review src/main.py
  debug "ModuleNotFoundError: No module named 'flask'"
  git commit -m "fix: bug fix"
  ui modern login form --framework react
""")
            return

        self.console.print("\n[bold cyan]📚 Commands:[/bold cyan]")

        commands_table = Table(show_header=True, header_style="bold magenta")
        commands_table.add_column("Command", style="cyan", width=12)
        commands_table.add_column("Description", style="white")
        commands_table.add_column("Example", style="green", width=35)

        commands_table.add_row(
            "create", "Create new projects/components", "create a React chat app"
        )
        commands_table.add_row(
            "scaffold", "Scaffold a new project", "scaffold myapp --type python_package"
        )
        commands_table.add_row("review", "Review code for issues", "review src/main.py")
        commands_table.add_row("generate", "Generate code", "generate a REST API")
        commands_table.add_row(
            "ui",
            "Generate UI with Stitch MCP",
            "ui modern login form --framework react",
        )
        commands_table.add_row(
            "debug", "Debug issues", 'debug "ModuleNotFoundError..."'
        )
        commands_table.add_row("git", "Git operations", 'git commit -m "fix: bug"')
        commands_table.add_row("test", "Run tests", "test --framework pytest")

        self.console.print(commands_table)

        self.console.print("\n[bold cyan]🔧 Slash Commands:[/bold cyan]")
        slash_commands = [
            "/help",
            "/agents",
            "/agent",
            "/clear",
            "/history",
            "/sessions",
            "/session",
            "/config",
            "/status",
            "/workspace",
            "/gateway",
            "/models",
            "/files",
            "/undo",
            "/settings",
        ]
        self.console.print(
            "  " + "  ".join(f"[yellow]{cmd}[/yellow]" for cmd in slash_commands)
        )

        self.console.print("\n[bold cyan]💡 Tips:[/bold cyan]")
        self.console.print("  • Use [green]Tab[/green] for auto-completion")
        self.console.print("  • Use [green]↑/↓[/green] for history navigation")
        self.console.print("  • Use [green]Ctrl+D[/green] to exit")
        self.console.print("  • Use [green]/clear[/green] to clear screen\n")

    def _default_session_name(self) -> str:
        return datetime.now().strftime("session-%Y%m%d-%H%M%S")

    def _resolve_session_dir(self) -> Path:
        candidates = [
            os.environ.get("JEBAT_TUI_SESSION_DIR"),
            str(Path.home() / ".jebat" / "tui-sessions"),
            str(Path.cwd() / ".jebat" / "tui-sessions"),
            str(Path("/tmp") / "jebat-tui-sessions"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            target = Path(candidate)
            try:
                target.mkdir(parents=True, exist_ok=True)
                probe = target / ".write-test"
                probe.write_text("ok", encoding="utf-8")
                probe.unlink(missing_ok=True)
                return target
            except Exception:
                continue
        return Path.cwd()

    def _session_payload(self) -> Dict[str, Any]:
        return {
            "session_name": self.session_name,
            "active_agent": self.active_agent,
            "context": self.context,
            "history": self.history[-200:],
            "stats": {
                **self.stats,
                "start_time": self.stats["start_time"].isoformat(),
            },
            "updated_at": datetime.now().isoformat(),
        }

    def _restore_latest_session(self):
        try:
            if not self.session_dir.exists():
                return
            candidates = sorted(
                self.session_dir.glob("*.json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            if not candidates:
                return
            self._load_session(candidates[0].stem, quiet=True)
        except Exception:
            return

    def _save_session(self, name: Optional[str] = None) -> Path:
        session_name = name or self.session_name
        target = self.session_dir / f"{session_name}.json"
        payload = self._session_payload()
        payload["session_name"] = session_name
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.session_name = session_name
        return target

    def _load_session(self, name: str, quiet: bool = False) -> bool:
        target = self.session_dir / f"{name}.json"
        if not target.exists():
            return False
        payload = json.loads(target.read_text(encoding="utf-8"))
        self.session_name = payload.get("session_name", name)
        self.active_agent = payload.get("active_agent", "jebat")
        self.context = payload.get(
            "context",
            {"current_project": None, "last_command": None, "last_result": None},
        )
        self.history = payload.get("history", [])
        stats = payload.get("stats", {})
        start_time = stats.get("start_time")
        self.stats = {
            "commands_executed": stats.get("commands_executed", 0),
            "successful_commands": stats.get("successful_commands", 0),
            "failed_commands": stats.get("failed_commands", 0),
            "start_time": datetime.fromisoformat(start_time)
            if start_time
            else datetime.now(),
        }
        if not quiet and self.use_rich:
            self.console.print(
                f"[green]✓[/green] Loaded session [cyan]{self.session_name}[/cyan]"
            )
        elif not quiet:
            print(f"Loaded session {self.session_name}")
        return True

    def _list_sessions(self) -> List[Path]:
        if not self.session_dir.exists():
            return []
        return sorted(
            self.session_dir.glob("*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )

    def _get_input(self) -> str:
        """Get user input with advanced features."""
        if self.use_prompt_toolkit and self.completer:
            try:
                user_input = prompt(
                    [("class:prompt", "🗡️  ")],
                    completer=self.completer,
                    complete_while_typing=True,
                    auto_suggest=AutoSuggestFromHistory(),
                    history=FileHistory(str(Path.home() / ".jebat_history")),
                    key_bindings=self.bindings,
                    style=self.prompt_style,
                    multiline=False,
                )
                return user_input.strip()
            except EOFError:
                return "exit"
            except KeyboardInterrupt:
                return ""
        else:
            try:
                if self.use_rich:
                    return self.console.input("[bold green]🗡️  [/bold green]")
                else:
                    return input("🗡️  ")
            except EOFError:
                return "exit"
            except KeyboardInterrupt:
                print()
                return ""

    def _show_spinner(self, message: str):
        """Show spinner during processing."""
        if self.use_rich:
            return Spinner("dots", text=f"[cyan]{message}[/cyan]", style="green")
        else:
            print(f"⏳ {message}...")
            return None

    def _print_result(self, result: TaskResult, command: str):
        """Print task result with rich formatting."""
        if not self.use_rich:
            if result.success:
                print(f"✅ {result.message}")
            else:
                print(f"❌ {result.message}")
            if result.issues:
                print("Issues:")
                for issue in result.issues:
                    print(f"  - {issue}")
            if result.cause:
                print(f"Cause: {result.cause}")
            if result.fix:
                print(f"Fix: {result.fix}")
            return

        # Success panel
        if result.success:
            panel = Panel(
                Text(result.message, style="green"),
                title="[bold green]✅ Success[/bold green]",
                border_style="green",
            )
        else:
            panel = Panel(
                Text(result.message, style="red"),
                title="[bold red]❌ Failed[/bold red]",
                border_style="red",
            )

        self.console.print(panel)

        # Issues
        if result.issues:
            self.console.print("\n[bold yellow]⚠️  Issues:[/bold yellow]")
            for issue in result.issues:
                self.console.print(f"  [red]•[/red] {issue}")

        # Debug info
        if result.cause:
            self.console.print(f"\n[bold yellow]🔍 Cause:[/bold yellow] {result.cause}")

        if result.fix:
            self.console.print(f"[bold green]🔧 Fix:[/bold green] {result.fix}")

        # Files created
        if result.files:
            self.console.print("\n[bold cyan]📁 Files:[/bold cyan]")
            for f in result.files:
                self.console.print(f"  [green]✓[/green] {f}")

        # Metadata
        if result.metadata:
            self._print_metadata(result.metadata)

    def _print_metadata(self, metadata: Dict[str, Any]):
        """Print metadata with formatting."""
        if not self.use_rich or not metadata:
            return

        if "status" in metadata and metadata["status"]:
            self.console.print(f"\n[bold cyan]Status:[/bold cyan]")
            self.console.print(metadata["status"])

        if "total" in metadata and "passed" in metadata:
            total = metadata.get("total", 0)
            passed = metadata.get("passed", 0)
            failed = metadata.get("failed", 0)

            self.console.print(f"\n[bold cyan]📊 Test Results:[/bold cyan]")
            self.console.print(
                f"  Total: {total} | [green]Passed: {passed}[/green] | [red]Failed: {failed}[/red]"
            )

    def _handle_slash_command(self, command: str) -> bool:
        """
        Handle slash commands.

        Returns:
            True if command was handled, False otherwise
        """
        cmd = command.lower().strip()
        parts = cmd.split()
        primary = parts[0]

        if primary == "/help":
            self._print_help()
            return True

        elif primary == "/agents":
            self._show_agents()
            return True

        elif primary == "/agent":
            agent = parts[1] if len(parts) > 1 else ""
            self._switch_agent(agent)
            return True

        elif primary == "/clear":
            if self.use_rich:
                self.console.clear()
            else:
                os.system("cls" if os.name == "nt" else "clear")
            self.print_banner()
            return True

        elif primary == "/history":
            self._show_history()
            return True

        elif primary == "/sessions":
            self._show_sessions()
            return True

        elif primary == "/session":
            action = parts[1] if len(parts) > 1 else "show"
            name = parts[2] if len(parts) > 2 else None
            self._handle_session_action(action, name)
            return True

        elif primary == "/config":
            self._show_config()
            return True

        elif primary == "/status":
            self._show_status()
            return True

        elif primary == "/workspace":
            self._show_workspace()
            return True

        elif primary == "/gateway":
            self._show_gateway()
            return True

        elif primary == "/models":
            self._show_models()
            return True

        elif primary == "/files":
            self._show_recent_files()
            return True

        elif primary == "/undo":
            self._undo_last()
            return True

        elif primary == "/settings":
            self._show_settings()
            return True

        elif primary in ["/exit", "/quit"]:
            return False

        return False

    def _show_agents(self):
        if not self.use_rich:
            print("Agents:")
            for name, meta in self.AGENT_ROLES.items():
                marker = "*" if name == self.active_agent else "-"
                print(f"  {marker} {name}: {meta['description']}")
            return

        self.console.print("\n[bold cyan]🧭 Control Agents:[/bold cyan]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan")
        table.add_column("Role", style="yellow")
        table.add_column("Default", style="green")
        table.add_column("State", style="white")
        for name, meta in self.AGENT_ROLES.items():
            state = "[green]Active[/green]" if name == self.active_agent else "Idle"
            table.add_row(name, meta["description"], meta["default_task"], state)
        self.console.print(table)

    def _switch_agent(self, agent: str):
        if agent not in self.AGENT_ROLES:
            message = f"Unknown agent: {agent}. Use /agents."
            if self.use_rich:
                self.console.print(f"\n[red]✗[/red] {message}\n")
            else:
                print(message)
            return
        self.active_agent = agent
        if self.use_rich:
            self.console.print(
                f"\n[green]✓[/green] Active agent set to [cyan]{agent}[/cyan]\n"
            )
        else:
            print(f"Active agent: {agent}")

    def _show_sessions(self):
        sessions = self._list_sessions()
        if not self.use_rich:
            print("Sessions:")
            for item in sessions[:20]:
                print(f"  - {item.stem}")
            return

        self.console.print("\n[bold cyan]💾 Sessions:[/bold cyan]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Updated", style="yellow")
        table.add_column("Current", style="green")
        for item in sessions[:20]:
            updated = datetime.fromtimestamp(item.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )
            current = "[green]●[/green]" if item.stem == self.session_name else ""
            table.add_row(item.stem, updated, current)
        if sessions:
            self.console.print(table)
        else:
            self.console.print("  No saved sessions yet.")

    def _handle_session_action(self, action: str, name: Optional[str]):
        if action == "show":
            self._show_sessions()
            return
        if action == "save":
            target = self._save_session(name)
            if self.use_rich:
                self.console.print(
                    f"\n[green]✓[/green] Session saved: [cyan]{target.stem}[/cyan]\n"
                )
            else:
                print(f"Session saved: {target.stem}")
            return
        if action == "new":
            self.session_name = name or self._default_session_name()
            self.history = []
            self.context = {
                "current_project": None,
                "last_command": None,
                "last_result": None,
            }
            self.stats = {
                "commands_executed": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "start_time": datetime.now(),
            }
            self._save_session(self.session_name)
            if self.use_rich:
                self.console.print(
                    f"\n[green]✓[/green] New session: [cyan]{self.session_name}[/cyan]\n"
                )
            else:
                print(f"New session: {self.session_name}")
            return
        if action == "load" and name:
            if self._load_session(name):
                return
        message = "Usage: /session save [name] | /session load <name> | /session new [name]"
        if self.use_rich:
            self.console.print(f"\n[yellow]{message}[/yellow]\n")
        else:
            print(message)

    def _show_history(self):
        """Show command history."""
        if not self.use_rich:
            print("Command History:")
            for i, item in enumerate(self.history[-20:], 1):
                print(f"  {i}. {item.get('command', 'N/A')}")
            return

        self.console.print("\n[bold cyan]📜 Command History (last 20):[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Command", style="white")
        table.add_column("Result", style="green", width=10)
        table.add_column("Time", style="yellow", width=8)

        for i, item in enumerate(self.history[-20:], 1):
            result_style = "[green]✓[/green]" if item.get("success") else "[red]✗[/red]"
            time_str = item.get("timestamp", "")[:16] if item.get("timestamp") else ""
            table.add_row(
                str(i),
                item.get("command", "N/A"),
                result_style,
                time_str,
            )

        self.console.print(table)

    def _show_config(self):
        """Show current configuration."""
        if not self.use_rich:
            print("Configuration:")
            print(f"  Sandbox strict mode: {self.sandbox.strict_mode}")
            print(f"  Allowed paths: {len(self.sandbox.ALLOWED_PATHS)}")
            return

        self.console.print("\n[bold cyan]⚙️  Configuration:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Sandbox Strict Mode", str(self.sandbox.strict_mode))
        table.add_row("Allowed Paths", str(len(self.sandbox.ALLOWED_PATHS)))
        table.add_row("Allowed Commands", str(len(self.sandbox.ALLOWED_COMMANDS)))
        table.add_row("Current Project", self.context.get("current_project", "None"))
        table.add_row("Active Agent", self.active_agent)
        table.add_row("Session", self.session_name)

        self.console.print(table)

    def _show_status(self):
        """Show system status."""
        if not self.use_rich:
            print("System Status:")
            print(f"  Commands executed: {self.stats['commands_executed']}")
            print(f"  Successful: {self.stats['successful_commands']}")
            print(f"  Failed: {self.stats['failed_commands']}")
            return

        uptime = datetime.now() - self.stats["start_time"]

        self.console.print("\n[bold cyan]📊 System Status:[/bold cyan]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Commands Executed", str(self.stats["commands_executed"]))
        table.add_row(
            "Successful", f"[green]{self.stats['successful_commands']}[/green]"
        )
        table.add_row("Failed", f"[red]{self.stats['failed_commands']}[/red]")
        table.add_row("Uptime", str(uptime).split(".")[0])
        table.add_row("Active Agent", self.active_agent)
        table.add_row("Session", self.session_name)
        table.add_row(
            "Rich UI", "[green]Enabled[/green]" if self.use_rich else "Disabled"
        )
        table.add_row(
            "Prompt Toolkit",
            "[green]Enabled[/green]" if self.use_prompt_toolkit else "Disabled",
        )

        self.console.print(table)

    def _show_workspace(self):
        current_dir = str(Path.cwd())
        allowed = any(Path(current_dir).resolve() == path for path in self.sandbox.ALLOWED_PATHS)
        current_project = self.context.get("current_project") or current_dir

        if not self.use_rich:
            print("Workspace:")
            print(f"  cwd: {current_dir}")
            print(f"  project: {current_project}")
            print(f"  sandbox allowed: {allowed}")
            return

        self.console.print("\n[bold cyan]🗂️ Workspace:[/bold cyan]\n")
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Current Dir", current_dir)
        table.add_row("Project", str(current_project))
        table.add_row("Sandbox Allowed", "[green]Yes[/green]" if allowed else "[red]No[/red]")
        table.add_row("Allowed Roots", str(len(self.sandbox.ALLOWED_PATHS)))
        self.console.print(table)

    def _show_gateway(self):
        state = {}
        config = {}
        if self.gateway_state_path.exists():
            try:
                state = json.loads(self.gateway_state_path.read_text(encoding="utf-8"))
            except Exception:
                state = {}
        if self.gateway_config_path.exists():
            try:
                config = json.loads(self.gateway_config_path.read_text(encoding="utf-8"))
            except Exception:
                config = {}

        configured_port = config.get("gateway", {}).get("port", "unknown")
        actual_port = state.get("actualPort") or configured_port

        if not self.use_rich:
            print("Gateway:")
            print(f"  configured port: {configured_port}")
            print(f"  actual port: {actual_port}")
            print(f"  state: {state.get('status', 'unknown')}")
            print(f"  reason: {state.get('reason', 'n/a')}")
            return

        self.console.print("\n[bold cyan]🚪 Gateway:[/bold cyan]\n")
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Configured Port", str(configured_port))
        table.add_row("Actual Port", str(actual_port))
        table.add_row("State", state.get("status", "unknown"))
        table.add_row("Reason", state.get("reason", "n/a"))
        table.add_row("Runtime", state.get("runtimePath", "n/a"))
        table.add_row("Updated", state.get("updatedAt", "n/a"))
        self.console.print(table)

    def _show_models(self):
        """Show available AI models."""
        if not self.use_rich:
            print("Available Models:")
            print("  - Ultra-Think (JEBAT native)")
            print("  - Stitch MCP (UI generation)")
            return

        self.console.print("\n[bold cyan]🤖 Available AI Models:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Description", style="white")

        table.add_row(
            "Ultra-Think",
            "Reasoning",
            "[green]✓ Active[/green]",
            "Deep reasoning and analysis",
        )
        table.add_row(
            "Ultra-Loop",
            "Processing",
            "[green]✓ Active[/green]",
            "Continuous processing loop",
        )
        table.add_row(
            "Stitch MCP",
            "UI Generation",
            "[yellow]⏳ Simulated[/yellow]",
            "Text-to-UI generation (server not running)",
        )

        self.console.print(table)

    def _show_recent_files(self):
        """Show recently modified files."""
        if not self.use_rich:
            print("Recent files not implemented yet")
            return

        self.console.print("\n[bold cyan]📁 Recent Files:[/bold cyan]\n")
        self.console.print(
            "  (Feature coming soon - will show recently modified files)\n"
        )

    def _undo_last(self):
        """Undo last action."""
        if not self.use_rich:
            print("Undo not implemented yet")
            return

        self.console.print("\n[yellow]⚠️  Undo feature coming soon[/yellow]\n")

    def _show_settings(self):
        """Show settings panel."""
        if not self.use_rich:
            print("Settings not implemented yet")
            return

        self.console.print("\n[bold cyan]🔧 Settings:[/bold cyan]\n")
        self.console.print("  (Interactive settings editor coming soon)\n")

    async def _execute_command(self, command: str) -> TaskResult:
        """
        Execute a command and return result.

        Args:
            command: User command string

        Returns:
            TaskResult
        """
        routed_agent = None
        command = command.strip()
        if command.startswith("@"):
            agent_token, _, remainder = command.partition(" ")
            routed_agent = agent_token[1:].strip().lower()
            if routed_agent and routed_agent in self.AGENT_ROLES:
                self.active_agent = routed_agent
                command = remainder.strip()
                if not command:
                    return TaskResult(
                        success=True,
                        message=f"Active agent switched to {routed_agent}",
                        metadata={"active_agent": routed_agent},
                    )
            else:
                return TaskResult(
                    success=False,
                    message=f"Unknown agent route: {agent_token}",
                )

        # Parse command
        parts = shlex.split(command)
        if not parts:
            return TaskResult(success=False, message="Empty command")

        cmd_type = parts[0]
        args = parts[1:]

        explicit_commands = {
            "create",
            "modify",
            "review",
            "generate",
            "ui",
            "debug",
            "scaffold",
            "git",
            "test",
            "help",
        }

        if cmd_type not in explicit_commands:
            default_task = self.AGENT_ROLES[self.active_agent]["default_task"]
            if self.active_agent == "reviewer":
                cmd_type = "review"
                args = [command]
            elif self.active_agent == "debugger":
                cmd_type = "debug"
                args = [command]
            elif self.active_agent == "designer":
                cmd_type = "ui"
                args = [command]
            elif self.active_agent == "operator":
                if command.startswith("git "):
                    cmd_type = "git"
                    args = shlex.split(command)[1:]
                elif command.startswith("test "):
                    cmd_type = "test"
                    args = shlex.split(command)[1:]
                else:
                    return TaskResult(
                        success=False,
                        message="Operator agent expects git/test commands or explicit subcommands.",
                    )
            else:
                cmd_type = default_task
                args = [command]

        # Route to appropriate handler
        if cmd_type == "create":
            result = await self.brain.execute_task(
                task_type="create",
                description=" ".join(args),
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "scaffold":
            project_name = args[0] if args else "my_project"
            project_type = "python_package"

            # Parse --type argument
            for i, arg in enumerate(args):
                if arg == "--type" and i + 1 < len(args):
                    project_type = args[i + 1]

            result = await self.brain.execute_task(
                task_type="scaffold",
                project_name=project_name,
                project_type=project_type,
                sandbox=self.sandbox,
            )
            self.context["current_project"] = str(Path.cwd() / "projects" / project_name)
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "review":
            path = args[0] if args else "."
            result = await self.brain.execute_task(
                task_type="review",
                path=path,
                description=path,
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "generate":
            result = await self.brain.execute_task(
                task_type="generate",
                description=" ".join(args),
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "ui":
            description = " ".join(args)
            framework = "react"

            # Parse --framework argument
            for i, arg in enumerate(args):
                if arg == "--framework" and i + 1 < len(args):
                    framework = args[i + 1]

            result = await self.brain.execute_task(
                task_type="ui_generate",
                description=description,
                framework=framework,
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "debug":
            error = " ".join(args)
            file_path = None

            # Parse --file argument
            for i, arg in enumerate(args):
                if arg == "--file" and i + 1 < len(args):
                    file_path = args[i + 1]

            result = await self.brain.execute_task(
                task_type="debug",
                error=error,
                description=error,
                file_path=file_path,
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "git":
            operation = args[0] if args else "status"
            path = "."
            message = ""
            files = "."

            # Parse arguments
            for i, arg in enumerate(args[1:], 1):
                if arg == "--path" and i + 1 < len(args):
                    path = args[i + 1]
                elif arg == "-m" and i + 1 < len(args):
                    message = args[i + 1]
                elif arg == "--files" and i + 1 < len(args):
                    files = args[i + 1]

            result = await self.brain.execute_task(
                task_type="git",
                description=f"{operation} {path}".strip(),
                operation=operation,
                path=path,
                message=message,
                files=files,
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "test":
            path = "."
            framework = "auto"

            # Parse arguments
            for i, arg in enumerate(args):
                if arg == "--path" and i + 1 < len(args):
                    path = args[i + 1]
                elif arg == "--framework" and i + 1 < len(args):
                    framework = args[i + 1]

            result = await self.brain.execute_task(
                task_type="test",
                description=f"{framework} {path}".strip(),
                path=path,
                framework=framework,
                sandbox=self.sandbox,
            )
            result.metadata.setdefault("active_agent", self.active_agent)
            return result

        elif cmd_type == "help":
            self._print_help()
            return TaskResult(success=True, message="Help displayed")

        else:
            return TaskResult(
                success=False,
                message=f"Unknown command: {cmd_type}. Type 'help' for available commands.",
            )

    async def run(self):
        """Run the interactive CLI."""
        self.print_banner()

        while True:
            # Get input
            user_input = self._get_input()

            if not user_input:
                continue

            # Check for exit
            if user_input.lower() in ["exit", "quit"]:
                if self.use_rich:
                    self.console.print(
                        "\n[bold cyan]👋 Goodbye! Come back soon![/bold cyan]\n"
                    )
                else:
                    print("\n👋 Goodbye!")
                break

            # Handle slash commands
            if user_input.startswith("/"):
                if not self._handle_slash_command(user_input):
                    break
                continue

            # Add to history
            self.history.append(
                {
                    "command": user_input,
                    "timestamp": datetime.now().isoformat(),
                    "success": None,
                }
            )

            # Add words to completer
            if self.completer:
                for word in user_input.split():
                    self.completer.add_word(word)

            # Show spinner and execute
            with (
                Live(
                    self._show_spinner("Thinking"),
                    console=self.console if self.use_rich else None,
                    refresh_per_second=10,
                    transient=True,
                )
                if self.use_rich
                else type(
                    "obj",
                    (object,),
                    {"__enter__": lambda s: s, "__exit__": lambda s, *a: None},
                )()
            ):
                result = await self._execute_command(user_input)

            # Update history
            if self.history:
                self.history[-1]["success"] = result.success
                self.history[-1]["result"] = result

            # Update stats
            self.stats["commands_executed"] += 1
            if result.success:
                self.stats["successful_commands"] += 1
            else:
                self.stats["failed_commands"] += 1

            # Update context
            self.context["last_command"] = user_input
            self.context["last_result"] = result

            # Print result
            self._print_result(result, user_input)
            self._save_session()


# ==================== Main Entry Point ====================


def main():
    """Main entry point for interactive CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🗡️ JEBAT DevAssistant - Interactive CLI"
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Single command to execute (non-interactive mode)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Force interactive mode",
    )
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable Rich UI formatting",
    )
    parser.add_argument(
        "--no-prompt-toolkit",
        action="store_true",
        help="Disable prompt toolkit features",
    )

    args = parser.parse_args()

    # Create CLI
    cli = InteractiveCLI(
        use_rich=not args.no_rich,
        use_prompt_toolkit=not args.no_prompt_toolkit,
    )

    # Run
    if args.command and not args.interactive:
        # Single command mode
        async def run_single():
            if args.command.startswith("/"):
                handled = cli._handle_slash_command(args.command)
                return 0 if handled else 1
            result = await cli._execute_command(args.command)
            cli._print_result(result, args.command)
            cli._save_session()
            return 0 if result.success else 1

        exit_code = asyncio.run(run_single())
        sys.exit(exit_code)
    else:
        # Interactive mode
        try:
            asyncio.run(cli.run())
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
