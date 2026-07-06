#!/usr/bin/env python3
"""
JEBAT CLI — Repo-aware AI Agent Framework.

Modular command system with unified agent runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from jebat.cli.commands import COMMANDS, execute_command
from jebat.config.unified import ensure_config, create_default_config


def build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="jebat",
        description="JEBAT v6.1 — Repo-aware AI Agent Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Core: status, init, loop, think, memory, config, doctor, mode-guide, skills
Chat: chat, chat-project, chat-repl
Ops: file, exec, wiki, agent, search, tools, mcp
Pentest: pentest (quick/standard/full/vuln scan)
Social: social (send/search/timeline), tts
Orchestration: delegate, cron, safety, session
Personal: todo (add/list/remove/update/clear)
Security: auth (keyring/env/enc), sandbox, undo
Dev: git (status/diff/log/commit/blame/stash), coding, review

Run 'jebat <command> --help' for command-specific help.
        """,
    )

    parser.add_argument("--debug", action="store_true", help="Show full traceback on errors")
    parser.add_argument("--version", action="version", version="JEBAT 6.1.0")

    return parser


def add_subcommand_parsers(parser: argparse.ArgumentParser):
    """Add all subcommand parsers."""
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Run a one-shot agent task with tool-calling")
    agent_parser.add_argument("prompt", help="Task prompt")
    agent_parser.add_argument("--provider", help="Override provider")
    agent_parser.add_argument("--model", help="Override model")
    agent_parser.add_argument("--yolo", action="store_true", help="YOLO mode — auto-approve ALL tool calls")
    agent_parser.add_argument("--safety", default="auto", choices=["auto", "confirm", "dangerous"])
    agent_parser.add_argument("--mode", help="Reasoning mode (fast/deliberate/deep/strategic/creative/critical)")
    agent_parser.add_argument("--max-iterations", type=int, default=25)
    agent_parser.add_argument("--session", "-s", help="Resume a specific session by ID")
    agent_parser.add_argument("--stream", action="store_true", help="Stream tokens as they arrive")

    # Agent-def command
    agent_def_parser = subparsers.add_parser("agent-def", help="Custom agent definitions (YAML)")
    agent_def_sub = agent_def_parser.add_subparsers(dest="agent_def_command")
    agent_def_sub.add_parser("list", help="List available agent definitions")
    agent_def_show = agent_def_sub.add_parser("show", help="Show agent definition")
    agent_def_show.add_argument("name", help="Agent name")
    agent_def_create = agent_def_sub.add_parser("create", help="Create new agent definition")
    agent_def_create.add_argument("name", help="Agent name")
    agent_def_create.add_argument("--template", action="store_true", help="Create from template")
    agent_def_create.add_argument("--file", help="Load from YAML file")
    agent_def_run = agent_def_sub.add_parser("run", help="Run an agent")
    agent_def_run.add_argument("name", help="Agent name")
    agent_def_run.add_argument("prompt", help="Prompt to send")
    agent_def_run.add_argument("--model", help="Override model")
    agent_def_delete = agent_def_sub.add_parser("delete", help="Delete agent definition")
    agent_def_delete.add_argument("name", help="Agent name")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with JEBAT using the configured LLM")
    chat_parser.add_argument("prompt", help="Prompt to send")
    chat_parser.add_argument("--provider", help="Override provider")
    chat_parser.add_argument("--model", help="Override model")
    chat_parser.add_argument("--skill", action="append", default=[], help="Force one or more JEBAT skills")
    chat_parser.add_argument("--yolo", action="store_true", help="YOLO mode")
    chat_parser.add_argument("--stream", action="store_true", help="Stream tokens live")

    # Chat-project command
    chat_project_parser = subparsers.add_parser("chat-project", help="Chat with JEBAT using current project context")
    chat_project_parser.add_argument("prompt", help="Prompt to send")
    chat_project_parser.add_argument("--provider", help="Override provider")
    chat_project_parser.add_argument("--model", help="Override model")
    chat_project_parser.add_argument("--skill", action="append", default=[], help="Force one or more JEBAT skills")
    chat_project_parser.add_argument("--yolo", action="store_true", help="YOLO mode")
    chat_project_parser.add_argument("--stream", action="store_true", help="Stream tokens live")

    # REPL command
    repl_parser = subparsers.add_parser("repl", help="Start interactive chat REPL with tool-calling")
    repl_parser.add_argument("--provider", help="Override provider")
    repl_parser.add_argument("--model", help="Override model")
    repl_parser.add_argument("--preset", help="Override preset")
    repl_parser.add_argument("--safety", default="auto", choices=["auto", "confirm", "dangerous"], help="Safety mode")
    repl_parser.add_argument("--yolo", action="store_true", help="YOLO mode — auto-approve ALL tool calls")
    repl_parser.add_argument("--session", "-s", help="Resume a specific session by ID")

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
    code_parser.add_argument("--auto-commit", "-a", action="store_true", help="Auto-commit changes to git")

    # Conversation command
    conv_parser = subparsers.add_parser("conversation", help="Manage persistent chat conversations")
    conv_sub = conv_parser.add_subparsers(dest="conv_command")
    conv_new = conv_sub.add_parser("new", help="Start a new conversation")
    conv_new.add_argument("--title", default="", help="Conversation title")
    conv_new.add_argument("--model", default="", help="Model preference")
    conv_new.add_argument("--system-prompt", default="", help="System prompt")
    conv_sub.add_parser("list", help="List all conversations").add_argument("--limit", type=int, default=20)
    conv_show = conv_sub.add_parser("show", help="Show a conversation with messages")
    conv_show.add_argument("id", type=int, help="Conversation ID")
    conv_send = conv_sub.add_parser("send", help="Send a message to an existing conversation")
    conv_send.add_argument("id", type=int, help="Conversation ID")
    conv_send.add_argument("message", help="Message to send")
    conv_send.add_argument("--model", default="", help="Override model")
    conv_delete = conv_sub.add_parser("delete", help="Delete a conversation")
    conv_delete.add_argument("id", type=int, help="Conversation ID")
    conv_serve = conv_sub.add_parser("serve", help="Start the chat web UI server")
    conv_serve.add_argument("--host", default="127.0.0.1")
    conv_serve.add_argument("--port", type=int, default=8080)
    conv_export = conv_sub.add_parser("export", help="Export a conversation to file")
    conv_export.add_argument("id", type=int)
    conv_export.add_argument("--format", choices=["json", "markdown", "md"], default="json")
    conv_export.add_argument("--output", "-o", help="Output file path")
    conv_search = conv_sub.add_parser("search", help="Search conversations by content")
    conv_search.add_argument("query", help="Search query")
    conv_search.add_argument("--limit", type=int, default=20)
    conv_regen = conv_sub.add_parser("regenerate", help="Regenerate last assistant response")
    conv_regen.add_argument("id", type=int, help="Conversation ID")
    conv_share = conv_sub.add_parser("share", help="Create shareable link for conversation")
    conv_share.add_argument("id", type=int, help="Conversation ID")
    conv_share.add_argument("--expires", help="Expiration date (ISO format)")
    conv_share.add_argument("--max-access", type=int, help="Maximum number of accesses")
    conv_list_share = conv_sub.add_parser("share-list", help="List share tokens for conversation")
    conv_list_share.add_argument("id", type=int, help="Conversation ID")
    conv_delete_share = conv_sub.add_parser("share-delete", help="Delete a share token")
    conv_delete_share.add_argument("id", type=int, help="Conversation ID")
    conv_delete_share.add_argument("token", help="Share token to delete")

    # Model command
    model_parser = subparsers.add_parser("model", help="Manage and select LLM models")
    model_sub = model_parser.add_subparsers(dest="model_command")
    model_list = model_sub.add_parser("list", help="List all registered models")
    model_list.add_argument("--provider", help="Filter by provider")
    model_list.add_argument("--capability", help="Filter by capability")
    model_info = model_sub.add_parser("info", help="Show model details")
    model_info.add_argument("id", help="Model ID")
    model_select = model_sub.add_parser("select", help="Select default model")
    model_select.add_argument("id", help="Model ID")
    model_rec = model_sub.add_parser("recommend", help="Ask the router for a model recommendation")
    model_rec.add_argument("task", help="Task description")
    model_rec.add_argument("--strategy", default="auto", choices=["auto", "cheapest", "fastest", "best_quality", "fallback_chain"])
    model_rec.add_argument("--provider", help="Preferred provider")
    model_test = model_sub.add_parser("test", help="Quick smoke test of a model")
    model_test.add_argument("id", help="Model ID")
    model_test.add_argument("prompt", nargs="?", default="Say hello in one short sentence.", help="Test prompt")
    model_bench = model_sub.add_parser("bench", help="Benchmark LLM models")
    model_bench.add_argument("--prompt", help="Custom prompt to benchmark")
    model_bench.add_argument("--suite", choices=["coding", "reasoning", "creative", "analysis"], default="coding")
    model_bench.add_argument("--models", default="all", help="Model pattern or 'all'")
    model_bench.add_argument("--provider", help="Filter by provider")
    model_bench.add_argument("--iterations", type=int, default=1, help="Runs per prompt")
    model_bench.add_argument("--output", "-o", help="Save results to JSON file")
    tool_market_parser = subparsers.add_parser("tool-market", help="Tool marketplace (install, list, search)")
    tm_sub = tool_market_parser.add_subparsers(dest="tm_command")
    tm_install = tm_sub.add_parser("install", help="Install a tool")
    tm_install.add_argument("--github", help="GitHub repo (owner/repo)")
    tm_install.add_argument("--branch", default="main", help="Branch to install")
    tm_install.add_argument("--subdirectory", default="", help="Subdirectory in repo")
    tm_install.add_argument("--pypi", help="PyPI package name")
    tm_install.add_argument("--version", default="", help="Package version")
    tm_install.add_argument("--local", help="Local directory path")
    tm_list = tm_sub.add_parser("list", help="List available tools")
    tm_list.add_argument("--installed", action="store_true", help="List installed tools only")
    tm_list.add_argument("--tag", help="Filter by tag")
    tm_list.add_argument("--search", help="Search query")
    tm_search = tm_sub.add_parser("search", help="Search tools")
    tm_search.add_argument("query", help="Search query")
    tm_remove = tm_sub.add_parser("remove", help="Remove installed tool")
    tm_remove.add_argument("name", help="Tool name to remove")
    tm_create = tm_sub.add_parser("create", help="Create new tool template")
    tm_create.add_argument("name", help="Tool name")
    tm_create.add_argument("--dir", default="", help="Output directory")

    # BYOK command
    byok_parser = subparsers.add_parser("byok", help="Manage API keys (Bring Your Own Key)")
    byok_sub = byok_parser.add_subparsers(dest="byok_command")
    byok_add = byok_sub.add_parser("add", help="Add an API key")
    byok_add.add_argument("api_key", help="API key to store")
    byok_add.add_argument("--provider", default="", help="Provider name (auto-detected if omitted)")
    byok_add.add_argument("--label", default="", help="Human-friendly label")
    byok_sub.add_parser("list", help="List stored keys")
    byok_remove = byok_sub.add_parser("remove", help="Remove a stored key")
    byok_remove.add_argument("id", help="Key ID to remove")
    byok_test = byok_sub.add_parser("test", help="Test a stored key against its provider")
    byok_test.add_argument("id", help="Key ID to test")
    byok_sub.add_parser("providers", help="List supported providers")

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark and compare LLM models")
    benchmark_parser.add_argument("--models", help="Comma-separated model IDs to benchmark")
    benchmark_parser.add_argument("--category", default="all", choices=["all", "coding", "reasoning", "creative", "analysis", "general"], help="Prompt category")
    benchmark_parser.add_argument("--runs", type=int, default=1, help="Runs per prompt")
    benchmark_parser.add_argument("--max-prompts", type=int, default=10, help="Max prompts per category")
    benchmark_parser.add_argument("--output", "-o", help="Output JSON file")

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="List and inspect registered tools")
    tools_sub = tools_parser.add_subparsers(dest="tools_command")
    tools_list = tools_sub.add_parser("list", help="List all registered tools")
    tools_list.add_argument("--tier", help="Filter by safety tier (auto/confirm/dangerous)")
    tools_inspect = tools_sub.add_parser("inspect", help="Show tool details")
    tools_inspect.add_argument("name", help="Tool name to inspect")

    # GitHub command
    gh_parser = subparsers.add_parser("gh", help="GitHub integration (PRs, issues, CI)")
    gh_sub = gh_parser.add_subparsers(dest="gh_command")
    gh_pr = gh_sub.add_parser("pr", help="Pull request operations")
    gh_pr_sub = gh_pr.add_subparsers(dest="pr_command")
    gh_pr_list = gh_pr_sub.add_parser("list", help="List PRs")
    gh_pr_list.add_argument("--repo", help="Repository (owner/repo)")
    gh_pr_list.add_argument("--state", choices=["open", "closed", "all"], default="open")
    gh_pr_list.add_argument("--limit", type=int, default=20)
    gh_pr_show = gh_pr_sub.add_parser("show", help="Show PR details")
    gh_pr_show.add_argument("number", type=int)
    gh_pr_show.add_argument("--repo", help="Repository (owner/repo)")
    gh_pr_create = gh_pr_sub.add_parser("create", help="Create a PR")
    gh_pr_create.add_argument("title", help="PR title")
    gh_pr_create.add_argument("--body", default="", help="PR body")
    gh_pr_create.add_argument("--head", help="Head branch (default: current)")
    gh_pr_create.add_argument("--base", default="main", help="Base branch")
    gh_pr_create.add_argument("--repo", help="Repository (owner/repo)")
    gh_pr_create.add_argument("--draft", action="store_true", help="Create as draft")
    gh_pr_merge = gh_pr_sub.add_parser("merge", help="Merge a PR")
    gh_pr_merge.add_argument("number", type=int)
    gh_pr_merge.add_argument("--repo", help="Repository (owner/repo)")
    gh_pr_merge.add_argument("--method", choices=["merge", "squash", "rebase"], default="merge")
    gh_issue = gh_sub.add_parser("issue", help="Issue operations")
    gh_issue_sub = gh_issue.add_subparsers(dest="issue_command")
    gh_issue_list = gh_issue_sub.add_parser("list", help="List issues")
    gh_issue_list.add_argument("--repo", help="Repository (owner/repo)")
    gh_issue_list.add_argument("--state", choices=["open", "closed", "all"], default="open")
    gh_issue_list.add_argument("--limit", type=int, default=20)
    gh_issue_show = gh_issue_sub.add_parser("show", help="Show issue details")
    gh_issue_show.add_argument("number", type=int)
    gh_issue_show.add_argument("--repo", help="Repository (owner/repo)")
    gh_issue_create = gh_issue_sub.add_parser("create", help="Create an issue")
    gh_issue_create.add_argument("title", help="Issue title")
    gh_issue_create.add_argument("--body", default="", help="Issue body")
    gh_issue_create.add_argument("--repo", help="Repository (owner/repo)")
    gh_issue_create.add_argument("--labels", help="Comma-separated labels")
    gh_checks = gh_sub.add_parser("checks", help="Check CI status")
    gh_checks.add_argument("--repo", help="Repository (owner/repo)")
    gh_checks.add_argument("--ref", help="Commit ref (default: HEAD)")
    gh_workflows = gh_sub.add_parser("workflows", help="List recent workflow runs")
    gh_workflows.add_argument("--repo", help="Repository (owner/repo)")
    gh_workflows.add_argument("--limit", type=int, default=10)
    gh_repo = gh_sub.add_parser("repo", help="Repository info")
    gh_repo.add_argument("--repo", help="Repository (owner/repo)")
    gh_repo.add_argument("command", nargs="?", choices=["info", "branches", "commits"], default="info")

    # Voice command
    voice_parser = subparsers.add_parser("voice", help="Voice I/O (STT/TTS)")
    voice_subparsers = voice_parser.add_subparsers(dest="voice_command")
    voice_transcribe = voice_subparsers.add_parser("transcribe", help="Transcribe audio file")
    voice_transcribe.add_argument("file", help="Audio file path")
    voice_transcribe.add_argument("--model", default="base", help="Whisper model (tiny/base/small/medium/large)")
    voice_speak = voice_subparsers.add_parser("speak", help="Synthesize speech from text")
    voice_speak.add_argument("text", help="Text to speak")
    voice_speak.add_argument("--voice", default="en-US-AriaNeural", help="TTS voice")
    voice_speak.add_argument("--output", "-o", help="Output audio file")
    voice_chat = voice_subparsers.add_parser("chat", help="Start voice chat (experimental)")
    voice_chat.add_argument("--stt-model", default="base", help="Whisper model (tiny/base/small/medium/large)")
    voice_chat.add_argument("--tts-voice", default="en-US-AriaNeural", help="TTS voice")
    voice_chat.add_argument("--tts-provider", default="edge", help="TTS provider (edge/local)")
    voice_chat.add_argument("--model", help="Override model for agent")

    # Config command with subcommands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_sub = config_parser.add_subparsers(dest="config_command")
    config_sub.add_parser("show", help="Show current configuration")
    config_set = config_sub.add_parser("set", help="Set a configuration value (dot notation)")
    config_set.add_argument("key", help="Config key (e.g., agent.safety_mode)")
    config_set.add_argument("value", help="Config value")
    config_sub.add_parser("reset", help="Reset configuration to defaults")
    config_sub.add_parser("edit", help="Open configuration in $EDITOR")
    config_sub.add_parser("path", help="Show configuration file path")
    config_init = config_sub.add_parser("init", help="Create default configuration file")
    config_init.add_argument("--file", help="Output file path")

    # File command with subcommands
    file_parser = subparsers.add_parser("file", help="File system operations")
    file_sub = file_parser.add_subparsers(dest="file_command")
    file_read = file_sub.add_parser("read", help="Read a file with line numbers")
    file_read.add_argument("path", help="Path to the file")
    file_read.add_argument("--offset", "-o", type=int, default=1, help="Starting line (1-indexed)")
    file_read.add_argument("--limit", "-l", type=int, default=500, help="Max lines to read")
    file_write = file_sub.add_parser("write", help="Write content to a file (overwrites)")
    file_write.add_argument("path", help="Path to the file")
    file_write.add_argument("content", nargs="?", default="", help="Content to write (or use --file)")
    file_write.add_argument("--file", "-f", help="Read content from file")
    file_write.add_argument("--force", action="store_true", help="Overwrite without warning")
    file_patch = file_sub.add_parser("patch", help="Find and replace text in a file")
    file_patch.add_argument("path", help="Path to the file")
    file_patch.add_argument("old_string", help="Text to find")
    file_patch.add_argument("new_string", help="Replacement text")
    file_patch.add_argument("--replace-all", action="store_true", help="Replace all occurrences")
    file_search = file_sub.add_parser("search", help="Search file contents or find files by name")
    file_search.add_argument("pattern", help="Search pattern (regex for content, glob for files)")
    file_search.add_argument("--path", "-p", default=".", help="Directory to search")
    file_search.add_argument("--file-glob", "-g", help="Filter by file pattern (e.g. *.py)")
    file_search.add_argument("--target", choices=["content", "files"], default="content", help="Target type")
    file_search.add_argument("--limit", "-l", type=int, default=50, help="Max results")
    file_undo = file_sub.add_parser("undo", help="Restore a file from backup")
    file_undo.add_argument("path", help="Path to the file")
    file_tree = file_sub.add_parser("tree", help="Show directory tree")
    file_tree.add_argument("--path", "-p", default=".", help="Directory path")
    file_tree.add_argument("--depth", "-d", type=int, default=3, help="Max depth")
    file_tree.add_argument("--gitignore", action="store_true", default=True, help="Respect .gitignore (default)")
    file_tree.add_argument("--no-gitignore", action="store_false", dest="gitignore", help="Don't respect .gitignore")

    # Pentest command with subcommands
    pentest_parser = subparsers.add_parser("pentest", help="Pentesting automation — scan targets, generate vulnerability reports")
    pentest_parser.add_argument("-t", "--target", help="Target domain, IP, or URL")
    pentest_parser.add_argument("-s", "--scan", default="quick", choices=["quick", "standard", "full", "vuln"], help="Scan profile (default: quick)")
    pentest_parser.add_argument("-v", "--verbose", action="store_true", help="Show scan progress")
    pentest_parser.add_argument("-o", "--output", default="report", choices=["report", "json", "both"], help="Output format (default: report)")
    pentest_parser.add_argument("--list-profiles", action="store_true", help="List available scan profiles")
    pentest_parser.add_argument("--shodan-key", help="Shodan API key for enhanced recon")
    pentest_parser.add_argument("--orchestrate", action="store_true", help="Enable agent-based orchestrated analysis")

    # Catalyst command with subcommands
    catalyst_parser = subparsers.add_parser("catalyst", help="Inference.net Catalyst — tracing, gateway, signals, evals, training")
    catalyst_sub = catalyst_parser.add_subparsers(dest="catalyst_command")
    catalyst_sub.add_parser("status", help="Check Catalyst integration status")
    catalyst_init = catalyst_sub.add_parser("init", help="Initialize Catalyst with API key")
    catalyst_init.add_argument("--api-key", help="Inference.net API key")
    catalyst_init.add_argument("--project-id", help="Inference.net project ID")
    catalyst_init.add_argument("--gateway", action="store_true", help="Enable Gateway routing")
    catalyst_init.add_argument("--sample-rate", type=float, default=1.0, help="Trace sample rate (0.0-1.0)")
    catalyst_sub.add_parser("instrument", help="Auto-instrument JEBAT agent loop")
    catalyst_trace = catalyst_sub.add_parser("trace", help="Create a trace span")
    catalyst_trace.add_argument("name", help="Trace span name")
    catalyst_trace.add_argument("--attrs", help="JSON attributes")
    catalyst_eval = catalyst_sub.add_parser("eval", help="Run evaluation")
    catalyst_eval.add_argument("--dataset", help="Dataset ID")
    catalyst_eval.add_argument("--models", nargs="+", help="Model IDs to evaluate")
    catalyst_train = catalyst_sub.add_parser("train", help="Train custom model")
    catalyst_train.add_argument("--name", required=True, help="Training job name")
    catalyst_train.add_argument("--dataset", required=True, help="Dataset ID")
    catalyst_train.add_argument("--base-model", required=True, help="Base model")
    catalyst_halo = catalyst_sub.add_parser("halo", help="Run HALO analysis on traces")
    catalyst_halo.add_argument("traces", nargs="+", help="Trace IDs to analyze")
    catalyst_halo.add_argument("--type", default="full", choices=["full", "prompt", "tool", "reasoning"])

    # Ghost command with subcommands
    ghost_parser = subparsers.add_parser("ghost", help="Ghost database — unlimited Postgres with forking, MCP")
    ghost_sub = ghost_parser.add_subparsers(dest="ghost_command")
    ghost_sub.add_parser("status", help="Check Ghost CLI availability")
    ghost_sub.add_parser("list", help="List all Ghost databases")
    ghost_create = ghost_sub.add_parser("create", help="Create a new database")
    ghost_create.add_argument("name", help="Database name")
    ghost_create.add_argument("--dedicated", action="store_true", help="Create as dedicated database")
    ghost_fork = ghost_sub.add_parser("fork", help="Fork a database")
    ghost_fork.add_argument("source", help="Source database name")
    ghost_fork.add_argument("name", help="New database name")
    ghost_fork.add_argument("--dedicated", action="store_true", help="Create fork as dedicated")
    ghost_delete = ghost_sub.add_parser("delete", help="Delete a database")
    ghost_delete.add_argument("name", help="Database name")
    ghost_delete.add_argument("--force", action="store_true", help="Force delete")
    ghost_sql = ghost_sub.add_parser("sql", help="Execute SQL query")
    ghost_sql.add_argument("database", help="Database name")
    ghost_sql.add_argument("query", help="SQL query")
    ghost_sub.add_parser("pause", help="Pause a database")
    ghost_sub.add_parser("resume", help="Resume a database")
    ghost_workspace = ghost_sub.add_parser("workspace", help="Create agent workspace")
    ghost_workspace.add_argument("agent", help="Agent name")
    ghost_workspace.add_argument("task", help="Task name")
    ghost_workspace.add_argument("--base", help="Base database to fork from")
    ghost_checkpoint = ghost_sub.add_parser("checkpoint", help="Create checkpoint")
    ghost_checkpoint.add_argument("source", help="Source database")
    ghost_checkpoint.add_argument("name", help="Checkpoint name")
    ghost_cleanup = ghost_sub.add_parser("cleanup", help="Clean old workspaces")
    ghost_cleanup.add_argument("--prefix", default="agent-", help="Prefix to match")
    ghost_cleanup.add_argument("--hours", type=int, default=24, help="Older than hours")
    ghost_cleanup.add_argument("--dry-run", action="store_true", default=True, help="Dry run")

    # Other commands
    subparsers.add_parser("cron", help="Scheduled task management")
    subparsers.add_parser("delegate", help="Multi-agent task delegation")

    # Plugin command with subcommands
    plugin_parser = subparsers.add_parser("plugin", help="Plugin management")
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_command")
    plugin_sub.add_parser("discover", help="Discover available plugins (local + pip)")
    plugin_sub.add_parser("list", help="List loaded plugins")
    plugin_load = plugin_sub.add_parser("load", help="Load a plugin")
    plugin_load.add_argument("name", help="Plugin name")
    plugin_load.add_argument("--source", choices=["local", "pip", "git"], default="local")
    plugin_unload = plugin_sub.add_parser("unload", help="Unload a plugin")
    plugin_unload.add_argument("name", help="Plugin name")
    plugin_install_git = plugin_sub.add_parser("install-git", help="Install plugin from Git repository")
    plugin_install_git.add_argument("repo_url", help="Git repository URL")
    plugin_install_git.add_argument("--name", help="Plugin name (optional)")
    plugin_install_pip = plugin_sub.add_parser("install-pip", help="Install plugin from pip")
    plugin_install_pip.add_argument("package", help="Pip package name")
    plugin_uninstall = plugin_sub.add_parser("uninstall", help="Uninstall a plugin")
    plugin_uninstall.add_argument("name", help="Plugin name")
    plugin_uninstall.add_argument("--source", choices=["local", "pip"], default="local")
    plugin_sub.add_parser("tools", help="List plugin system tools")

    subparsers.add_parser("search", help="Web search")
    subparsers.add_parser("session", help="Session management")
    subparsers.add_parser("status", help="System status")
    subparsers.add_parser("think", help="Thinking session")
    subparsers.add_parser("undo", help="Undo/rollback file changes")
    subparsers.add_parser("wiki", help="Wiki knowledge base")
    subparsers.add_parser("social", help="Social media integration")
    subparsers.add_parser("skills", help="TokGuru skills management")
    subparsers.add_parser("orchestrate", help="Multi-agent orchestration")
    subparsers.add_parser("sandbox", help="Docker sandbox for code execution")

    return parser


def main():
    """Main entry point."""
    # Ensure config exists
    from jebat.config.unified import ensure_config
    ensure_config()

    parser = build_parser()
    add_subcommand_parsers(parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    try:
        from jebat.cli.commands import execute_command
        return execute_command(args.command, args)
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())