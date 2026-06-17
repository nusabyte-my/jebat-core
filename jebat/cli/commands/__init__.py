"""
JEBAT CLI Commands — Modular command implementations.

Each command group is in its own module for maintainability.
"""

from __future__ import annotations

import sys
from typing import Any

from jebat.cli.commands.agent_cmd import agent_command
from jebat.cli.commands.agent_def_cmd import agent_def_command
from jebat.cli.commands.benchmark_cmd import benchmark_command
from jebat.cli.commands.byok_cmd import byok_command
from jebat.cli.commands.chat_cmd import chat_command
from jebat.cli.commands.code_index_cmd import code_index_command
from jebat.cli.commands.conversation_cmd import conversation_command
from jebat.cli.commands.gh_cmd import gh_command
from jebat.cli.commands.model_cmd import model_command
from jebat.cli.commands.plugin_cmd import plugin_command
from jebat.cli.commands.telemetry_cmd import telemetry_command
from jebat.cli.commands.tool_gen_cmd import tool_gen_command
from jebat.cli.commands.tools_cmd import tools_command
from jebat.cli.commands.config_cmd import config_command
from jebat.cli.commands.file_cmd import file_command
from jebat.cli.commands.voice_cmd import voice_command
from jebat.cli.commands.repl_cmd import repl_command

# Command registry
COMMANDS = {
    "agent": agent_command,
    "agent-def": agent_def_command,
    "benchmark": benchmark_command,
    "byok": byok_command,
    "chat": chat_command,
    "code-index": code_index_command,
    "config": config_command,
    "conversation": conversation_command,
    "file": file_command,
    "gh": gh_command,
    "model": model_command,
    "plugin": plugin_command,
    "repl": repl_command,
    "telemetry": telemetry_command,
    "tool-gen": tool_gen_command,
    "tools": tools_command,
    "voice": voice_command,
}


def execute_command(command: str, args: Any) -> int:
    """Execute a command by name."""
    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(sorted(COMMANDS.keys()))}")
        return 1

    try:
        handler = COMMANDS[command]
        return handler(args)
    except Exception as e:
        print(f"Error executing {command}: {e}")
        if "--debug" in sys.argv:
            import traceback

            traceback.print_exc()
        return 1