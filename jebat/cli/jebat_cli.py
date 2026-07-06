#!/usr/bin/env python3
"""
JEBAT CLI v6.1 — Command Line Interface

41 subcommands: status, init, loop, think, memory, config,
llm-providers, llm-config, llm-auth, llm-best-provider, auth, doctor,
mode-guide, skills, chat, chat-project, chat-repl, code, tools, mcp, search,
agent, git, file, exec, wiki, delegate, cron, safety, session, todo,
social, tts, free-models, cost, undo, telemetry, sandbox, plugins

Usage examples:
    jebat status                  - Show system status
    jebat init                    - First-run setup
    jebat chat "hello"            - One-shot chat
    jebat chat-repl               - Interactive REPL
    jebat code "build login page" - Coding agent with multi-agent orchestration
    jebat file read path/to/file  - Read a file
    jebat exec "ls -la"           - Run shell command
    jebat wiki search "topic"     - Search knowledge base
    jebat delegate "fix bug"      - Spawn subagent
    jebat cron add "daily check"  - Schedule recurring task
    jebat session search "query"  - Search past conversations
    jebat todo add "task"         - Add personal task
    jebat social send "hello"     - Send to Telegram/Discord/Twitter
    jebat tts "hello world"       - Text to speech
    jebat auth set provider key   - Store credentials in keyring
"""

import argparse
import asyncio
import json
import uuid
import sys
import urllib.error
import urllib.request
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

# Suppress runpy RuntimeWarning when package is imported before __main__ execution
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*found in sys.modules.*")

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

from jebat.tools.base import BaseTool, ToolRegistry

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

    async def cmd_init(
        self,
        provider: str | None = None,
        key: str | None = None,
        model: str | None = None,
        no_probe: bool = False,
        force: bool = False,
    ):
        """First-run setup wizard — configure LLM provider and API key.

        Walks the user through:
        1. Pick a provider (interactive if not passed via --provider)
        2. Enter API key (or endpoint for ollama/llamacpp)
        3. Pick default model
        4. Write to ~/.jebat/secrets.env
        5. Create ~/.jebat/config.yaml if missing
        6. Test connectivity (unless --no-probe)
        """
        from jebat.features.auth.auth import SUPPORTED_PROVIDERS, _store_env, _read_env_file, _write_env_file
        from jebat.llm.auth import PROVIDER_ENV_MAP

        self.print("\n" + "=" * 54, "bold blue")
        self.print("  JEBAT First-Run Setup", "bold blue")
        self.print("=" * 54, "bold blue")

        # ── Check if already configured ───────────────────────────
        existing = _read_env_file()
        if existing and not force:
            self.print("\n  Secrets already exist in ~/.jebat/secrets.env:", "yellow")
            for k in sorted(existing):
                masked = existing[k][:4] + "***" if len(existing[k]) > 4 else "****"
                self.print(f"    {k}={masked}")
            self.print("\n  Use --force to overwrite. Continuing with existing config for probe test.", "dim")
            provider = provider or "openai"
        else:
            # ── Step 1: Pick provider ──────────────────────────────
            if not provider:
                self.print("\n  Supported providers:", "bold")
                for i, p in enumerate(SUPPORTED_PROVIDERS, 1):
                    env_vars = PROVIDER_ENV_MAP.get(p, ())
                    env_hint = f"  (needs {' or '.join(env_vars)})" if env_vars else ""
                    self.print(f"    {i}. {p}{env_hint}")

                choice = input("\n  Enter provider name (or number): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(SUPPORTED_PROVIDERS):
                    provider = SUPPORTED_PROVIDERS[int(choice) - 1]
                else:
                    provider = choice.lower()
                    if provider not in SUPPORTED_PROVIDERS:
                        provider = "openai"
                        self.print(f"  Unrecognised — defaulting to: {provider}", "yellow")
                self.print(f"  Selected: {provider}", "green")

            # ── Step 2: API key ────────────────────────────────────
            env_vars = PROVIDER_ENV_MAP.get(provider, ())
            env_key_name = env_vars[0] if env_vars else f"{provider.upper()}_API_KEY"
            is_local = provider in ("local", "llamacpp", "ollama")

            if not key:
                if is_local:
                    prompt = f"  {provider} endpoint (e.g., http://localhost:11434): "
                else:
                    prompt = f"  {provider.upper()} API key: "
                key = input(prompt).strip()

            if key:
                # Write to secrets.env
                if is_local:
                    if provider == "ollama":
                        _write_env_file({"OLLAMA_HOST": key})
                    elif provider == "llamacpp":
                        _write_env_file({"LLAMA_CPP_HOST": key})
                    else:
                        _write_env_file({env_key_name: key})
                else:
                    _store_env(provider, "api_key", key)
            else:
                self.print("  No key provided — skipping write. Set later with:", "yellow")
                self.print(f"    echo '{env_key_name}=your-key' >> ~/.jebat/secrets.env", "dim")

        # ── Step 3: Default model ─────────────────────────────────
        if not model:
            default_models = {
                "openai": "gpt-4o",
                "anthropic": "claude-sonnet-4",
                "google": "gemini-2.5-pro",
                "openrouter": "openai/gpt-4o",
                "deepseek": "deepseek-chat",
                "groq": "llama-3.3-70b",
                "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "mistral": "mistral-large",
                "cohere": "command-r-plus",
                "ollama": "llama3.2",
                "custom": "default",
            }
            model = default_models.get(provider, "gpt-4o")
            model_input = input(f"  Default model [{model}]: ").strip()
            if model_input:
                model = model_input

        # ── Step 4: Write config.yaml if missing ──────────────────
        config_path = Path.home() / ".jebat" / "config.yaml"
        if not config_path.exists() or force:
            config_content = (
                f"# JEBAT configuration — auto-generated by `jebat init`\n"
                f"model:\n"
                f"  provider: {provider}\n"
                f"  model: {model}\n"
                f"  temperature: 0.2\n"
                f"\nfeatures:\n"
                f"  terminal:\n"
                f"    enabled: true\n"
                f"    timeout: 300\n"
                f"    dangerous_commands: confirm\n"
                f"  browser:\n"
                f"    enabled: false\n"
                f"  mcp:\n"
                f"    enabled: true\n"
            )
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(config_content, encoding="utf-8")
            self.print(f"\n  Config written: {config_path}", "green")
        else:
            self.print(f"\n  Config exists: {config_path}  (use --force to overwrite)", "dim")

        # ── Step 5: Connectivity test ─────────────────────────────
        if not no_probe:
            self.print("\n  Testing connectivity...", "bold")
            from jebat.llm.auth import _ensure_secrets_loaded
            _ensure_secrets_loaded()

            try:
                import time
                test_start = time.time()
                result = await generate_with_failover(
                    prompt="Reply with the single word: pong",
                    system_prompt="You are a connectivity test. Reply with exactly one word: pong.",
                    provider_override=provider,
                    model_override=model,
                )
                test_elapsed = time.time() - test_start
                self.print(f"  Connected! ({test_elapsed:.1f}s)", "green")
                self.print(f"  Response: {str(result.text)[:200]}", "dim")
            except Exception as e:
                self.print(f"  Connection failed: {e}", "red")
                self.print("  You can retry later with:  jebat doctor --probe", "dim")

        self.print("\n" + "=" * 54, "bold blue")
        self.print("  Setup complete! Try:  jebat agent 'hello!'", "bold green")
        self.print("=" * 54 + "\n", "bold blue")

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
        yolo: bool = False,
        stream: bool = False,
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

        sys_prompt = (
            "You are JEBAT, a pragmatic multi-provider AI development assistant. "
            "Use any provided JEBAT skills as operating guidance."
        )
        self.print("\n Response:", "bold green")

        if stream:
            from jebat.llm.stream_output import StreamPrinter, generate_streaming_with_failover
            printer = StreamPrinter(console=self.console)
            response, used_provider = await generate_streaming_with_failover(
                config=config,
                prompt=active_prompt,
                system_prompt=sys_prompt,
                printer=printer,
            )
        else:
            response, used_provider = await generate_with_failover(
                config=config,
                prompt=active_prompt,
                system_prompt=sys_prompt,
            )
            self.print(response)

        if used_provider != config.provider:
            self.print(f"  Fallback Used: {used_provider}", "yellow")

    async def cmd_chat_project(
        self,
        prompt: str,
        project_path: str,
        provider_override: str | None = None,
        model_override: str | None = None,
        skill_names: list[str] | None = None,
        yolo: bool = False,
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
        yolo: bool = False,
    ):
        """Interactive REPL chat with AgentLoop tool-calling."""
        from jebat.features.repl.repl import ReplLoop

        # Build system prompt with optional skill context
        system_prompt = "You are JEBAT, a pragmatic engineering assistant. Be direct, use tools when appropriate, and keep responses actionable."
        if skill_names:
            skill_lines = []
            for sname in skill_names:
                try:
                    _prompt, _skills = build_skill_prompt(
                        f"use skill {sname}",
                        requested_skills=[sname],
                        auto_discover=False,
                    )
                    if _skills:
                        skill_lines.append(f"- {_skills[0].name}: {_skills[0].description}")
                except Exception:
                    skill_lines.append(f"- {sname}")
            system_prompt += "\n\nPinned skills:\n" + "\n".join(skill_lines)

        # Create and run the ReplLoop — it handles everything
        repl = ReplLoop(
            session_id=session_id,
            ephemeral=False,
            system_prompt=system_prompt,
        )

        # Set provider/model overrides on the REPL
        if provider_override:
            repl._provider_override = provider_override
        if model_override:
            repl._model_override = model_override
        
        # YOLO mode — skip all tool approval prompts
        if yolo:
            from jebat.core.agent_loop import SafetyMode
            repl._safety_mode = SafetyMode.DANGEROUS
            self.print("  YOLO MODE ON — all tool calls auto-approved (dangerous)", "bold red")

        # The ReplLoop.run() is the main loop — it connects to AgentLoop
        await repl.run()

    async def cmd_code(
        self,
        prompt: str | None = None,
        *,
        project_path: str = ".",
        provider_override: str | None = None,
        model_override: str | None = None,
        preset: str | None = None,
        safety: str = "auto",
        yolo: bool = False,
        no_stream: bool = False,
        auto_commit: bool = False,
    ) -> None:
        """Launch the JEBAT Coding Agent — Hermes-style with multi-agent orchestration."""
        from jebat.features.code_agent import CodeAgent

        agent = CodeAgent(
            project_path=project_path,
            provider_override=provider_override,
            model_override=model_override,
            preset=preset,
            safety_mode=safety,
            yolo=yolo,
            stream=not no_stream,
            auto_commit=auto_commit,
        )

        if prompt:
            await agent.run_prompt(prompt)
        else:
            await agent.run_interactive()

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
            "llamacpp_host": config.llamacpp_host,
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

        llamacpp_item = next((item for item in auth_items if item.provider == "llamacpp"), None)
        if llamacpp_item and llamacpp_item.configured:
            ok, detail = self._check_llamacpp(config.llamacpp_host)
            style = "green" if ok else "red"
            self.print(f"  llama.cpp: {detail}", style)

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

    def _check_llamacpp(self, host: str) -> tuple[bool, str]:
        """Check whether the llama.cpp OpenAI-compatible API responds."""
        target = f"{host.rstrip('/')}/health"
        try:
            with urllib.request.urlopen(target, timeout=3):
                return True, "online"
        except (urllib.error.URLError, TimeoutError) as exc:
            return False, f"offline ({exc})"

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
        description="JEBAT v6.1 — 41-CLI AI Agent\n\nCore: status, init, loop, think, memory, config, doctor, mode-guide, skills\nChat: chat, chat-project, chat-repl\nCode: code (Hermes-style coding agent with multi-agent orchestration)\nOps: file, exec, wiki, agent, search, tools, mcp\nSocial: social (send/search/timeline), tts\nOrchestration: delegate, cron, safety, session\nPersonal: todo (add/list/remove/update/clear)\nSecurity: auth (keyring/env/enc), sandbox, undo\nDev: git (status/diff/log/commit/blame/stash), plugins\nInfo: llm-providers, llm-config, llm-auth, llm-best-provider, free-models, cost, telemetry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Init command — first-run setup wizard
    init_parser = subparsers.add_parser("init", help="First-run setup: configure LLM provider and API key")
    init_parser.add_argument("--provider", help="Provider name (openai, anthropic, google, openrouter, groq, deepseek, ollama, custom)")
    init_parser.add_argument("--key", help="API key (or endpoint for ollama/llamacpp)")
    init_parser.add_argument("--model", help="Default model (e.g., gpt-4o, claude-sonnet-4)")
    init_parser.add_argument("--no-probe", action="store_true", help="Skip the connectivity test ping")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing configuration without asking")

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

    # Auth commands — credential storage
    auth_parser = subparsers.add_parser("auth", help="Manage credentials (OS keyring, env, encrypted)")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_action")
    auth_set = auth_subparsers.add_parser("set", help="Store a credential")
    auth_set.add_argument("provider", help="Provider name (openai, anthropic, ...)")
    auth_set.add_argument("key_type", choices=["api_key"], help="Credential type")
    auth_set.add_argument("value", help="The credential value")
    auth_get = auth_subparsers.add_parser("get", help="Retrieve a credential")
    auth_get.add_argument("provider", help="Provider name")
    auth_get.add_argument("key_type", choices=["api_key"], help="Credential type")
    auth_delete = auth_subparsers.add_parser("delete", help="Remove a credential")
    auth_delete.add_argument("provider", help="Provider name")
    auth_delete.add_argument("key_type", choices=["api_key"], help="Credential type")
    auth_list = auth_subparsers.add_parser("list", help="List stored credentials")
    auth_which = auth_subparsers.add_parser("which", help="Show which backend is active")

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
    chat_parser.add_argument("--yolo", action="store_true", help="YOLO mode — auto-approve ALL tool calls (like --dangerously-skip-permissions)")
    chat_parser.add_argument("--stream", action="store_true", help="Stream tokens live as they arrive (character-by-character output)")

    chat_project_parser = subparsers.add_parser("chat-project", help="Chat with JEBAT using current project context")
    chat_project_parser.add_argument("prompt", help="Prompt to send")
    chat_project_parser.add_argument("--project-path", default=".", help="Project path to summarize")
    chat_project_parser.add_argument("--provider", help="Override provider for this request")
    chat_project_parser.add_argument("--model", help="Override model for this request")
    chat_project_parser.add_argument("--skill", action="append", default=[], help="Force one or more JEBAT skills")

    repl_parser = subparsers.add_parser("chat-repl", help="Interactive chat session with AgentLoop tool-calling")
    repl_parser.add_argument("--provider", help="Override provider for this session")
    repl_parser.add_argument("--model", help="Override model for this session")
    repl_parser.add_argument("--project-path", help="Optional project path for context")
    repl_parser.add_argument("--session-id", help="Reuse an existing session id")
    repl_parser.add_argument("--skill", action="append", default=[], help="Pin one or more JEBAT skills for the session")
    repl_parser.add_argument("--yolo", action="store_true", help="YOLO mode — auto-approve ALL tool calls")
    repl_parser.add_argument("--stream", action="store_true", help="Stream tokens live as they arrive")

    # Tools command — list registered tools
    tools_parser = subparsers.add_parser("tools", help="List and inspect registered tools")
    tools_subparsers = tools_parser.add_subparsers(dest="tools_command")
    tools_list = tools_subparsers.add_parser("list", help="List all registered tools")
    tools_list.add_argument("--tier", help="Filter by safety tier (auto/confirm/dangerous)")
    tools_inspect = tools_subparsers.add_parser("inspect", help="Show tool details")
    tools_inspect.add_argument("name", help="Tool name to inspect")

    # MCP command — manage MCP server connections
    mcp_parser = subparsers.add_parser("mcp", help="MCP server management")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command")
    mcp_connect = mcp_subparsers.add_parser("connect", help="Connect to an MCP server")
    mcp_connect.add_argument("server_url", help="Server URL or command (stdio:// or http://)")
    mcp_connect.add_argument("--name", help="Custom name for this server")
    mcp_list = mcp_subparsers.add_parser("list", help="List connected MCP servers and their tools")
    mcp_start_all = mcp_subparsers.add_parser("start-all", help="Start all configured MCP servers")
    mcp_serve = mcp_subparsers.add_parser("serve", help="Start JEBAT as MCP server (for IDE integration)")
    mcp_serve.add_argument("--transport", default="stdio", choices=["stdio", "http", "streamable-http"], help="Transport mode (stdio for IDEs, http for remote, streamable-http for MCP 2025-03-26)")
    mcp_serve.add_argument("--port", type=int, default=8099, help="HTTP port (for http transport)")
    mcp_serve.add_argument("--host", default="127.0.0.1", help="HTTP host (for http transport)")
    mcp_ide_config = mcp_subparsers.add_parser("ide-config", help="Print IDE configuration templates for JEBAT MCP")

    # Search command — web search from CLI
    search_parser = subparsers.add_parser("search", help="Search the web")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--engine", default="searxng", help="Search engine (searxng, duckduckgo, brave)")
    search_parser.add_argument("--limit", type=int, default=5, help="Max results")

    # Agent command — one-shot agent execution
    agent_parser = subparsers.add_parser("agent", help="Run a one-shot agent task with tool-calling")
    agent_parser.add_argument("prompt", help="Task prompt")
    agent_parser.add_argument("--provider", help="Override provider")
    agent_parser.add_argument("--model", help="Override model")
    agent_parser.add_argument("--yolo", action="store_true", help="YOLO mode — auto-approve ALL tool calls")
    agent_parser.add_argument("--safety", default="auto", help="Safety tier (auto/confirm/dangerous)")
    agent_parser.add_argument("--mode", help="Reasoning mode (fast/deliberate/deep/strategic/creative/critical)")
    agent_parser.add_argument("--max-iterations", type=int, default=25, help="Max tool-calling iterations")
    agent_parser.add_argument("--session", "-s", help="Resume a specific session by ID")
    agent_parser.add_argument("--stream", action="store_true", help="Stream tokens as they arrive")

    # Code command — Hermes-style coding agent with multi-agent orchestration
    code_parser = subparsers.add_parser("code", help="Hermes-style coding agent with multi-agent orchestration")
    code_parser.add_argument("prompt", nargs="?", help="Coding prompt (omit for interactive mode)")
    code_parser.add_argument("--provider", help="Override provider")
    code_parser.add_argument("--model", help="Override model")
    code_parser.add_argument("--preset", help="Chat preset (fast, deliberate, deep, strategic, creative, critical)")
    code_parser.add_argument("--project-path", default=".", help="Project root path")
    code_parser.add_argument("--yolo", action="store_true", help="YOLO mode — auto-approve ALL tool calls")
    code_parser.add_argument("--safety", default="auto", help="Safety tier (auto/confirm/dangerous)")
    code_parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    code_parser.add_argument("--auto-commit", "-a", action="store_true", help="Auto-commit changes to git after each action")

    # Git command — PendekarGit (Code Warrior)
    git_parser = subparsers.add_parser("git", help="Git operations: status, diff, log, commit, blame, branch, stash")
    git_subparsers = git_parser.add_subparsers(dest="git_command")
    git_status = git_subparsers.add_parser("status", help="Show working tree status")
    git_diff = git_subparsers.add_parser("diff", help="Show staged or unstaged diff")
    git_diff.add_argument("--staged", action="store_true", help="Show staged diff")
    git_diff.add_argument("--stat", action="store_true", help="Show stat summary")
    git_diff.add_argument("--file", help="Restrict diff to specific file")
    git_log = git_subparsers.add_parser("log", help="Show commit history")
    git_log.add_argument("-n", type=int, default=10, help="Number of commits")
    git_log.add_argument("--author", help="Filter by author")
    git_log.add_argument("--oneline", action="store_true", default=True, help="One-line format")
    git_commit = git_subparsers.add_parser("commit", help="Commit staged changes")
    git_commit.add_argument("-m", dest="message", help="Commit message")
    git_commit.add_argument("--amend", action="store_true", help="Amend previous commit")
    git_blame = git_subparsers.add_parser("blame", help="Show who wrote each line")
    git_blame.add_argument("file", help="File to blame")
    git_branch = git_subparsers.add_parser("branch", help="List/create/switch branches")
    git_branch.add_argument("action", nargs="?", default="list", help="list/create/switch/delete")
    git_branch.add_argument("name", nargs="?", help="Branch name")
    git_stash = git_subparsers.add_parser("stash", help="Stash/pop/list stashes")
    git_stash.add_argument("action", nargs="?", default="push", help="push/pop/list/drop")

    # File operations command — read, write, patch, search
    file_parser = subparsers.add_parser("file", help="File read/write/patch/search operations")
    file_subparsers = file_parser.add_subparsers(dest="file_command")
    file_read = file_subparsers.add_parser("read", help="Read a file with line numbers")
    file_read.add_argument("path", help="File path to read")
    file_read.add_argument("--offset", type=int, default=1, help="Start line (1-indexed)")
    file_read.add_argument("--limit", type=int, default=500, help="Max lines to return")
    file_write = file_subparsers.add_parser("write", help="Write content to a file (creates backup)")
    file_write.add_argument("path", help="File path to write to")
    file_write.add_argument("content", help="Content to write")
    file_patch = file_subparsers.add_parser("patch", help="Find-and-replace edit in a file")
    file_patch.add_argument("path", help="File path to edit")
    file_patch.add_argument("old_string", help="Text to find")
    file_patch.add_argument("new_string", help="Replacement text")
    file_patch.add_argument("--all", dest="replace_all", action="store_true", help="Replace all occurrences")
    file_search = file_subparsers.add_parser("search", help="Search file contents (regex) or find files by glob")
    file_search.add_argument("pattern", help="Search pattern (regex for content, glob for files)")
    file_search.add_argument("--dir", dest="search_dir", default=".", help="Directory to search in")
    file_search.add_argument("--files", dest="search_files_mode", action="store_true", help="Search by file name (glob) instead of content")
    file_search.add_argument("--limit", type=int, default=50, help="Max results")
    file_undo = file_subparsers.add_parser("undo", help="Undo the last write to a file")
    file_undo.add_argument("path", help="File path to undo")

    # --- NEW: exec and wiki subcommands ---

    # Terminal execution command
    exec_parser = subparsers.add_parser("exec", help="Run shell commands (foreground or background)")
    exec_parser.add_argument("cmd", nargs="?", help="Shell command to run")
    exec_parser.add_argument("--bg", action="store_true", help="Run in background")
    exec_parser.add_argument("--poll", metavar="SESSION_ID", help="Poll background process")
    exec_parser.add_argument("--wait", metavar="SESSION_ID", help="Wait for background process")
    exec_parser.add_argument("--kill", metavar="SESSION_ID", help="Kill background process")
    exec_parser.add_argument("--list-bg", action="store_true", help="List background processes")
    exec_parser.add_argument("--pty", action="store_true", help="Run in pseudo-terminal mode")

    # Wiki / Knowledge Base command
    wiki_parser = subparsers.add_parser("wiki", help="Knowledge base: create, read, edit, search, list")
    wiki_parser.add_argument("action", nargs="?", default="list",
                            choices=["create", "read", "edit", "delete", "list", "search", "link", "stats"],
                            help="Wiki action")
    wiki_parser.add_argument("title", nargs="?", help="Page title")
    wiki_parser.add_argument("content", nargs="?", help="Page content (for create)")
    wiki_parser.add_argument("--query", help="Search query (for search)")

    # Delegation command
    delegate_parser = subparsers.add_parser("delegate", help="Spawn subagents for delegated tasks")
    delegate_subparsers = delegate_parser.add_subparsers(dest="delegate_action")

    delegate_run = delegate_subparsers.add_parser("run", help="Run a delegated subagent task")
    delegate_run.add_argument("goal", help="What the subagent should accomplish")
    delegate_run.add_argument("--context", default="", help="Background context for the subagent")
    delegate_run.add_argument("--tools", default="", help="Comma-separated toolset names (empty = all)")
    delegate_run.add_argument("--model", default="", help="Model override for this subagent")
    delegate_run.add_argument("--provider", default="", help="Provider override for this subagent")
    delegate_run.add_argument("--timeout", type=int, default=120, help="Max seconds before kill")
    delegate_run.add_argument("--max-iterations", type=int, default=10, help="Max agent loop iterations")

    delegate_list = delegate_subparsers.add_parser("list", help="List active subagents")
    delegate_cancel = delegate_subparsers.add_parser("cancel", help="Cancel a running subagent")
    delegate_cancel.add_argument("task_id", help="Subagent task ID to cancel")

    # Cron / Scheduled Jobs command
    cron_parser = subparsers.add_parser("cron", help="Schedule recurring tasks")
    cron_subparsers = cron_parser.add_subparsers(dest="cron_action")

    cron_add = cron_subparsers.add_parser("add", help="Add a scheduled job")
    cron_add.add_argument("prompt", help="Prompt to run on schedule")
    cron_add.add_argument("--every", default="", help="Interval (e.g. '5m', '2h', '1d')")
    cron_add.add_argument("--schedule", default="", help="Cron expression (e.g. '*/5 * * * *')")
    cron_add.add_argument("--name", default="", help="Human-friendly job name")
    cron_add.add_argument("--no-agent", action="store_true", help="Run as watchdog script (no LLM)")

    cron_list = cron_subparsers.add_parser("list", help="List all scheduled jobs")
    cron_run = cron_subparsers.add_parser("run", help="Execute a job immediately")
    cron_run.add_argument("job_id", nargs="?", help="Job ID to run, or omit for all due jobs")
    cron_pause = cron_subparsers.add_parser("pause", help="Pause a job")
    cron_pause.add_argument("job_id", help="Job ID to pause")
    cron_resume = cron_subparsers.add_parser("resume", help="Resume a paused job")
    cron_resume.add_argument("job_id", help="Job ID to resume")
    cron_remove = cron_subparsers.add_parser("remove", help="Delete a job")
    cron_remove.add_argument("job_id", help="Job ID to remove")

    # Safety command - audit log viewer
    safety_parser = subparsers.add_parser("safety", help="Security: audit log, classify commands, sandbox toggle")
    safety_subparsers = safety_parser.add_subparsers(dest="safety_action")

    safety_subparsers.add_parser("audit", help="View audit log")
    safety_subparsers.add_parser("clear-audit", help="Clear audit log")
    safety_subparsers.add_parser("sandbox-on", help="Enable sandbox mode (dry run)")
    safety_subparsers.add_parser("sandbox-off", help="Disable sandbox mode")

    classify_cmd = safety_subparsers.add_parser("classify", help="Classify command safety tier")
    classify_cmd.add_argument("command", help="Command to classify")

    # Session commands — list and search history
    session_parser = subparsers.add_parser("session", help="Session management: list, search past conversations")
    session_subparsers = session_parser.add_subparsers(dest="session_action")
    session_subparsers.add_parser("list", help="List recent sessions")
    session_search_cmd = session_subparsers.add_parser("search", help="Search across all sessions (FTS5)")
    session_search_cmd.add_argument("query", help="Search query (supports boolean expressions: 'term1 OR term2')")
    session_search_cmd.add_argument("--role-filter", help="Filter by role: user,assistant (comma-separated)")
    session_search_cmd.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # Todo commands — personal task tracker
    todo_parser = subparsers.add_parser("todo", help="Personal todo list (add, list, remove, update, clear)")
    todo_subparsers = todo_parser.add_subparsers(dest="todo_action")
    # todo add
    todo_add = todo_subparsers.add_parser("add", help="Add a new todo")
    todo_add.add_argument("content", help="Todo content")
    # todo list
    todo_subparsers.add_parser("list", help="List all todos")
    # todo remove
    todo_remove = todo_subparsers.add_parser("remove", help="Remove a todo by ID")
    todo_remove.add_argument("todo_id", help="Todo ID to remove")
    # todo update
    todo_update = todo_subparsers.add_parser("update", help="Update a todo's status")
    todo_update.add_argument("todo_id", help="Todo ID to update")
    todo_update.add_argument("status", help="New status: pending, in_progress, completed, cancelled")
    # todo clear
    todo_subparsers.add_parser("clear", help="Remove all todos")

    # Social commands — messaging platforms
    social_parser = subparsers.add_parser("social", help="Send messages via Telegram, Twitter, Discord")
    social_subparsers = social_parser.add_subparsers(dest="social_action")
    # social send
    social_send = social_subparsers.add_parser("send", help="Send a message")
    social_send.add_argument("target", help="Destination (Telegram chat ID, Discord webhook URL, or 'self' for Twitter)")
    social_send.add_argument("message", help="Message text")
    social_send.add_argument("--platform", default="telegram", choices=["telegram", "twitter", "discord"], help="Target platform")
    # social twitter-search
    social_search = social_subparsers.add_parser("twitter-search", help="Search Twitter/X")
    social_search.add_argument("query", help="Search query")
    social_search.add_argument("--limit", type=int, default=10, help="Max tweets (default: 10)")
    # social twitter-timeline
    social_timeline = social_subparsers.add_parser("twitter-timeline", help="Get home timeline")
    social_timeline.add_argument("--limit", type=int, default=20, help="Max tweets")

    # TTS commands — text-to-speech (Edge TTS free, OpenAI TTS with key)
    tts_parser = subparsers.add_parser("tts", help="Text-to-speech generation (edge, openai, voices)")
    tts_subparsers = tts_parser.add_subparsers(dest="tts_action")
    # tts edge
    tts_edge = tts_subparsers.add_parser("edge", help="Generate speech via Microsoft Edge TTS (free)")
    tts_edge.add_argument("text", help="Text to convert to speech")
    tts_edge.add_argument("--voice", default="en-US-JennyNeural",
                          help="Voice name or shortcut (e.g., en-US-female, ms-MY-female)")
    tts_edge.add_argument("--rate", default="+0%", help="Speed adjustment (+10%%, -5%%)")
    tts_edge.add_argument("--pitch", default="+0Hz", help="Pitch adjustment (+2Hz)")
    tts_edge.add_argument("--output-dir", help="Custom output directory")
    # tts openai
    tts_open = tts_subparsers.add_parser("openai", help="Generate speech via OpenAI TTS (API key)")
    tts_open.add_argument("text", help="Text to convert to speech")
    tts_open.add_argument("--voice", default="alloy",
                          choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
    tts_open.add_argument("--model", default="tts-1", choices=["tts-1", "tts-1-hd"])
    tts_open.add_argument("--speed", type=float, default=1.0, help="Speed 0.25-4.0")
    tts_open.add_argument("--format", default="mp3", choices=["mp3", "opus", "aac", "flac", "wav", "pcm"],
                          dest="response_format")
    tts_open.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env)")
    tts_open.add_argument("--output-dir", help="Custom output directory")
    # tts voices
    tts_voices_cmd = tts_subparsers.add_parser("voices", help="List available Edge TTS voices")
    tts_voices_cmd.add_argument("language", nargs="?", default=None,
                                help="Language prefix filter (e.g., 'en', 'ms', 'zh', 'ja')")

    # Companion command — Sahabat (conversational AI for daily ops)
    companion_parser = subparsers.add_parser("companion", help="Sahabat Companion — conversational AI for daily ops")
    companion_subparsers = companion_parser.add_subparsers(dest="companion_action")
    companion_chat = companion_subparsers.add_parser("chat", help="Interactive chat with Sahabat")
    companion_chat.add_argument("--provider", help="Override provider")
    companion_chat.add_argument("--model", help="Override model")
    companion_briefing = companion_subparsers.add_parser("briefing", help="Generate daily briefing")
    companion_briefing.add_argument("--timezone", default="Asia/Kuala_Lumpur", help="Timezone")
    companion_tasks = companion_subparsers.add_parser("tasks", help="Task management")
    companion_tasks.add_argument("task_action", nargs="?", default="list", help="add/list/complete/stats")
    companion_tasks.add_argument("--title", help="Task title (for add)")
    companion_tasks.add_argument("--priority", default="medium", help="Priority (low/medium/high/urgent)")
    companion_tasks.add_argument("--id", dest="task_id", help="Task ID (for complete)")
    companion_meeting = companion_subparsers.add_parser("meeting", help="Summarize meeting transcript")
    companion_meeting.add_argument("--file", help="Transcript file path")
    companion_meeting.add_argument("--title", help="Meeting title")
    companion_meeting.add_argument("--followup", action="store_true", help="Generate follow-up email")
    companion_stats = companion_subparsers.add_parser("stats", help="Show companion statistics")

    # Free-models command — list free/cheap AI models via 9Router
    freemodels_parser = subparsers.add_parser("free-models", help="List free/cheap AI models available via 9Router")
    freemodels_parser.add_argument("--setup", action="store_true", help="Print 9Router setup guide")

    # Cost tracking command
    cost_parser = subparsers.add_parser("cost", help="Token cost dashboard and tracking")
    cost_parser.add_argument("--summary", action="store_true", help="Show daily cost summary")
    cost_parser.add_argument("--weekly", action="store_true", help="Show weekly cost summary")
    cost_parser.add_argument("--export", action="store_true", help="Export cost data to JSON")

    # Undo/Rollback command
    undo_parser = subparsers.add_parser("undo", help="Undo file changes (rollback to backup)")
    undo_parser.add_argument("path", nargs="?", help="File path to rollback")
    undo_parser.add_argument("--list", action="store_true", help="List available backups")
    undo_parser.add_argument("--diff", action="store_true", help="Show diff vs backup")
    undo_parser.add_argument("--version", type=int, default=-1, help="Backup version (-1=latest)")
    undo_parser.add_argument("--purge", action="store_true", help="Purge all backups")

    # Telemetry command
    telemetry_parser = subparsers.add_parser("telemetry", help="Opt-in usage analytics")
    telemetry_parser.add_argument("--enable", action="store_true", help="Enable telemetry (opt-in)")
    telemetry_parser.add_argument("--disable", action="store_true", help="Disable telemetry")
    telemetry_parser.add_argument("--report", action="store_true", help="Show telemetry report")

    # Sandbox command
    sandbox_parser = subparsers.add_parser("sandbox", help="Docker sandbox for code execution")
    sandbox_parser.add_argument("--check", action="store_true", help="Check if Docker is available")
    sandbox_parser.add_argument("--run", help="Python code to execute in sandbox")
    sandbox_parser.add_argument("--shell-cmd", dest="sandbox_command", help="Shell command to execute in sandbox")
    sandbox_parser.add_argument("--network", action="store_true", help="Allow network in sandbox")

    # Plugins command
    plugins_parser = subparsers.add_parser("plugins", help="Manage JEBAT plugins")
    plugins_parser.add_argument("--list", action="store_true", help="List discovered plugins")
    plugins_parser.add_argument("--load", help="Load a specific plugin")
    plugins_parser.add_argument("--load-all", action="store_true", help="Load all discovered plugins")
    plugins_parser.add_argument("--install-git", help="Install plugin from Git URL")
    plugins_parser.add_argument("--install-pip", help="Install plugin from pip")
    plugins_parser.add_argument("--uninstall", help="Uninstall a plugin")

    args = parser.parse_args()

    if not args.command:
        # Default: start the REPL directly (like Hermes, Claude Code, Codex)
        from jebat.features.repl.repl import ReplLoop
        repl = ReplLoop(ephemeral=False)
        await repl.run()
        return 0

    cli = JEBATCLI()

    try:
        if args.command == "status":
            await cli.cmd_status()

        elif args.command == "init":
            await cli.cmd_init(args.provider, args.key, args.model, args.no_probe, args.force)

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

        elif args.command == "auth":
            from jebat.features.auth.auth import _store, _retrieve, _delete, _active_backend
            if args.auth_action == "set":
                backend = _store(args.provider, args.key_type, args.value)
                print(f"  Stored {args.key_type} for {args.provider} → {backend}")
            elif args.auth_action == "get":
                val = _retrieve(args.provider, args.key_type)
                if val:
                    masked = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
                    print(f"  {args.key_type} for {args.provider}: {masked}")
                else:
                    print(f"  No {args.key_type} found for {args.provider}")
            elif args.auth_action == "delete":
                success = _delete(args.provider, args.key_type)
                if success:
                    print(f"  Removed {args.key_type} for {args.provider}")
                else:
                    print(f"  No {args.key_type} found for {args.provider}")
            elif args.auth_action == "list":
                # Probe known providers through retrieve
                from jebat.features.auth.auth import SUPPORTED_PROVIDERS
                probers = ["api_key"]
                found = []
                for prov in SUPPORTED_PROVIDERS:
                    for kt in probers:
                        if _retrieve(prov, kt):
                            found.append({"provider": prov, "key_type": kt})
                if not found:
                    print("  No credentials stored in fast path — check env/auth.enc/keyring")
                else:
                    print(f"  Stored credentials ({len(found)}):")
                    for c in found:
                        print(f"    {c['provider']}/{c['key_type']}")
            elif args.auth_action == "which":
                backend = _active_backend()
                print(f"  Active credential backend: {backend}")
            else:
                auth_parser.print_help()

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
            yolo = getattr(args, 'yolo', False)
            stream = getattr(args, 'stream', False)
            await cli.cmd_chat(args.prompt, args.provider, args.model, args.skill, yolo=yolo, stream=stream)

        elif args.command == "chat-project":
            yolo = getattr(args, 'yolo', False)
            await cli.cmd_chat_project(
                args.prompt,
                args.project_path,
                args.provider,
                args.model,
                args.skill,
                yolo=yolo,
            )

        elif args.command == "chat-repl":
            yolo = getattr(args, 'yolo', False)
            await cli.cmd_chat_repl(
                provider_override=args.provider,
                model_override=args.model,
                project_path=args.project_path,
                session_id=args.session_id,
                skill_names=args.skill,
                yolo=yolo,
            )

        elif args.command == "code":
            # Check for stdin pipe (cat file | jebat code)
            piped_input = ""
            if not args.prompt and not sys.stdin.isatty():
                try:
                    piped_input = sys.stdin.read()
                except Exception:
                    pass
            prompt = args.prompt or piped_input
            await cli.cmd_code(
                prompt=prompt,
                project_path=args.project_path,
                provider_override=args.provider,
                model_override=args.model,
                preset=args.preset,
                safety=args.safety,
                yolo=getattr(args, 'yolo', False),
                no_stream=getattr(args, 'no_stream', False),
                auto_commit=getattr(args, 'auto_commit', False),
            )

        elif args.command == "tools":
            from jebat.tools import TOOL_REGISTRY
            # Trigger tool imports
            try:
                from jebat.core.agent_loop import AgentLoop
                tmp = AgentLoop.__new__(AgentLoop)
                tmp._tools_imported = False
                tmp._ensure_tools_imported()
            except Exception:
                pass
            if args.tools_command == "inspect":
                tdef = TOOL_REGISTRY.get(args.name)
                if tdef:
                    cli.print(f"  Tool: {tdef.name}", "bold cyan")
                    cli.print(f"  Safety tier: {tdef.safety_tier or 'auto'}")
                    cli.print(f"  Timeout: {tdef.timeout}s")
                    cli.print(f"  Description: {tdef.description or 'N/A'}")
                    cli.print(f"  Schema: {json.dumps(tdef.schema, indent=2)}")
                else:
                    cli.print(f"  Tool '{args.name}' not found", "red")
            else:
                # List mode (default)
                tier_filter = getattr(args, 'tier', None)
                for name, tdef in sorted(TOOL_REGISTRY.items()):
                    tier = tdef.safety_tier or "auto"
                    if tier_filter and tier != tier_filter:
                        continue
                    desc = (tdef.description or "N/A")[:60]
                    cli.print(f"  {name} [{tier}] -- {desc}")

        elif args.command == "mcp":
            from jebat.features.mcp.mcp_client import MCPClient
            mgr = MCPClient()
            if args.mcp_command == "connect":
                server_name = args.name or "dynamic"
                # Dynamically add a server config and start it
                srv_cfg = {
                    "name": server_name,
                    "transport": "http" if args.server_url.startswith("http") else "stdio",
                    "url": args.server_url if args.server_url.startswith("http") else None,
                    "command": args.server_url if not args.server_url.startswith("http") else None,
                    "enabled": True,
                }
                parsed = mgr._parse_server_config(srv_cfg)
                mgr._servers[server_name] = parsed
                await mgr.start_server(server_name)
                tools = mgr.list_discovered_tools(server_name)
                cli.print(f"  Connected: {server_name}")
                cli.print(f"  Tools discovered: {len(tools)}")
                for t in tools:
                    cli.print(f"    - {t.name}: {t.description[:60]}")
            elif args.mcp_command == "list":
                server_names = list(mgr._servers.keys())
                if not server_names:
                    cli.print("  No MCP servers configured.", "yellow")
                else:
                    for name in server_names:
                        tools = mgr.list_discovered_tools(name)
                        transport = mgr._servers[name].transport.value
                        cli.print(f"  {name} ({transport}) -- {len(tools)} tools")
            elif args.mcp_command == "start-all":
                await mgr.start_all()
                total_tools = len(mgr.list_discovered_tools())
                cli.print(f"  All MCP servers started. Total tools: {total_tools}")
            elif args.mcp_command == "serve":
                from jebat.features.mcp.mcp_server import MCPServer, TransportMode, run_server
                if args.transport == "streamable-http":
                    from jebat.features.mcp.mcp_transport import StreamableHTTPTransport
                    cli.print(f"  Starting JEBAT MCP server (Streamable HTTP, MCP 2025-03-26)...")
                    server = MCPServer(transport=TransportMode.HTTP, http_port=args.port, host=args.host)
                    transport = StreamableHTTPTransport(server, host=args.host, port=args.port)
                    await transport.run()
                else:
                    cli.print(f"  Starting JEBAT MCP server ({args.transport} transport)...")
                    run_server(transport=args.transport, port=args.port, host=args.host)
            elif args.mcp_command == "ide-config":
                from jebat.features.mcp.mcp_server import print_ide_configs
                print_ide_configs()
            else:
                mcp_parser.print_help()

        elif args.command == "search":
            from jebat.features.search.web_search import search_web
            results = await search_web(query=args.query, engine=args.engine, limit=args.limit)
            if isinstance(results, dict) and "results" in results:
                for i, r in enumerate(results["results"][:args.limit], 1):
                    title = r.get("title", "")
                    url = r.get("url", "")
                    snippet = r.get("snippet", "")[:120]
                    cli.print(f"  {i}. {title}", "bold")
                    cli.print(f"     {url}", "cyan")
                    cli.print(f"     {snippet}", "dim")
            else:
                cli.print(f"  {results}")

        elif args.command == "agent":
            from jebat.core.agent_loop import AgentLoop, SafetyMode
            safety_map = {"auto": SafetyMode.AUTO, "confirm": SafetyMode.CONFIRM, "dangerous": SafetyMode.DANGEROUS}
            yolo = getattr(args, 'yolo', False)
            # YOLO mode overrides safety to dangerous
            safety = SafetyMode.DANGEROUS if yolo else safety_map.get(args.safety, SafetyMode.AUTO)
            loop = AgentLoop(
                provider_override=args.provider,
                model_override=args.model,
                max_iterations=args.max_iterations,
                safety_mode=safety,
                session_id=getattr(args, 'session', None),
            )
            if getattr(args, 'stream', False):
                async def _stream_write(chunk):
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                result = await loop.run(user_message=args.prompt, mode=args.mode, stream_callback=_stream_write)
                cli.print()  # trailing newline after stream
            else:
                result = await loop.run(user_message=args.prompt, mode=args.mode)
                cli.print(f"\n{result.final_response}", "green")
            if result.tool_calls_made:
                cli.print(f"\n  Tool calls: {len(result.tool_calls_made)}", "dim")
                for step in result.tool_calls_made:
                    status = "OK" if step.error is None else "ERR"
                    cli.print(f"    [{status}] {step.tool_name} -- {step.duration_ms}ms", "dim")
            cli.print(f"  Sessions: {result.session_id} | Iterations: {result.iterations_used} | Provider: {result.provider_used} | Tokens: {result.tokens_used.get('total_tokens', 0)}", "dim")

        elif args.command == "git":
            # PendekarGit — Git operations
            from jebat.features.git.git_tools import (
                git_status, git_diff, git_log, git_commit,
                git_blame, git_branch, git_stash
            )
            git_cmd = getattr(args, 'git_command', None)
            if not git_cmd:
                cli.print("  Usage: jebat git <status|diff|log|commit|blame|branch|stash>", "yellow")
                return 1
            
            dispatch = {
                "status": lambda: git_status(short=True),
                "diff": lambda: git_diff(
                    target="staged" if getattr(args, 'staged', False) else "unstaged",
                    file=getattr(args, 'file', None),
                    stat=getattr(args, 'stat', False),
                ),
                "log": lambda: git_log(
                    count=getattr(args, 'n', 10),
                    author=getattr(args, 'author', None),
                    oneline=getattr(args, 'oneline', True),
                ),
                "commit": lambda: git_commit(
                    message=getattr(args, 'message', None),
                    amend=getattr(args, 'amend', False),
                ),
                "blame": lambda: git_blame(file=args.file),
                "branch": lambda: git_branch(
                    action=getattr(args, 'action', 'list'),
                    name=getattr(args, 'name', None),
                ),
                "stash": lambda: git_stash(action=getattr(args, 'action', 'push')),
            }
            handler = dispatch.get(git_cmd)
            if handler:
                result = handler()
                if result.get("success"):
                    cli.print(result.get("stdout", "OK"), "green")
                else:
                    cli.print(result.get("stderr", "Unknown git error"), "red")
            else:
                cli.print(f"  Unknown git subcommand: {git_cmd}", "red")
                return 1

        elif args.command == "file":
            from jebat.fileops import read_file, write_file, patch_file, search_files
            cmd = getattr(args, 'file_command', None)
            if not cmd:
                file_parser.print_help()
            elif cmd == "read":
                result = read_file(args.path, offset=args.offset, limit=args.limit)
                print(result.get("content", ""))
            elif cmd == "write":
                result = write_file(args.path, args.content)
                if result.get("written"):
                    print(f"  OK: wrote {result.get('bytes', 0)} bytes to {result['path']}")
                else:
                    print(f"  FAIL: {result.get('error', 'unknown')}")
            elif cmd == "patch":
                result = patch_file(args.path, args.old_string, args.new_string, replace_all=getattr(args, 'replace_all', False))
                if result.get("patched"):
                    print(f"  OK: {result.get('matches', 0)} replacement(s)")
                else:
                    print(f"  FAIL: {result.get('error', 'unknown')}")
            elif cmd == "search":
                target = "files" if getattr(args, 'search_files_mode', False) else "content"
                result = search_files(args.pattern, target=target, path=getattr(args, 'search_dir', '.'), limit=args.limit)
                for m in result.get("matches", []):
                    if isinstance(m, dict):
                        print(f"  {m.get('file', '')}:{m.get('line', '')}  {m.get('text', '')[:120]}")
                    else:
                        print(f"  {m}")
            elif cmd == "undo":
                from jebat.fileops.write import undo_write
                result = undo_write(args.path)
                if result.get("restored"):
                    print(f"  OK: restored {result['path']}")
                else:
                    print(f"  FAIL: {result.get('error', 'unknown')}")
            else:
                file_parser.print_help()

        elif args.command == "exec":
            from jebat.terminal import get_executor
            executor = get_executor()

            if args.list_bg:
                result = executor.list_bg()
                for p in result["processes"]:
                    print(f"  {p['session_id']}: {p['command'][:60]} ({p['status']})")
            elif args.poll:
                result = await executor.poll(args.poll)
                print(f"  Session: {result.get('session_id')} | Status: {result.get('status')}")
                if result.get("output_tail"):
                    print("  --- tail ---")
                    print(result["output_tail"])
            elif args.wait:
                result = await executor.wait(args.wait)
                print(f"  Session: {result.get('session_id')} | Status: {result.get('status')} | Exit: {result.get('exit_code')}")
                if result.get("output"):
                    print(result["output"])
            elif args.kill:
                result = await executor.kill(args.kill)
                print(f"  {result['session_id']}: {result.get('status')}")
            elif args.cmd:
                if args.bg:
                    result = await executor.start_bg(args.cmd)
                    if result.get("session_id"):
                        print(f"  Started: {result['session_id']} — {result['command'][:60]}")
                    else:
                        print(f"  FAIL: {result.get('error')}")
                else:
                    result = await executor.run(args.cmd, pty=args.pty)
                    if result.get("error"):
                        print(f"  FAIL: {result['error']}")
                    else:
                        print(result["output"])
                        print(f"\n  [exit={result['exit_code']} | {result['duration_ms']}ms]")
            else:
                exec_parser.print_help()

        elif args.command == "wiki":
            from jebat.features.wiki import WikiStore
            wiki = WikiStore()

            action = args.action
            if action == "list":
                result = wiki.list_pages()
                if result["count"] == 0:
                    print("  No wiki pages yet. Create one with: jebat wiki create \"My Title\" \"content\"")
                else:
                    print(f"  Wiki — {result['count']} page(s):")
                    for p in result["pages"]:
                        print(f"    {p['title']} ({p['size_bytes']}b)")
            elif action == "create":
                if not args.title:
                    print("  Usage: jebat wiki create <title> <content>")
                else:
                    content = args.content or "(empty)"
                    result = wiki.create_page(args.title, content)
                    if result.get("error"):
                        print(f"  FAIL: {result['error']}")
                    else:
                        print(f"  Created: {result['title']} ({result['size_bytes']} bytes)")
            elif action == "read":
                if not args.title:
                    print("  Usage: jebat wiki read <title>")
                else:
                    result = wiki.read_page(args.title)
                    if result.get("error"):
                        print(f"  Not found: {args.title}")
                    else:
                        print(f"  {result['title']} ({result['size_bytes']}b, updated {result.get('updated_at', 0):.0f})")
                        print("  " + "-" * 40)
                        print(result["content"])
            elif action == "edit":
                if not args.title or not args.content:
                    print("  Usage: jebat wiki edit <title> <content>")
                else:
                    result = wiki.update_page(args.title, args.content)
                    if result.get("error"):
                        print(f"  FAIL: {result['error']}")
                    else:
                        print(f"  Updated: {result['title']} ({result['size_bytes']} bytes)")
            elif action == "delete":
                if not args.title:
                    print("  Usage: jebat wiki delete <title>")
                else:
                    result = wiki.delete_page(args.title)
                    if result.get("error"):
                        print(f"  FAIL: {result['error']}")
                    else:
                        print(f"  Deleted: {result['title']}")
            elif action == "search":
                query = args.query or args.title
                if not query:
                    print("  Usage: jebat wiki search --query <search terms>")
                else:
                    result = wiki.search(query)
                    print(f"  Search '{query}': {result['count']} match(es)")
                    for m in result["matches"]:
                        print(f"    {m['title']} — {m['snippet']}")
            elif action == "link":
                if not args.title:
                    print("  Usage: jebat wiki link <title>")
                else:
                    result = wiki.get_backlinks(args.title)
                    links = result["backlinks"]
                    print(f"  Pages linking to '{args.title}': {len(links)}")
                    for src in links:
                        print(f"    {src}")
            elif action == "stats":
                stats = wiki.get_stats()
                print(f"  Wiki stats: {stats['page_count']} pages, {stats['total_size_bytes']} bytes, {stats['backlink_count']} backlinks")
                if stats["last_updated"]:
                    print(f"  Last updated: {stats['last_updated']['title']} ({stats['last_updated']['updated_at']:.0f})")

        elif args.command == "delegate":
            from jebat.core.delegation import DelegationManager, SubagentConfig

            manager = DelegationManager()

            if args.delegate_action == "run":
                toolsets = [t.strip() for t in args.tools.split(",")] if args.tools else []

                config = SubagentConfig(
                    goal=args.goal,
                    context=args.context or "",
                    toolsets=toolsets,
                    model=args.model or "",
                    provider=args.provider or "",
                    max_iterations=args.max_iterations,
                    timeout=args.timeout,
                )

                print(f"  Spawning subagent for: {args.goal[:80]}")
                print(f"  Toolsets: {toolsets or '(all)'}")
                print(f"  Timeout: {args.timeout}s | Max iterations: {args.max_iterations}")

                result = await manager.spawn_subagent(config)

                print(f"\n{'='*60}")
                print(f"  Status: {'SUCCESS' if result.success else 'FAILED'}")
                print(f"  Tool calls: {len(result.tool_calls_made)}")
                if result.error:
                    print(f"  Error: {result.error}")
                print(f"\n  Summary: {result.summary}")
                print(f"{'='*60}")

                if result.tokens_used:
                    print(f"  Tokens: {result.tokens_used}")

            elif args.delegate_action == "list":
                active = manager._active_subagents
                if not active:
                    print("  No active subagents")
                else:
                    print(f"  Active subagents: {len(active)}")
                    for tid, task in active.items():
                        status = "running" if not task.done() else "completed"
                        print(f"    {tid[:8]}... — {status}")

            elif args.delegate_action == "cancel":
                if args.task_id in manager._active_subagents:
                    manager._active_subagents[args.task_id].cancel()
                    print(f"  Cancelled {args.task_id[:12]}...")
                else:
                    print(f"  No subagent found with ID {args.task_id[:12]}...")
            else:
                delegate_parser.print_help()

        elif args.command == "cron":
            from jebat.features.cron import cron as cron_mod
            import asyncio

            if args.cron_action == "add":
                name = args.name or args.prompt[:50]
                schedule = args.every or args.schedule
                if not schedule:
                    print("  Error: --every or --schedule is required")
                    return

                result = await cron_mod.cron_create(
                    name=name,
                    schedule=schedule,
                    prompt=args.prompt,
                    no_agent=args.no_agent,
                )
                if result.get("ok"):
                    print(f"  Job created: {result.get('id', '?')[:12]}...")
                    print(f"  Schedule: {schedule}")
                else:
                    print(f"  Error: {result.get('error', 'unknown')}")

            elif args.cron_action == "list":
                jobs = cron_mod.get_due_jobs()
                conn = cron_mod._get_conn()
                all_jobs = conn.execute("SELECT * FROM cron_jobs ORDER BY created_at DESC").fetchall()
                conn.close()
                if not all_jobs:
                    print("  No scheduled jobs")
                else:
                    for row in all_jobs:
                        job = cron_mod._row_to_dict(row)
                        state = "enabled" if job.get("enabled") else "paused"
                        print(f"  [{state}] {job['id']} — {job.get('name', job['prompt'][:40])}")
                        print(f"    Schedule: {job.get('schedule', '?')} | Runs: {job.get('run_count', 0)}")

            elif args.cron_action == "run":
                if args.job_id:
                    job = cron_mod.get_job(args.job_id)
                    if job:
                        result = await cron_mod.cron_run_now(job_id=args.job_id)
                        print(f"  Running {args.job_id[:12]}...")
                        print(f"  Output: {result.get('output', '')[:500]}")
                    else:
                        print(f"  Job not found: {args.job_id[:12]}...")
                else:
                    due = cron_mod.get_due_jobs()
                    if not due:
                        print("  No jobs due")
                    for job in due:
                        result = await cron_mod.cron_run_now(job_id=job["id"])
                        print(f"  {job['id'][:12]}... → {result.get('output', '')[:200]}")

            elif args.cron_action == "pause":
                result = await cron_mod.cron_pause(job_id=args.job_id)
                print(f"  {result.get('message', result)}")

            elif args.cron_action == "resume":
                result = await cron_mod.cron_resume(job_id=args.job_id)
                print(f"  {result.get('message', result)}")

            elif args.cron_action == "remove":
                result = await cron_mod.cron_remove(job_id=args.job_id)
                print(f"  {result.get('message', result)}")

            else:
                cron_parser.print_help()

        elif args.command == "safety":
            from jebat.features.security import (
                read_audit_log, clear_audit_log, enable_sandbox, disable_sandbox,
                is_sandbox, AUDIT_LOG_PATH,
            )
            from jebat.tools import classify_command

            if args.safety_action == "audit":
                entries = read_audit_log(limit=50)
                if not entries:
                    print("  No audit log entries found")
                else:
                    print(f"  Recent audit entries ({len(entries)}):\n")
                    for e in entries[-20:]:
                        print(f"  [{e.get('safety','?')}] {e.get('ts','?')[:19]} | "
                              f"{e.get('tool','?')} | {'OK' if e.get('approved') else 'BLOCKED'} | "
                              f"{e.get('params',{}).get('command','')[:60]}")
                    print(f"\n  Log path: {AUDIT_LOG_PATH}")
                    print(f"  Total on disk: {len(entries)} entries")

            elif args.safety_action == "clear-audit":
                clear_audit_log()
                print("  Audit log cleared")

            elif args.safety_action == "sandbox-on":
                enable_sandbox()
                print("  Sandbox mode ON — commands will dry-run")

            elif args.safety_action == "sandbox-off":
                disable_sandbox()
                print("  Sandbox mode OFF — commands execute normally")

            elif args.safety_action == "classify":
                tier = classify_command(args.command)
                print(f"  Command: {args.command}")
                print(f"  Safety tier: {tier.upper()}")
                if tier == "dangerous":
                    print("  ⚠ Needs --dangerous flag to execute")
                elif tier == "confirm":
                    print("  WARN: Will prompt for confirmation before executing")

            else:
                safety_parser.print_help()
                print(f"  Sandbox mode: {'ON (dry-run)' if is_sandbox() else 'OFF'}")

        elif args.command == "session":
            from jebat.session.session_manager import SessionManager
            sm = SessionManager()

            if args.session_action == "list":
                sessions = sm.list_sessions(limit=20)
                if not sessions:
                    print("  No sessions found")
                else:
                    print(f"  Recent sessions ({len(sessions)}):\n")
                    for s in sessions:
                        title = s["title"][:60]
                        msg_count = s["msg_count"]
                        from datetime import datetime
                        updated_str = datetime.fromtimestamp(s["updated_at"]).strftime("%Y-%m-%d %H:%M")
                        # Truncate UUID for display
                        short_id = s["id"][:8]
                        print(f"  [{short_id}] {title} — {msg_count} msgs, last: {updated_str}")

            elif args.session_action == "search":
                results = sm.search_messages(args.query, limit=args.limit, role_filter=args.role_filter)
                if not results:
                    print(f"  No results for: '{args.query}'")
                else:
                    print(f"  Session search results for '{args.query}' ({len(results)}):\n")
                    for r in results:
                        role = r["role"]
                        snippet = r["snippet"] or r["content"][:80]
                        session_ref = f"[{r['session_id'][:8]}] {r['session_title']}"
                        print(f"  [{role}] {session_ref}")
                        print(f"    {snippet}")
                        print()

            else:
                session_parser.print_help()

        elif args.command == "todo":
            from jebat.features.todo import add_todo, list_todos, remove_todo, update_todo_status, clear_todos
            import asyncio
            import concurrent.futures

            def _run_async(coro):
                """Run a coroutine in a separate thread with its own event loop."""
                def run_in_thread():
                    return asyncio.run(coro)

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_in_thread)
                    return future.result()

            if args.todo_action == "add":
                result = _run_async(add_todo(args.content))
                if "error" in result:
                    print(f"  Error: {result['error']}")
                else:
                    print(f"  Added todo [{result['id'][:8]}]: {result['content']}")
            elif args.todo_action == "list":
                todos = _run_async(list_todos())
                if not todos:
                    print("  No todos")
                else:
                    print(f"  Todos ({len(todos)}):")
                    for t in todos:
                        status_icon = {"pending": "○", "in_progress": "⧗", "completed": "✓", "cancelled": "✗"}.get(t["status"], "?")
                        print(f"  [{status_icon}] {t['id'][:8]}: {t['content']}")
            elif args.todo_action == "remove":
                result = _run_async(remove_todo(args.todo_id))
                if "error" in result:
                    print(f"  Error: {result['error']}")
                else:
                    print(f"  Removed todo [{result['id'][:8]}]: {result['content']}")
            elif args.todo_action == "update":
                result = _run_async(update_todo_status(args.todo_id, args.status))
                if "error" in result:
                    print(f"  Error: {result['error']}")
                else:
                    print(f"  Updated todo [{result['id'][:8]}]: {result['content']} → {result['status']}")
            elif args.todo_action == "clear":
                result = _run_async(clear_todos())
                print(f"  Cleared {result['removed']} todos")
            else:
                todo_parser.print_help()

        elif args.command == "social":
            from jebat.features.social_media.social_media import send_message, twitter_search, twitter_timeline
            import asyncio, concurrent.futures

            def _run_async(coro):
                def run_in_thread():
                    return asyncio.run(coro)
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as e:
                    return e.submit(run_in_thread).result()

            if args.social_action == "send":
                print(f"  Sending message via {args.platform}...")
                try:
                    result = _run_async(send_message(
                        target=args.target,
                        message=args.message,
                        platform=args.platform,
                    ))
                    if result.get("status") == "sent":
                        print(f"  Sent to {args.platform} — details: {result}")
                    else:
                        print(f"  Failed: {result.get('error', 'unknown')}")
                except Exception as exc:
                    print(f"  Error: {exc}")
            elif args.social_action == "twitter-search":
                print(f"  Searching Twitter for: {args.query}...")
                try:
                    tweets = _run_async(twitter_search(args.query, limit=args.limit))
                    if not tweets:
                        print("  No results")
                    else:
                        print(f"  {len(tweets)} tweets found:")
                        for tw in tweets[:args.limit]:
                            print(f"    @{tw.get('from_user','?'):>15} — {tw.get('text','')[:80]}")
                except Exception as exc:
                    print(f"  Error: {exc}")
            elif args.social_action == "twitter-timeline":
                print(f"  Fetching home timeline...")
                try:
                    tweets = _run_async(twitter_timeline(limit=args.limit))
                    if not tweets:
                        print("  No timeline tweets")
                    else:
                        print(f"  {len(tweets)} tweets:")
                        for tw in tweets[:args.limit]:
                            print(f"    @{tw.get('from_user','?'):>15} — {tw.get('text','')[:80]}")
                except Exception as exc:
                    print(f"  Error: {exc}")
            else:
                social_parser.print_help()

        elif args.command == "free-models":
            from jebat.llm.ninerouter_provider import list_free_models, print_ninerouter_setup
            if args.setup:
                print_ninerouter_setup()
            else:
                cli.print("  Free/Cheap AI Models via 9Router:", "bold cyan")
                models = list_free_models()
                for m in models:
                    tier_color = {"free": "green", "cheap": "yellow", "free-credits": "cyan"}.get(m["tier"], "white")
                    cli.print(f"  {m['model']} ({m['tier']}) {m['provider']} — {m['notes']}", tier_color)

        elif args.command == "cost":
            from jebat.features.cost_tracking.cost_tracking import get_daily_summary, get_weekly_summary, format_summary, export_to_json
            if args.weekly:
                summary = get_weekly_summary()
                print(format_summary(summary, "weekly"))
            elif args.export:
                path = export_to_json()
                print(f"  Exported to: {path}")
            else:
                summary = get_daily_summary()
                print(format_summary(summary, "daily"))

        elif args.command == "undo":
            from jebat.features.undo.undo import undo, list_backups, diff_backup, purge_backups
            if args.purge:
                result = purge_backups()
                print(f"  Purged {result['purged']} backup files")
            elif args.list and args.path:
                backups = list_backups(args.path)
                if not backups:
                    print(f"  No backups found for {args.path}")
                else:
                    print(f"  Backups for {args.path}:")
                    for b in backups:
                        print(f"    {b.get('backup_file', '')} — {b.get('operation', '')} — {b.get('timestamp', '')}")
            elif args.diff and args.path:
                diff = diff_backup(args.path, args.version)
                print(diff)
            elif args.path:
                result = undo(args.path, args.version)
                if result.success:
                    print(f"  Restored {result.restored_path} — {result.message}")
                else:
                    print(f"  Undo failed: {result.message}")
            else:
                print("  Usage: jebat undo <path> [--list|--diff|--purge|--version N]")

        elif args.command == "telemetry":
            from jebat.features.telemetry.telemetry import enable_telemetry, disable_telemetry, format_telemetry_report, load_config
            if args.enable:
                config = enable_telemetry()
                print(f"  Telemetry ENABLED — categories: {', '.join(config.categories)}")
            elif args.disable:
                config = disable_telemetry()
                print(f"  Telemetry DISABLED")
            elif args.report:
                print(format_telemetry_report())
            else:
                config = load_config()
                print(f"  Telemetry status: {'ENABLED' if config.enabled else 'DISABLED'}")
                if config.enabled:
                    print(f"  Categories: {', '.join(config.categories)}")

        elif args.command == "sandbox":
            from jebat.features.sandbox.sandbox import check_docker_available, sandbox_exec_python, sandbox_exec_command
            if args.check:
                available = check_docker_available()
                print(f"  Docker available: {available}")
            elif args.run:
                result = sandbox_exec_python(args.run, network=args.network)
                print(f"  Exit code: {result.exit_code}")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            elif getattr(args, 'sandbox_command', None):  # avoid collision with args.command
                result = sandbox_exec_command(args.sandbox_command, network=args.network)
                print(f"  Exit code: {result.exit_code}")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            else:
                print("  Usage: jebat sandbox [--check|--run 'code'|--command 'cmd'] [--network]")

        elif args.command == "plugins":
            from jebat.features.plugins.plugins import discover_local_plugins, discover_pip_plugins, load_plugin, load_all_plugins, install_from_git, install_from_pip, uninstall_plugin
            if args.list:
                local = discover_local_plugins()
                pip = discover_pip_plugins()
                print(f"  Local plugins ({len(local)}):")
                for p in local:
                    print(f"    {p}")
                print(f"  Pip plugins ({len(pip)}):")
                for p in pip:
                    print(f"    {p}")
            elif args.load:
                status = load_plugin(args.load)
                if status.loaded:
                    print(f"  Plugin '{status.name}' loaded — {status.tools_registered} tools registered")
                else:
                    print(f"  Failed: {status.error}")
            elif args.load_all:
                statuses = load_all_plugins()
                for s in statuses:
                    icon = "OK" if s.loaded else "FAIL"
                    print(f"  [{icon}] {s.name} — {s.tools_registered} tools ({s.error or 'loaded'})")
            elif args.install_git:
                status = install_from_git(args.install_git)
                print(f"  Plugin installed: {status.name} — {status.tools_registered} tools")
            elif args.install_pip:
                status = install_from_pip(args.install_pip)
                print(f"  Plugin installed: {status.name} — {status.tools_registered} tools")
            elif args.uninstall:
                result = uninstall_plugin(args.uninstall)
                print(f"  {result.get('status', 'unknown')}: {result}")
            else:
                print("  Usage: jebat plugins [--list|--load|--load-all|--install-git|--install-pip|--uninstall]")

        elif args.command == "tts":
            from jebat.features.tts import edge_tts, openai_tts, list_tts_voices, EDGE_VOICES
            import asyncio
            import concurrent.futures

            def _run_async(coro):
                def _run():
                    return asyncio.run(coro)
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    return executor.submit(_run).result()

            if args.tts_action == "edge":
                # Resolve voice shortcuts
                voice = EDGE_VOICES.get(args.voice, args.voice)
                print(f"  Generating speech with Edge TTS...")
                print(f"  Voice: {voice}")
                try:
                    result = _run_async(edge_tts(
                        args.text, voice=voice,
                        rate=args.rate, pitch=args.pitch,
                        output_dir=args.output_dir,
                    ))
                    print(f"  Saved: {result.filepath}")
                    print(f"  Format: {result.format} | Text length: {result.text_length} chars")
                except Exception as e:
                    print(f"  TTS failed: {e}")
                    print(f"  Tip: Install edge-tts for offline use: pip install edge-tts")

            elif args.tts_action == "openai":
                print(f"  Generating speech with OpenAI TTS...")
                print(f"  Model: {args.model} | Voice: {args.voice}")
                try:
                    result = _run_async(openai_tts(
                        args.text,
                        api_key=args.api_key,
                        model=args.model,
                        voice=args.voice,
                        speed=args.speed,
                        response_format=args.response_format,
                        output_dir=args.output_dir,
                    ))
                    print(f"  Saved: {result.filepath}")
                    print(f"  Format: {result.format} | Text length: {result.text_length} chars")
                except Exception as e:
                    print(f"  TTS failed: {e}")

            elif args.tts_action == "voices":
                voices = list_tts_voices(args.language)
                if not voices:
                    print(f"  No voices found for language '{args.language}'")
                else:
                    filter_text = f" for '{args.language}'" if args.language else ""
                    print(f"  Available Edge TTS voices{filter_text} ({len(voices)}):")
                    for shortcut, full_name in voices.items():
                        print(f"    {shortcut:20s} → {full_name}")

            else:
                tts_parser.print_help()

        elif args.command == "companion":
            import asyncio as _aio

            def _run(coro):
                def _f():
                    return _aio.run(coro)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    return ex.submit(_f).result()

            from jebat.features.companion import SahabatCompanion, DailyBriefing, TaskManager, MeetingSummarizer

            if args.companion_action == "chat":
                comp = SahabatCompanion(provider=args.provider, model=args.model)
                print("\n🤖 Sahabat — JEBAT Companion")
                print("   Conversational AI for daily operations")
                print("   Type 'quit' to exit, 'stats' for info\n")
                session = comp.start_session()

                async def _chat_loop():
                    while True:
                        try:
                            user_input = input("You: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            print("\n👋 Goodbye!")
                            break
                        if not user_input:
                            continue
                        if user_input.lower() in ("quit", "exit", "q"):
                            print("\n👋 Goodbye!")
                            break
                        if user_input.lower() == "stats":
                            stats = comp.get_stats()
                            print(f"\n📊 Sessions: {stats['total_sessions']} | Messages: {stats['total_messages']}")
                            if stats['recent_topics']:
                                print(f"   Recent: {', '.join(stats['recent_topics'][:3])}\n")
                            continue
                        response, provider = await comp.chat(user_input, session=session)
                        print(f"\nSahabat [{provider}]: {response}\n")

                _run(_chat_loop())

            elif args.companion_action == "briefing":
                briefing = DailyBriefing()
                print("\n🌅 Generating your daily briefing...\n")
                result = _run(briefing.generate(timezone_str=args.timezone))
                print(f"📅 {result.date} | Provider: {result.provider}")
                print(f"   Tasks: {result.task_count} | Topics: {len(result.recent_topics)}\n")
                print(result.content)

            elif args.companion_action == "tasks":
                tm = TaskManager()
                action = args.task_action

                if action == "add":
                    if not args.title:
                        print("  Usage: jebat companion tasks add --title 'Task name'")
                    else:
                        task = tm.add_task(title=args.title, priority=args.priority)
                        print(f"  ✅ Task added: {task.title} [{task.priority}] ({task.task_id})")

                elif action == "complete":
                    if not args.task_id:
                        print("  Usage: jebat companion tasks complete --id <task-id>")
                    else:
                        task = tm.complete_task(args.task_id)
                        if task:
                            print(f"  ✅ Completed: {task.title}")
                        else:
                            print(f"  ❌ Task not found: {args.task_id}")

                elif action == "stats":
                    stats = tm.get_stats()
                    print(f"\n📊 Task Stats:")
                    print(f"   Total: {stats['total']} | Pending: {stats['pending']} | Completed: {stats['completed']}")
                    print(f"   Urgent: {stats['urgent']} | Rate: {stats['completion_rate']}")

                else:  # list
                    tasks = tm.list_tasks(status="pending", limit=20)
                    print(f"\n📋 Pending Tasks ({len(tasks)}):")
                    print(tm.format_tasks(tasks))

            elif args.companion_action == "meeting":
                summarizer = MeetingSummarizer()
                if args.file:
                    from pathlib import Path as _P
                    transcript = _P(args.file).read_text(encoding="utf-8")
                else:
                    print("  Paste your meeting transcript (Ctrl+D to finish):")
                    import sys as _sys
                    transcript = _sys.stdin.read()

                if not transcript.strip():
                    print("  ❌ No transcript provided.")
                else:
                    print("\n📝 Summarizing meeting...\n")
                    meeting = _run(summarizer.summarize(
                        transcript=transcript,
                        title=args.title,
                        generate_followup=args.followup,
                    ))
                    print(summarizer.format_meeting(meeting))

            elif args.companion_action == "stats":
                comp = SahabatCompanion()
                stats = comp.get_stats()
                tm = TaskManager()
                task_stats = tm.get_stats()
                print(f"\n🤖 Sahabat Companion Stats:")
                print(f"   Sessions: {stats['total_sessions']}")
                print(f"   Messages: {stats['total_messages']}")
                print(f"   Tasks: {task_stats['total']} ({task_stats['pending']} pending)")
                if stats['recent_topics']:
                    print(f"   Recent topics:")
                    for topic in stats['recent_topics'][:5]:
                        print(f"     • {topic}")

            else:
                companion_parser.print_help()

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
