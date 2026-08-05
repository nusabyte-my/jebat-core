"""
🗡️ JEBAT Skill Registry

Central registry for all JEBAT Awesome Skills.
Provides skill discovery, loading, and execution.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillConfig:
    """Skill configuration."""

    temperature: float = 0.7
    max_tokens: int = 4096
    context_window: int = 8192
    requires: List[str] = field(default_factory=list)


@dataclass
class Skill:
    """Skill definition."""

    name: str
    version: str
    description: str
    category: str
    author: str = "JEBAT Team"
    license: str = "MIT"
    tags: List[str] = field(default_factory=list)
    ide_support: List[str] = field(default_factory=list)
    config: SkillConfig = field(default_factory=SkillConfig)
    depends_on: List[str] = field(default_factory=list)
    triggers: List[Dict[str, str]] = field(default_factory=list)
    content: str = ""
    prompt: str = ""
    examples: List[str] = field(default_factory=list)
    path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "author": self.author,
            "license": self.license,
            "tags": self.tags,
            "ide_support": self.ide_support,
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "context_window": self.config.context_window,
            },
            "depends_on": self.depends_on,
            "triggers": self.triggers,
            "path": self.path,
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Get MCP input schema for skill."""
        return {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Code or context to apply skill to",
                },
                "question": {
                    "type": "string",
                    "description": "Question or task for the skill",
                },
            },
            "required": ["context"],
        }


class SkillRegistry:
    """
    Central Skill Registry for JEBAT.

    Manages skill discovery, loading, and execution.
    """

    def __init__(
        self,
        skills_path: Optional[str] = None,
        auto_load: bool = True,
    ):
        """
        Initialize Skill Registry.

        Args:
            skills_path: Path to skills directory
            auto_load: Auto-load skills on init
        """
        self.skills_path = Path(skills_path or "~/.jebat/tokguru").expanduser()
        self.skills: Dict[str, Skill] = {}
        self.categories: Dict[str, List[str]] = {}
        self.bundles: Dict[str, List[str]] = {}
        self.loaded_count = 0

        if auto_load:
            self.load_all_skills()

    def load_all_skills(self) -> int:
        """Load all skills from skills directory."""
        if not self.skills_path.exists():
            logger.warning(f"Skills path not found: {self.skills_path}")
            return 0

        # Try to load from index first
        index_path = self.skills_path / "skills_index.json"
        if index_path.exists():
            self._load_from_index(index_path)

        # Scan for SKILL.md files
        for skill_file in self.skills_path.rglob("SKILL.md"):
            try:
                skill = self._parse_skill_file(skill_file)
                if skill:
                    self.skills[skill.name] = skill
                    self._add_to_category(skill.category, skill.name)
                    self.loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load skill {skill_file}: {e}")

        # Load bundles
        self._load_bundles()

        logger.info(f"Loaded {self.loaded_count} skills")
        return self.loaded_count

    def _load_from_index(self, index_path: Path):
        """Load skills from skills_index.json."""
        try:
            index_data = json.loads(index_path.read_text())

            for skill_data in index_data.get("skills", []):
                skill = Skill(
                    name=skill_data["name"],
                    version=skill_data.get("version", "1.0.0"),
                    description=skill_data["description"],
                    category=skill_data["category"],
                    tags=skill_data.get("tags", []),
                    ide_support=skill_data.get("ide_support", []),
                    path=str(self.skills_path / skill_data.get("path", "")),
                )
                self.skills[skill.name] = skill
                self._add_to_category(skill.category, skill.name)

            # Load bundles
            for bundle in index_data.get("bundles", []):
                self.bundles[bundle["name"]] = bundle["skills"]

        except Exception as e:
            logger.error(f"Failed to load skills index: {e}")

    def _parse_skill_file(self, skill_file: Path) -> Optional[Skill]:
        """Parse a SKILL.md file."""
        try:
            content = skill_file.read_text(encoding="utf-8")

            # Parse frontmatter
            frontmatter, body = self._parse_frontmatter(content)

            # Parse configuration
            config_data = frontmatter.get("config", {})
            config = SkillConfig(
                temperature=config_data.get("temperature", 0.7),
                max_tokens=config_data.get("max_tokens", 4096),
                context_window=config_data.get("context_window", 8192),
                requires=config_data.get("requires", []),
            )

            skill = Skill(
                name=frontmatter.get("name", skill_file.parent.name),
                version=frontmatter.get("version", "1.0.0"),
                description=frontmatter.get("description", ""),
                category=frontmatter.get("category", "general"),
                author=frontmatter.get("author", "JEBAT Team"),
                license=frontmatter.get("license", "MIT"),
                tags=frontmatter.get("tags", []),
                ide_support=frontmatter.get("ide_support", []),
                config=config,
                depends_on=frontmatter.get("depends_on", []),
                triggers=frontmatter.get("triggers", []),
                content=body,
                path=str(skill_file),
            )

            # Try to load prompt.md if exists
            prompt_file = skill_file.parent / "prompt.md"
            if prompt_file.exists():
                skill.prompt = prompt_file.read_text()

            # Try to load examples
            examples_dir = skill_file.parent / "examples"
            if examples_dir.exists():
                for example_file in examples_dir.glob("*.md"):
                    skill.examples.append(example_file.read_text())

            return skill

        except Exception as e:
            logger.error(f"Error parsing skill {skill_file}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse YAML frontmatter."""
        if not content.startswith("---"):
            return {}, content

        end_index = content.find("---", 3)
        if end_index == -1:
            return {}, content

        # Simple YAML parsing
        frontmatter_text = content[3:end_index].strip()
        frontmatter = {}

        current_key = None
        current_list = []

        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("- "):
                if current_key:
                    current_list.append(line[2:])
                    frontmatter[current_key] = current_list
                continue

            if ": " in line:
                key, value = line.split(": ", 1)
                current_key = key
                if value == "":
                    current_list = []
                    frontmatter[key] = current_list
                else:
                    frontmatter[key] = value
                    current_key = None

        body = content[end_index + 3 :].strip()
        return frontmatter, body

    def _add_to_category(self, category: str, skill_name: str):
        """Add skill to category."""
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(skill_name)

    def _load_bundles(self):
        """Load skill bundles."""
        bundles_dir = self.skills_path / "bundles"
        if not bundles_dir.exists():
            return

        for bundle_file in bundles_dir.glob("*.json"):
            try:
                bundle_data = json.loads(bundle_file.read_text())
                bundle_name = bundle_file.stem
                self.bundles[bundle_name] = bundle_data.get("skills", [])
            except Exception as e:
                logger.error(f"Failed to load bundle {bundle_file}: {e}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get skill by name."""
        return self.skills.get(name)

    def search_skills(self, query: str) -> List[Skill]:
        """Search skills by query."""
        query_lower = query.lower()
        results = []

        for skill in self.skills.values():
            if (
                query_lower in skill.name.lower()
                or query_lower in skill.description.lower()
                or any(query_lower in tag.lower() for tag in skill.tags)
            ):
                results.append(skill)

        return results

    def get_skills_by_category(self, category: str) -> List[Skill]:
        """Get all skills in a category."""
        skill_names = self.categories.get(category, [])
        return [self.skills[name] for name in skill_names if name in self.skills]

    def get_skills_by_tag(self, tag: str) -> List[Skill]:
        """Get all skills with a tag."""
        return [skill for skill in self.skills.values() if tag in skill.tags]

    def get_bundle(self, name: str) -> List[Skill]:
        """Get all skills in a bundle."""
        skill_names = self.bundles.get(name, [])
        return [self.skills[name] for name in skill_names if name in self.skills]

    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self.categories.keys())

    def list_bundles(self) -> List[str]:
        """List all bundles."""
        return list(self.bundles.keys())

    def get_all_skills(self) -> List[Skill]:
        """Get all skills."""
        return list(self.skills.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary."""
        return {
            "total_skills": len(self.skills),
            "categories": {
                name: len(skills) for name, skills in self.categories.items()
            },
            "bundles": list(self.bundles.keys()),
            "skills": [skill.to_dict() for skill in self.skills.values()],
        }

    def export_index(self, output_path: str):
        """Export skills index to JSON."""
        index_data = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "total_skills": len(self.skills),
            "categories": self.categories,
            "bundles": self.bundles,
            "skills": [skill.to_dict() for skill in self.skills.values()],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported skills index to {output_path}")
