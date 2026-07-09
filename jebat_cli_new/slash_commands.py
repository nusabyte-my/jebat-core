"""
JEBAT — slash commands (OpenClaude-style command palette).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SlashCommand:
    name: str
    aliases: List[str]
    help: str
    usage: str = ""

    def match(self, token: str) -> bool:
        t = token.strip().lower().lstrip("/").split()[0]
        return t == self.name.lower() or t in {a.lower() for a in self.aliases}

    def invoke(self, args: str) -> str:
        return f"{self.name}: {self.help}\nUsage: {self.usage or '/' + self.name}"


COMMANDS = [
    SlashCommand(name="help", aliases=["h", "?"], help="Show this help", usage="[command]"),
    SlashCommand(name="provider", aliases=["prov", "p"], help="Switch provider", usage="<provider>"),
    SlashCommand(name="model", aliases=["m"], help="Switch model", usage="<model>"),
    SlashCommand(name="preset", aliases=["pr"], help="Change preset", usage="fast|deliberate|deep|strategic|creative|critical"),
    SlashCommand(name="tools", aliases=["t"], help="Toggle tool use", usage="on|off"),
    SlashCommand(name="yolo", aliases=["y"], help="Toggle auto-approve tool calls", usage="on|off"),
    SlashCommand(name="commit", aliases=["ci"], help="Auto-commit changes", usage="[message]"),
    SlashCommand(name="exit", aliases=["quit", "q"], help="Exit session"),
    SlashCommand(name="clear", aliases=["reset"], help="Clear conversation history"),
    SlashCommand(name="plan", aliases=["think"], help="Plan-then-answer mode", usage="<task>"),
    SlashCommand(name="rerank", aliases=["r"], help="Rerank last answer"),
    SlashCommand(name="compact", aliases=["c"], help="Compact chat context"),
    SlashCommand(name="system", aliases=["sys"], help="Set system prompt", usage="<prompt>"),
]


def match_command(input_text: str) -> Optional[SlashCommand]:
    if not input_text.strip().startswith("/"):
        return None
    for cmd in COMMANDS:
        if cmd.match(input_text):
            return cmd
    return None


def render_help(topic: Optional[str] = None) -> str:
    if topic:
        cmd = next((c for c in COMMANDS if c.match(f"/{topic}")), None)
        if cmd:
            return cmd.invoke("")
        return f"Unknown command: /{topic}"
    return "Commands:\n" + "\n".join([f"  /{c.name:10} {c.help}" for c in COMMANDS])
