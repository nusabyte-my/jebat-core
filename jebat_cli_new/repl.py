"""
JEBAT — interactive REPL with OpenClaude & OpenManus styles.
"""

from __future__ import annotations

import json
from pathlib import Path
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
    def __init__(self, agent: AgentLoop, style: str = "jebat"):
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

    @staticmethod
    def _expand_at_files(raw: str) -> str:
        """Expand @path tokens into file-content context blocks.

        @src/main.py or @"path with spaces.py" inline the file (capped) so the
        model sees the actual source. Missing files are flagged inline, never
        silently dropped.
        """
        import re as _re

        def _sub(m: "_re.Match") -> str:
            quoted = m.group(1)
            path_str = quoted[1:-1] if quoted else m.group(2)
            p = Path(path_str).expanduser()
            if not p.exists():
                return f"@{path_str} [file not found]"
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                return f"@{path_str} [read error: {exc}]"
            lines = text.splitlines()
            cap = 400
            if len(lines) > cap:
                text = "\n".join(lines[:cap]) + f"\n… [truncated {len(lines) - cap} lines]"
            return f"--- file: {p} ---\n{text}\n--- end of {p.name} ---"

        pattern = _re.compile(r'@(?:"([^"]+)"|([\w./\\-]+))')
        return pattern.sub(_sub, raw)

    def start(self):
        """Start the interactive REPL with OMP style."""
        TerminalUX.banner(provider=self.provider, model=self.model)
        TerminalUX.info("Commands: /help, /plan, /provider, /model, /preset, /yolo, /clear, /exit")
        print()
        while True:
            try:
                prompt_str = TerminalUX.prompt_prefix(self.provider, self.model)
                raw = input(prompt_str).rstrip()
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
                expanded = self._expand_at_files(raw)
                text, latency_ms = self._call_runtime(expanded)
                TerminalUX.response_card(text, latency_ms=latency_ms)

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

        if cmd.name == "agentix":
            from jebat_cli_new.agentix import run_agentix_command

            tokens = args.split() if args else ["status"]
            rc = run_agentix_command(tokens)
            if rc == 0:
                # Keep the REPL alive; surface nothing else on success.
                return True
            TerminalUX.warn(f"agentix exited with code {rc}")
            return True

        if cmd.name == "status":
            self._print_status_card()
            return True

        if cmd.name == "import":
            from jebat_cli_new.config_import import run_config_command

            tokens = ["import"] + (args.split() if args else ["--dry-run"])
            rc = run_config_command(tokens)
            if rc != 0:
                TerminalUX.warn(f"import exited with code {rc}")
            return True

        if cmd.name == "init":
            from jebat_cli_new.init_cmd import run_init

            rc = run_init(Path.cwd(), force=False)
            if rc != 0:
                TerminalUX.warn(f"init exited with code {rc}")
            return True

        if cmd.name == "resume":
            from jebat_cli_new.resume import pick, load_by_id
            from jebat_cli_new.agent import AgentMessage

            picked = load_by_id(args.strip()) if args.strip() else pick()
            if not picked:
                return True
            path, msgs = picked
            self.agent.messages.clear()
            self.agent.messages.extend(AgentMessage(role=m["role"], content=m.get("content", "")) for m in msgs)
            TerminalUX.info(f"resumed {path.name} · {len(msgs)} messages")
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
            if new_style in {"jebat", "openmanus"}:
                self.style = new_style
                self.agent.style = new_style
                print(f"  style: {self.style}")
            else:
                print("  Styles: jebat, openmanus")
            return True

        print(render_help())
        return True

    def _print_status_card(self):
        """One-glance session card (omp-style status line, boxed)."""
        from jebat_cli_new.theme import box, C, format_cost

        msgs = len(self.agent.messages)
        lines = [
            f"provider : {self.provider}   model: {self.model}",
            f"preset   : {self.preset}   mode: {self.mode}   tools: {'on' if self.tools_enabled else 'off'}",
            f"yolo     : {'ON — no approvals' if self.yolo else 'off — staged approvals'}   messages: {msgs}",
        ]
        print(box("⚡ session status", "\n".join(lines), width=66, theme="info"))

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
