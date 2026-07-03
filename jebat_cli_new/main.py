#!/usr/bin/env python3
"""
JEBAT CLI — unified entrypoint.

Examples:
  python -m jebat_cli_new code [prompt]
  python -m jebat_cli_new code --auto-commit "Fix the bug"
  python -m jebat_cli_new code --yolo "Refactor this"
  python -m jebat_cli_new chat [prompt]
  python -m jebat_cli_new provider list
  python -m jebat_cli_new provider add openai --id work --api-key sk-...
  python -m jebat_cli_new agent run [prompt]
  python -m jebat_cli_new repl
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from jebat_cli_new.agent import AgentLoop
from jebat_cli_new.models import ProviderConfig
from jebat_cli_new.providers import ProviderRegistry
from jebat_cli_new.ux import TerminalUX


def _default_api_base(kind: str) -> str:
    return {
        "ollama": "http://127.0.0.1:11434",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        "github": "https://models.github.ai/inference",
    }.get(kind, "")


def _default_model(kind: str) -> str:
    return {
        "ollama": "qwen2.5-coder:7b",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.5-pro",
        "github": "openai/gpt-4o-mini",
    }.get(kind, "")


def _run_with_auto_commit(agent: AgentLoop, prompt: str, provider: str, model: str,
                           auto_commit: bool = False, yolo: bool = False,
                           project_path: Optional[str] = None):
    """Run agent step and optionally auto-commit if files were modified."""
    out = agent.step(prompt, provider=provider, model=model)

    # Print response
    print(out.response.text + "\n")

    # Auto-commit if requested and files were modified
    if auto_commit and out.tool_actions:
        from jebat_cli_new.git import auto_commit as do_auto_commit, get_changed_files
        cwd = project_path or "."
        files = get_changed_files(cwd)
        if files:
            TerminalUX.info(f"Auto-committing {len(files)} changed files...")
            ok, msg = do_auto_commit(
                message=f"JEBAT: {prompt[:80]}",
                path=cwd,
            )
            if ok:
                TerminalUX.info(f"Committed: {msg}")
            else:
                TerminalUX.warn(f"Commit failed: {msg}")

    return out


def cmd_code(args, registry: ProviderRegistry):
    provider = args.provider or "ollama"
    model = args.model or "qwen2.5-coder:7b"
    TerminalUX.info(f"code provider={provider} model={model}")

    # Load project context if path provided
    project_context = ""
    project_path = getattr(args, "project_path", None)
    if project_path:
        try:
            from pathlib import Path
            p = Path(project_path)
            if p.is_dir():
                project_context = f"Working directory: {p.absolute()}\n"
                claude_md = p / "CLAUDE.md"
                if claude_md.exists():
                    project_context += claude_md.read_text(encoding="utf-8")[:2000] + "\n"
        except Exception as e:
            TerminalUX.warn(f"Could not load project path: {e}")

    full_prompt = project_context + (args.prompt or "")

    agent = AgentLoop(
        registry,
        default_provider=provider,
        model=model,
        yolo=getattr(args, "yolo", False),
        auto_commit=getattr(args, "auto_commit", False),
    )

    if args.prompt:
        _run_with_auto_commit(
            agent, full_prompt, provider, model,
            auto_commit=getattr(args, "auto_commit", False),
            yolo=getattr(args, "yolo", False),
            project_path=project_path,
        )
    else:
        agent.interactive(provider=provider, model=model)


def cmd_chat(args, registry: ProviderRegistry):
    cmd_code(args, registry)


def cmd_provider(args, registry: ProviderRegistry):
    if args.action == "list":
        for key in registry.providers:
            print(key)
        return
    if args.action == "use":
        target = args.provider
        if target not in registry.configs and target not in registry.providers:
            print(f"Unknown provider: {target}")
            print(f"Available: {', '.join(registry.configs.keys())}")
            sys.exit(1)
        cfg = registry.configs.get(target)
        if cfg:
            print(f"Using provider: {target} (model={cfg.model}, base={cfg.api_base})")
        else:
            print(f"Using provider: {target}")
        return
    if args.action == "add":
        kind = (args.provider or "").strip().lower()
        if kind not in {"ollama", "openai", "anthropic", "gemini", "github"}:
            print("Supported provider kinds: ollama|openai|anthropic|gemini|github")
            return
        provider_id = getattr(args, "provider_id", None) or kind
        config = ProviderConfig(
            id=provider_id,
            name=kind.capitalize(),
            api_base=getattr(args, "api_base", None) or _default_api_base(kind),
            model=getattr(args, "model", None) or _default_model(kind),
            api_key=getattr(args, "api_key", None),
            kind=kind,
        )
        from jebat_cli_new.providers import _provider_factory
        impl = _provider_factory(config, kind)
        registry.register(config.id, impl, cfg=config)
        print(f"Added provider: {config.id} ({kind})")
        return
    raise SystemExit("Use: jebat provider list|use <provider>|add <kind> --id <id>")


def cmd_agent_run(args, registry: ProviderRegistry):
    agent = AgentLoop(
        registry,
        default_provider=args.provider or "ollama",
        model=args.model or "qwen2.5-coder:7b",
        yolo=getattr(args, "yolo", False),
    )
    out = agent.step(args.prompt or "Start.", provider=args.provider, model=args.model)
    print(out.response.text)


def cmd_repl(registry: ProviderRegistry):
    from jebat_cli_new.repl import REPL
    agent = AgentLoop(registry, default_provider="ollama", model="qwen2.5-coder:7b")
    REPL(agent).start()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="jebat", description="JEBAT unified coding-agent CLI v6.1+")
    sub = parser.add_subparsers(dest="command")

    code = sub.add_parser("code", help="Coding agent")
    code.add_argument("prompt", nargs="?")
    code.add_argument("--provider", default="ollama")
    code.add_argument("--model", default="qwen2.5-coder:7b")
    code.add_argument("--project-path", dest="project_path")
    code.add_argument("--yolo", action="store_true", help="Bypass safety confirmations")
    code.add_argument("--safety", default="auto", choices=["auto", "confirm", "off"])
    code.add_argument("--no-stream", action="store_true")
    code.add_argument("--auto-commit", "-a", action="store_true", help="Auto-commit after file changes")
    code.add_argument("--preset", dest="preset", choices=["fast", "deliberate", "deep", "strategic", "creative", "critical"])

    chat = sub.add_parser("chat", help="Chat agent")
    chat.add_argument("prompt", nargs="?")
    chat.add_argument("--provider", default="ollama")
    chat.add_argument("--model", default="qwen2.5-coder:7b")
    chat.add_argument("--preset", dest="preset", choices=["fast", "deliberate", "deep", "strategic", "creative", "critical"])

    prov = sub.add_parser("provider", help="Provider management")
    prov_sub = prov.add_subparsers(dest="action")
    list_p = prov_sub.add_parser("list")
    list_p.add_argument("--json", action="store_true")
    use_p = prov_sub.add_parser("use")
    use_p.add_argument("provider")
    add_p = prov_sub.add_parser("add")
    add_p.add_argument("provider", help="Provider kind: ollama|openai|anthropic|gemini|github")
    add_p.add_argument("--id", dest="provider_id")
    add_p.add_argument("--api-base", dest="api_base")
    add_p.add_argument("--model")
    add_p.add_argument("--api-key", dest="api_key")

    agent_p = sub.add_parser("agent", help="Agent runner")
    agent_sub = agent_p.add_subparsers(dest="action")
    run = agent_sub.add_parser("run")
    run.add_argument("prompt", nargs="?")
    run.add_argument("--provider", default="ollama")
    run.add_argument("--model", default="qwen2.5-coder:7b")
    run.add_argument("--yolo", action="store_true")

    sub.add_parser("repl", help="Interactive REPL")

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)
    registry = ProviderRegistry()

    if args.command == "code":
        cmd_code(args, registry)
    elif args.command == "chat":
        cmd_chat(args, registry)
    elif args.command == "provider":
        cmd_provider(args, registry)
    elif args.command == "agent":
        if args.action == "run":
            cmd_agent_run(args, registry)
        else:
            raise SystemExit("Use: jebat agent run [prompt]")
    elif args.command == "repl":
        cmd_repl(registry)
    else:
        raise SystemExit("Use: jebat code|chat|provider|agent|repl")


if __name__ == "__main__":
    main()
