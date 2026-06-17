"""Base skill framework with registry, parameters, and execution support."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type


@dataclass
class SkillParameter:
    name: str = ""
    type: type = str
    description: str = ""
    required: bool = False
    default: Any = None
    min_value: Any = None
    max_value: Any = None

    def validate(self, value: Any) -> bool:
        if not isinstance(value, self.type):
            try:
                value = self.type(value)
            except (ValueError, TypeError):
                return False
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True


@dataclass
class SkillCapability:
    name: str = ""
    description: str = ""
    enabled: bool = True


@dataclass
class SkillResult:
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "cached": self.cached,
        }


class BaseSkill:
    """Base class for all JEBAT skills."""

    name: str = "base_skill"
    skill_type: str = "custom"
    description: str = ""
    version: str = "1.0.0"
    timeout_seconds: int = 30
    max_retries: int = 0
    parameters: List[SkillParameter] = field(default_factory=list)
    capabilities: List[SkillCapability] = field(default_factory=list)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    async def execute(self, **kwargs: Any) -> SkillResult:
        return SkillResult(success=True, data={})

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.skill_type,
            "description": self.description,
            "version": self.version,
            "parameters": len(self.parameters),
            "capabilities": len(self.capabilities),
        }


class SkillRegistry:
    """Registry for managing and discovering skills."""

    def __init__(self):
        self._skills: Dict[str, Type[BaseSkill]] = {}
        self._instances: Dict[str, BaseSkill] = {}

    def register_skill(self, skill_class: Type[BaseSkill]) -> None:
        instance = skill_class()
        self._skills[instance.name] = skill_class
        self._instances[instance.name] = instance

    def get_skill_class(self, name: str) -> Optional[Type[BaseSkill]]:
        return self._skills.get(name)

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        return self._instances.get(name)

    def list_skills(self) -> List[str]:
        return list(self._skills.keys())

    def get_skill_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        instance = self._instances.get(name)
        return instance.get_metadata() if instance else None

    def get_all_skills(self) -> List[BaseSkill]:
        return list(self._instances.values())


def skill(cls: Type[BaseSkill]) -> Type[BaseSkill]:
    """Decorator to register a skill class."""
    return cls
