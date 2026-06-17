"""Skill loading, selection, and prompt building for LLM context."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class SkillEntry:
    name: str
    content: str
    tags: List[str] = field(default_factory=list)


class SkillRegistry:
    """Registry of available skills loaded from markdown files."""

    def __init__(self):
        self._skills: Dict[str, SkillEntry] = {}

    def register(self, skill: SkillEntry) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[SkillEntry]:
        return self._skills.get(name)

    def get_all_skills(self) -> List[SkillEntry]:
        return list(self._skills.values())

    def search(self, query: str) -> List[SkillEntry]:
        query_lower = query.lower()
        return [s for s in self._skills.values() if any(t in query_lower for t in s.tags)]


def default_skills_path() -> Path:
    """Return path to the tokguru skills directory."""
    candidate = Path(__file__).parent.parent.parent / "jebat-tokguru" / "skills"
    if candidate.exists():
        return candidate
    # Fallback: create a minimal built-in registry
    return Path("skills")


def build_skill_registry(path: Path) -> SkillRegistry:
    registry = SkillRegistry()

    # Built-in skills
    built_in = [
        SkillEntry(name="python-patterns", content="# Python Patterns\nPython best practices and design patterns.", tags=["python", "patterns", "design"]),
        SkillEntry(name="cortex-reasoning", content="# Cortex Reasoning\nAdvanced reasoning and system design patterns.", tags=["reasoning", "system", "design", "architecture"]),
        SkillEntry(name="jebat-agent", content="# JEBAT Agent\nJEBAT daily coding copilot and agent behavior.", tags=["jebat", "agent", "coding", "copilot"]),
    ]
    for skill in built_in:
        registry.register(skill)

    # Try loading from disk
    if path.exists():
        for md_file in path.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="replace")
            name = md_file.stem
            tags = [word.lower() for word in name.replace("-", " ").split()]
            registry.register(SkillEntry(name=name, content=content, tags=tags))

    return registry


def select_relevant_skills(
    prompt: str,
    registry: SkillRegistry,
    max_skills: int = 3,
) -> List[SkillEntry]:
    prompt_lower = prompt.lower()
    scored: List[Tuple[float, SkillEntry]] = []
    for skill in registry.get_all_skills():
        score = sum(1 for tag in skill.tags if tag in prompt_lower)
        if score > 0:
            scored.append((score, skill))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_skills]]


def build_skill_prompt(
    prompt: str,
    registry: SkillRegistry,
    requested_skills: Optional[List[str]] = None,
    auto_discover: bool = True,
) -> Tuple[str, List[SkillEntry]]:
    selected: List[SkillEntry] = []

    if requested_skills:
        for name in requested_skills:
            skill = registry.get(name)
            if skill:
                selected.append(skill)

    if auto_discover and not selected:
        selected = select_relevant_skills(prompt, registry)

    parts = []
    for skill in selected:
        parts.append(f"Skill: {skill.name}\n{skill.content}")

    return "\n\n".join(parts), selected
