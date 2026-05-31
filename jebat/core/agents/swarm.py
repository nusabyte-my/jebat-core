"""JEBAT Swarm Orchestrator — multi-agent delegation engine.

Maps ORCHESTRA.md roles to execution paths. Swarm dispatcher 
acts as the Hang Nadim classifier — decides *which* agents to
deploy and *how* (single, parallel, or consensus).

Roles:
  Hang Tuah    — Orchestrator (multitask coordinator)
  Hulubalang   — Warrior (pentest & security)
  Bendahara    — Treasurer (cost tracking & optimization)
  Tok Guru     — Sage (strategy & architecture)
  TukangBesi   — Blacksmith (code execution & builds)
  Laksamana    — Navigator (research & web search)
  Panglima     — Commander (task decomposition & planning)
"""

from __future__ import annotations

import json
from typing import Any

# ── Role definitions ───────────────────────────────────────────────────────

ROLE_DESCRIPTIONS: dict[str, str] = {
    "hang_tuah": "Admiral — coordinates multi-agent workflows, delegates to specialists",
    "hulubalang": "Warrior — security scanning, pentest, vulnerability assessment",
    "bendahara": "Treasurer — token cost analysis, optimization, budget enforcement",
    "tok_guru": "Sage — strategic planning, architecture review, design decisions",
    "tukang_besi": "Blacksmith — code generation, builds, testing, CI/CD",
    "laksamana": "Navigator — web research, data gathering, competitive analysis",
    "panglima": "Commander — task decomposition, sprint planning, milestone tracking",
}

# Mapping from role to task toolsets (for future Hermes delegate_task integration)
ROLE_TOOLSETS: dict[str, list[str]] = {
    "hang_tuah": ["terminal", "file", "web"],
    "hulubalang": ["terminal", "file", "web"],
    "bendahara": ["terminal", "file"],
    "tok_guru": ["terminal", "file", "web"],
    "tukang_besi": ["terminal", "file"],
    "laksamana": ["web", "search"],
    "panglima": ["terminal", "file"],
}


def classify_goal(goal: str) -> list[str]:
    """Hang Nadim classifier — maps a goal string to relevant roles.

    Returns a ranked list of role keys most suited for the task.
    """
    text = goal.lower()
    scores: dict[str, int] = {r: 0 for r in ROLE_DESCRIPTIONS}

    # Security/pentest keywords → Hulubalang
    if any(k in text for k in
           ["pentest", "security", "vulnerability", "scan", "exploit", "cve",
            "nmap", "sqlmap", "burp", "metasploit"]):
        scores["hulubalang"] += 10
        scores["hang_tuah"] += 3

    # Cost/token optimization → Bendahara
    if any(k in text for k in
           ["cost", "token", "budget", "optimize", "save", "cheap",
            "free", "pricing", "bill"]):
        scores["bendahara"] += 10

    # Architecture/design → Tok Guru
    if any(k in text for k in
           ["architecture", "design", "strategy", "plan", "review",
            "audit", "tradeoff", "migration"]):
        scores["tok_guru"] += 8
        scores["hang_tuah"] += 2

    # Code/build → TukangBesi
    if any(k in text for k in
           ["code", "build", "test", "compile", "deploy", "ci/cd",
            "fix", "patch", "implement", "refactor"]):
        scores["tukang_besi"] += 9

    # Research → Laksamana
    if any(k in text for k in
           ["research", "search", "find", "compare", "market",
            "competitor", "investigate", "look up"]):
        scores["laksamana"] += 8

    # Planning/decomposition → Panglima
    if any(k in text for k in
           ["sprint", "milestone", "decompose", "break down",
            "roadmap", "timeline", "estimate"]):
        scores["panglima"] += 7

    # Multi-domain tasks → Hang Tuah (orchestrator)
    domain_count = sum(1 for s in scores.values() if s > 0)
    if domain_count >= 2:
        scores["hang_tuah"] += 5

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [role for role, score in ranked if score > 0][:5]


def build_agent_prompt(role: str, goal: str, profile: str = "lean") -> str:
    """Build the prompt for a specific role agent."""
    desc_html = ROLE_DESCRIPTIONS.get(role, "")
    profile_guide = {
        "cavement": "Be extremely concise. Use 1-2 sentences. No explanations.",
        "lean": "Be concise. Use short paragraphs. Skip fluff.",
        "deep": "Provide evidence-backed reasoning. Surface tradeoffs and risks.",
    }.get(profile, "")

    return f"""You are {role.replace('_', ' ').title()} ({desc_html}).

{profile_guide}

TASK: {goal}

Return your analysis, findings, or recommendations directly.
Use the available tools to gather information if needed."""


async def dispatch_single(
    role: str,
    goal: str,
    profile: str = "lean",
) -> dict[str, Any]:
    """Dispatch a single agent by printing the prompt for the user.

    This is a synchronous dispatch pattern — JEBAT's agent loop doesn't
    have delegate_task. Instead, we print the scoped prompt so the user
    can run it directly or the orchestrator can feed it to the next turn.
    """
    prompt = build_agent_prompt(role, goal, profile)
    toolsets = ROLE_TOOLSETS.get(role, ["terminal", "file"])

    return {
        "role": role,
        "role_name": role.replace("_", " ").title(),
        "description": ROLE_DESCRIPTIONS.get(role, ""),
        "prompt": prompt,
        "toolsets": toolsets,
        "status": "ready",
    }


async def dispatch_swarm(
    roles: list[str],
    goal: str,
    profile: str = "lean",
    max_agents: int = 3,
) -> list[dict[str, Any]]:
    """Dispatch multiple agents in parallel (swarm mode).

    Each agent scopes to the same goal from their role's perspective.
    """
    import asyncio
    limited = roles[:max_agents]
    tasks = [dispatch_single(role, goal, profile) for role in limited]
    return await asyncio.gather(*tasks)


async def dispatch_consensus(
    roles: list[str],
    goal: str,
    profile: str = "lean",
    max_agents: int = 3,
) -> dict[str, Any]:
    """Dispatch multiple agents and provide all perspectives (consensus-style).

    Each role gives its take. All responses shown — user decides.
    """
    results = await dispatch_swarm(roles, goal, profile, max_agents)

    prompts = [r["prompt"] for r in results if r.get("status") == "ready"]
    roles_used = [r["role"] for r in results if r.get("status") == "ready"]

    return {
        "mode": "consensus",
        "roles": roles_used,
        "agent_count": len(prompts),
        "prompts": prompts,
    }


async def run_orchestration(
    goal: str,
    mode: str = "auto",
    roles: list[str] | None = None,
    max_agents: int = 3,
    profile: str = "lean",
) -> dict[str, Any]:
    """Main entry point for the orchestrate command.

    Args:
        goal: The task goal to orchestrate
        mode: "auto", "swarm", "consensus", or "single"
        roles: Optional explicit list of roles (overrides classifier)
        max_agents: Maximum number of agents to deploy
        profile: Prompt profile ("cavement", "lean", "deep")

    Returns:
        Dict with orchestration results
    """
    # Step 1: Classify or use provided roles
    if not roles:
        classified = classify_goal(goal)
    else:
        classified = [r.lower().replace("-", "_") for r in roles]

    if not classified:
        classified = ["hang_tuah"]

    # Step 2: Execute based on mode
    if mode == "single":
        result = await dispatch_single(classified[0], goal, profile)
    elif mode == "swarm":
        swarm = await dispatch_swarm(classified, goal, profile, max_agents)
        result = [r for r in swarm if r.get("status") == "ready"]
    elif mode == "consensus":
        result = await dispatch_consensus(classified, goal, profile, max_agents)
    else:
        # auto: single if one role, swarm if multiple
        if len(classified) == 1:
            result = await dispatch_single(classified[0], goal, profile)
        else:
            swarm = await dispatch_swarm(classified, goal, profile, max_agents)
            result = [r for r in swarm if r.get("status") == "ready"]

    return {
        "goal": goal,
        "mode": mode,
        "roles_used": classified[:max_agents],
        "profile": profile,
        "result": result,
    }