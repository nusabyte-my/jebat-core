"""JEBAT Skill Management Tool — agent-callable skill authoring.

The agent can create, update, delete, and read skills using structured
SKILL.md writing. Skills are the agent's procedural memory — reusable
approaches for recurring task types.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from jebat.tools import register_tool


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILLS_DIR = Path(os.environ.get(
    "JEBAT_SKILLS_DIR",
    str(Path.home() / ".jebat" / "tokguru"),
)).expanduser()


def _ensure_skills_dir() -> Path:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    return SKILLS_DIR


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------

async def skill_manage(
    action: str,
    name: str | None = None,
    content: str | None = None,
    category: str | None = None,
    old_string: str | None = None,
    new_string: str | None = None,
) -> dict[str, Any]:
    """Create, read, update, or delete a skill.

    Supports 6 actions:

    - create(name, content, category?): Write a new SKILL.md. content must
      include YAML frontmatter (---\nname: x\n...\n---) followed by markdown.
    - read(name): Return the full SKILL.md content for inspection.
    - list(category?): List all skills, optionally filtered by category.
    - patch(name, old_string, new_string): Find/replace within an existing
      SKILL.md. Uses fuzzy matching.
    - edit(name, content): Overwrite the full SKILL.md content.
    - delete(name): Remove a skill directory entirely.
    """
    _ensure_skills_dir()

    if action == "list":
        return _list_skills(category)

    if not name:
        return {"status": "error", "error": "`name` is required for this action"}

    skill_path = _resolve_skill_path(name)

    if action == "read":
        return _read_skill(skill_path, name)

    if action == "create":
        return _create_skill(skill_path, name, content, category)

    if action == "edit":
        if not content:
            return {"status": "error", "error": "`content` is required for edit"}
        return _edit_skill(skill_path, name, content)

    if action == "patch":
        if not old_string or new_string is None:
            return {"status": "error", "error": "`old_string` and `new_string` are required for patch"}
        return _patch_skill(skill_path, name, old_string, new_string)

    if action == "delete":
        return _delete_skill(skill_path, name)

    return {"status": "error", "error": f"Unknown action: {action}. Use: create, read, list, patch, edit, delete"}


# ---------------------------------------------------------------------------
# Internal actions
# ---------------------------------------------------------------------------

def _resolve_skill_path(name: str) -> Path:
    """Get the skill directory path, creating if needed."""
    return SKILLS_DIR / name


def _list_skills(category: str | None) -> dict[str, Any]:
    """List all skills, optionally filtered by category."""
    if not SKILLS_DIR.exists():
        return {"status": "ok", "skills": []}

    skills: list[dict[str, str]] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        # Quick parse for name/category/description from frontmatter
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        meta = _parse_frontmatter(content)
        skill_name = meta.get("name") or skill_dir.name
        skill_cat = meta.get("category", "")

        if category and skill_cat != category:
            continue

        skills.append({
            "name": skill_name,
            "category": skill_cat,
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "tags": meta.get("tags", []),
            "path": str(skill_file),
        })

    return {"status": "ok", "skills": skills}


def _read_skill(skill_path: Path, name: str) -> dict[str, Any]:
    """Read a skill's SKILL.md content."""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        return {
            "status": "error",
            "error": f"Skill '{name}' not found at {skill_file}",
        }

    content = skill_file.read_text(encoding="utf-8", errors="replace")
    return {
        "status": "ok",
        "name": name,
        "content": content,
    }


def _create_skill(
    skill_path: Path,
    name: str,
    content: str | None,
    category: str | None,
) -> dict[str, Any]:
    """Create a new skill SKILL.md."""
    # Build minimal frontmatter if not provided
    if content and content.startswith("---"):
        # Content already has frontmatter — validate name matches
        meta = _parse_frontmatter(content)
        meta_name = meta.get("name") or name
    else:
        # Build frontmatter automatically
        body = content or f"# {name}\n\nDescription of the {name} skill."
        lines = ["---", f"name: {name}", "version: 1.0.0"]
        if category:
            lines.append(f"category: {category}")
        lines.append("---")
        lines.append("")
        lines.append(body)
        content = "\n".join(lines)
        meta_name = name

    # Write the file
    skill_file = skill_path / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(content, encoding="utf-8")

    return {"status": "ok", "path": str(skill_file), "name": meta_name}


def _edit_skill(skill_path: Path, name: str, content: str) -> dict[str, Any]:
    """Overwrite a skill's SKILL.md."""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        return {
            "status": "error",
            "error": f"Skill '{name}' not found — use action='create' to create new skills",
        }

    skill_file.write_text(content, encoding="utf-8")
    return {"status": "ok", "path": str(skill_file), "message": f"Skill '{name}' updated"}


def _patch_skill(
    skill_path: Path,
    name: str,
    old_string: str,
    new_string: str,
) -> dict[str, Any]:
    """Find-and-replace within a skill's SKILL.md."""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        return {
            "status": "error",
            "error": f"Skill '{name}' not found at {skill_file}",
        }

    content = skill_file.read_text(encoding="utf-8")

    if old_string not in content:
        return {
            "status": "error",
            "error": f"Could not find '{old_string[:80]}' in {name}'s SKILL.md",
        }

    updated = content.replace(old_string, new_string)
    skill_file.write_text(updated, encoding="utf-8")

    count = content.count(old_string)
    return {
        "status": "ok",
        "path": str(skill_file),
        "message": f"Patched {count} occurrence(s)",
    }


def _delete_skill(skill_path: Path, name: str) -> dict[str, Any]:
    """Delete a skill directory."""
    if not skill_path.exists():
        return {"status": "error", "error": f"Skill '{name}' not found"}

    import shutil
    shutil.rmtree(skill_path)
    return {
        "status": "ok",
        "message": f"Skill '{name}' and its directory deleted",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Simple YAML frontmatter parser for SKILL.md files."""
    meta: dict[str, Any] = {}

    if not content.startswith("---"):
        return meta

    end = content.find("---", 3)
    if end == -1:
        return meta

    front_text = content[3:end].strip()
    current_key = None
    current_list: list[str] = []

    for line in front_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("- "):
            if current_key:
                current_list.append(line[2:].strip())
                meta[current_key] = list(current_list)
            continue
        if ": " in line:
            key, value = line.split(": ", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value == "" or value == "[]":
                current_list = []
                meta[key] = current_list
            else:
                # Try to interpret common types
                if value.lower() == "true":
                    meta[key] = True
                elif value.lower() == "false":
                    meta[key] = False
                else:
                    meta[key] = value
                current_key = None

    return meta


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    "skill_manage",
    schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "read", "list", "patch", "edit", "delete"],
                "description": (
                    "create: write a new SKILL.md (content must have YAML frontmatter). "
                    "read: return full SKILL.md content. "
                    "list: list all skills (optional category filter). "
                    "patch: find-and-replace within an existing skill. "
                    "edit: overwrite full SKILL.md. "
                    "delete: remove a skill directory entirely."
                ),
            },
            "name": {
                "type": "string",
                "description": "Skill name (lowercase, hyphens/underscores, max 64 chars). Required for create/read/patch/edit/delete.",
            },
            "content": {
                "type": "string",
                "description": (
                    "Full SKILL.md content including YAML frontmatter. Required for create and edit. "
                    "If content for 'create' does not start with '---', frontmatter is auto-generated "
                    "with name, version, and category."
                ),
            },
            "category": {
                "type": "string",
                "description": "Optional category for organizing skills (e.g., 'devops', 'mlops'). Used with create and list.",
            },
            "old_string": {
                "type": "string",
                "description": "Text to find for 'patch' action. Must be unique — include surrounding lines for precision.",
            },
            "new_string": {
                "type": "string",
                "description": "Replacement text for 'patch' action.",
            },
        },
        "required": ["action"],
    },
    safety_tier="auto",
    timeout=60,
    description=(
        "Manage skills (create, read, list, patch, edit, delete). Skills are "
        "your procedural memory — reusable approaches for recurring task types. "
        "Create after complex task successes, patch when you discover missing "
        "steps or pitfalls. Skills live in ~/.jebat/tokguru/<name>/SKILL.md."
    ),
)(skill_manage)