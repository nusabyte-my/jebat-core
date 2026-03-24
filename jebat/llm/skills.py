from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from jebat.mcp.skill_registry import Skill, SkillRegistry


@dataclass(frozen=True, slots=True)
class SelectedSkill:
    name: str
    category: str
    description: str
    source_path: str
    content: str
    score: int = 0


def default_skills_path() -> Path:
    configured = os.getenv("JEBAT_SKILLS_PATH")
    if configured:
        return Path(configured).expanduser()
    repo_path = Path(__file__).resolve().parents[2] / "jebat-tokguru"
    if repo_path.exists():
        return repo_path
    return Path("~/.jebat/tokguru").expanduser()


def build_skill_registry(skills_path: str | Path | None = None) -> SkillRegistry:
    return SkillRegistry(str(skills_path or default_skills_path()), auto_load=True)


def summarize_skill(skill: Skill) -> dict[str, str]:
    return {
        "name": skill.name,
        "category": skill.category,
        "description": skill.description,
        "path": skill.path,
    }


def select_relevant_skills(
    prompt: str,
    registry: SkillRegistry | None = None,
    requested_skills: Iterable[str] | None = None,
    limit: int = 3,
    auto_discover: bool = True,
) -> list[SelectedSkill]:
    active_registry = registry or build_skill_registry()
    selected: list[SelectedSkill] = []
    seen: set[str] = set()

    for name in requested_skills or ():
        skill = active_registry.get_skill(name)
        if not skill:
            continue
        selected.append(_convert_skill(skill, score=10_000))
        seen.add(skill.name)

    if not auto_discover:
        return selected[:limit]

    prompt_tokens = set(_tokenize(prompt))
    scored: list[SelectedSkill] = []
    for skill in active_registry.get_all_skills():
        if skill.name in seen:
            continue
        haystack = " ".join(
            [
                skill.name,
                skill.description,
                skill.category,
                " ".join(skill.tags),
                skill.content[:500],
            ]
        ).lower()
        score = 0
        for token in prompt_tokens:
            if token in haystack:
                score += 1
        if score > 0:
            scored.append(_convert_skill(skill, score=score))

    scored.sort(key=lambda item: (-item.score, item.name))
    selected.extend(scored[: max(0, limit - len(selected))])
    return selected[:limit]


def build_skill_prompt(
    prompt: str,
    registry: SkillRegistry | None = None,
    requested_skills: Iterable[str] | None = None,
    limit: int = 3,
    auto_discover: bool = True,
) -> tuple[str, list[SelectedSkill]]:
    selected = select_relevant_skills(
        prompt=prompt,
        registry=registry,
        requested_skills=requested_skills,
        limit=limit,
        auto_discover=auto_discover,
    )
    if not selected:
        return prompt, []

    skill_sections = []
    for skill in selected:
        body = skill.content.strip()
        if len(body) > 1200:
            body = body[:1200].rstrip() + "\n..."
        skill_sections.append(
            "\n".join(
                [
                    f"Skill: {skill.name}",
                    f"Category: {skill.category}",
                    f"Description: {skill.description}",
                    "Guidance:",
                    body,
                ]
            )
        )

    enriched_prompt = (
        "Apply the following JEBAT skills when answering.\n\n"
        + "\n\n".join(skill_sections)
        + "\n\nUser request:\n"
        + prompt
    )
    return enriched_prompt, selected


def _convert_skill(skill: Skill, score: int) -> SelectedSkill:
    return SelectedSkill(
        name=skill.name,
        category=skill.category,
        description=skill.description,
        source_path=skill.path,
        content=skill.content,
        score=score,
    )


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9_-]{3,}", text.lower()) if token]
