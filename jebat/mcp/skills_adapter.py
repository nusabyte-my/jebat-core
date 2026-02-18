"""
🗡️ JEBAT MCP - Skills Adapter

Load and integrate JEBAT Awesome Skills via MCP.

Usage:
    from jebat.mcp.skills_adapter import SkillsAdapter

    adapter = SkillsAdapter(skills_path="~/.jebat/skills")
    await adapter.load_skills()
    await adapter.use_skill("typescript-expert", context)
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """Skill definition."""

    name: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)
    ide_support: List[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"
    content: str = ""
    path: str = ""


class SkillsAdapter:
    """
    JEBAT MCP Skills Adapter.

    Loads and manages skills from jebat-awesome-skills repository.
    """

    def __init__(
        self,
        skills_path: Optional[str] = None,
        mcp_server=None,
    ):
        """
        Initialize Skills Adapter.

        Args:
            skills_path: Path to skills directory
            mcp_server: MCP server instance
        """
        self.skills_path = Path(skills_path or "~/.jebat/skills").expanduser()
        self.mcp_server = mcp_server
        self.skills: Dict[str, Skill] = {}
        self.loaded_skills: List[str] = []

        logger.info(f"SkillsAdapter initialized (path: {self.skills_path})")

    async def load_skills(self) -> int:
        """
        Load all skills from skills directory.

        Returns:
            Number of skills loaded
        """
        if not self.skills_path.exists():
            logger.warning(f"Skills path not found: {self.skills_path}")
            return 0

        loaded = 0

        # Scan for SKILL.md files
        for skill_file in self.skills_path.rglob("SKILL.md"):
            try:
                skill = await self._load_skill(skill_file)
                if skill:
                    self.skills[skill.name] = skill
                    loaded += 1
            except Exception as e:
                logger.error(f"Failed to load skill {skill_file}: {e}")

        logger.info(f"Loaded {loaded} skills")
        return loaded

    async def _load_skill(self, skill_file: Path) -> Optional[Skill]:
        """Load a single skill from file."""
        try:
            content = skill_file.read_text(encoding="utf-8")

            # Parse frontmatter
            frontmatter, body = self._parse_frontmatter(content)

            skill = Skill(
                name=frontmatter.get("name", skill_file.parent.name),
                description=frontmatter.get("description", ""),
                category=frontmatter.get("category", "general"),
                tags=frontmatter.get("tags", []),
                ide_support=frontmatter.get("ide_support", []),
                author=frontmatter.get("author", ""),
                version=frontmatter.get("version", "1.0.0"),
                content=body,
                path=str(skill_file),
            )

            return skill

        except Exception as e:
            logger.error(f"Error loading skill {skill_file}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse YAML frontmatter from skill content."""
        if not content.startswith("---"):
            return {}, content

        # Find end of frontmatter
        end_index = content.find("---", 3)
        if end_index == -1:
            return {}, content

        # Parse frontmatter (simple YAML parsing)
        frontmatter_text = content[3:end_index].strip()
        frontmatter = {}

        current_key = None
        current_list = []

        for line in frontmatter_text.split("\n"):
            line = line.strip()

            if not line:
                continue

            # Check for list item
            if line.startswith("- "):
                if current_key:
                    current_list.append(line[2:])
                    frontmatter[current_key] = current_list
                continue

            # Check for key: value
            if ": " in line:
                key, value = line.split(": ", 1)
                current_key = key

                # Check if it's a list
                if value == "":
                    current_list = []
                    frontmatter[key] = current_list
                else:
                    frontmatter[key] = value
                    current_key = None

        body = content[end_index + 3 :].strip()

        return frontmatter, body

    async def use_skill(
        self,
        skill_name: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Activate and use a skill.

        Args:
            skill_name: Name of skill to use
            context: Current context (code, conversation, etc.)

        Returns:
            Skill response
        """
        if skill_name not in self.skills:
            return {
                "success": False,
                "error": f"Skill not found: {skill_name}",
                "available_skills": list(self.skills.keys())[:10],
            }

        skill = self.skills[skill_name]
        logger.info(f"Using skill: {skill_name}")

        # Load skill content into context
        enhanced_context = {
            **context,
            "skill": {
                "name": skill.name,
                "description": skill.description,
                "tags": skill.tags,
            },
            "skill_content": skill.content,
        }

        # If MCP server available, register skill as tool
        if self.mcp_server:
            await self._register_skill_tool(skill)

        return {
            "success": True,
            "skill": skill.name,
            "description": skill.description,
            "context": enhanced_context,
        }

    async def _register_skill_tool(self, skill: Skill):
        """Register skill as MCP tool."""
        # This would integrate with the MCP server's tool registration
        logger.debug(f"Registering skill tool: {skill.name}")

    def search_skills(self, query: str) -> List[Skill]:
        """Search skills by query."""
        query_lower = query.lower()

        results = []
        for skill in self.skills.values():
            # Search in name, description, tags
            if (
                query_lower in skill.name.lower()
                or query_lower in skill.description.lower()
                or any(query_lower in tag.lower() for tag in skill.tags)
            ):
                results.append(skill)

        return results

    def get_skills_by_category(self, category: str) -> List[Skill]:
        """Get all skills in a category."""
        return [skill for skill in self.skills.values() if skill.category == category]

    def get_skills_by_tag(self, tag: str) -> List[Skill]:
        """Get all skills with a tag."""
        return [skill for skill in self.skills.values() if tag in skill.tags]

    def list_categories(self) -> List[str]:
        """List all skill categories."""
        return list(set(skill.category for skill in self.skills.values()))

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a specific skill by name."""
        return self.skills.get(name)

    async def load_from_index(self, index_path: Optional[str] = None):
        """Load skills from skills_index.json."""
        index_path = Path(index_path or (self.skills_path / "skills_index.json"))

        if not index_path.exists():
            logger.warning(f"Skills index not found: {index_path}")
            return

        try:
            index_data = json.loads(index_path.read_text())

            for skill_data in index_data.get("skills", []):
                skill = Skill(
                    name=skill_data["name"],
                    description=skill_data["description"],
                    category=skill_data["category"],
                    tags=skill_data.get("tags", []),
                    ide_support=skill_data.get("ide_support", []),
                    path=skill_data.get("path", ""),
                )
                self.skills[skill.name] = skill

            logger.info(f"Loaded {len(self.skills)} skills from index")

        except Exception as e:
            logger.error(f"Failed to load skills index: {e}")


# MCP Tool Registration
async def register_skills_tools(mcp_server, skills_adapter: SkillsAdapter):
    """Register all skills as MCP tools."""

    @mcp_server.list_tools()
    async def list_tools():
        """List available skills as tools."""
        from mcp.types import Tool

        tools = []
        for skill in skills_adapter.skills.values():
            tools.append(
                Tool(
                    name=f"skill.{skill.name}",
                    description=f"Use skill: {skill.description}",
                    inputSchema={
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
                    },
                )
            )

        return tools

    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        """Call a skill tool."""
        if name.startswith("skill."):
            skill_name = name[6:]  # Remove "skill." prefix

            result = await skills_adapter.use_skill(
                skill_name,
                context={
                    "code": arguments.get("context", ""),
                    "question": arguments.get("question", ""),
                },
            )

            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        raise ValueError(f"Unknown tool: {name}")
