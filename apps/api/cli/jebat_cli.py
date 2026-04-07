#!/usr/bin/env python3
"""
JEBAT CLI - Command Line Interface

Control JEBAT AI Assistant from the command line.

Usage:
    jebat status              - Show system status
    jebat loop start          - Start Ultra-Loop
    jebat loop stop           - Stop Ultra-Loop
    jebat loop status         - Show Ultra-Loop status
    jebat think <question>    - Run thinking session
    jebat memory store <text> - Store a memory
    jebat memory search <q>   - Search memories
    jebat config              - Show configuration
"""

import argparse
import asyncio
import json
import uuid
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

from jebat.llm import (
    build_skill_prompt,
    build_skill_registry,
    ChatHistoryStore,
    build_project_context,
    generate_with_failover,
    list_provider_auth_status,
    list_supported_providers,
    load_llm_config,
    select_best_provider,
)

# Rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better CLI output: pip install rich")


class JEBATCLI:
    """JEBAT Command Line Interface"""

    def __init__(self):
        """Initialize CLI"""
        self.console = Console() if RICH_AVAILABLE else None
        self.ultra_loop = None
        self.ultra_think = None
        self.memory_manager = None
        self.initialized = False

    def print(self, message: str, style: str = ""):
        """Print message with optional style"""
        if self.console:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)

    async def initialize(self):
        """Initialize JEBAT systems"""
        if self.initialized:
            return

        self.print("\nJEBAT  JEBAT - Initializing systems...", "bold blue")

        try:
            # Import JEBAT components
            from jebat import MemoryManager
            from jebat.features.ultra_loop import create_ultra_loop
            from jebat.features.ultra_think import create_ultra_think

            # Initialize Memory Manager
            self.memory_manager = MemoryManager()
            self.print("  [OK] Memory Manager", "green")

            # Initialize Ultra-Loop
            self.ultra_loop = await create_ultra_loop(
                config={"cycle_interval": 1.0, "max_cycles": 0},
                enable_db_persistence=False,
            )
            self.print("  [OK] Ultra-Loop", "green")

            # Initialize Ultra-Think
            self.ultra_think = await create_ultra_think(
                config={"max_thoughts": 20, "default_mode": "deliberate"},
                memory_manager=self.memory_manager,
                enable_db_persistence=False,
                enable_memory_integration=True,
            )
            self.print("  [OK] Ultra-Think", "green")

            self.initialized = True
            self.print("[OK] All systems initialized\n", "bold green")

        except Exception as e:
            self.print(f"[ERR] Initialization failed: {e}\n", "bold red")
            raise

    async def cmd_status(self):
        """Show system status"""
        await self.initialize()

        self.print("\n" + "=" * 60, "bold blue")
        self.print("JEBAT  JEBAT System Status", "bold blue")
        self.print("=" * 60 + "\n", "bold blue")

        # System components status
        status_table = self._create_table("Component", "Status")
        status_table.add_row(
            "Memory Manager", "[OK] Connected" if self.memory_manager else "[ERR] Disconnected"
        )
        status_table.add_row(
            "Ultra-Loop", "[OK] Ready" if self.ultra_loop else "[ERR] Not initialized"
        )
        status_table.add_row(
            "Ultra-Think", "[OK] Ready" if self.ultra_think else "[ERR] Not initialized"
        )

        self.print(status_table)

        # Ultra-Loop metrics
        if self.ultra_loop:
            metrics = self.ultra_loop.get_metrics()
            self.print("\n Ultra-Loop Metrics:", "bold")
            self.print(f"  Total Cycles: {metrics.get('total_cycles', 0)}")
            self.print(f"  Successful: {metrics.get('successful_cycles', 0)}")
            self.print(f"  Failed: {metrics.get('failed_cycles', 0)}")
            success_rate = (
                metrics.get("successful_cycles", 0)
                / max(metrics.get("total_cycles", 1), 1)
                * 100
            )
            self.print(f"  Success Rate: {success_rate:.1f}%")

        # Ultra-Think stats
        if self.ultra_think:
            stats = self.ultra_think.get_stats()
            self.print("\n Ultra-Think Statistics:", "bold")
            self.print(f"  Total Sessions: {stats.get('total_sessions', 0)}")
            self.print(f"  Total Thoughts: {stats.get('total_thoughts', 0)}")
            avg_thoughts = stats.get("avg_thoughts_per_session", 0)
            self.print(f"  Avg Thoughts/Session: {avg_thoughts:.1f}")

        self.print("\n" + "=" * 60 + "\n", "bold blue")

    async def cmd_loop_start(self, cycles: int = 0):
        """Start Ultra-Loop"""
        await self.initialize()

        if not self.ultra_loop:
            self.print("[ERR] Ultra-Loop not initialized", "red")
            return

        self.print("\n Starting Ultra-Loop...", "bold blue")

        if cycles > 0:
            self.ultra_loop.max_cycles = cycles
            self.print(f"  Will run for {cycles} cycles", "yellow")

        await self.ultra_loop.start()
        self.print("[OK] Ultra-Loop started", "green")

        if cycles > 0:
            # Wait for cycles to complete
            import time

            start = time.time()
            while self.ultra_loop._current_cycle < cycles:
                await asyncio.sleep(0.1)
            elapsed = time.time() - start
            self.print(f"  Completed {cycles} cycles in {elapsed:.2f}s", "green")

    async def cmd_loop_stop(self):
        """Stop Ultra-Loop"""
        await self.initialize()

        if not self.ultra_loop:
            self.print("[ERR] Ultra-Loop not initialized", "red")
            return

        self.print("\n  Stopping Ultra-Loop...", "bold blue")
        await self.ultra_loop.stop()
        self.print("[OK] Ultra-Loop stopped", "green")

    async def cmd_loop_status(self):
        """Show Ultra-Loop status"""
        await self.initialize()

        if not self.ultra_loop:
            self.print("[ERR] Ultra-Loop not initialized", "red")
            return

        status = self.ultra_loop.get_status()

        self.print("\n Ultra-Loop Status:", "bold blue")
        self.print(f"  Running: {status['is_running']}")
        self.print(f"  Current Cycle: {status['current_cycle']}")
        self.print(f"  Cycle Interval: {status['cycle_interval']}s")
        self.print(
            f"  Max Cycles: {status['max_cycles'] if status['max_cycles'] > 0 else 'Unlimited'}"
        )

    async def cmd_think(self, question: str, mode: str = "deliberate"):
        """Run thinking session"""
        await self.initialize()

        if not self.ultra_think:
            self.print("[ERR] Ultra-Think not initialized", "red")
            return

        self.print(f"\n Thinking about: {question[:80]}...", "bold blue")
        self.print(f"  Mode: {mode}", "yellow")

        from jebat.features.ultra_think import ThinkingMode

        try:
            thinking_mode = ThinkingMode(mode.lower())
        except ValueError:
            thinking_mode = ThinkingMode.DELIBERATE
            self.print(
                f"  Note: Using DELIBERATE mode (unknown mode: {mode})", "yellow"
            )

        result = await self.ultra_think.think(
            problem=question,
            mode=thinking_mode,
            timeout=30,
        )

        self.print("\n Conclusion:", "bold green")
        self.print(f"  {result.conclusion}", "white")
        self.print(f"\n  Confidence: {result.confidence:.1%}", "cyan")
        self.print(f"  Thinking Steps: {len(result.reasoning_steps)}", "cyan")
        self.print(f"  Execution Time: {result.execution_time:.2f}s", "cyan")

    async def cmd_memory_store(self, text: str):
        """Store a memory"""
        await self.initialize()

        if not self.memory_manager:
            self.print("[ERR] Memory Manager not initialized", "red")
            return

        self.print(f"\n Storing memory: {text[:80]}...", "bold blue")

        from jebat.core.memory.layers import MemoryLayer

        memory_id = await self.memory_manager.store(
            content=text,
            layer=MemoryLayer.M1_EPISODIC,
            user_id="cli_user",
        )

        self.print(f"[OK] Memory stored with ID: {memory_id}", "green")

    async def cmd_memory_search(self, query: str):
        """Search memories"""
        await self.initialize()

        if not self.memory_manager:
            self.print("[ERR] Memory Manager not initialized", "red")
            return

        self.print(f"\n Searching memories: {query}...", "bold blue")

        memories = self.memory_manager.search(
            query=query,
            user_id="cli_user",
            limit=10,
        )

        if memories:
            self.print(f"\n[OK] Found {len(memories)} memories:", "green")
            for i, memory in enumerate(memories[:5], 1):
                content = (
                    memory.content[:100]
                    if hasattr(memory, "content")
                    else str(memory)[:100]
                )
                self.print(f"  {i}. {content}...")
        else:
            self.print("  No memories found", "yellow")

    async def cmd_config(self):
        """Show configuration"""
        self.print("\n  JEBAT Configuration:", "bold blue")

        config = {
            "ultra_loop": {
                "cycle_interval": "1.0s",
                "max_cycles": "0 (unlimited)",
            },
            "ultra_think": {
                "max_thoughts": "20",
                "default_mode": "deliberate",
                "memory_integration": "enabled",
            },
            "memory": {
                "layers": "5 (M0-M4)",
                "consolidation": "automatic",
            },
        }

        for section, settings in config.items():
            self.print(f"\n  {section.upper()}:", "bold cyan")
            for key, value in settings.items():
                self.print(f"    {key}: {value}")

    async def cmd_chat(
        self,
        prompt: str,
        provider_override: str | None = None,
        model_override: str | None = None,
        skill_names: list[str] | None = None,
    ):
        """Run chat completion via configured LLM provider."""
        config = load_llm_config()
        config = self._override_config(config, provider_override, model_override)
        active_prompt, selected_skills = build_skill_prompt(
            prompt,
            requested_skills=skill_names,
            auto_discover=not bool(skill_names),
        )

        self.print(f"\n  Provider: {config.provider}", "bold blue")
        self.print(f"  Model: {config.model}", "cyan")
        if selected_skills:
            self.print(
                f"  Skills: {', '.join(skill.name for skill in selected_skills)}",
                "cyan",
            )
        response, used_provider = await generate_with_failover(
            config=config,
            prompt=active_prompt,
            system_prompt=(
                "You are JEBAT, a pragmatic multi-provider AI development assistant. "
                "Use any provided JEBAT skills as operating guidance."
            ),
        )
        if used_provider != config.provider:
            self.print(f"  Fallback Used: {used_provider}", "yellow")
        self.print("\n Response:", "bold green")
        self.print(response)

    async def cmd_chat_project(
        self,
        prompt: str,
        project_path: str,
        provider_override: str | None = None,
        model_override: str | None = None,
        skill_names: list[str] | None = None,
    ):
        """Run project-aware chat."""
        config = self._override_config(load_llm_config(), provider_override, model_override)
        project = build_project_context(project_path)
        full_prompt = (
            f"{prompt}\n\n"
            f"Project context:\n{project.summary}"
        )
        full_prompt, selected_skills = build_skill_prompt(
            full_prompt,
            requested_skills=skill_names,
            auto_discover=not bool(skill_names),
        )
        response, used_provider = await generate_with_failover(
            config=config,
            prompt=full_prompt,
            system_prompt=(
                "You are JEBAT, a project-aware AI development assistant. "
                "Use the supplied repository context and any provided JEBAT skills."
            ),
        )
        self.print(f"\n  Provider: {used_provider}", "bold blue")
        self.print(f"  Model: {config.model}", "cyan")
        if selected_skills:
            self.print(
                f"  Skills: {', '.join(skill.name for skill in selected_skills)}",
                "cyan",
            )
        self.print("\n Response:", "bold green")
        self.print(response)

    async def cmd_chat_repl(
        self,
        provider_override: str | None = None,
        model_override: str | None = None,
        project_path: str | None = None,
        session_id: str | None = None,
        skill_names: list[str] | None = None,
    ):
        """Interactive REPL chat with history."""
        config = self._override_config(load_llm_config(), provider_override, model_override)
        history = ChatHistoryStore(config.history_path)
        session = session_id or uuid.uuid4().hex[:12]
        project_context = build_project_context(project_path or ".") if project_path else None
        pinned_skills = skill_names or []
        self.print(f"\n  REPL session: {session}", "bold blue")
        self.print("  Type '/exit' to quit.\n", "cyan")
        while True:
            try:
                user_input = input("jebat> ").strip()
            except EOFError:
                break
            if not user_input:
                continue
            if user_input in {"/exit", "/quit"}:
                break
            prior_turns = history.load(session, limit=12)
            transcript = []
            for turn in prior_turns:
                transcript.append(f"{turn.role}: {turn.content}")
            if project_context:
                transcript.append(f"project: {project_context.summary}")
            transcript.append(f"user: {user_input}")
            full_prompt = "\n".join(transcript)
            active_prompt, selected_skills = build_skill_prompt(
                full_prompt,
                requested_skills=pinned_skills,
                auto_discover=not bool(pinned_skills),
            )
            response, used_provider = await generate_with_failover(
                config=config,
                prompt=active_prompt,
                system_prompt=(
                    "You are JEBAT, continuing a CLI conversation with short but useful replies. "
                    "Use provided JEBAT skills when they are present."
                ),
            )
            history.append(session, "user", user_input)
            history.append(session, "assistant", response)
            if selected_skills:
                self.print(
                    f"[{used_provider}] skills={', '.join(skill.name for skill in selected_skills)}",
                    "cyan",
                )
            self.print(f"[{used_provider}] {response}", "green")

    async def cmd_llm_providers(self):
        """Show supported providers."""
        table = self._create_table("Provider", "Environment", "Notes")
        for item in list_supported_providers():
            table.add_row(item["name"], item["env"], item["notes"])
        self.print(table)

    async def cmd_llm_config(self):
        """Show resolved LLM config."""
        config = load_llm_config()
        payload = {
            "provider": config.provider,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "ollama_host": config.ollama_host,
            "fallback_providers": list(config.fallback_providers),
            "history_path": config.history_path,
        }
        self.print(json.dumps(payload, indent=2))

    async def cmd_llm_auth(self, missing_only: bool = False):
        """Show auth status for supported providers."""
        table = self._create_table("Provider", "Configured", "Env Vars", "Notes")
        items = list_provider_auth_status()
        if missing_only:
            items = [item for item in items if not item.configured]
            if not items:
                self.print("All major provider auth paths look configured.", "green")
                return
        for item in items:
            table.add_row(
                item.provider,
                "yes" if item.configured else "no",
                ", ".join(item.env_vars) if item.env_vars else "-",
                item.notes,
            )
        self.print(table)

    async def cmd_llm_best_provider(self):
        """Show the best configured provider based on preference and fallbacks."""
        config = load_llm_config()
        provider = select_best_provider(config.provider, config.fallback_providers)
        self.print(provider)

    async def cmd_doctor(self, probe: bool = False):
        """Run a lightweight health check for the configured LLM stack."""
        config = load_llm_config()
        best_provider = select_best_provider(config.provider, config.fallback_providers)
        auth_items = list_provider_auth_status()

        self.print("\nJEBAT Doctor", "bold blue")
        self.print(f"  Configured Provider: {config.provider}")
        self.print(f"  Configured Model: {config.model}")
        self.print(f"  Best Available Provider: {best_provider}")

        configured = [item.provider for item in auth_items if item.configured]
        missing = [item.provider for item in auth_items if not item.configured]
        self.print(f"  Configured Auth: {', '.join(configured) if configured else 'none'}")
        if missing:
            self.print(f"  Missing Auth: {', '.join(missing)}", "yellow")

        ollama_item = next((item for item in auth_items if item.provider == "ollama"), None)
        if ollama_item and ollama_item.configured:
            ok, detail = self._check_ollama(config.ollama_host)
            style = "green" if ok else "red"
            self.print(f"  Ollama: {detail}", style)

        if probe:
            response, used_provider = await generate_with_failover(
                config=config,
                prompt="Reply with OK.",
                system_prompt="You are a health check. Reply with OK only.",
            )
            snippet = " ".join(response.strip().split())[:120]
            self.print(f"  Probe Provider: {used_provider}", "green")
            self.print(f"  Probe Response: {snippet}", "green")

    def _check_ollama(self, host: str) -> tuple[bool, str]:
        """Check whether the local Ollama HTTP API responds."""
        target = f"{host.rstrip('/')}/api/tags"
        try:
            with urllib.request.urlopen(target, timeout=3) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return False, f"offline ({exc})"

        models = payload.get("models", [])
        return True, f"online ({len(models)} models)"

    async def cmd_skills_list(self, category: str | None = None):
        """List available JEBAT skills."""
        registry = build_skill_registry()
        skills = registry.get_skills_by_category(category) if category else registry.get_all_skills()
        table = self._create_table("Skill", "Category", "Description")
        for skill in sorted(skills, key=lambda item: item.name):
            table.add_row(skill.name, skill.category, skill.description)
        self.print(table)

    async def cmd_skills_search(self, query: str):
        """Search JEBAT skills."""
        registry = build_skill_registry()
        results = registry.search_skills(query)
        table = self._create_table("Skill", "Category", "Description")
        for skill in sorted(results, key=lambda item: item.name):
            table.add_row(skill.name, skill.category, skill.description)
        self.print(table)

    async def cmd_skills_show(self, name: str):
        """Show one JEBAT skill."""
        registry = build_skill_registry()
        skill = registry.get_skill(name)
        if not skill:
            self.print(f"Skill not found: {name}", "red")
            return
        payload = {
            "name": skill.name,
            "category": skill.category,
            "description": skill.description,
            "tags": skill.tags,
            "path": skill.path,
            "content": skill.content,
        }
        self.print(json.dumps(payload, indent=2))

    async def cmd_mode_guide(self):
        """Show the local JEBAT assistant guide path."""
        guide_path = Path(__file__).resolve().parents[2] / "JEBAT_ASSISTANT_GUIDE.md"
        self.print(str(guide_path))

    def _override_config(self, config, provider_override: str | None, model_override: str | None):
        return type(config)(
            provider=provider_override or config.provider,
            model=model_override or config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            ollama_host=config.ollama_host,
            fallback_providers=config.fallback_providers,
            history_path=config.history_path,
        )

    def _create_table(self, *columns):
        """Create a table (Rich or fallback)"""
        if self.console:
            table = Table(show_header=True, header_style="bold")
            for col in columns:
                table.add_column(col)
            return table
        else:
            # Simple text table
            class SimpleTable:
                def __init__(self, *cols):
                    self.rows = []
                    self.cols = cols

                def add_row(self, *row):
                    self.rows.append(row)

                def __str__(self):
                    lines = [" | ".join(self.cols)]
                    lines.append("-" * len(lines[0]))
                    for row in self.rows:
                        lines.append(" | ".join(str(x) for x in row))
                    return "\n".join(lines)

            return SimpleTable(*columns)


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="JEBAT  JEBAT - AI Assistant CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Loop commands
    loop_parser = subparsers.add_parser("loop", help="Ultra-Loop control")
    loop_subparsers = loop_parser.add_subparsers(dest="loop_command")
    loop_subparsers.add_parser("start", help="Start Ultra-Loop")
    loop_subparsers.add_parser("stop", help="Stop Ultra-Loop")
    loop_subparsers.add_parser("status", help="Show Ultra-Loop status")

    # Think command
    think_parser = subparsers.add_parser("think", help="Run thinking session")
    think_parser.add_argument("question", help="Question to think about")
    think_parser.add_argument(
        "--mode",
        default="deliberate",
        help="Thinking mode (fast, deliberate, deep, strategic, creative, critical)",
    )

    # Memory commands
    memory_parser = subparsers.add_parser("memory", help="Memory operations")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")

    memory_store = memory_subparsers.add_parser("store", help="Store a memory")
    memory_store.add_argument("text", help="Memory text")

    memory_search = memory_subparsers.add_parser("search", help="Search memories")
    memory_search.add_argument("query", help="Search query")

    # Config command
    subparsers.add_parser("config", help="Show configuration")
    subparsers.add_parser("llm-providers", help="List supported LLM providers")
    subparsers.add_parser("llm-config", help="Show resolved LLM configuration")
    llm_auth_parser = subparsers.add_parser("llm-auth", help="Show provider authentication status")
    llm_auth_parser.add_argument("--missing-only", action="store_true", help="Show only missing provider auth")
    subparsers.add_parser("llm-best-provider", help="Show the best configured provider")
    doctor_parser = subparsers.add_parser("doctor", help="Check LLM/provider health")
    doctor_parser.add_argument("--probe", action="store_true", help="Send a real test prompt using the configured provider flow")
    subparsers.add_parser("mode-guide", help="Print the local JEBAT assistant guide path")

    skills_parser = subparsers.add_parser("skills", help="Inspect JEBAT TokGuru skills")
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command")
    skills_list_parser = skills_subparsers.add_parser("list", help="List skills")
    skills_list_parser.add_argument("--category", help="Filter skills by category")
    skills_search_parser = skills_subparsers.add_parser("search", help="Search skills")
    skills_search_parser.add_argument("query", help="Search query")
    skills_show_parser = skills_subparsers.add_parser("show", help="Show one skill")
    skills_show_parser.add_argument("name", help="Skill name")

    chat_parser = subparsers.add_parser("chat", help="Chat with JEBAT using the configured LLM")
    chat_parser.add_argument("prompt", help="Prompt to send")
    chat_parser.add_argument("--provider", help="Override provider for this request")
    chat_parser.add_argument("--model", help="Override model for this request")
    chat_parser.add_argument("--skill", action="append", default=[], help="Force one or more JEBAT skills")

    chat_project_parser = subparsers.add_parser("chat-project", help="Chat with JEBAT using current project context")
    chat_project_parser.add_argument("prompt", help="Prompt to send")
    chat_project_parser.add_argument("--project-path", default=".", help="Project path to summarize")
    chat_project_parser.add_argument("--provider", help="Override provider for this request")
    chat_project_parser.add_argument("--model", help="Override model for this request")
    chat_project_parser.add_argument("--skill", action="append", default=[], help="Force one or more JEBAT skills")

    repl_parser = subparsers.add_parser("chat-repl", help="Interactive chat session with history")
    repl_parser.add_argument("--provider", help="Override provider for this session")
    repl_parser.add_argument("--model", help="Override model for this session")
    repl_parser.add_argument("--project-path", help="Optional project path for context")
    repl_parser.add_argument("--session-id", help="Reuse an existing session id")
    repl_parser.add_argument("--skill", action="append", default=[], help="Pin one or more JEBAT skills for the session")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    cli = JEBATCLI()

    try:
        if args.command == "status":
            await cli.cmd_status()

        elif args.command == "loop":
            if args.loop_command == "start":
                await cli.cmd_loop_start()
            elif args.loop_command == "stop":
                await cli.cmd_loop_stop()
            elif args.loop_command == "status":
                await cli.cmd_loop_status()
            else:
                loop_parser.print_help()

        elif args.command == "think":
            await cli.cmd_think(args.question, args.mode)

        elif args.command == "memory":
            if args.memory_command == "store":
                await cli.cmd_memory_store(args.text)
            elif args.memory_command == "search":
                await cli.cmd_memory_search(args.query)
            else:
                memory_parser.print_help()

        elif args.command == "config":
            await cli.cmd_config()

        elif args.command == "llm-providers":
            await cli.cmd_llm_providers()

        elif args.command == "llm-config":
            await cli.cmd_llm_config()

        elif args.command == "llm-auth":
            await cli.cmd_llm_auth(args.missing_only)

        elif args.command == "llm-best-provider":
            await cli.cmd_llm_best_provider()

        elif args.command == "doctor":
            await cli.cmd_doctor(args.probe)

        elif args.command == "mode-guide":
            await cli.cmd_mode_guide()

        elif args.command == "skills":
            if args.skills_command == "list":
                await cli.cmd_skills_list(args.category)
            elif args.skills_command == "search":
                await cli.cmd_skills_search(args.query)
            elif args.skills_command == "show":
                await cli.cmd_skills_show(args.name)
            else:
                skills_parser.print_help()

        elif args.command == "chat":
            await cli.cmd_chat(args.prompt, args.provider, args.model, args.skill)

        elif args.command == "chat-project":
            await cli.cmd_chat_project(
                args.prompt,
                args.project_path,
                args.provider,
                args.model,
                args.skill,
            )

        elif args.command == "chat-repl":
            await cli.cmd_chat_repl(
                provider_override=args.provider,
                model_override=args.model,
                project_path=args.project_path,
                session_id=args.session_id,
                skill_names=args.skill,
            )

        else:
            parser.print_help()

        return 0

    except KeyboardInterrupt:
        cli.print("\n\n⚠️  Interrupted by user", "yellow")
        return 130

    except Exception as e:
        cli.print(f"\n[ERR] Error: {e}\n", "bold red")
        if cli.console:
            cli.console.print_exception()
        return 1

    finally:
        # Cleanup
        if cli.ultra_loop and cli.ultra_loop._is_running:
            await cli.ultra_loop.stop()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


def run():
    """Console script entry point."""
    return asyncio.run(main())
