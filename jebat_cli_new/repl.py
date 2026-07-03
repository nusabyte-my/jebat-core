"""
JEBAT — interactive REPL with OpenClaude & OpenManus styles.
"""

from __future__ import annotations

import json
from typing import Optional

from jebat_cli_new.agent import AgentLoop
from jebat_cli_new.slash_commands import match_command, render_help
from jebat_cli_new.ux import TerminalUX, streaming_print


PRESETS = {
    "fast": {"temperature": 0.1, "max_tokens": 2048},
    "deliberate": {"temperature": 0.2, "max_tokens": 4096},
    "deep": {"temperature": 0.3, "max_tokens": 6144},
    "strategic": {"temperature": 0.2, "max_tokens": 4096},
    "creative": {"temperature": 0.7, "max_tokens": 4096},
    "critical": {"temperature": 0.1, "max_tokens": 4096},
}


class REPL:
    def __init__(self, agent: AgentLoop, style: str = "openclaude"):
        self.agent = agent
        self.provider = agent.default_provider
        self.model = agent.model
        self.style = style
        self.mode = "auto"
        self.sys_prompt = ""
        self.tools_enabled = True
        self.yolo = agent.yolo
        self.auto_commit = agent.auto_commit
        self.preset = "deliberate"

    def start(self):
        """Start the interactive REPL."""
        print()
        if self.style == "openmanus":
            print("  JEBAT  ⚔️  unified coding agent (OpenManus mode)")
        else:
            print("  JEBAT  ⚔️  unified coding agent")
        print(f"  provider: {self.provider}  model: {self.model}")
        print(f"  style: {self.style}  preset: {self.preset}")
        print(f"  yolo: {self.yolo}  auto-commit: {self.auto_commit}")
        print()
        print("  /help, /plan, /provider, /model, /preset, /yolo, /commit, /clear, /exit")
        print()

        while True:
            try:
                raw = input(f"  [{self.provider}:{self.model}] ").rstrip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not raw:
                continue

            if raw.startswith("/"):
                handled = self._handle_slash(raw)
                if handled is False:
                    break
                if handled is True:
                    continue
            else:
                text, _ = self._call_runtime(raw)
                streaming_print(text, self.provider, self.model)

    def _handle_slash(self, raw: str):
        """Handle slash commands."""
        cmd = match_command(raw)
        if not cmd:
            print(render_help())
            return True

        parts = raw.strip().split(maxsplit=1)
        args = parts[1] if len(parts) > 1 else ""

        if cmd.name == "help":
            print(render_help(args or None))
            return True

        if cmd.name == "exit":
            print("  Exiting.")
            return False

        if cmd.name == "clear":
            self.agent.messages.clear()
            print("  Conversation cleared.")
            return True

        if cmd.name == "provider":
            if args:
                self.provider = args.split()[0]
            print(f"  provider: {self.provider}")
            return True

        if cmd.name == "model":
            if args:
                self.model = args.split()[0]
            print(f"  model: {self.model}")
            return True

        if cmd.name == "preset":
            key = (args or self.preset).strip()
            if key in PRESETS:
                self.preset = key
                print(f"  preset: {self.preset}")
            else:
                print(f"  Unknown preset: {key}")
            return True

        if cmd.name == "plan":
            out = self.agent.run_plan_then_answer(args or raw.replace("/plan", "", 1),
                                                  provider=self.provider, model=self.model)
            streaming_print(out.response.text, self.provider, self.model)
            return True

        if cmd.name == "system":
            self.sys_prompt = args
            print(f"  System prompt set ({len(self.sys_prompt)} chars)")
            return True

        if cmd.name in {"tools", "yolo"}:
            val = (args or "toggle").strip().lower()
            if cmd.name == "tools":
                self.tools_enabled = not self.tools_enabled if val == "toggle" else val in {"on", "true", "1"}
                print(f"  tools: {self.tools_enabled}")
            else:
                self.yolo = not self.yolo if val == "toggle" else val in {"on", "true", "1"}
                self.agent.yolo = self.yolo
                print(f"  yolo: {self.yolo}")
            return True

        if cmd.name == "commit":
            self._do_auto_commit(args)
            return True

        if cmd.name == "style":
            new_style = (args or "").strip().lower()
            if new_style in {"openclaude", "openmanus"}:
                self.style = new_style
                self.agent.style = new_style
                print(f"  style: {self.style}")
            else:
                print("  Styles: openclaude, openmanus")
            return True

        print(render_help())
        return True

    def _do_auto_commit(self, message: str = ""):
        """Manually trigger auto-commit."""
        from jebat_cli_new.git import auto_commit as do_auto_commit
        msg = message or "JEBAT: manual commit"
        ok, result = do_auto_commit(message=msg)
        if ok:
            TerminalUX.info(f"Committed: {result}")
        else:
            TerminalUX.warn(f"Commit failed: {result}")

    def _call_runtime(self, prompt: str) -> tuple[str, int]:
        """Call the agent runtime."""
        full = prompt
        if self.sys_prompt:
            full = f"SYSTEM: {self.sys_prompt}\nUSER: {full}"
        try:
            out = self.agent.step(full, provider=self.provider, model=self.model, plan=False)

            # Auto-commit after tool calls if enabled
            if self.auto_commit and out.tool_actions:
                self._do_auto_commit(f"JEBAT: {prompt[:80]}")

            return out.response.text, out.response.latency_ms if hasattr(out.response, "latency_ms") else 0
        except Exception as exc:
            return f"[provider error: {exc}]", 0
