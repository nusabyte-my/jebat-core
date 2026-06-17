"""Project context collector for LLM context injection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .tldr_context import build_tldr_summary

@dataclass
class ProjectContext:
    summary: str
    files: list


def build_project_context(root: Path) -> ProjectContext:
    files = []
    summary_parts = []
    for item in sorted(root.iterdir()):
        if item.is_file() and item.suffix in (".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt"):
            files.append(str(item.name))
            summary_parts.append(item.name)
    return ProjectContext(summary=" | ".join(summary_parts), files=files)
