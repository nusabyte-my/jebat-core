"""🗡️ JEBAT Cross-Agent Skill Bridge — PawangIlmu (Knowledge Shaman).

Bidirectional skill import/export across 4 CLI agent formats:

  1. HERMES   → SKILL.md (YAML frontmatter: name, description, metadata.hermes)
  2. OPENCLAW → SKILL.md (YAML frontmatter: name, description, category, tags, ide_support, author, version)
  3. CLAUDE   → CLAUDE.md (plain markdown, no frontmatter, project-root config)
  4. CODEX    → AGENTS.md / CODEX_PROFILE.md (plain markdown, workspace/rules config)

Usage:
    from jebat.features.skills.cross_agent_bridge import (
        CrossAgentBridge,
        import_hermes_skills,
        import_claude_skills,
        import_codex_skills,
        import_openclaw_skills,
        export_to_hermes,
        export_to_claude,
        export_to_codex,
        export_to_openclaw,
        SkillFormat,
    )

    bridge = CrossAgentBridge(registry_path="~/.jebat/skills")
    count = await bridge.import_all()          # auto-discover from all agent dirs
    count = await bridge.import_from("hermes") # specific format only
    count = bridge.export_all()                 # export JEBAT skills to all formats
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Format Enum ─────────────────────────────────────────────────────────────

class SkillFormat(str, Enum):
    """Supported agent skill formats."""

    HERMES = "hermes"         # SKILL.md with YAML frontmatter + metadata.hermes
    OPENCLAW = "openclaw"     # SKILL.md with YAML frontmatter (JEBAT native)
    CLAUDE = "claude"         # CLAUDE.md (plain markdown, no frontmatter)
    CODEX = "codex"           # AGENTS.md / CODEX_PROFILE.md (plain markdown)

    @classmethod
    def all(cls) -> list["SkillFormat"]:
        return list(cls)


# ── Normalized Skill (bridge-internal) ──────────────────────────────────────

@dataclass
class BridgedSkill:
    """Normalized skill representation used internally by the bridge.

    All 4 agent formats are normalized into this shape, then de-normalized
    back when exporting.
    """

    name: str
    title: str
    description: str
    trigger: str = ""
    category: str = "uncategorized"
    tags: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    author: str = "JEBAT Cross-Agent Bridge"
    version: str = "1.0.0"
    source_format: SkillFormat = SkillFormat.HERMES
    source_path: str = ""
    body: str = ""  # Full markdown body (after frontmatter)
    steps: list[str] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    linked_files: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_jebat_skill(self) -> dict[str, Any]:
        """Convert to JEBAT's internal Skill schema (dict form)."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "author": self.author,
            "license": "MIT",
            "tags": self.tags,
            "ide_support": [],
            "config": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "context_window": 8192,
            },
            "depends_on": [],
            "triggers": [{"pattern": self.trigger}] if self.trigger else [],
            "content": self.body or f"# {self.title}\n\n{self.description}",
            "path": self.source_path,
        }

    def to_skill_md(self) -> str:
        """Render as JEBAT/OpenClaw SKILL.md."""
        lines = ["---"]
        lines.append(f"name: {self.name}")
        if self.description:
            lines.append(f'description: "{self.description}"')
        if self.trigger:
            lines.append(f'trigger: "{self.trigger}"')
        if self.category:
            lines.append(f"category: {self.category}")
        if self.author:
            lines.append(f"author: {self.author}")
        if self.version:
            lines.append(f"version: {self.version}")
        if self.tags:
            lines.append("tags:")
            for t in self.tags:
                lines.append(f"  - {t}")
        if self.platforms:
            lines.append("platforms:")
            for p in self.platforms:
                lines.append(f"  - {p}")
        lines.append(f"created: \"{self.created_at}\"")
        lines.append("---")
        lines.append("")
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(self.description)
        lines.append("")
        if self.trigger:
            lines.append(f"> **Trigger:** {self.trigger}")
            lines.append("")

        if self.steps:
            lines.append("## Steps")
            lines.append("")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        if self.pitfalls:
            lines.append("## Pitfalls")
            lines.append("")
            for p in self.pitfalls:
                lines.append(f"- {p}")
            lines.append("")

        if self.verification:
            lines.append("## Verification")
            lines.append("")
            for v in self.verification:
                lines.append(f"- [ ] {v}")
            lines.append("")

        if self.references:
            lines.append("## References")
            lines.append("")
            for r in self.references:
                lines.append(f"- {r}")
            lines.append("")

        # Append original body if substantial and not already included
        if self.body and len(self.body) > 200 and "## Steps" not in self.body and "## Pitfalls" not in self.body:
            lines.append("---")
            lines.append("")
            lines.append("## Original Content")
            lines.append("")
            lines.append(self.body)

        return "\n".join(lines)

    def to_claude_md(self) -> str:
        """Render as CLAUDE.md (plain markdown, no frontmatter)."""
        lines = []
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"*{self.description}*")
        lines.append("")
        if self.trigger:
            lines.append(f"**When to use:** {self.trigger}")
            lines.append("")

        if self.steps:
            lines.append("## Steps")
            lines.append("")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        if self.pitfalls:
            lines.append("## Common Pitfalls")
            lines.append("")
            for p in self.pitfalls:
                lines.append(f"- {p}")
            lines.append("")

        if self.verification:
            lines.append("## Verification")
            lines.append("")
            for v in self.verification:
                lines.append(f"- [ ] {v}")
            lines.append("")

        # Include full body if available
        if self.body:
            lines.append("---")
            lines.append("")
            lines.append(self.body)

        return "\n".join(lines)

    def to_codex_profile(self) -> str:
        """Render as CODEX_PROFILE.md."""
        lines = []
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"> {self.description}")
        lines.append("")

        if self.tags:
            lines.append(f"**Tags:** {', '.join(self.tags)}")
            lines.append("")

        if self.steps:
            lines.append("## Rules")
            lines.append("")
            for step in self.steps:
                lines.append(f"- {step}")
            lines.append("")

        if self.pitfalls:
            lines.append("## Anti-Rules (Don'ts)")
            lines.append("")
            for p in self.pitfalls:
                lines.append(f"- {p}")
            lines.append("")

        if self.body:
            lines.append("---")
            lines.append("")
            lines.append(self.body)

        return "\n".join(lines)

    def to_agents_md_entry(self) -> str:
        """Render as an entry in AGENTS.md."""
        lines = []
        lines.append(f"### {self.title}")
        lines.append("")
        lines.append(f"*{self.description}*")
        lines.append("")
        if self.steps:
            lines.append("Procedure:")
            for step in self.steps:
                lines.append(f"- {step}")
            lines.append("")
        if self.pitfalls:
            lines.append("Pitfalls:")
            for p in self.pitfalls:
                lines.append(f"- {p}")
            lines.append("")
        return "\n".join(lines)


# ── Parsers (format → BridgedSkill) ─────────────────────────────────────────

def _parse_frontmatter_yaml(content: str) -> tuple[dict[str, Any], str]:
    """Parse simple YAML frontmatter (--- ... ---) from content."""
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()
    frontmatter: dict[str, Any] = {}

    current_key = None
    current_list: list[str] = []
    is_list = False

    for line in fm_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # List item continuation
        if line.startswith("- "):
            item = line[2:].strip()
            if current_key:
                current_list.append(item)
                frontmatter[current_key] = list(current_list)
            is_list = True
            continue

        # Nested map (e.g. metadata.hermes)
        if ":" in line and not line.startswith("-"):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            current_list = []
            is_list = False

            # Handle dotted keys (e.g. "metadata.hermes")
            if "." in key:
                parts = key.split(".")
                d = frontmatter
                for p in parts[:-1]:
                    if p not in d:
                        d[p] = {}
                    d = d[p]
                d[parts[-1]] = value if value else []
            else:
                frontmatter[key] = value if value else []

    return frontmatter, body


def _extract_nested_lists(fm: dict[str, Any], key: str) -> list[str]:
    """Extract a list from frontmatter that might be a string or list."""
    val = fm.get(key, [])
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return val
    return []


def parse_hermes_skill(content: str, source_path: str = "") -> Optional[BridgedSkill]:
    """Parse a Hermes-format SKILL.md (with metadata.hermes tags).

    Hermes format:
      ---
      name: skill-name
      description: "Use when ..."
      version: 1.0.0
      author: ...
      metadata:
        hermes:
          tags: [a, b]
          category: devops
      ---
      # Body
    """
    fm, body = _parse_frontmatter_yaml(content)
    if not fm.get("name"):
        return None

    name = fm.get("name", "").strip()
    description = fm.get("description", "").strip().strip('"').strip("'")
    version = fm.get("version", "1.0.0")
    author = fm.get("author", "Hermes")

    # Extract nested metadata.hermes
    metadata = {}
    tags: list[str] = []
    category = "uncategorized"
    if "metadata" in fm and isinstance(fm["metadata"], dict):
        hermes_dict = fm["metadata"].get("hermes")
        if isinstance(hermes_dict, dict):
            tags = _extract_nested_lists(hermes_dict, "tags")
            category = hermes_dict.get("category", "uncategorized")
        elif isinstance(hermes_dict, str):
            # Raw string — try to parse as list or comma-separated
            if hermes_dict.startswith("[") and hermes_dict.endswith("]"):
                tags = [t.strip().strip('"').strip("'") for t in hermes_dict[1:-1].split(",") if t.strip()]
    elif "tags" in fm:
        tags = _extract_nested_lists(fm, "tags")
    if "category" in fm and category == "uncategorized":
        category = fm.get("category", "uncategorized")

    # Extract linked files from Hermes skill dir
    linked_files: dict[str, list[str]] = {}
    if source_path:
        src_dir = Path(source_path).parent
        for subdir in ["references", "templates", "scripts", "assets"]:
            sub_path = src_dir / subdir
            if sub_path.exists() and sub_path.is_dir():
                files = sorted(f.name for f in sub_path.iterdir() if f.is_file())
                if files:
                    linked_files[subdir] = files

    # Extract title from body
    title = name
    for line in body.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Extract structure
    steps = _extract_section_list(body, "steps", "how", "guide", "usage")
    pitfalls = _extract_section_list(body, "pitfall", "warning", "gotcha", "troubleshoot")
    verification = _extract_section_list(body, "verify", "check", "test")

    trigger = description if description.startswith("Use when") else f"Use when {name}"
    platforms = _extract_nested_lists(fm, "platforms")

    return BridgedSkill(
        name=name,
        title=title,
        description=description,
        trigger=trigger,
        category=category,
        tags=tags,
        platforms=platforms,
        author=author,
        version=version,
        source_format=SkillFormat.HERMES,
        source_path=source_path,
        body=body,
        steps=steps[:15],
        pitfalls=pitfalls[:10],
        verification=verification[:10],
        linked_files=linked_files,
        metadata=metadata,
    )


def parse_openclaw_skill(content: str, source_path: str = "") -> Optional[BridgedSkill]:
    """Parse an OpenClaw/JEBAT-native SKILL.md.

    OpenClaw/JEBAT format:
      ---
      name: fullstack
      description: Fullstack web development...
      category: development
      tags: [fullstack, react]
      ide_support: [vscode, zed]
      author: JEBATCore / NusaByte
      version: 2.0.0
      ---
      # Title
      ## Shared Core
      ## Jiwa
      ## Steps/Patterns
    """
    fm, body = _parse_frontmatter_yaml(content)
    if not fm.get("name"):
        # No frontmatter → plain markdown file (treat as generic skill)
        return None

    name = fm.get("name", "").strip()
    description = fm.get("description", "").strip().strip('"').strip("'")
    category = fm.get("category", "uncategorized")
    author = fm.get("author", "OpenClaw")
    version = fm.get("version", "1.0.0")

    # Tags may be YAML list or comma-separated string with optional brackets
    tags = _extract_nested_lists(fm, "tags")
    raw_tags = fm.get("tags")
    if isinstance(raw_tags, str):
        ts = raw_tags.strip()
        if ts.startswith("[") and ts.endswith("]"):
            tags = [t.strip().strip('"').strip("'") for t in ts[1:-1].split(",") if t.strip()]
        else:
            tags = [t.strip() for t in ts.split(",") if t.strip()]

    # Extract title
    title = name.replace("-", " ").title()
    for line in body.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Extract ide_support
    ide_support = _extract_nested_lists(fm, "ide_support")
    platforms = ["macos", "linux"]
    if "windows" in " ".join(ide_support).lower():
        platforms.append("windows")

    # Extract structured sections from body
    steps = _extract_section_list(body, "step", "how to", "guide", "pattern", "procedure")
    pitfalls = _extract_section_list(body, "pitfall", "warning", "caution", "gotcha", "troubleshoot")
    verification = _extract_section_list(body, "verify", "test", "check", "confirm", "validation")

    trigger = f"Use when {description[:60]}" if description else f"Use when {name}"

    # Check for linked files
    linked_files: dict[str, list[str]] = {}
    if source_path:
        src_dir = Path(source_path).parent
        for subdir in ["references", "scripts", "templates", "assets", "_core"]:
            sub_path = src_dir / subdir
            if sub_path.exists() and sub_path.is_dir():
                files = sorted(f.name for f in sub_path.iterdir() if f.is_file())
                if files:
                    linked_files[subdir] = files

    return BridgedSkill(
        name=name,
        title=title,
        description=description,
        trigger=trigger,
        category=category,
        tags=tags,
        platforms=platforms,
        author=author,
        version=version,
        source_format=SkillFormat.OPENCLAW,
        source_path=source_path,
        body=body,
        steps=steps[:15],
        pitfalls=pitfalls[:10],
        verification=verification[:10],
        linked_files=linked_files,
    )


def parse_claude_md(content: str, source_path: str = "") -> Optional[BridgedSkill]:
    """Parse a CLAUDE.md file (Claude Code config, no frontmatter).

    Claude Code format:
      # Skill Name
      Plain markdown with headings, no YAML frontmatter.
      ## Steps / Rules / Patterns
      ## Pitfalls / Warnings
    """
    body = content.strip()
    if not body:
        return None

    # Derive name from filename or first heading
    name = Path(source_path).stem if source_path else "claude-skill"
    title = name
    for line in body.split("\n"):
        if line.startswith("# ") and not line.startswith("##"):
            title = line[2:].strip()
            break
    if title and name == Path(source_path).stem:
        name = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    # Extract first paragraph as description
    description = ""
    in_para = False
    para_lines = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
            in_para = True
            para_lines.append(stripped)
        elif in_para and not stripped:
            break
        elif in_para and stripped.startswith("#"):
            break
    if para_lines:
        description = " ".join(para_lines)[:200]

    # Extract structure
    steps = _extract_section_list(body, "step", "rule", "procedure", "how to", "pattern", "guide", "workflow")
    pitfalls = _extract_section_list(body, "pitfall", "warning", "caution", "gotcha", "dont", "avoid", "troubleshoot", "error")
    verification = _extract_section_list(body, "verify", "test", "check", "confirm")

    # Detect category from tags/headings
    category = _detect_category_from_content(body)

    trigger = f"Use when {description[:60]}" if description else f"Use when {title.lower()}"

    return BridgedSkill(
        name=name,
        title=title,
        description=description or f"Claude Code skill: {title}",
        trigger=trigger,
        category=category,
        author="Claude Code",
        version="1.0.0",
        source_format=SkillFormat.CLAUDE,
        source_path=source_path,
        body=body,
        steps=steps[:15],
        pitfalls=pitfalls[:10],
        verification=verification[:10],
    )


def parse_codex_md(content: str, source_path: str = "") -> Optional[BridgedSkill]:
    """Parse a CODEX_PROFILE.md or AGENTS.md file (Codex format).

    Codex format:
      # Role / Skill Name
      > Description quote
      ## Rules
      - rule 1
      ## Anti-Rules (Don'ts)
      - don't do this
      Plain markdown body.
    """
    body = content.strip()
    if not body:
        return None

    name = Path(source_path).stem if source_path else "codex-skill"
    title = name
    for line in body.split("\n"):
        if line.startswith("# ") and not line.startswith("##"):
            title = line[2:].strip()
            break
    if title and name == Path(source_path).stem:
        name = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    # Extract description from blockquote or first paragraph
    description = ""
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith(">"):
            description = stripped[1:].strip()
            break
    if not description:
        for line in body.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
                description = stripped[:200]
                break

    # Rules section → steps
    steps = _extract_section_list(body, "rule", "step", "procedure", "workflow", "task")
    # Anti-Rules → pitfalls
    pitfalls = _extract_section_list(body, "anti-rule", "dont", "avoid", "pitfall", "warning")

    # Tags from inline mentions (e.g. **Tags:**)
    tags: list[str] = []
    tag_match = re.search(r'\*\*Tags?:\*\*\s*(.+?)(?:\n|$)', body)
    if tag_match:
        tags = [t.strip() for t in tag_match.group(1).split(",") if t.strip()]

    category = _detect_category_from_content(body)
    trigger = f"Use when {description[:60]}" if description else f"Use when {title.lower()}"

    return BridgedSkill(
        name=name,
        title=title,
        description=description or f"Codex skill: {title}",
        trigger=trigger,
        category=category,
        tags=tags,
        author="Codex",
        version="1.0.0",
        source_format=SkillFormat.CODEX,
        source_path=source_path,
        body=body,
        steps=steps[:15],
        pitfalls=pitfalls[:10],
    )


# ── Helpers ─────────────────────────────────────────────────────────────────

def _extract_section_list(body: str, *keywords: str) -> list[str]:
    """Extract bullet/numbered items from sections matching keywords."""
    items: list[str] = []
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for heading with keyword
        if line.startswith("##") and any(kw.lower() in line.lower() for kw in keywords):
            i += 1
            # Collect bulleted items until next heading
            while i < len(lines) and not lines[i].startswith("##"):
                stripped = lines[i].strip()
                # Numbered items
                num_match = re.match(r"^\d+[.)]\s+(.+)", stripped)
                if num_match:
                    items.append(num_match.group(1))
                # Bullet items
                elif stripped.startswith("- ") or stripped.startswith("* "):
                    items.append(stripped[2:].strip())
                # Checklist items
                elif stripped.startswith("- [") and "] " in stripped:
                    items.append(stripped.split("] ", 1)[1])
                i += 1
            continue
        # Also pick up bullet items adjacent to keyword mentions
        i += 1

    return items


def _detect_category_from_content(content: str) -> str:
    """Detect skill category from content keywords."""
    keywords: dict[str, list[str]] = {
        "development": ["python", "javascript", "typescript", "rust", "go", "java", "react", "vue",
                        "frontend", "backend", "api", "fullstack", "node", "npm", "yarn"],
        "devops": ["docker", "kubernetes", "nginx", "deploy", "ci/cd", "pipeline", "terraform",
                   "ansible", "helm", "kubectl", "gitlab", "github actions"],
        "security": ["pentest", "nmap", "vulnerability", "cve", "security", "encryption", "ssh",
                     "firewall", "auth", "oauth", "oidc", "zitadel"],
        "data-science": ["pandas", "numpy", "jupyter", "analysis", "visualization", "dataset",
                         "machine learning", "deep learning", "scikit"],
        "mlops": ["model", "training", "inference", "ml", "ai", "neural", "transformer", "llm",
                  "fine-tune", "gguf", "huggingface"],
        "database": ["sql", "postgres", "mysql", "mongodb", "redis", "migration", "schema",
                     "prisma", "drizzle", "sqlalchemy"],
        "mcp": ["mcp", "model context protocol", "tool server", "stdio transport",
                "streamable http"],
        "creative": ["design", "ui", "ux", "figma", "css", "scss", "tailwind", "animation",
                     "svg", "canvas", "ascii art"],
    }

    lower = content.lower()
    scores: dict[str, int] = {}
    for cat, kws in keywords.items():
        score = sum(1 for kw in kws if kw in lower)
        if score:
            scores[cat] = score

    if scores:
        return max(scores, key=scores.get)
    return "uncategorized"


def _parse_skill_directory(path: Path, format_type: SkillFormat) -> list[BridgedSkill]:
    """Parse all skill files in a directory for a given format."""
    skills: list[BridgedSkill] = []

    if not path.exists() or not path.is_dir():
        logger.debug(f"Directory not found: {path}")
        return skills

    if format_type == SkillFormat.HERMES:
        # Hermes: skills/<category>/<name>/SKILL.md
        for skill_file in path.rglob("SKILL.md"):
            try:
                content = skill_file.read_text(encoding="utf-8")
                skill = parse_hermes_skill(content, str(skill_file))
                if skill:
                    skills.append(skill)
                    logger.debug(f"Imported Hermes skill: {skill.name} from {skill_file}")
            except Exception as e:
                logger.warning(f"Failed to parse Hermes skill {skill_file}: {e}")

    elif format_type == SkillFormat.OPENCLAW:
        # OpenClaw: skills/<category>/<name>/SKILL.md or <name>/SKILL.md
        for skill_file in path.rglob("SKILL.md"):
            try:
                content = skill_file.read_text(encoding="utf-8")
                skill = parse_openclaw_skill(content, str(skill_file))
                if skill:
                    skills.append(skill)
                    logger.debug(f"Imported OpenClaw skill: {skill.name} from {skill_file}")
            except Exception as e:
                logger.warning(f"Failed to parse OpenClaw skill {skill_file}: {e}")

    elif format_type == SkillFormat.CLAUDE:
        # Claude: CLAUDE.md files (project root or .claude/*.md)
        for md_file in path.rglob("CLAUDE.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                skill = parse_claude_md(content, str(md_file))
                if skill:
                    skills.append(skill)
                    logger.debug(f"Imported Claude skill: {skill.name} from {md_file}")
            except Exception as e:
                logger.warning(f"Failed to parse CLAUDE.md {md_file}: {e}")

        # Also scan .claude/*.md
        claude_dir = path / ".claude"
        if claude_dir.exists():
            for md_file in claude_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    skill = parse_claude_md(content, str(md_file))
                    if skill:
                        skills.append(skill)
                        logger.debug(f"Imported Claude skill: {skill.name} from {md_file}")
                except Exception as e:
                    logger.warning(f"Failed to parse {md_file}: {e}")

    elif format_type == SkillFormat.CODEX:
        # Codex: CODEX_PROFILE.md, AGENTS.md, CODEX.md
        for pattern in ["CODEX_PROFILE.md", "AGENTS.md", "CODEX.md"]:
            for md_file in path.rglob(pattern):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    skill = parse_codex_md(content, str(md_file))
                    if skill:
                        skills.append(skill)
                        logger.debug(f"Imported Codex skill: {skill.name} from {md_file}")
                except Exception as e:
                    logger.warning(f"Failed to parse {md_file}: {e}")

    return skills


# ── Exporters (BridgedSkill → format-specific output) ───────────────────────

def _ensure_skill_dir(base_dir: Path, skill: BridgedSkill, format_type: SkillFormat) -> Path:
    """Get the output directory for a skill in the given format."""
    if format_type == SkillFormat.HERMES:
        out = base_dir / "hermes" / skill.category / skill.name
    elif format_type == SkillFormat.OPENCLAW:
        out = base_dir / "openclaw" / skill.category / skill.name
    elif format_type == SkillFormat.CLAUDE:
        out = base_dir / "claude" / skill.category
    elif format_type == SkillFormat.CODEX:
        out = base_dir / "codex" / skill.category
    else:
        out = base_dir / "unknown" / skill.name
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── Import functions (public API) ───────────────────────────────────────────

def import_hermes_skills(path: str | Path) -> list[BridgedSkill]:
    """Import skills from Hermes-format SKILL.md files.

    Scans the given path recursively for SKILL.md files with Hermes frontmatter.
    """
    return _parse_skill_directory(Path(path), SkillFormat.HERMES)


def import_openclaw_skills(path: str | Path) -> list[BridgedSkill]:
    """Import skills from OpenClaw/JEBAT-format SKILL.md files.

    Scans the given path recursively for SKILL.md files with OpenClaw frontmatter.
    """
    return _parse_skill_directory(Path(path), SkillFormat.OPENCLAW)


def import_claude_skills(path: str | Path) -> list[BridgedSkill]:
    """Import skills from Claude Code CLAUDE.md files.

    Scans the given path recursively for CLAUDE.md files and .claude/*.md files.
    """
    return _parse_skill_directory(Path(path), SkillFormat.CLAUDE)


def import_codex_skills(path: str | Path) -> list[BridgedSkill]:
    """Import skills from Codex AGENTS.md / CODEX_PROFILE.md files.

    Scans the given path recursively for CODEX_PROFILE.md, AGENTS.md, CODEX.md.
    """
    return _parse_skill_directory(Path(path), SkillFormat.CODEX)


# ── Export functions (public API) ───────────────────────────────────────────

def export_to_hermes(
    skills: list[BridgedSkill],
    *,
    output_base: str | Path | None = None,
    overwrite: bool = True,
) -> list[Path]:
    """Export bridged skills to Hermes-format SKILL.md files.

    Hermes format: skills/<category>/<name>/SKILL.md with metadata.hermes tags.
    """
    base = Path(output_base or Path.home() / ".jebat" / "skills-export")
    created: list[Path] = []

    for skill in skills:
        skill_dir = _ensure_skill_dir(base, skill, SkillFormat.HERMES)
        skill_file = skill_dir / "SKILL.md"

        if skill_file.exists() and not overwrite:
            logger.info(f"Skipping existing: {skill_file}")
            continue

        # Build Hermes-format SKILL.md
        lines = ["---"]
        lines.append(f"name: {skill.name}")
        lines.append(f'description: "{skill.trigger or skill.description}"')
        if skill.version:
            lines.append(f"version: {skill.version}")
        if skill.author:
            lines.append(f"author: {skill.author}")
        if skill.platforms:
            lines.append("platforms:")
            for p in skill.platforms:
                lines.append(f"  - {p}")
        if skill.tags or skill.category != "uncategorized":
            lines.append("metadata:")
            lines.append("  hermes:")
            if skill.tags:
                lines.append("    tags:")
                for t in skill.tags:
                    lines.append(f"      - {t}")
            if skill.category:
                lines.append(f"    category: {skill.category}")
        lines.append("---")
        lines.append("")
        # Body: use original full body for Hermes (rich content preserved)
        if skill.body:
            lines.append(skill.body)
        else:
            lines.append(f"# {skill.title}")
            lines.append("")
            lines.append(skill.description)

        skill_file.write_text("\n".join(lines), encoding="utf-8")
        created.append(skill_file)
        logger.info(f"Exported Hermes skill: {skill.name} → {skill_file}")

    return created


def export_to_openclaw(
    skills: list[BridgedSkill],
    *,
    output_base: str | Path | None = None,
    overwrite: bool = True,
) -> list[Path]:
    """Export bridged skills to OpenClaw/JEBAT-format SKILL.md files.

    OpenClaw format: skills/<category>/<name>/SKILL.md with full frontmatter.
    """
    base = Path(output_base or Path.home() / ".jebat" / "skills-export")
    created: list[Path] = []

    for skill in skills:
        skill_dir = _ensure_skill_dir(base, skill, SkillFormat.OPENCLAW)
        skill_file = skill_dir / "SKILL.md"

        if skill_file.exists() and not overwrite:
            logger.info(f"Skipping existing: {skill_file}")
            continue

        skill_file.write_text(skill.to_skill_md(), encoding="utf-8")
        created.append(skill_file)
        logger.info(f"Exported OpenClaw skill: {skill.name} → {skill_file}")

    return created


def export_to_claude(
    skills: list[BridgedSkill],
    *,
    output_base: str | Path | None = None,
    overwrite: bool = True,
    single_file: bool = False,
) -> list[Path]:
    """Export bridged skills to Claude Code CLAUDE.md files.

    If single_file=True, all skills are concatenated into one CLAUDE.md.
    Otherwise, each skill gets its own file in claude/<category>/<name>.md.
    """
    base = Path(output_base or Path.home() / ".jebat" / "skills-export")
    created: list[Path] = []

    if single_file:
        # Single consolidated CLAUDE.md
        out_dir = base / "claude"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "CLAUDE.md"

        parts = []
        parts.append("# JEBAT Imported Skills")
        parts.append("")
        parts.append(f"*Auto-imported from JEBAT Cross-Agent Bridge on {datetime.now().strftime('%Y-%m-%d')}*")
        parts.append("")
        parts.append(f"Contains {len(skills)} skills imported from JEBAT.")
        parts.append("")
        parts.append("---")
        parts.append("")

        for skill in skills:
            parts.append(skill.to_claude_md())
            parts.append("")
            parts.append("---")
            parts.append("")

        out_file.write_text("\n".join(parts), encoding="utf-8")
        created.append(out_file)
        logger.info(f"Exported {len(skills)} skills to single CLAUDE.md → {out_file}")
    else:
        for skill in skills:
            out_dir = base / "claude" / skill.category
            out_dir.mkdir(parents=True, exist_ok=True)
            file_name = f"{skill.name}.md"
            out_file = out_dir / file_name

            if out_file.exists() and not overwrite:
                continue

            out_file.write_text(skill.to_claude_md(), encoding="utf-8")
            created.append(out_file)
            logger.info(f"Exported Claude skill: {skill.name} → {out_file}")

    return created


def export_to_codex(
    skills: list[BridgedSkill],
    *,
    output_base: str | Path | None = None,
    overwrite: bool = True,
    single_file: bool = True,
) -> list[Path]:
    """Export bridged skills to Codex CODEX_PROFILE.md files.

    If single_file=True, all skills are concatenated into one CODEX_PROFILE.md.
    Otherwise, each skill gets its own file.
    """
    base = Path(output_base or Path.home() / ".jebat" / "skills-export")
    created: list[Path] = []
    out_dir = base / "codex"
    out_dir.mkdir(parents=True, exist_ok=True)

    if single_file:
        out_file = out_dir / "CODEX_PROFILE.md"
        parts = []
        parts.append("# Codex Profile — Imported from JEBAT")
        parts.append("")
        parts.append(f"*Auto-imported on {datetime.now().strftime('%Y-%m-%d')}*")
        parts.append("")
        parts.append(f"Contains {len(skills)} skills from JEBAT's cross-agent bridge.")
        parts.append("")

        for skill in skills:
            parts.append(skill.to_codex_profile())
            parts.append("")
            parts.append("---")
            parts.append("")

        out_file.write_text("\n".join(parts), encoding="utf-8")
        created.append(out_file)
    else:
        for skill in skills:
            skill_dir = out_dir / skill.category
            skill_dir.mkdir(parents=True, exist_ok=True)
            out_file = skill_dir / f"{skill.name}.md"
            if out_file.exists() and not overwrite:
                continue
            out_file.write_text(skill.to_codex_profile(), encoding="utf-8")
            created.append(out_file)

    logger.info(f"Exported {len(skills)} skills to Codex format → {out_dir}")
    return created


# ── CrossAgentBridge (orchestrator) ──────────────────────────────────────────

class CrossAgentBridge:
    """Orchestrator for importing and exporting skills across agent formats.

    Automatically discovers skill files from each agent's default directories
    and provides bidirectional format conversion.

    Default search paths (OS-aware):
      - HERMES:   ~/.hermes/skills/
      - OPENCLAW: ~/.jebat/skills/ or ~/.openclaw/skills/
      - CLAUDE:   project root / .claude/ / CLAUDE.md
      - CODEX:    CODEX_PROFILE.md / AGENTS.md / CODEX.md
    """

    def __init__(
        self,
        registry_path: str | Path | None = None,
        hermes_path: str | Path | None = None,
        openclaw_path: str | Path | None = None,
        claude_path: str | Path | None = None,
        codex_path: str | Path | None = None,
    ):
        home = Path.home()

        self.registry_path = Path(registry_path or home / ".jebat" / "skills").expanduser()
        self.registry_path.mkdir(parents=True, exist_ok=True)

        # Default search paths for each agent format
        self._search_paths: dict[SkillFormat, list[Path]] = {
            SkillFormat.HERMES: [
                Path(hermes_path or home / ".hermes" / "skills").expanduser(),
            ],
            SkillFormat.OPENCLAW: [
                Path(openclaw_path or home / ".jebat" / "skills").expanduser(),
                Path(home / ".openclaw" / "skills").expanduser(),
            ],
            SkillFormat.CLAUDE: [
                Path(claude_path or home / ".claude").expanduser(),
                Path.cwd(),  # Check current project root
            ],
            SkillFormat.CODEX: [
                Path(codex_path or home / ".codex").expanduser(),
                Path.cwd(),
            ],
        }

        self.imported_skills: dict[SkillFormat, list[BridgedSkill]] = {
            fmt: [] for fmt in SkillFormat.all()
        }
        self.total_imported = 0

    def add_search_path(self, format_type: SkillFormat, path: str | Path):
        """Add an additional search path for a specific format."""
        p = Path(path).expanduser().resolve()
        if p not in self._search_paths[format_type]:
            self._search_paths[format_type].append(p)
            logger.info(f"Added {format_type.value} search path: {p}")

    # ── Import ──

    def import_from(self, format_type: SkillFormat) -> list[BridgedSkill]:
        """Import skills from a specific agent format."""
        all_skills: list[BridgedSkill] = []
        seen_names: set[str] = set()

        for search_path in self._search_paths[format_type]:
            if not search_path.exists():
                logger.debug(f"Search path not found: {search_path}")
                continue

            logger.info(f"Scanning {format_type.value} skills in: {search_path}")

            # Dispatch to correct parser based on format
            if format_type == SkillFormat.HERMES:
                skills = import_hermes_skills(search_path)
            elif format_type == SkillFormat.OPENCLAW:
                skills = import_openclaw_skills(search_path)
            elif format_type == SkillFormat.CLAUDE:
                skills = import_claude_skills(search_path)
            elif format_type == SkillFormat.CODEX:
                skills = import_codex_skills(search_path)
            else:
                skills = []

            for s in skills:
                if s.name not in seen_names:
                    all_skills.append(s)
                    seen_names.add(s.name)

        self.imported_skills[format_type] = all_skills
        self.total_imported += len(all_skills)

        logger.info(
            f"Imported {len(all_skills)} {format_type.value} skills "
            f"(total: {self.total_imported})"
        )
        return all_skills

    async def import_all(self) -> int:
        """Import skills from all available agent formats."""
        total = 0
        for fmt in SkillFormat.all():
            try:
                imported = self.import_from(fmt)
                total += len(imported)
            except Exception as e:
                logger.error(f"Failed to import {fmt.value} skills: {e}")

        logger.info(f"Cross-agent import complete: {total} skills from {len(SkillFormat.all())} formats")
        return total

    # ── Export ──

    def export_to(
        self,
        format_type: SkillFormat,
        *,
        output_base: str | Path | None = None,
        overwrite: bool = True,
        single_file: bool = False,
    ) -> list[Path]:
        """Export all imported skills to a specific agent format."""
        base = Path(output_base or self.registry_path / "exports").expanduser()

        # Flatten all imported skills
        all_skills: list[BridgedSkill] = []
        seen: set[str] = set()
        for skills in self.imported_skills.values():
            for s in skills:
                if s.name not in seen:
                    all_skills.append(s)
                    seen.add(s.name)

        if not all_skills:
            logger.warning("No skills to export. Run import_from() or import_all() first.")
            return []

        if format_type == SkillFormat.HERMES:
            return export_to_hermes(all_skills, output_base=base, overwrite=overwrite)
        elif format_type == SkillFormat.OPENCLAW:
            return export_to_openclaw(all_skills, output_base=base, overwrite=overwrite)
        elif format_type == SkillFormat.CLAUDE:
            return export_to_claude(all_skills, output_base=base, overwrite=overwrite, single_file=single_file)
        elif format_type == SkillFormat.CODEX:
            return export_to_codex(all_skills, output_base=base, overwrite=overwrite, single_file=single_file)
        else:
            logger.error(f"Unknown format: {format_type}")
            return []

    def export_all(
        self,
        output_base: str | Path | None = None,
        overwrite: bool = True,
    ) -> dict[str, list[Path]]:
        """Export all imported skills to all agent formats."""
        results: dict[str, list[Path]] = {}
        for fmt in SkillFormat.all():
            try:
                single = fmt in (SkillFormat.CLAUDE, SkillFormat.CODEX)
                paths = self.export_to(fmt, output_base=output_base, overwrite=overwrite, single_file=single)
                results[fmt.value] = paths
            except Exception as e:
                logger.error(f"Failed to export to {fmt.value}: {e}")
                results[fmt.value] = []
        return results

    # ── Registry integration ──

    def register_with_jebat(self, registry=None) -> int:
        """Register imported skills into JEBAT's SkillRegistry.

        Returns the number of skills registered.
        """
        try:
            from jebat.mcp.skill_registry import SkillRegistry, Skill as JebatSkill
        except ImportError:
            logger.warning("JEBAT SkillRegistry not available, skipping registration")
            return 0

        if registry is None:
            registry = SkillRegistry(str(self.registry_path), auto_load=False)

        count = 0
        for fmt, skills in self.imported_skills.items():
            for skill in skills:
                data = skill.to_jebat_skill()
                # Create JEBAT Skill object and add to registry
                try:
                    jebat_skill = JebatSkill(
                        name=data["name"],
                        version=data["version"],
                        description=data["description"],
                        category=data["category"],
                        author=data["author"],
                        license=data.get("license", "MIT"),
                        tags=data.get("tags", []),
                        content=data.get("content", ""),
                        path=skill.source_path,
                    )
                    # Add format tag
                    jebat_skill.tags.append(f"imported:{fmt.value}")

                    registry.skills[skill.name] = jebat_skill
                    registry._add_to_category(skill.category, skill.name)
                    registry.loaded_count += 1
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to register skill {skill.name}: {e}")

        logger.info(f"Registered {count} cross-agent skills into JEBAT registry")
        return count

    # ── Reporting ──

    def summary(self) -> dict[str, Any]:
        """Get a summary of imported skills."""
        by_format: dict[str, int] = {}
        by_category: dict[str, int] = {}
        all_names: list[str] = []

        for fmt, skills in self.imported_skills.items():
            by_format[fmt.value] = len(skills)
            for s in skills:
                all_names.append(s.name)
                cat = s.category
                by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_imported": self.total_imported,
            "unique_skills": len(set(all_names)),
            "by_format": by_format,
            "by_category": by_category,
            "formats_available": [fmt.value for fmt in SkillFormat.all()],
            "search_paths": {
                fmt.value: [str(p) for p in paths]
                for fmt, paths in self._search_paths.items()
            },
        }