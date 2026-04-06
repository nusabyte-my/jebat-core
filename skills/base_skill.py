"""
Base Skill Framework
Provides the core interface and functionality for all skills in the system.
Skills are reusable components that can be attached to agents to provide specific capabilities.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class SkillType(Enum):
    """Types of skills available"""

    DATA_PROCESSING = "data_processing"
    COMMUNICATION = "communication"
    FILE_OPERATIONS = "file_operations"
    WEB_SCRAPING = "web_scraping"
    API_INTEGRATION = "api_integration"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    DATABASE = "database"
    MACHINE_LEARNING = "machine_learning"
    UTILITY = "utility"


class SkillStatus(Enum):
    """Skill execution status"""

    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class SkillResult:
    """Standard result format for skill operations"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    skill_used: str = ""


@dataclass
class SkillParameter:
    """Parameter definition for skills"""

    name: str
    param_type: type
    required: bool = True
    default: Any = None
    description: str = ""
    validation_func: Optional[callable] = None


class BaseSkill(ABC):
    """
    Abstract base class for all skills.
    Skills are modular capabilities that can be attached to agents.
    """

    def __init__(
        self,
        skill_id: str,
        name: str,
        skill_type: SkillType,
        description: str = "",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the base skill.

        Args:
            skill_id: Unique identifier for the skill
            name: Human-readable name
            skill_type: Type/category of the skill
            description: Description of skill functionality
            version: Skill version
            config: Configuration parameters
        """
        self.skill_id = skill_id
        self.name = name
        self.skill_type = skill_type
        self.description = description
        self.version = version
        self.config = config or {}
        self.status = SkillStatus.READY
        self.logger = self._setup_logging()
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution = None
        self.error_count = 0
        self.dependencies = []

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the skill"""
        logger = logging.getLogger(f"skill_{self.skill_id}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"[{self.name}] %(asctime)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """
        Execute the skill with given parameters.
        Must be implemented by subclasses.

        Args:
            parameters: Input parameters for skill execution

        Returns:
            SkillResult with execution results
        """
        pass

    @abstractmethod
    def get_parameters(self) -> List[SkillParameter]:
        """
        Get list of parameters this skill accepts.
        Must be implemented by subclasses.

        Returns:
            List of SkillParameter objects
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input parameters against skill requirements.

        Args:
            parameters: Parameters to validate

        Returns:
            Validated and processed parameters

        Raises:
            ValueError: If validation fails
        """
        skill_params = self.get_parameters()
        validated = {}

        # Check required parameters
        for param in skill_params:
            if param.required and param.name not in parameters:
                raise ValueError(f"Required parameter '{param.name}' is missing")

            value = parameters.get(param.name, param.default)

            # Type checking
            if value is not None and not isinstance(value, param.param_type):
                try:
                    value = param.param_type(value)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Parameter '{param.name}' must be of type {param.param_type.__name__}"
                    )

            # Custom validation
            if param.validation_func and value is not None:
                if not param.validation_func(value):
                    raise ValueError(
                        f"Parameter '{param.name}' failed custom validation"
                    )

            validated[param.name] = value

        return validated

    async def safe_execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """
        Execute skill with error handling and metrics tracking.

        Args:
            parameters: Input parameters

        Returns:
            SkillResult with execution results
        """
        start_time = time.time()
        self.status = SkillStatus.EXECUTING
        self.logger.info(f"Executing skill: {self.name}")

        try:
            # Validate parameters
            validated_params = self.validate_parameters(parameters)

            # Execute the skill
            result = await self.execute(validated_params)
            result.skill_used = self.name
            result.execution_time = time.time() - start_time

            # Update metrics
            self.execution_count += 1
            self.total_execution_time += result.execution_time
            self.last_execution = datetime.now()
            self.status = SkillStatus.COMPLETED

            self.logger.info(
                f"Skill executed successfully in {result.execution_time:.2f}s"
            )
            return result

        except Exception as e:
            self.error_count += 1
            self.status = SkillStatus.ERROR
            error_msg = f"Skill execution failed: {str(e)}"
            self.logger.error(error_msg)

            return SkillResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time,
                skill_used=self.name,
            )

    def get_info(self) -> Dict[str, Any]:
        """Get skill information and metadata"""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "type": self.skill_type.value,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "avg_execution_time": self.get_average_execution_time(),
            "last_execution": self.last_execution.isoformat()
            if self.last_execution
            else None,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type.__name__,
                    "required": p.required,
                    "description": p.description,
                }
                for p in self.get_parameters()
            ],
            "dependencies": self.dependencies,
        }

    def get_average_execution_time(self) -> float:
        """Calculate average execution time"""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count

    def reset_metrics(self):
        """Reset skill metrics"""
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0
        self.last_execution = None
        self.logger.info("Metrics reset")

    def enable(self):
        """Enable the skill"""
        self.status = SkillStatus.READY
        self.logger.info("Skill enabled")

    def disable(self):
        """Disable the skill"""
        self.status = SkillStatus.DISABLED
        self.logger.info("Skill disabled")

    def is_enabled(self) -> bool:
        """Check if skill is enabled"""
        return self.status != SkillStatus.DISABLED

    def add_dependency(self, dependency: str):
        """Add a dependency requirement"""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)

    def check_dependencies(self, available_skills: List[str]) -> bool:
        """Check if all dependencies are available"""
        return all(dep in available_skills for dep in self.dependencies)

    def export_config(self) -> Dict[str, Any]:
        """Export skill configuration"""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "type": self.skill_type.value,
            "version": self.version,
            "config": self.config,
            "dependencies": self.dependencies,
        }

    def load_config(self, config: Dict[str, Any]):
        """Load skill configuration"""
        self.config.update(config.get("config", {}))
        self.dependencies = config.get("dependencies", [])
        self.logger.info("Configuration loaded")

    def __str__(self) -> str:
        return f"Skill({self.name}, {self.skill_type.value})"

    def __repr__(self) -> str:
        return f"BaseSkill(skill_id='{self.skill_id}', name='{self.name}', type='{self.skill_type.value}')"
