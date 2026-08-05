"""Enhanced CodeAgent CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .enhanced_agent import EnhancedCodeAgent, create_enhanced_agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jebat-code-enhanced",
        description="JEBAT Enhanced Coding Agent — Branch agents, multi-orchestration, spec-driven dev",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Coding prompt (if omitted, runs in interactive mode)",
    )
    parser.add_argument(
        "-p", "--project",
        default=".",
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--provider",
        help="LLM provider override (ollama, anthropic, openai, etc.)",
    )
    parser.add_argument(
        "--model",
        help="Model override (e.g., anthropic/claude-sonnet-4)",
    )
    parser.add_argument(
        "--preset",
        choices=["fast", "deliberate", "deep", "strategic", "creative", "critical"],
        help="Thinking mode preset",
    )
    parser.add_argument(
        "--safety",
        choices=["auto", "confirm", "dangerous"],
        default="auto",
        help="Safety mode for tool execution",
    )
    parser.add_argument(
        "--yolo",
        action="store_true",
        help="Disable confirmations (same as --safety dangerous)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Auto-commit changes after each iteration",
    )
    parser.add_argument(
        "--branch",
        help="Run on a specific branch (creates if not exists)",
    )
    parser.add_argument(
        "--branch-strategy",
        choices=["new_branch", "worktree", "stash", "inline"],
        default="new_branch",
        help="Branch isolation strategy",
    )
    parser.add_argument(
        "--orchestrate",
        help="Orchestration mode: sequential, parallel, consensus, pipeline, competitive",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=25,
        help="Maximum loop iterations",
    )
    parser.add_argument(
        "--token-budget",
        type=int,
        default=100000,
        help="Token budget for the session",
    )
    parser.add_argument(
        "--cost-budget",
        type=float,
        default=5.0,
        help="Cost budget in USD",
    )
    parser.add_argument(
        "--spec",
        help="Implement a spec by ID",
    )
    parser.add_argument(
        "--skill",
        help="Use a skill by ID",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive mode",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="JEBAT Enhanced CodeAgent 1.0.0",
    )
    return parser


async def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_path = Path(args.project).resolve()

    agent = EnhancedCodeAgent(
        project_path=str(project_path),
        provider_override=args.provider,
        model_override=args.model,
        preset=args.preset,
        safety_mode=args.safety,
        yolo=args.yolo,
        stream=not args.no_stream,
        auto_commit=args.auto_commit,
        loop_config=None,  # Will use defaults
    )

    # Apply CLI overrides to loop config
    if args.max_iterations:
        agent.loop_config.max_iterations = args.max_iterations
    if args.token_budget:
        agent.loop_config.token_budget = args.token_budget
    if args.cost_budget:
        agent.loop_config.cost_budget_usd = args.cost_budget

    # Handle spec implementation
    if args.spec:
        await agent.run_prompt(f"/spec implement {args.spec}")
        return 0

    # Handle skill usage
    if args.skill:
        await agent.run_prompt(f"/skill use {args.skill}")
        return 0

    # Handle branch agent
    if args.branch:
        await agent.run_prompt(f"/branch create {args.branch}")
        return 0

    # Handle orchestration mode
    if args.orchestrate:
        # Would set up orchestration plan
        print(f"Orchestration mode: {args.orchestrate}")

    if args.prompt:
        # Single prompt mode
        prompt = " ".join(args.prompt)
        await agent.run_prompt(prompt)
    else:
        # Interactive mode
        await agent.run_interactive()

    return 0


def cli_main() -> int:
    """Entry point for console script."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())