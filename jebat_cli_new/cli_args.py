"""Typed parsing for canonical JEBAT CLI command options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class CodeOptions:
    """Parsed options for the one-shot coding-agent command."""

    prompt_parts: tuple[str, ...]
    provider: str | None = None
    model: str | None = None
    yolo: bool = False
    auto_commit: bool = False
    plan: bool = False


@dataclass(frozen=True, slots=True)
class ChatOptions:
    """Parsed options for the one-shot chat command."""

    prompt_parts: tuple[str, ...]
    provider: str | None = None
    model: str | None = None


def parse_code_options(tokens: Sequence[str]) -> CodeOptions:
    """Parse code command flags while preserving the prompt token order."""
    prompt_parts: list[str] = []
    provider: str | None = None
    model: str | None = None
    yolo = False
    auto_commit = False
    plan = False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--yolo", "--auto-commit", "-a", "--plan"):
            yolo = yolo or token == "--yolo"
            auto_commit = auto_commit or token in ("--auto-commit", "-a")
            plan = plan or token == "--plan"
        elif token in ("--provider", "--model"):
            if index + 1 >= len(tokens):
                raise ValueError(f"{token} requires a value")
            value = tokens[index + 1]
            if token == "--provider":
                provider = value
            else:
                model = value
            index += 1
        else:
            prompt_parts.append(token)
        index += 1
    return CodeOptions(
        prompt_parts=tuple(prompt_parts),
        provider=provider,
        model=model,
        yolo=yolo,
        auto_commit=auto_commit,
        plan=plan,
    )


def parse_chat_options(tokens: Sequence[str]) -> ChatOptions:
    """Parse chat provider and model flags while preserving message words."""
    prompt_parts: list[str] = []
    provider: str | None = None
    model: str | None = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--provider", "--model"):
            if index + 1 >= len(tokens):
                raise ValueError(f"{token} requires a value")
            value = tokens[index + 1]
            if token == "--provider":
                provider = value
            else:
                model = value
            index += 1
        else:
            prompt_parts.append(token)
        index += 1
    return ChatOptions(prompt_parts=tuple(prompt_parts), provider=provider, model=model)
