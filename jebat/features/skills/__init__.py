"""JEBAT Skills Feature — PawangIlmu (Knowledge Shaman).

Submodules:
  skill_gatherer  — Auto-discover, scrape, package skills from web/repos
  cross_agent_bridge — Import/export skills across agent formats (Hermes, OpenClaw, Claude, Codex)
"""

from jebat.features.skills.skill_gatherer import (
    GatheredSkill,
    gather_from_url,
    generate_skill,
    package_skill,
    discover_skills_from_repo,
)

from jebat.features.skills.cross_agent_bridge import (
    CrossAgentBridge,
    SkillFormat,
    import_hermes_skills,
    import_claude_skills,
    import_codex_skills,
    import_openclaw_skills,
    export_to_hermes,
    export_to_claude,
    export_to_codex,
    export_to_openclaw,
)

__all__ = [
    "GatheredSkill",
    "gather_from_url",
    "generate_skill",
    "package_skill",
    "discover_skills_from_repo",
    "CrossAgentBridge",
    "SkillFormat",
    "import_hermes_skills",
    "import_claude_skills",
    "import_codex_skills",
    "import_openclaw_skills",
    "export_to_hermes",
    "export_to_claude",
    "export_to_codex",
    "export_to_openclaw",
]