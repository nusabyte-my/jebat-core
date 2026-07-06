"""JEBAT Skill Gatherer + Generator — PawangIlmu (Knowledge Shaman).

Auto-discover, scrape, package, and generate JEBAT skills from:
  - Web pages / blog posts / documentation
  - GitHub repos (README, docs/, wiki)
  - API documentation (OpenAPI/Swagger)
  - CLI tool help output
  - Raw text / markdown files

Generated skills follow the JEBAT SKILL.md format:
  ---
  name: skill-name
  trigger: when to use this skill
  category: domain
  ---
  # Skill Title
  ## Steps
  ## Pitfalls
  ## Verification
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# ── Skill Format ──────────────────────────────────────────────────────────

SKILL_TEMPLATE = """---
name: {name}
trigger: "{trigger}"
category: {category}
created: "{created}"
source: "{source}"
---

# {title}

{description}

## Steps

{steps}

## Pitfalls

{pitfalls}

## Verification

{verification}

## References

{references}
"""


# ── Skill Gatherer ────────────────────────────────────────────────────────

@dataclass(slots=True)
class GatheredSkill:
    name: str
    title: str
    description: str
    trigger: str
    category: str
    steps: list[str] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    source_url: str = ""
    raw_content: str = ""


async def gather_from_url(url: str, name: str | None = None) -> GatheredSkill:
    """Scrape a web page and extract skill information.
    
    Supports:
      - GitHub README repos (extracts steps, pitfalls from headings)
      - Blog posts (extracts numbered steps)
      - Documentation pages (extracts headings + code blocks)
      - Raw markdown files
    
    Safety: AUTO (read-only HTTP GET)
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
    
    content = response.text
    
    # Detect content type
    is_markdown = url.endswith(".md") or "readme" in url.lower()
    is_github = "github.com" in url
    
    if is_github and not url.endswith(".md"):
        # Try to fetch README.md from the repo
        # Extract owner/repo from URL
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if match:
            owner, repo = match.group(1), match.group(2)
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
            try:
                async with httpx.AsyncClient(timeout=15) as readme_client:
                    readme_resp = await readme_client.get(readme_url)
                    if readme_resp.status_code == 200:
                        content = readme_resp.text
                        is_markdown = True
            except Exception:
                pass
    
    # Parse content based on type
    if is_markdown:
        return _parse_markdown_skill(content, url, name)
    else:
        return _parse_html_skill(content, url, name)


def _parse_markdown_skill(content: str, source_url: str, name: str | None = None) -> GatheredSkill:
    """Parse markdown content into a GatheredSkill."""
    lines = content.split("\n")
    title = ""
    description = ""
    steps: list[str] = []
    pitfalls: list[str] = []
    verification: list[str] = []
    references: list[str] = []
    
    # Extract title from first heading
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    
    if not title:
        title = "Untitled Skill"
    
    # Auto-generate name from title
    if not name:
        name = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    
    # Parse sections by heading
    current_section = ""
    section_content: list[str] = []
    
    for line in lines:
        heading_match = re.match(r"^#{1,3}\s+(.+)", line)
        if heading_match:
            # Save previous section
            if current_section and section_content:
                _classify_section(current_section, section_content, steps, pitfalls, verification)
            current_section = heading_match.group(1).lower()
            section_content = []
        else:
            section_content.append(line)
    
    # Process last section
    if current_section and section_content:
        _classify_section(current_section, section_content, steps, pitfalls, verification)
    
    # If no steps found, extract numbered items from full content
    if not steps:
        numbered = re.findall(r"^\d+\.\s+(.+)", content, re.MULTILINE)
        steps = numbered[:10]
    
    # Extract references (links)
    link_refs = re.findall(r"https?://[^\s\)]+", content)
    references = link_refs[:5]
    
    # Generate trigger from title
    trigger = f"Use when {title.lower()}"
    
    # Determine category from content keywords
    category = _detect_category(content)
    
    return GatheredSkill(
        name=name,
        title=title,
        description=description or f"Auto-gathered from {source_url}",
        trigger=trigger,
        category=category,
        steps=steps,
        pitfalls=pitfalls,
        verification=verification,
        references=references,
        source_url=source_url,
        raw_content=content[:5000],
    )


def _parse_html_skill(content: str, source_url: str, name: str | None = None) -> GatheredSkill:
    """Parse HTML content into a GatheredSkill (basic extraction)."""
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", content)
    text = re.sub(r"\s+", " ", text).strip()
    
    # Extract title from <title> or first line
    title_match = re.search(r"<title>([^<]+)</title>", content)
    title = title_match.group(1).strip() if title_match else "Web Skill"
    
    if not name:
        name = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    
    # Extract numbered steps
    steps = re.findall(r"\d+\.\s+([^.]{10,})", text)[:10]
    
    # Detect category
    category = _detect_category(content + text)
    
    return GatheredSkill(
        name=name,
        title=title,
        description=f"Auto-gathered from {source_url}",
        trigger=f"Use when {title.lower()}",
        category=category,
        steps=steps,
        source_url=source_url,
        raw_content=text[:5000],
    )


def _classify_section(section: str, content: list[str], steps: list, pitfalls: list, verification: list):
    """Classify a markdown section into steps/pitfalls/verification."""
    text = "\n".join(content).strip()
    
    if any(kw in section for kw in ["step", "how to", "guide", "tutorial", "instruction", "setup", "install", "getting started", "usage", "quick start"]):
        numbered = re.findall(r"^\d+\.\s+(.+)", text, re.MULTILINE)
        if numbered:
            steps.extend(numbered[:10])
        else:
            # Bullet points become steps
            bullets = re.findall(r"^\s*[-*]\s+(.+)", text, re.MULTILINE)
            if bullets:
                steps.extend(bullets[:10])
    
    elif any(kw in section for kw in ["pitfall", "warning", "caution", "error", "troubleshoot", "common mistake", "gotcha", "bug", "issue", "limitation"]):
        bullets = re.findall(r"^\s*[-*]\s+(.+)", text, re.MULTILINE)
        pitfalls.extend(bullets[:10])
    
    elif any(kw in section for kw in ["verify", "test", "check", "confirm", "validation"]):
        bullets = re.findall(r"^\s*[-*]\s+(.+)", text, re.MULTILINE)
        verification.extend(bullets[:10])


def _detect_category(content: str) -> str:
    """Detect skill category from content keywords."""
    categories = {
        "devops": ["docker", "kubernetes", "nginx", "deploy", "ci/cd", "pipeline", "terraform"],
        "cybersec": ["pentest", "nmap", "vulnerability", "cve", "security", "encryption", "ssh", "firewall"],
        "web-developer": ["html", "css", "javascript", "react", "vue", "angular", "frontend", "backend"],
        "fullstack": ["api", "database", "server", "client", "fullstack", "endpoint"],
        "mlops": ["model", "training", "inference", "ml", "ai", "neural", "transformer", "llm"],
        "data-science": ["pandas", "numpy", "jupyter", "analysis", "visualization", "dataset"],
        "database": ["sql", "postgres", "mysql", "mongodb", "redis", "migration", "schema"],
        "mcp": ["mcp", "model context protocol", "tool server", "stdio transport"],
    }
    
    content_lower = content.lower()
    for cat, keywords in categories.items():
        if any(kw in content_lower for kw in keywords):
            return cat
    
    return "general"


# ── Skill Generator ───────────────────────────────────────────────────────

async def generate_skill(
    task_description: str,
    category: str = "general",
    source_context: str = "",
) -> GatheredSkill:
    """Generate a skill from a task description using LLM.
    
    This is the "self-improving" aspect — JEBAT can generate its own skills
    from task descriptions, creating reusable procedural knowledge.
    
    Safety: AUTO (LLM generation only)
    """
    # Generate skill name from task
    name = re.sub(r"[^a-z0-9]+", "-", task_description.lower()[:50]).strip("-")
    
    # Build prompt for skill generation
    system_prompt = """You are JEBAT's skill generator. Generate a SKILL.md format skill from the task description.

Format your output EXACTLY as:

---
name: <skill-name>
trigger: "<when to use>"
category: <category>
---

# <Skill Title>

<1-2 sentence description>

## Steps

1. <step 1 with exact commands if applicable>
2. <step 2>
... (5-8 steps max)

## Pitfalls

- <pitfall 1: what goes wrong and how to avoid>
- <pitfall 2>
... (3-5 pitfalls)

## Verification

- <how to verify step 1 worked>
- <how to verify the whole task succeeded>

Be specific with commands, file paths, and error messages. Include exact shell commands where relevant."""

    user_prompt = f"""Task: {task_description}

Category: {category}

Additional context: {source_context[:2000] if source_context else "None provided"}

Generate a practical, actionable skill for this task."""

    # Try to use LLM for generation
    skill_content = ""
    try:
        from jebat.llm.config import JebatLLMConfig, load_llm_config
        from jebat.llm.providers import build_provider
        
        config = load_llm_config()
        provider = build_provider(config)
        skill_content = await provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )
    except Exception:
        # Fallback: generate a basic skill from the description
        skill_content = _generate_basic_skill(name, task_description, category)
    
    # Parse generated content
    if skill_content.startswith("---"):
        return _parse_generated_skill(skill_content, name, category)
    else:
        # Raw text from LLM — wrap in skill format
        return GatheredSkill(
            name=name,
            title=task_description[:60],
            description=skill_content[:200],
            trigger=f"Use when {task_description.lower()[:50]}",
            category=category,
            steps=re.findall(r"^\d+\.\s+(.+)", skill_content, re.MULTILINE)[:8],
            pitfalls=re.findall(r"^\s*[-*]\s+(.+)", skill_content, re.MULTILINE)[:5],
            source_url="llm-generated",
            raw_content=skill_content,
        )


def _generate_basic_skill(name: str, task_description: str, category: str) -> str:
    """Fallback: generate a basic skill from description without LLM."""
    return f"""---
name: {name}
trigger: "Use when {task_description.lower()[:50]}"
category: {category}
---

# {task_description[:60]}

Auto-generated skill from task description.

## Steps

1. Research the task requirements and constraints
2. Plan the implementation approach
3. Execute the core task steps
4. Test the result against expectations
5. Document any discoveries for future reference

## Pitfalls

- Skipping research phase leads to wrong assumptions
- Not testing intermediate results wastes time on errors

## Verification

- Verify each step produces expected output
- Run end-to-end test of the complete task"""


def _parse_generated_skill(content: str, fallback_name: str, category: str) -> GatheredSkill:
    """Parse LLM-generated skill content into GatheredSkill."""
    # Parse YAML frontmatter
    frontmatter_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    fm_data: dict[str, str] = {}
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        for line in fm_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm_data[key.strip()] = value.strip().strip('"')
    
    # Parse body
    body = content
    if frontmatter_match:
        body = content[frontmatter_match.end():]
    
    # Extract sections
    title = ""
    for line in body.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break
    
    steps = re.findall(r"^\d+\.\s+(.+)", body, re.MULTILINE)[:8]
    pitfalls = re.findall(r"^\s*[-*]\s+(.+)", re.findall(r"## Pitfalls?\n(.+?)(?=\n##|\Z)", body, re.DOTALL)[0] if re.findall(r"## Pitfalls?\n(.+?)(?=\n##|\Z)", body, re.DOTALL) else "", re.MULTILINE)[:5]
    verification = re.findall(r"^\s*[-*]\s+(.+)", re.findall(r"## Verification\n(.+?)(?=\n##|\Z)", body, re.DOTALL)[0] if re.findall(r"## Verification\n(.+?)(?=\n##|\Z)", body, re.DOTALL) else "", re.MULTILINE)[:5]
    
    # If pitfalls/verification not found by section parsing, try bullet items
    if not pitfalls:
        pitfalls_match = re.findall(r"## Pitfalls?\n(.+?)(?=\n##)", body, re.DOTALL)
        if pitfalls_match:
            pitfalls = re.findall(r"[-*]\s+(.+)", pitfalls_match[0], re.MULTILINE)[:5]
    
    if not verification:
        verify_match = re.findall(r"## Verification\n(.+?)(?=\n##|\Z)", body, re.DOTALL)
        if verify_match:
            verification = re.findall(r"[-*]\s+(.+)", verify_match[0], re.MULTILINE)[:5]
    
    return GatheredSkill(
        name=fm_data.get("name", fallback_name),
        title=title or fm_data.get("name", fallback_name),
        description=fm_data.get("trigger", ""),
        trigger=fm_data.get("trigger", f"Use when {fallback_name}"),
        category=fm_data.get("category", category),
        steps=steps,
        pitfalls=pitfalls,
        verification=verification,
        source_url="llm-generated",
        raw_content=content,
    )


# ── Skill Packager ────────────────────────────────────────────────────────

def package_skill(skill: GatheredSkill, output_dir: str | Path | None = None) -> Path:
    """Package a GatheredSkill into a SKILL.md file.
    
    Args:
        skill: The gathered/generated skill
        output_dir: Directory to write to (default: ~/.jebat/skills/)
    
    Returns:
        Path to the created SKILL.md file
    """
    if output_dir is None:
        output_dir = Path.home() / ".jebat" / "skills" / skill.category
    
    output_dir = Path(output_dir)
    skill_dir = output_dir / skill.name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Write SKILL.md
    skill_md = SKILL_TEMPLATE.format(
        name=skill.name,
        title=skill.title,
        trigger=skill.trigger,
        category=skill.category,
        created=datetime.now().isoformat(),
        source=skill.source_url,
        description=skill.description,
        steps="\n".join(f"{i+1}. {s}" for i, s in enumerate(skill.steps)) if skill.steps else "1. Follow the procedure described above",
        pitfalls="\n".join(f"- {p}" for p in skill.pitfalls) if skill.pitfalls else "- None documented yet",
        verification="\n".join(f"- {v}" for v in skill.verification) if skill.verification else "- Verify the task produces expected output",
        references="\n".join(f"- {r}" for r in skill.references) if skill.references else "- None",
    )
    
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(skill_md, encoding="utf-8")
    
    # Write raw content as reference if available
    if skill.raw_content:
        ref_path = skill_dir / "references" / "source.md"
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_text(skill.raw_content[:10000], encoding="utf-8")
    
    return skill_path


# ── Skill Discovery ───────────────────────────────────────────────────────

async def discover_skills_from_repo(repo_url: str) -> list[GatheredSkill]:
    """Discover skills from a GitHub repository's docs, README, and wiki.
    
    Safety: AUTO (read-only GitHub API + raw content)
    """
    skills: list[GatheredSkill] = []
    
    # Try main README
    try:
        readme_skill = await gather_from_url(repo_url)
        if readme_skill.steps:
            skills.append(readme_skill)
    except Exception:
        pass
    
    # Try docs/ directory (common doc patterns)
    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if match:
        owner, repo = match.group(1), match.group(2)
        base = f"https://raw.githubusercontent.com/{owner}/{repo}/main"
        
        doc_paths = [
            f"{base}/docs/README.md",
            f"{base}/docs/CONTRIBUTING.md",
            f"{base}/docs/ARCHITECTURE.md",
            f"{base}/docs/DEPLOYMENT.md",
            f"{base}/.github/CONTRIBUTING.md",
        ]
        
        for doc_url in doc_paths:
            try:
                doc_skill = await gather_from_url(doc_url)
                if doc_skill.steps and doc_skill.name != readme_skill.name:
                    skills.append(doc_skill)
            except Exception:
                continue
    
    return skills


# ── CLI Helpers ────────────────────────────────────────────────────────────

def list_available_skill_sources() -> list[dict[str, str]]:
    """List common skill source URLs for gathering."""
    return [
        {"url": "https://github.com/decolua/9router", "category": "devops", "notes": "9Router — free AI proxy"},
        {"url": "https://github.com/owasp/owasp-mstg", "category": "cybersec", "notes": "OWASP Mobile Security"},
        {"url": "https://github.com/zitadel/zitadel", "category": "devops", "notes": "Zitadel OIDC/OAuth"},
        {"url": "https://github.com/openai/openai-python", "category": "mlops", "notes": "OpenAI Python SDK"},
        {"url": "https://github.com/anthropics/anthropic-cookbook", "category": "mlops", "notes": "Anthropic cookbook"},
        {"url": "https://github.com/run-llama/llama_index", "category": "mlops", "notes": "LlamaIndex RAG"},
        {"url": "https://github.com/langchain-ai/langchain", "category": "mlops", "notes": "LangChain"},
        {"url": "https://github.com/modelcontextprotocol/python-sdk", "category": "mcp", "notes": "MCP Python SDK"},
    ]