"""Skill registry and execution endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from jebat.skills.base_skill import SkillRegistry
from jebat.skills.built_in_skills import (
    DataAnalyzeSkill,
    MemoryRememberSkill,
    TaskExecuteSkill,
    WebSearchSkill,
)

router = APIRouter(prefix="/api/skills", tags=["skills"])

# Populate registry with built-in skills
_registry = SkillRegistry()
for cls in [WebSearchSkill, DataAnalyzeSkill, TaskExecuteSkill, MemoryRememberSkill]:
    _registry.register_skill(cls)


class SkillExecuteRequest(BaseModel):
    skill_name: str = Field(..., description="Name of the skill to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")


@router.get("")
async def list_skills() -> Dict[str, Any]:
    """List all registered skills."""
    skills = []
    for name in _registry.list_skills():
        meta = _registry.get_skill_metadata(name)
        skills.append(meta or {"name": name})
    return {"skills": skills, "total": len(skills)}


@router.get("/{skill_name}")
async def skill_detail(skill_name: str) -> Dict[str, Any]:
    """Get detailed metadata for a specific skill."""
    meta = _registry.get_skill_metadata(skill_name)
    if not meta:
        return {"error": f"Skill '{skill_name}' not found"}
    return meta


@router.post("/execute")
async def execute_skill(req: SkillExecuteRequest) -> Dict[str, Any]:
    """Execute a registered skill by name."""
    skill = _registry.get_skill(req.skill_name)
    if not skill:
        return {"success": False, "error": f"Skill '{req.skill_name}' not found"}
    result = await skill.execute(**req.parameters)
    return result.to_dict()
