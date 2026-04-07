"""
Skills Package
Contains all skill implementations for the Multi-Agent Automation System.

This package provides:
- BaseSkill: Abstract base class for all skills
- FileProcessingSkill: Comprehensive file operations skill
- APICommunicationSkill: Advanced API integration skill
- Additional skill implementations

Usage:
    from skills import BaseSkill, FileProcessingSkill, APICommunicationSkill
    from skills.base_skill import SkillType, SkillResult

    # Create a file processing skill
    file_skill = FileProcessingSkill()

    # Create an API communication skill
    api_skill = APICommunicationSkill()
"""

__version__ = "1.0.0"

# Import base classes and enums
# Import concrete implementations
from .api_communication_skill import APICommunicationSkill
from .base_skill import BaseSkill, SkillParameter, SkillResult, SkillStatus, SkillType
from .file_processing_skill import FileProcessingSkill

# Define what gets imported with "from skills import *"
__all__ = [
    # Base classes and data types
    "BaseSkill",
    "SkillResult",
    "SkillStatus",
    "SkillType",
    "SkillParameter",
    # Concrete skill implementations
    "FileProcessingSkill",
    "APICommunicationSkill",
]

# Skill registry for dynamic skill creation
SKILL_REGISTRY = {
    "base": BaseSkill,
    "file_processing": FileProcessingSkill,
    "api_communication": APICommunicationSkill,
}


def create_skill(skill_type: str, skill_id: str = None, name: str = None, **kwargs):
    """
    Factory function to create skills by type.

    Args:
        skill_type: Type of skill to create ("file_processing", "api_communication", etc.)
        skill_id: Unique identifier for the skill (optional, auto-generated if None)
        name: Human-readable name for the skill (optional, default based on type)
        **kwargs: Additional configuration parameters

    Returns:
        Skill instance of the specified type

    Raises:
        ValueError: If skill_type is not registered

    Example:
        skill = create_skill("file_processing", "file_001", "My File Processor")
    """
    if skill_type not in SKILL_REGISTRY:
        available_types = list(SKILL_REGISTRY.keys())
        raise ValueError(
            f"Unknown skill type '{skill_type}'. Available types: {available_types}"
        )

    skill_class = SKILL_REGISTRY[skill_type]
    if skill_class == BaseSkill:
        raise ValueError("Cannot instantiate abstract BaseSkill directly")

    # Generate default values if not provided
    if skill_id is None:
        skill_id = f"{skill_type}_001"

    if name is None:
        name = skill_type.replace("_", " ").title()

    return skill_class(skill_id=skill_id, name=name, **kwargs)


def list_skill_types():
    """
    List all available skill types.

    Returns:
        List of available skill type names
    """
    return [skill_type for skill_type in SKILL_REGISTRY.keys() if skill_type != "base"]


def get_skills_by_type(skill_type_filter: SkillType = None):
    """
    Get skills filtered by SkillType enum.

    Args:
        skill_type_filter: SkillType enum to filter by (optional)

    Returns:
        List of skill classes that match the filter
    """
    filtered_skills = []

    for skill_name, skill_class in SKILL_REGISTRY.items():
        if skill_name == "base":
            continue

        # Create temporary instance to check skill type
        try:
            temp_instance = skill_class(f"temp_{skill_name}", f"Temp {skill_name}")
            if (
                skill_type_filter is None
                or temp_instance.skill_type == skill_type_filter
            ):
                filtered_skills.append(
                    {
                        "name": skill_name,
                        "class": skill_class,
                        "type": temp_instance.skill_type,
                    }
                )
        except Exception:
            # Skip skills that can't be instantiated temporarily
            continue

    return filtered_skills


def get_skill_info():
    """
    Get information about all available skill types.

    Returns:
        Dictionary mapping skill types to their class information
    """
    info = {}
    for skill_type, skill_class in SKILL_REGISTRY.items():
        if skill_type != "base":
            # Try to get skill type enum and description
            try:
                temp_instance = skill_class(f"temp_{skill_type}", f"Temp {skill_type}")
                skill_type_enum = temp_instance.skill_type
                description = (
                    skill_class.__doc__.split("\n")[1].strip()
                    if skill_class.__doc__
                    else "No description available"
                )

                info[skill_type] = {
                    "class_name": skill_class.__name__,
                    "module": skill_class.__module__,
                    "skill_type": skill_type_enum.value,
                    "description": description,
                }
            except Exception:
                # Fallback info if instantiation fails
                info[skill_type] = {
                    "class_name": skill_class.__name__,
                    "module": skill_class.__module__,
                    "skill_type": "unknown",
                    "description": "Could not retrieve description",
                }

    return info


def register_skill(skill_type: str, skill_class: type):
    """
    Register a new skill type with the registry.

    Args:
        skill_type: String identifier for the skill type
        skill_class: Class that implements BaseSkill

    Raises:
        ValueError: If skill_class doesn't inherit from BaseSkill
    """
    if not issubclass(skill_class, BaseSkill):
        raise ValueError("Skill class must inherit from BaseSkill")

    SKILL_REGISTRY[skill_type] = skill_class


def unregister_skill(skill_type: str):
    """
    Remove a skill type from the registry.

    Args:
        skill_type: String identifier for the skill type to remove

    Returns:
        bool: True if skill was removed, False if not found
    """
    if skill_type in SKILL_REGISTRY and skill_type != "base":
        del SKILL_REGISTRY[skill_type]
        return True
    return False
