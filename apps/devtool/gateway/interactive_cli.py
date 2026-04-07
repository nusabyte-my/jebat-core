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
import os
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
        "/clear",
        "/history",
        "/config",
        "/status",
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
            self._print_help()
        else:
            print(self.BANNER)
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
  /clear     Clear screen
  /history   Show command history
  /config    Show configuration
  /status    Show system status
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
            "/clear",
            "/history",
            "/config",
            "/status",
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

        if cmd == "/help":
            self._print_help()
            return True

        elif cmd == "/clear":
            if self.use_rich:
                self.console.clear()
            else:
                subprocess.run("cls" if os.name == "nt" else "clear")
            self.print_banner()
            return True

        elif cmd == "/history":
            self._show_history()
            return True

        elif cmd == "/config":
            self._show_config()
            return True

        elif cmd == "/status":
            self._show_status()
            return True

        elif cmd == "/models":
            self._show_models()
            return True

        elif cmd == "/files":
            self._show_recent_files()
            return True

        elif cmd == "/undo":
            self._undo_last()
            return True

        elif cmd == "/settings":
            self._show_settings()
            return True

        elif cmd in ["/exit", "/quit"]:
            return False

        return False

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
        table.add_row(
            "Rich UI", "[green]Enabled[/green]" if self.use_rich else "Disabled"
        )
        table.add_row(
            "Prompt Toolkit",
            "[green]Enabled[/green]" if self.use_prompt_toolkit else "Disabled",
        )

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
        # Parse command
        parts = command.split()
        if not parts:
            return TaskResult(success=False, message="Empty command")

        cmd_type = parts[0]
        args = parts[1:]

        # Route to appropriate handler
        if cmd_type == "create":
            return await self.brain.execute_task(
                task_type="create",
                description=" ".join(args),
                sandbox=self.sandbox,
            )

        elif cmd_type == "scaffold":
            project_name = args[0] if args else "my_project"
            project_type = "python_package"

            # Parse --type argument
            for i, arg in enumerate(args):
                if arg == "--type" and i + 1 < len(args):
                    project_type = args[i + 1]

            return await self.brain.execute_task(
                task_type="scaffold",
                project_name=project_name,
                project_type=project_type,
                sandbox=self.sandbox,
            )

        elif cmd_type == "review":
            path = args[0] if args else "."
            return await self.brain.execute_task(
                task_type="review",
                path=path,
                sandbox=self.sandbox,
            )

        elif cmd_type == "generate":
            return await self.brain.execute_task(
                task_type="generate",
                description=" ".join(args),
                sandbox=self.sandbox,
            )

        elif cmd_type == "ui":
            description = " ".join(args)
            framework = "react"

            # Parse --framework argument
            for i, arg in enumerate(args):
                if arg == "--framework" and i + 1 < len(args):
                    framework = args[i + 1]

            return await self.brain.execute_task(
                task_type="ui_generate",
                description=description,
                framework=framework,
                sandbox=self.sandbox,
            )

        elif cmd_type == "debug":
            error = " ".join(args)
            file_path = None

            # Parse --file argument
            for i, arg in enumerate(args):
                if arg == "--file" and i + 1 < len(args):
                    file_path = args[i + 1]

            return await self.brain.execute_task(
                task_type="debug",
                error=error,
                file_path=file_path,
                sandbox=self.sandbox,
            )

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

            return await self.brain.execute_task(
                task_type="git",
                operation=operation,
                path=path,
                message=message,
                files=files,
                sandbox=self.sandbox,
            )

        elif cmd_type == "test":
            path = "."
            framework = "auto"

            # Parse arguments
            for i, arg in enumerate(args):
                if arg == "--path" and i + 1 < len(args):
                    path = args[i + 1]
                elif arg == "--framework" and i + 1 < len(args):
                    framework = args[i + 1]

            return await self.brain.execute_task(
                task_type="test",
                path=path,
                framework=framework,
                sandbox=self.sandbox,
            )

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
            result = await cli._execute_command(args.command)
            cli._print_result(result, args.command)
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
