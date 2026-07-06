# ==================== JEBAT AI System - Base Skill Class ====================
# Version: 1.0.0
# Base skill class with abstract methods and skill interface
#
# This module provides the foundation for all skills in the JEBAT system:
# - Abstract base class for skill implementation
# - Skill interface with required methods
# - Skill metadata and configuration management
# - Skill execution with error recovery and retry logic
# - Skill capabilities and parameter validation
# - Integration with database, cache, and enhanced systems
# - Performance tracking and metrics collection

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from ..database.models import Skill, SkillExecution, User
from ..database.repositories import SkillExecutionRepository, SkillRepository

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for skill classes
S = TypeVar("S", bound="BaseSkill")


class SkillStatus(str, Enum):
    """Skill execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SkillParameter:
    """
    Skill parameter definition for validation and documentation.

    Attributes:
        name: Parameter name
        type: Parameter type (str, int, float, bool, list, dict)
        description: Parameter description
        required: Whether parameter is required
        default: Default value (optional)
        min_value: Minimum value for numeric parameters (optional)
        max_value: Maximum value for numeric parameters (optional)
        allowed_values: List of allowed values for enum-like parameters (optional)
    """

    name: str
    type: Type[Union[str, int, float, bool, list, dict]]
    description: str
    required: bool = False
    default: Optional[Any] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None

    def validate(self, value: Any) -> bool:
        """
        Validate a parameter value.

        Args:
            value: Value to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Check required
        if self.required and value is None:
            return False

        # Check type
        if value is not None and not isinstance(value, self.type):
            return False

        # Check numeric constraints
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False

        # Check allowed values
        if self.allowed_values is not None and value not in self.allowed_values:
            return False

        return True


@dataclass
class SkillCapability:
    """
    Skill capability definition.

    Attributes:
        name: Capability name
        description: Capability description
        enabled: Whether capability is enabled
    """

    name: str
    description: str
    enabled: bool = True


@dataclass
class SkillResult:
    """
    Result of skill execution.

    Attributes:
        success: Whether execution was successful
        data: Result data
        error: Error message (if execution failed)
        execution_time_ms: Execution time in milliseconds
        metadata: Additional metadata about the result
        cached: Whether result was retrieved from cache
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
            "cached": self.cached,
        }


class BaseSkill(ABC):
    """
    Abstract base class for all skills in the JEBAT system.

    All skills must inherit from this class and implement the abstract methods.
    Provides common functionality for skill execution, validation, and tracking.

    Attributes:
        name: Skill name
        skill_type: Skill type (search, analyze, execute, remember, custom)
        description: Skill description
        version: Skill version
        author: Skill author
        parameters: List of skill parameters
        capabilities: List of skill capabilities
        timeout_seconds: Default timeout in seconds
        max_retries: Maximum number of retries
        enabled: Whether skill is enabled
    """

    # Class-level attributes (can be overridden in subclasses)
    name: str = "base_skill"
    skill_type: str = "custom"
    description: str = "Base skill class - not intended for direct use"
    version: str = "1.0.0"
    author: str = "JEBAT Development Team"
    timeout_seconds: int = 300
    max_retries: int = 3
    enabled: bool = True

    # Parameters and capabilities (to be defined in subclasses)
    parameters: List[SkillParameter] = []
    capabilities: List[SkillCapability] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize skill with configuration.

        Args:
            config: Skill configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"skill.{self.name}")
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_execution_time_ms = 0

        # Database repositories (injected after skill creation)
        self.skill_repo: Optional[SkillRepository] = None
        self.skill_execution_repo: Optional[SkillExecutionRepository] = None

        # Cache manager (injected after skill creation)
        self.cache_manager: Optional[Any] = None

        # Error recovery system (injected after skill creation)
        self.error_recovery: Optional[Any] = None

        self.logger.info(
            f"Initialized skill '{self.name}' (version {self.version}) with config: {self.config}"
        )

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill with given parameters.

        This is the main method that subclasses must implement.
        Should return a SkillResult with success status and data/error.

        Args:
            **kwargs: Skill parameters

        Returns:
            SkillResult: Result of skill execution
        """
        pass

    async def validate_parameters(
        self, parameters: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate skill parameters.

        Args:
            parameters: Dictionary of parameters to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check for required parameters
        for param in self.parameters:
            if param.required and param.name not in parameters:
                return False, f"Required parameter '{param.name}' is missing"

            # Validate parameter value
            if param.name in parameters:
                value = parameters[param.name]
                if not param.validate(value):
                    return (
                        False,
                        f"Parameter '{param.name}' is invalid: expected type {param.type.__name__}",
                    )

        # Check for unknown parameters
        param_names = {p.name for p in self.parameters}
        for param_name in parameters.keys():
            if param_name not in param_names:
                self.logger.warning(
                    f"Unknown parameter '{param_name}' provided to skill '{self.name}'"
                )

        return True, None

    async def execute_with_retry(
        self,
        skill_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> SkillResult:
        """
        Execute skill with retry logic and error recovery.

        Args:
            skill_id: Skill ID (for database tracking)
            agent_id: Agent ID executing the skill
            task_id: Task ID associated with execution
            user_id: User ID requesting execution
            **kwargs: Skill parameters

        Returns:
            SkillResult: Result of skill execution
        """
        start_time = datetime.now(timezone.utc)
        last_result = None
        last_error = None

        # Validate parameters
        is_valid, error_msg = await self.validate_parameters(kwargs)
        if not is_valid:
            self.logger.error(f"Parameter validation failed: {error_msg}")
            return SkillResult(
                success=False,
                error=f"Parameter validation failed: {error_msg}",
                execution_time_ms=0,
            )

        # Check cache
        cache_key = self._get_cache_key(**kwargs)
        if self.cache_manager:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self.logger.info(
                    f"Cache hit for skill '{self.name}' with key: {cache_key}"
                )
                return SkillResult(
                    success=True,
                    data=cached_result,
                    execution_time_ms=0,
                    cached=True,
                )

        # Execute with retry logic
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Executing skill '{self.name}' (attempt {attempt + 1}/{self.max_retries})"
                )
                self._execution_count += 1

                result = await asyncio.wait_for(
                    self.execute(**kwargs),
                    timeout=self.timeout_seconds,
                )

                # Update statistics
                execution_time_ms = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                )
                self._total_execution_time_ms += execution_time_ms
                result.execution_time_ms = execution_time_ms

                if result.success:
                    self._success_count += 1

                    # Cache successful result
                    if self.cache_manager and result.data is not None:
                        await self.cache_manager.set(
                            cache_key,
                            result.data,
                            ttl=300,  # 5 minutes default TTL
                        )

                    # Log execution to database
                    await self._log_execution(
                        skill_id=skill_id,
                        agent_id=agent_id,
                        task_id=task_id,
                        user_id=user_id,
                        input_parameters=kwargs,
                        output_results=result.to_dict(),
                        execution_time_ms=execution_time_ms,
                        status="success",
                    )

                    return result
                else:
                    self._error_count += 1
                    last_result = result
                    last_error = result.error

                    # Log error execution to database
                    await self._log_execution(
                        skill_id=skill_id,
                        agent_id=agent_id,
                        task_id=task_id,
                        user_id=user_id,
                        input_parameters=kwargs,
                        output_results=result.to_dict(),
                        execution_time_ms=execution_time_ms,
                        status="error",
                        error_message=result.error,
                    )

                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        delay = 2**attempt
                        self.logger.warning(
                            f"Skill execution failed, retrying in {delay}s: {result.error}"
                        )
                        await asyncio.sleep(delay)

            except asyncio.TimeoutError:
                self._error_count += 1
                error_msg = (
                    f"Skill execution timed out after {self.timeout_seconds} seconds"
                )
                self.logger.error(error_msg)

                await self._log_execution(
                    skill_id=skill_id,
                    agent_id=agent_id,
                    task_id=task_id,
                    user_id=user_id,
                    input_parameters=kwargs,
                    output_results=None,
                    execution_time_ms=self.timeout_seconds * 1000,
                    status="timeout",
                    error_message=error_msg,
                )

                last_error = error_msg

            except Exception as e:
                self._error_count += 1
                error_msg = f"Skill execution failed with exception: {str(e)}"
                self.logger.exception(error_msg)

                execution_time_ms = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                )

                await self._log_execution(
                    skill_id=skill_id,
                    agent_id=agent_id,
                    task_id=task_id,
                    user_id=user_id,
                    input_parameters=kwargs,
                    output_results=None,
                    execution_time_ms=execution_time_ms,
                    status="error",
                    error_message=error_msg,
                )

                last_error = error_msg

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = 2**attempt
                    self.logger.warning(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        # All retries failed
        return SkillResult(
            success=False,
            error=last_error or "All retry attempts failed",
            execution_time_ms=int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            ),
        )

    def _get_cache_key(self, **kwargs) -> str:
        """
        Generate cache key from parameters.

        Args:
            **kwargs: Skill parameters

        Returns:
            str: Cache key
        """
        import hashlib
        import json

        # Sort parameters for consistent key generation
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        hash_obj = hashlib.md5(param_str.encode())
        return f"skill:{self.name}:{hash_obj.hexdigest()}"

    async def _log_execution(
        self,
        skill_id: Optional[str],
        agent_id: Optional[str],
        task_id: Optional[str],
        user_id: Optional[str],
        input_parameters: Dict[str, Any],
        output_results: Optional[Dict[str, Any]],
        execution_time_ms: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log skill execution to database.

        Args:
            skill_id: Skill ID
            agent_id: Agent ID
            task_id: Task ID
            user_id: User ID
            input_parameters: Input parameters
            output_results: Output results
            execution_time_ms: Execution time
            status: Execution status
            error_message: Error message (if any)
        """
        if not self.skill_execution_repo:
            return

        try:
            await self.skill_execution_repo.create(
                skill_id=skill_id,
                agent_id=agent_id,
                task_id=task_id,
                user_id=user_id,
                input_parameters=input_parameters,
                output_results=output_results,
                execution_time_ms=execution_time_ms,
                status=status,
                error_message=error_message,
            )
        except Exception as e:
            self.logger.error(f"Failed to log skill execution: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get skill execution statistics.

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        avg_execution_time = (
            self._total_execution_time_ms / self._execution_count
            if self._execution_count > 0
            else 0
        )

        success_rate = (
            (self._success_count / self._execution_count * 100)
            if self._execution_count > 0
            else 0
        )

        return {
            "skill_name": self.name,
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": success_rate,
            "avg_execution_time_ms": avg_execution_time,
            "total_execution_time_ms": self._total_execution_time_ms,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get skill metadata.

        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        return {
            "name": self.name,
            "type": self.skill_type,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "parameters": [p.__dict__ for p in self.parameters],
            "capabilities": [c.__dict__ for c in self.capabilities],
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "enabled": self.enabled,
            "statistics": self.get_statistics(),
        }

    async def warmup(self) -> None:
        """
        Perform skill warmup.

        Override this method to perform any initialization
        that should happen before the skill is used.
        """
        pass

    async def cleanup(self) -> None:
        """
        Perform skill cleanup.

        Override this method to perform any cleanup
        that should happen when the skill is no longer needed.
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"BaseSkill(name='{self.name}', type='{self.skill_type}', version='{self.version}')"

    def __str__(self) -> str:
        """String representation."""
        return self.__repr__()


# ==================== Skill Registry ====================


class SkillRegistry:
    """
    Central registry for all skills in the JEBAT system.

    Manages skill registration, lookup, and lifecycle.
    """

    def __init__(self):
        """Initialize skill registry."""
        self._skills: Dict[str, Type[BaseSkill]] = {}
        self._instances: Dict[str, BaseSkill] = {}
        self.logger = logging.getLogger(__name__)

    def register_skill(self, skill_class: Type[BaseSkill]) -> None:
        """
        Register a skill class.

        Args:
            skill_class: Skill class to register
        """
        if not issubclass(skill_class, BaseSkill):
            raise ValueError(f"Skill class must inherit from BaseSkill")

        skill_name = skill_class.name
        self._skills[skill_name] = skill_class
        self.logger.info(
            f"Registered skill '{skill_name}' (class: {skill_class.__name__})"
        )

    def unregister_skill(self, skill_name: str) -> None:
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to unregister
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            self.logger.info(f"Unregistered skill '{skill_name}'")

    def get_skill_class(self, skill_name: str) -> Optional[Type[BaseSkill]]:
        """
        Get registered skill class by name.

        Args:
            skill_name: Name of skill

        Returns:
            Optional[Type[BaseSkill]]: Skill class or None if not found
        """
        return self._skills.get(skill_name)

    async def create_skill_instance(
        self, skill_name: str, config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseSkill]:
        """
        Create skill instance.

        Args:
            skill_name: Name of skill
            config: Skill configuration

        Returns:
            Optional[BaseSkill]: Skill instance or None if not found
        """
        skill_class = self.get_skill_class(skill_name)
        if not skill_class:
            self.logger.error(f"Skill '{skill_name}' not found in registry")
            return None

        instance = skill_class(config)
        self._instances[skill_name] = instance

        # Warmup skill
        await instance.warmup()

        self.logger.info(f"Created skill instance '{skill_name}'")
        return instance

    async def get_skill_instance(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Get or create skill instance.

        Args:
            skill_name: Name of skill

        Returns:
            Optional[BaseSkill]: Skill instance or None if not found
        """
        if skill_name in self._instances:
            return self._instances[skill_name]

        return await self.create_skill_instance(skill_name)

    def list_skills(self) -> List[str]:
        """
        List all registered skill names.

        Returns:
            List[str]: List of skill names
        """
        return list(self._skills.keys())

    def get_skill_metadata(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        Get skill metadata.

        Args:
            skill_name: Name of skill

        Returns:
            Optional[Dict[str, Any]]: Skill metadata or None if not found
        """
        skill_class = self.get_skill_class(skill_name)
        if not skill_class:
            return None

        # Create temporary instance to get metadata
        instance = skill_class()
        return instance.get_metadata()

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all registered skills.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of skill metadata
        """
        metadata = {}
        for skill_name in self.list_skills():
            metadata[skill_name] = self.get_skill_metadata(skill_name) or {}

        return metadata

    async def cleanup(self) -> None:
        """Cleanup all skill instances."""
        for skill_name, instance in self._instances.items():
            try:
                await instance.cleanup()
                self.logger.info(f"Cleaned up skill '{skill_name}'")
            except Exception as e:
                self.logger.error(f"Error cleaning up skill '{skill_name}': {e}")

        self._instances.clear()


# ==================== Global Skill Registry ====================

# Global instance of skill registry
_global_registry = SkillRegistry()


def get_global_registry() -> SkillRegistry:
    """
    Get global skill registry instance.

    Returns:
        SkillRegistry: Global registry instance
    """
    return _global_registry


def register_skill(skill_class: Type[BaseSkill]) -> None:
    """
    Register a skill class with the global registry.

    Args:
        skill_class: Skill class to register
    """
    _global_registry.register_skill(skill_class)


# ==================== Skill Decorator ====================


def skill(cls: Type[BaseSkill]) -> Type[BaseSkill]:
    """
    Decorator to automatically register a skill class.

    Usage:
        @skill
        class MySkill(BaseSkill):
            name = "my_skill"
            ...

    Args:
        cls: Skill class to decorate

    Returns:
        Type[BaseSkill]: The decorated class
    """
    register_skill(cls)
    return cls


# ==================== Example Usage ====================


# Example skill
@skill
class ExampleSkill(BaseSkill):
    """Example skill demonstrating the base skill interface."""

    name = "example_skill"
    skill_type = "custom"
    description = "Example skill for demonstration purposes"
    version = "1.0.0"

    parameters = [
        SkillParameter(
            name="message",
            type=str,
            description="Message to process",
            required=True,
        ),
        SkillParameter(
            name="count",
            type=int,
            description="Number of times to repeat",
            default=1,
            min_value=1,
            max_value=10,
        ),
    ]

    capabilities = [
        SkillCapability(
            name="text_processing",
            description="Can process text messages",
            enabled=True,
        ),
    ]

    async def execute(self, **kwargs) -> SkillResult:
        """Execute the example skill."""
        message = kwargs.get("message", "")
        count = kwargs.get("count", 1)

        if not message:
            return SkillResult(success=False, error="Message is required")

        result = " ".join([message] * count)

        return SkillResult(success=True, data={"result": result})


async def example_usage():
    """Example usage of base skill system."""
    from .built_in_skills import DataAnalyzeSkill, WebSearchSkill

    # Create skill instance
    skill = ExampleSkill()

    # Get skill metadata
    metadata = skill.get_metadata()
    print(f"Skill Metadata: {metadata}")

    # Execute skill
    result = await skill.execute_with_retry(message="Hello", count=3)
    print(f"Result: {result}")

    # Get statistics
    stats = skill.get_statistics()
    print(f"Statistics: {stats}")

    # Use global registry
    registry = get_global_registry()
    print(f"Registered skills: {registry.list_skills()}")

    # Get all metadata
    all_metadata = registry.get_all_metadata()
    print(f"All Skills Metadata: {all_metadata}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
