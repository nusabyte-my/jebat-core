"""
JEBAT Coding Agent — Hermes-style autonomous coding assistant.

Combines project-aware chat, multi-agent orchestration, and rich terminal UI
into a single "jebat code" experience.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent_prompt import get_agent_prompt

# Rich formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.table import Table
    from rich.rule import Rule
    from rich.text import Text
    from rich.syntax import Syntax
    from rich.layout import Layout
    from rich import box
    from rich.style import Style

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None  # type: ignore


# ── Shimmering Thinking Animation ──────────────────────────────────

import random

_SHIMMER_QUOTES = [
    # DevOps
    "It works on my machine",
    "sudo rm -rf / — just kidding",
    "Have you tried turning it off and on again",
    "CI/CD go brrr",
    "Docker inception",
    "It's not a bug, it's a feature flag",
    "Git commit -m 'fix everything'",
    "kubectl delete pod --all",
    "Works in staging, dies in prod",
    "The cloud is just someone else's computer",
    # Cybersecurity
    "Have you tried admin/admin",
    "It's not a vulnerability, it's an access feature",
    "Firewall? I hardly know her",
    "HTTPS doesn't mean it's safe",
    "The real treasure was the SQL injections we found along the way",
    "rm -rf / — penetration testing",
    "That's not a backdoor, that's a maintenance entrance",
    "Encryption: because Santa is watching",
    "127.0.0.1 is localhost, not a firewall rule",
    "Have you patched yet?",
    # Fullstack
    "It's a fullstack issue if you believe hard enough",
    "CSS is easy they said",
    "One more npm install and I'm done",
    "Backend works, frontend doesn't, must be the network",
    "Is it a frontend or backend problem? Yes",
    "The database is always the bottleneck",
    "async/await: because promises weren't confusing enough",
    "npm audit: 47,392 vulnerabilities found",
    "It's not a phase, it's a framework migration",
    "JSON.stringify the universe",
    # Funny
    "Have you tried asking ChatGPT",
    "The code is sending mixed signals",
    "It compiles on my machine",
    "99 little bugs in the code, 99 little bugs... fix one, 127 little bugs",
    "I don't always test, but when I do, I do it in production",
    "There are 10 types of people: those who understand binary and those who don't",
    "A SQL query walks into a bar, sees two tables and asks...",
    "To understand recursion, you must first understand recursion",
    "Debugging is like being the detective in a crime movie where you're also the murderer",
    "The best error message is the one that never shows up",
    # Random
    "Consulting the rubber duck",
    "Reading the bones of the stack trace",
    "Channeling inner developer zen",
    "Compiling wisdom from Stack Overflow",
    "Downloading more RAM",
    "Defragmenting the thought process",
    "Running diagnostics on the vibes",
    "Optimizing the chaos",
    "Rebooting the brain.exe",
    "Ctrl+Z the last 5 minutes",
]


class ShimmerThink:
    """Animated shimmering thinking indicator for Rich Live display.

    Cycles through spinner frames with a subtle monochrome pulse,
    matching Pi's minimal terminal aesthetic.
    """

    def __init__(self, text: str | None = None):
        self.text = text or random.choice(_SHIMMER_QUOTES)
        self._frame = 0
        self._frames = ["◐", "◓", "◑", "◒"]

    def __rich__(self) -> Text:
        self._frame += 1
        idx = self._frame % len(self._frames)

        # Monochrome pulse: oscillate brightness (white to dim gray)
        phase = (self._frame % 40) / 40
        intensity = 0.5 + 0.5 * (1 - abs(phase * 2 - 1))
        brightness = int(200 + 55 * intensity)

        return Text.assemble(
            (f" {self._frames[idx]} ", f"color({brightness},{brightness},{brightness})"),
            (self.text, "white" if intensity > 0.7 else "dim"),
            (" ◇", f"color({brightness},{brightness},{brightness})"),
        )

# Prompt toolkit for interactive input
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


# ── Project Context ──────────────────────────────────────────────────────

_PROJECT_CONTEXT_FILES = [
    "AGENTS.md",
    "MEMORY.md",
    "DESIGN.md",
    "CLAUDE.md",
    ".cursorrules",
    "CODEX_PROFILE.md",
    "JEBAT.md",
]

_PROJECT_MARKER_FILES = [
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "Makefile",
    "README.md",
    "Dockerfile",
    "docker-compose.yml",
    "Gemfile",
    "requirements.txt",
]


def _detect_project(path: Path | None = None) -> dict[str, Any]:
    """Scan the project directory and return context info (deep scan)."""
    root = (path or Path.cwd()).resolve()
    info: dict[str, Any] = {
        "root": str(root),
        "name": root.name,
        "context_files": {},
        "type": "generic",
        "stack": [],
        "has_git": (root / ".git").is_dir(),
    }

    # Read context files
    for fn in _PROJECT_CONTEXT_FILES:
        fp = root / fn
        if fp.exists():
            try:
                info["context_files"][fn] = fp.read_text(encoding="utf-8", errors="replace")[:2000]
            except Exception:
                pass

    # Deep scan: check root AND one level of subdirectories for marker files
    _MARKER_FILES = [
        ("pyproject.toml", "python"),
        ("requirements.txt", "python"),
        ("package.json", "node"),
        ("next.config.js", "nextjs"),
        ("next.config.mjs", "nextjs"),
        ("vite.config.ts", "vite"),
        ("vite.config.js", "vite"),
        ("angular.json", "angular"),
        ("go.mod", "go"),
        ("Cargo.toml", "rust"),
        ("Gemfile", "ruby"),
        ("composer.json", "php"),
        ("Dockerfile", "docker"),
        ("docker-compose.yml", "compose"),
        ("compose.yml", "compose"),
    ]

    # Scan root
    for fn, stack_name in _MARKER_FILES:
        if (root / fn).exists():
            info["stack"].append(stack_name)

    # Scan one level deep for monorepos / split frontend+backend
    try:
        for sub in root.iterdir():
            if sub.is_dir() and not sub.name.startswith("."):
                for fn, stack_name in _MARKER_FILES:
                    if (sub / fn).exists() and stack_name not in info["stack"]:
                        info["stack"].append(stack_name)
    except PermissionError:
        pass

    # Determine primary type from stack (prioritize explicit frameworks)
    type_priority = ["nextjs", "vite", "angular", "python", "node", "go", "rust", "ruby", "php", "generic"]
    for prio in type_priority:
        if prio in info["stack"]:
            info["type"] = prio
            break

    # Deduplicate stack while preserving order
    seen = set()
    deduped = []
    for s in info["stack"]:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    info["stack"] = deduped

    # Detect common directories
    dirs = []
    for d in ["src", "app", "lib", "server", "client", "frontend", "backend", "tests", "docs", "api"]:
        if (root / d).is_dir():
            dirs.append(d)
    info["directories"] = dirs

    # File tree: list files at root and key subdirectories (up to ~50 entries total)
    file_tree = []
    try:
        for entry in sorted(root.iterdir()):
            if entry.name.startswith(".") and entry.name not in (".env.example",):
                continue
            marker = "📁" if entry.is_dir() else "📄"
            file_tree.append(f"  {marker} {entry.name}")
        # Limit to first 40 entries
        info["file_tree"] = "\n".join(file_tree[:40])
        if len(file_tree) > 40:
            info["file_tree"] += f"\n  ... and {len(file_tree) - 40} more entries"
    except PermissionError:
        info["file_tree"] = ""

    return info


def _build_context_section(project_info: dict[str, Any]) -> str:
    """Build a project context string from detected info."""
    parts = [f"# Project: {project_info['name']}"]
    parts.append(f"Root: {project_info['root']}")
    parts.append(f"Type: {project_info['type']}")
    if project_info["stack"]:
        parts.append(f"Stack: {', '.join(project_info['stack'])}")
    if project_info["directories"]:
        parts.append(f"Directories: {', '.join(project_info['directories'])}")
    if project_info["has_git"]:
        parts.append("Git: initialized")
    parts.append("")

    # Include context file content
    for fn, content in project_info["context_files"].items():
        parts.append(f"--- {fn} ---")
        parts.append(content)
        parts.append("")

    # Include file tree
    if project_info.get("file_tree"):
        parts.append("--- File Tree (project root) ---")
        parts.append(project_info["file_tree"])
        parts.append("")

    # Include stack-specific conventions
    stack = project_info.get("stack", [])
    tips = []
    if "python" in stack:
        tips.append("- Python: use pytest for tests, pip/uv for deps, pyproject.toml for config")
    if "node" in stack or "nextjs" in stack or "vite" in stack:
        tips.append("- Node.js: package.json scripts for tasks, check if pnpm/yarn/npm is used")
    if "docker" in stack:
        tips.append("- Docker: Dockerfile at root, docker-compose.yml for multi-service")
    if "go" in stack:
        tips.append("- Go: go.mod for deps, go test for tests, standard project layout")
    if project_info.get("has_git"):
        tips.append("- Git: use conventional commits, keep commits focused")

    if tips:
        parts.append("--- Stack Conventions ---")
        parts.extend(tips)
        parts.append("")

    return "\n".join(parts)


# ── UI Helpers — Pi-style minimal ──────────────────────────────────


def _print(text: str, style: str = "") -> None:
    """Print with optional style. No frills."""
    if RICH_AVAILABLE and console:
        console.print(text, style=style)
    else:
        print(text)


def _panel(title: str, content: str, style: str = "dim") -> None:
    """Minimal section — no box, just a dim header line."""
    if RICH_AVAILABLE and console:
        console.print(f"  {title}", style=style)
        if content:
            console.print(f"  {content}", style=style)
    else:
        print(f"  {title}")
        if content:
            print(f"  {content}")


def _show_splash(project_info: dict[str, Any], capture_results: dict[str, list[str]] | None = None) -> None:
    """Display a minimal, Pi-style splash screen."""
    if RICH_AVAILABLE and console:
        # Minimal header — no box-drawing, just a clean one-liner
        header = Text()
        header.append("  ◈ JEBAT ", style="bold white")
        header.append("v6.1", style="dim")
        header.append("  —  coding agent", style="dim")
        console.print(header)

        # Project info — compact, inline-style
        parts = []
        parts.append(f"  {project_info['name']}")
        if project_info.get("stack"):
            parts.append(", ".join(project_info["stack"]))
        if project_info.get("directories"):
            parts.append(f"{len(project_info['directories'])} dirs")
        info_line = " · ".join(parts)
        console.print(f"  {info_line}", style="dim")

        # Context files hint
        if project_info.get("context_files"):
            console.print(f"  context: {', '.join(project_info['context_files'].keys())}", style="dim")

        # Workspace capture hint
        if capture_results:
            written = capture_results.get("written", [])
            skipped = capture_results.get("skipped", [])
            if written:
                console.print(f"  vs-code: {', '.join(written)}", style="dim")
            elif skipped and not written:
                console.print("  vs-code: files exist (use --overwrite)", style="dim")

        console.print()
    else:
        print(f"\n  ◈ JEBAT v6.1 — coding agent")
        print(f"  {project_info['name']} · {', '.join(project_info['stack']) if project_info['stack'] else 'generic'}")
        print()


def _show_tool_call(tool_name: str, status: str, duration: str, params: dict | None, error: str | None = None) -> None:
    """Display a single tool call with Pi-style compact formatting."""
    if RICH_AVAILABLE and console:
        status_styles = {"ok": "green", "err": "red", "skip": "yellow", "pending": "dim"}
        color = status_styles.get(status, "white")

        detail = ""
        if params:
            for k, v in list(params.items())[:2]:
                val_str = str(v)[:60]
                detail += f" {k}={val_str}"

        line = Text()
        line.append(f"  ▸ ", style=color)
        line.append(tool_name, style="bold white")
        if detail.strip():
            line.append(f" ({detail.strip()})", style="dim")
        line.append(f" — {duration}", style="dim")

        if error:
            line.append(f"  [{error[:60]}]", style="red")

        console.print(line)
    else:
        icon = {"ok": "OK", "err": "ERR", "skip": "SKIP", "pending": "..."}.get(status, "?")
        print(f"  ▸ {tool_name} -- {duration}")
        if error:
            print(f"    error: {error[:80]}")


def _show_stats(stats: dict[str, Any]) -> None:
    """Show compact session stats — Pi-style minimal footer."""
    parts = []
    if stats.get("provider"):
        parts.append(str(stats['provider']))
    if stats.get("iterations"):
        parts.append(f"{stats['iterations']} iters")
    if stats.get("tokens"):
        parts.append(f"{stats['tokens']:,} tokens")
    if stats.get("time"):
        parts.append(f"{stats['time']:.1f}s")
    if stats.get("tools"):
        parts.append(f"{stats['tools']} tools")

    if parts:
        line = "  " + " · ".join(parts)
        _print(line, "dim")


async def _input_line(prompt: str = "> ") -> str:
    """Get input with prompt_toolkit history, async-safe."""
    if PROMPT_TOOLKIT_AVAILABLE:
        history_path = Path.home() / ".jebat" / "code_history.txt"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        session = PromptSession(history=FileHistory(str(history_path)))
        try:
            return await session.prompt_async(prompt, multiline=False)
        except (EOFError, KeyboardInterrupt):
            return ""
    else:
        try:
            return await asyncio.to_thread(input, prompt)
        except (EOFError, KeyboardInterrupt):
            return ""


# ── Code Agent ───────────────────────────────────────────────────────────


class CodeAgent:
    """Hermes-style coding agent with multi-agent orchestration.

    The CodeAgent is JEBAT's flagship coding experience:
    - Hermes-style terminal UI with splash, tool visualization, and stats
    - Auto-loads project context (AGENTS.md, MEMORY.md, DESIGN.md)
    - Wires into the orchestrator for multi-agent task delegation
    - Supports both inline and interactive modes
    """

    def __init__(
        self,
        project_path: str | None = None,
        provider_override: str | None = None,
        model_override: str | None = None,
        preset: str | None = None,
        safety_mode: str = "auto",
        yolo: bool = False,
        stream: bool = True,
        auto_commit: bool = False,
    ):
        self.project_path = project_path or os.getcwd()
        self.provider_override = provider_override
        self.model_override = model_override
        self.preset = preset
        self.safety_mode = "confirm" if yolo else safety_mode
        self.yolo = yolo
        self.stream = stream
        self.auto_commit = auto_commit
        self.running = True

        # Detect project
        self.project_info = _detect_project(Path(self.project_path))
        self.project_context = _build_context_section(self.project_info)

        # Auto-generate workspace capture files (VS Code integration)
        self._capture_results = self._run_workspace_capture()

        # Orchestrator reference (lazy init)
        self._orchestrator = None

    def _run_workspace_capture(self) -> dict[str, list[str]]:
        """Generate VS Code workspace capture files (.vscode/jebat-workspace.json + PROJECT_START.md).

        Returns dict with 'written' and 'skipped' file paths.
        """
        try:
            from jebat_project.workspace_capture import WorkspaceCapture

            cap = WorkspaceCapture(Path(self.project_path))
            result = cap.write_vscode_capture(overwrite=False, include_copilot=True)
            return {
                "written": [str(p) for p in result.written],
                "skipped": [str(p) for p in result.skipped],
            }
        except Exception as e:
            return {"written": [], "skipped": [], "error": str(e)}

    def _load_pi_context(self) -> str:
        """Load Pi Coding Agent ecosystem context from bundled resources.

        Returns the PI_ECOSYSTEM.md content, or empty string if not found.
        """
        pi_resources_dir = Path(__file__).parent / "pi-resources"
        pi_ctx_file = pi_resources_dir / "PI_ECOSYSTEM.md"
        try:
            if pi_ctx_file.exists():
                return pi_ctx_file.read_text(encoding="utf-8")
        except Exception:
            pass
        return ""

    async def _init_orchestrator(self) -> Any:
        """Lazy-init the multi-agent orchestrator."""
        if self._orchestrator is None:
            from jebat.core.agents.orchestrator import AgentOrchestrator

            self._orchestrator = AgentOrchestrator(config={
                "auto_swarm": True,
                "full_orchestration": True,
                "force_swarm_for_all_tasks": True,
                "full_orchestration_execution_mode": "consensus",
                "full_orchestration_max_agents": 5,
                "default_swarm_size": 3,
            })
            self._orchestrator.register_builtin_agents()
            await self._orchestrator.start()

            _print("  agents ready", "dim")
            for agent in self._orchestrator.list_agents()[:5]:
                _print(f"    {agent['name']} ({agent['role']})", "dim")
            _print("")

        return self._orchestrator

    async def _run_external_agent(self, prompt: str, agent_name: str) -> None:
        """Delegate to an external coding agent (kilo, opencode, claude, pi, codex, gemini, qwen) via CLI."""
        import subprocess

        # Map agent name to CLI command
        cmd_map = {
            "kilo": ["kilo", "run", prompt],
            "opencode": ["opencode", "run", prompt],
            "claude": ["claude", "-p", prompt],
            "pi": ["pi", "-p", prompt],
            "codex": ["codex", "exec", "--skip-git-repo-check", prompt],
            "gemini": ["gemini", "-p", prompt],
            "qwen": ["qwen", "-p", prompt],
        }

        cmd = cmd_map.get(agent_name)
        if not cmd:
            _print(f"  Unknown agent: {agent_name}", "red")
            return

        # Verify the tool exists and resolve full path
        import shutil
        agent_path = shutil.which(agent_name)
        if not agent_path:
            _print(f"  {agent_name} not found", "bold red")
            return
        # Use the resolved command (handles .CMD/.EXE wrappers on Windows)
        cmd[0] = agent_path

        start_time = time.time()

        # Show shimmer animation while external agent runs
        if RICH_AVAILABLE and console:
            with Live(ShimmerThink(f"Delegating to {agent_name}"), console=console, refresh_per_second=12):
                try:
                    proc = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=600, cwd=self.project_path
                    )
                except subprocess.TimeoutExpired:
                    _print(f"  timed out (600s)", "red")
                    return
                except FileNotFoundError:
                    _print(f"  {agent_name} not found", "bold red")
                    return
                except Exception as e:
                    _print(f"  error: {e}", "red")
                    return
        else:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=600, cwd=self.project_path
                )
            except subprocess.TimeoutExpired:
                _print(f"  timed out (600s)", "red")
                return
            except FileNotFoundError:
                _print(f"  {agent_name} not found", "bold red")
                return
            except Exception as e:
                _print(f"  error: {e}", "red")
                return

        elapsed = time.time() - start_time

        # Render response as Markdown
        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        if RICH_AVAILABLE and console and output.strip():
            try:
                md = Markdown(output.strip(), code_theme="monokai")
                console.print(md)
            except Exception:
                console.print(output.strip())
        elif output.strip():
            print(f"\n{output.strip()}")

        if proc.returncode != 0:
            _print(f"  exit {proc.returncode}", "yellow")

        _print(f"  {agent_name} · {elapsed:.1f}s", "dim")

    async def run_prompt(self, prompt: str) -> None:
        """Run a single coding prompt through the AgentLoop or an external coding agent."""
        # Check for external coding agent providers
        provider = (self.provider_override or "").lower()
        external_agents = {"kilo", "opencode", "claude", "pi", "codex", "gemini", "qwen"}

        if provider in external_agents:
            # User explicitly requested this agent
            await self._run_external_agent(prompt, provider)
            return
        elif not provider:
            # Check if local provider is configured — skip external agents
            from jebat.llm.config import load_llm_config
            llm_cfg = load_llm_config()
            local_providers = {"ollama", "llamacpp", "local"}
            if llm_cfg.provider in local_providers:
                pass  # Fall through to internal agent loop
            else:
                # No provider specified — auto-detect best available external agent
                import shutil
                for name in ["pi", "kilo", "codex", "opencode", "claude", "gemini", "qwen"]:
                    if shutil.which(name):
                        note = " (15+ providers, exts, skills)" if name == "pi" else ""
                        _print(f"  → {name}{note}", "dim")
                        await self._run_external_agent(prompt, name)
                        return

        from jebat.core.agent_loop import AgentLoop, SafetyMode

        safety_map = {
            "auto": SafetyMode.AUTO,
            "confirm": SafetyMode.CONFIRM,
            "dangerous": SafetyMode.DANGEROUS,
        }
        safety = safety_map.get(self.safety_mode, SafetyMode.AUTO)

        # Build the system prompt with project context
        system_prompt = get_agent_prompt(self.project_context, auto_commit=self.auto_commit)

        # Inject Pi Coding Agent ecosystem context when relevant
        pi_keywords = ["pi ", " pi", "pi agent", "pi coding", "pi.dev", "pi-mono", "pi-extensions"]
        pi_context = ""
        if (self.provider_override and "pi" in self.provider_override.lower()) or \
           any(kw in prompt.lower() for kw in pi_keywords):
            _print("  pi ecosystem context loaded", "dim")
            pi_context = self._load_pi_context()
            if pi_context:
                system_prompt = f"{system_prompt}\n\n# Pi Coding Agent Ecosystem Reference\n\n{pi_context}"

        # Initialize orchestrator
        orchestrator = await self._init_orchestrator()

        # Run the agent loop with shimmering thinking animation
        loop = AgentLoop(
            provider_override=self.provider_override,
            model_override=self.model_override,
            preset=self.preset,
            safety_mode=safety,
            max_iterations=25,
            system_prompt=system_prompt,
        )

        start_time = time.time()

        # Stream final response tokens into a buffer, then render as Markdown
        response_chunks: list[str] = []

        async def _on_token(chunk: str) -> None:
            response_chunks.append(chunk)

        if RICH_AVAILABLE and console:
            with Live(ShimmerThink(), console=console, refresh_per_second=12):
                result = await loop.run(
                    user_message=prompt,
                    conversation_history=[],
                    mode=None,
                    stream_callback=_on_token if self.stream else None,
                )
        else:
            result = await loop.run(
                user_message=prompt,
                conversation_history=[],
                mode=None,
            )

        elapsed = time.time() - start_time

        # Show tool calls made (like Claude Code's live tool call display)
        if result.tool_calls_made:
            _print("", "")
            for step in result.tool_calls_made:
                status = "ok" if step.error is None else "err"
                if not step.approved:
                    status = "skip"
                duration = f"{step.duration_ms}ms" if step.duration_ms else "?"
                _show_tool_call(step.tool_name, status, duration, step.params, step.error)
            _print("", "")

        # Show the response — render as Markdown for code blocks, lists, headings
        final_text = "".join(response_chunks) if response_chunks else result.final_response
        if RICH_AVAILABLE and console and final_text.strip():
            try:
                md = Markdown(final_text, code_theme="monokai")
                console.print(md)
            except Exception:
                console.print(final_text)
        elif final_text.strip():
            print(f"\n{final_text}")

        _print("", "")

        # Stats footer — compact like Claude Code's footer
        stats = {
            "provider": result.provider_used,
            "iterations": result.iterations_used if result.iterations_used > 1 else None,
            "tokens": result.tokens_used.get("total_tokens") if result.tokens_used else None,
            "time": elapsed,
            "tools": len(result.tool_calls_made) if result.tool_calls_made else None,
        }
        _show_stats(stats)

    async def run_interactive(self) -> None:
        """Run the coding agent in interactive mode with history."""
        # Splash screen
        _show_splash(self.project_info, self._capture_results)

        # Show orchestrator init
        await self._init_orchestrator()

        _print("  type a prompt, /help for commands, Ctrl+C or /quit to exit", "dim")
        _print("")

        while self.running:
            try:
                user_input = await _input_line("\n> ")
                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                # Run the prompt
                await self.run_prompt(user_input)

            except (EOFError, KeyboardInterrupt):
                self.running = False
                print()

        _print("  session saved · bye", "dim")

    async def _handle_command(self, cmd_raw: str) -> None:
        """Handle slash commands."""
        parts = cmd_raw.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ("/quit", "/exit", "/q"):
            self.running = False

        elif cmd == "/help":
            _print("""
  Commands:
    /quit, /exit, /q    Exit
    /help               Show this help
    /clear              Clear screen
    /status             Show session status
    /model <m>          Switch model (e.g. /model anthropic/claude-sonnet-4)
    /provider <p>       Switch provider (kilo, pi, codex, opencode, claude, gemini, qwen, ollama)
    /providers          List all available providers and their status
    /preset <name>      Switch preset (fast, deliberate, deep, strategic, creative, critical)
    /agents             List available specialist agents
    /orchestrate <on|off>  Toggle multi-agent orchestration

  External Agents:
    kilo       Kilo Code (13 configured providers)
    pi         PI Coding Agent (15+ providers, extensions, skills)
    codex      OpenAI Codex CLI
    opencode   OpenCode CLI (20 configured providers)
    claude     Anthropic Claude Code (needs API key)
    gemini     Google Gemini CLI
    qwen       Qwen Code CLI
    ollama     Local Ollama (default, offline-capable)
            """.strip())

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            _show_splash(self.project_info, self._capture_results)

        elif cmd == "/status":
            _print(f"  Project: {self.project_info['name']}", "bold")
            _print(f"  Type:    {self.project_info['type']}")
            _print(f"  Stack:   {', '.join(self.project_info['stack']) or 'generic'}")
            _print(f"  Safety:  {self.safety_mode}")
            if self.provider_override:
                _print(f"  Provider: {self.provider_override}")
            if self.model_override:
                _print(f"  Model:   {self.model_override}")
            if self._orchestrator:
                agents = self._orchestrator.list_agents()
                _print(f"  Agents:  {len(agents)} registered")
                for a in agents[:8]:
                    _print(f"    - {a['name']} ({a['role']})", "dim")

        elif cmd == "/model" and args:
            if "/" in args:
                prov, mod = args.split("/", 1)
                self.provider_override = prov.strip()
                self.model_override = mod.strip()
            else:
                self.model_override = args.strip()
            _print(f"  Model: {self.provider_override or 'default'}/{self.model_override}", "green")

        elif cmd == "/provider" and args:
            self.provider_override = args.strip()
            _print(f"  Provider: {self.provider_override}", "green")

        elif cmd == "/preset" and args:
            self.preset = args.strip()
            _print(f"  Preset: {self.preset}", "green")

        elif cmd == "/agents":
            if self._orchestrator:
                _print("  Specialist Agents:", "bold cyan")
                for agent in self._orchestrator.list_agents():
                    caps = ", ".join(agent["capabilities"][:3])
                    _print(f"    {agent['name']:25s} ({agent['role']:15s}) [{caps}]", "white")
            else:
                _print("  Orchestrator not initialized.", "yellow")

        elif cmd == "/providers":
            import shutil
            _print("  Available Coding Agents:", "bold cyan")
            providers = [
                ("kilo", "kilo", "Kilo Code (13 providers)"),
                ("pi", "pi", "PI Coding Agent (15+ providers, exts, skills)"),
                ("codex", "codex", "OpenAI Codex CLI"),
                ("opencode", "opencode", "OpenCode CLI (20 providers)"),
                ("claude", "claude", "Anthropic Claude Code"),
                ("gemini", "gemini", "Google Gemini CLI"),
                ("qwen", "qwen", "Qwen Code CLI"),
                ("ollama", None, "Local Ollama (qwen2.5-coder:3b)"),
            ]
            for name, cmd_name, desc in providers:
                if name == "ollama":
                    _print(f"    {name:12s} ✓ Always available", "green")
                elif cmd_name and shutil.which(cmd_name):
                    _print(f"    {name:12s} ✓ Installed ({desc})", "green")
                else:
                    _print(f"    {name:12s} ✗ Not installed", "dim")
            _print("")
            _print("  Use: /provider <name> to switch, or --provider flag", "dim")

        elif cmd == "/orchestrate":
            if self._orchestrator:
                if args == "off":
                    self._orchestrator.config["auto_swarm"] = False
                    _print("  Multi-agent orchestration: OFF", "yellow")
                else:
                    self._orchestrator.config["auto_swarm"] = True
                    _print("  Multi-agent orchestration: ON", "green")
            else:
                _print("  Orchestrator not initialized.", "yellow")

        else:
            _print(f"  Unknown: {cmd_raw}. Try /help", "yellow")
