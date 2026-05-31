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

import asyncio
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


# ── Swarm result cache ─────────────────────────────────────────────────────
# Deduplicates identical goals so repeated queries don't re-dispatch.

import hashlib
import os

SWARM_CACHE_DIR = os.path.expanduser("~/.jebat/swarm_cache")


def _ensure_cache_dir() -> None:
    os.makedirs(SWARM_CACHE_DIR, exist_ok=True)


def _swarm_cache_key(goal: str, mode: str, profile: str, max_agents: int) -> str:
    raw = f"{goal}::{mode}::{profile}::{max_agents}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _swarm_cache_load(key: str) -> dict | None:
    path = os.path.join(SWARM_CACHE_DIR, f"{key}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _swarm_cache_save(key: str, data: dict) -> None:
    _ensure_cache_dir()
    path = os.path.join(SWARM_CACHE_DIR, f"{key}.json")
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except OSError:
        pass  # Cache is best-effort


def _swarm_cache_invalidate() -> int:
    """Clear all cached swarm results. Returns count of files removed."""
    _ensure_cache_dir()
    count = 0
    for fname in os.listdir(SWARM_CACHE_DIR):
        if fname.endswith(".json"):
            try:
                os.remove(os.path.join(SWARM_CACHE_DIR, fname))
                count += 1
            except OSError:
                pass
    return count


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
    execute: bool = False,
    model_override: str = "",
    provider_override: str = "",
) -> dict[str, Any]:
    """Dispatch a single agent. If execute=True, actually runs via AgentLoop.

    Args:
        role: Role key (hang_tuah, hulubalang, etc.)
        goal: The task goal
        profile: cavement/lean/deep
        execute: If True, actually invoke AgentLoop and return real results
        model_override: Optional model override for cost-aware routing
        provider_override: Optional provider override for cost-aware routing
    """
    from jebat.features.token_saver import model_for_profile

    prompt = build_agent_prompt(role, goal, profile)
    toolsets = ROLE_TOOLSETS.get(role, ["terminal", "file"])

    # Cost-aware model selection
    if not model_override:
        model_override = model_for_profile(profile)

    result = {
        "role": role,
        "role_name": role.replace("_", " ").title(),
        "description": ROLE_DESCRIPTIONS.get(role, ""),
        "prompt": prompt,
        "toolsets": toolsets,
        "model": model_override,
        "profile": profile,
        "executed": execute,
        "status": "ready",
    }

    if execute:
        try:
            from jebat.core.agent_loop import AgentLoop
            loop = AgentLoop(
                model_override=model_override,
                provider_override=provider_override or None,
                preset=profile,
            )
            agent_result = await loop.run(prompt)
            result["response"] = agent_result.final_response
            result["iterations"] = agent_result.iterations
            result["tool_calls"] = [tc.model_dump() if hasattr(tc, 'model_dump') else str(tc) for tc in agent_result.tool_calls]
            result["status"] = "completed"
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)

    return result


async def dispatch_swarm(
    roles: list[str],
    goal: str,
    profile: str = "lean",
    max_agents: int = 3,
    execute: bool = False,
    model_override: str = "",
) -> list[dict[str, Any]]:
    """Dispatch multiple agents in parallel (swarm mode).

    Each agent scopes to the same goal from their role's perspective.
    When execute=True, all agents run concurrently via AgentLoop
    (respects max_agents cap to avoid thrashing).
    """
    limited = roles[:max_agents]
    tasks = [dispatch_single(role, goal, profile, execute=execute, model_override=model_override) for role in limited]
    return await asyncio.gather(*tasks)


async def dispatch_consensus(
    roles: list[str],
    goal: str,
    profile: str = "lean",
    max_agents: int = 3,
    execute: bool = False,
    model_override: str = "",
) -> dict[str, Any]:
    """Dispatch multiple agents and provide all perspectives (consensus-style).

    Each role gives its take. All responses shown — user decides.
    When profile="deep", applies Taming Sari reduction:
    merges conflicting outputs, flags contradictions, synthesizes final answer.
    """
    results = await dispatch_swarm(roles, goal, profile, max_agents,
                                    execute=execute, model_override=model_override)

    prompts = [r["prompt"] for r in results if r.get("status") in ("ready", "completed")]
    roles_used = [r["role"] for r in results if r.get("status") in ("ready", "completed")]

    out = {
        "mode": "consensus",
        "roles": roles_used,
        "agent_count": len(prompts),
        "prompts": prompts,
    }

    # LEGENDARY: Taming Sari reduction for deep+consensus mode
    # Collect actual responses and merge them
    if profile == "deep" and execute:
        responses = [r.get("response", "") or r.get("prompt", "") for r in results]
        if len(responses) >= 2:
            taming = taming_sari_reduce(responses, goal)
            out["taming_sari"] = taming
            out["synthesis"] = taming.get("synthesis", "")
            out["contradictions"] = taming.get("contradictions", [])

    return out


async def run_orchestration(
    goal: str,
    mode: str = "auto",
    roles: list[str] | None = None,
    max_agents: int = 3,
    profile: str = "lean",
    execute: bool = False,
    model_override: str = "",
    provider_override: str = "",
) -> dict[str, Any]:
    """Main entry point for the orchestrate command.

    Args:
        goal: The task goal to orchestrate
        mode: "auto", "swarm", "consensus", or "single"
        roles: Optional explicit list of roles (overrides classifier)
        max_agents: Maximum number of agents to deploy
        profile: Prompt profile ("cavement", "lean", "deep")
        execute: If True, actually run agents via AgentLoop
        model_override: Optional model override
        provider_override: Optional provider override

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

    # Check swarm cache before dispatching (skip cache when executing)
    cache_key = _swarm_cache_key(goal, mode, profile, max_agents)
    if not execute:
        cached = _swarm_cache_load(cache_key)
        if cached is not None:
            cached["from_cache"] = True
            return cached

    # Cost-aware model: if profile=deep and no override, pick premium
    if not model_override:
        from jebat.features.token_saver import model_for_profile
        model_override = model_for_profile(profile)

    # Step 2: Execute based on mode
    if mode == "single":
        result = await dispatch_single(classified[0], goal, profile,
                                        execute=execute, model_override=model_override,
                                        provider_override=provider_override)
    elif mode == "swarm":
        swarm = await dispatch_swarm(classified, goal, profile, max_agents,
                                      execute=execute, model_override=model_override)
        result = [r for r in swarm if r.get("status") in ("ready", "completed")]
    elif mode == "consensus":
        result = await dispatch_consensus(classified, goal, profile, max_agents,
                                           execute=execute, model_override=model_override)
    else:
        # auto: single if one role, swarm if multiple
        if len(classified) == 1:
            result = await dispatch_single(classified[0], goal, profile,
                                            execute=execute, model_override=model_override,
provider_override=provider_override)
        else:
            swarm = await dispatch_swarm(classified, goal, profile, max_agents,
                                          execute=execute, model_override=model_override)
            result = [r for r in swarm if r.get("status") in ("ready", "completed")]
    out = {
        "goal": goal,
        "mode": mode,
        "roles_used": classified[:max_agents],
        "profile": profile,
        "model": model_override,
        "executed": execute,
        "result": result,
        "from_cache": False,
    }

    # Cache the result for future deduplication
    if not execute:
        _swarm_cache_save(cache_key, out)

    return out

# ── LEGENDARY: Taming Sari reduction ────────────────────────────────────────
# When deep+consensus mode runs with execute=True, the Taming Sari layer
# merges conflicting outputs, flags contradictions, and synthesizes a final
# unified answer. Named after Hang Tuah's legendary kris.

def taming_sari_reduce(
    responses: list[str],
    goal: str,
    max_summary_chars: int = 500,
) -> dict[str, Any]:
    """Merge and reduce multiple agent responses into one coherent answer.

    The Taming Sari (Hang Tuah's kris) cuts through noise, identifies
    conflicts, and produces a single sharp synthesis.

    Args:
        responses: List of agent response strings
        goal: The original task goal for context
        max_summary_chars: Max chars for the synthesized summary

    Returns:
        Dict with synthesis, contradictions, agent_count
    """
    contradictions: list[str] = []
    key_points: list[str] = []
    seen_points: set[str] = set()

    for i, resp in enumerate(responses):
        # Simple conflict detection: look for negation patterns
        lower = resp.lower()
        for j in range(i + 1, len(responses)):
            lower_j = responses[j].lower()
            # Check for common contradiction markers
            if ("not " in lower and lower_j != lower and j > i) or \
               ("however" in lower and "however" in lower_j):
                contradictions.append(
                    f"Agent {i+1} vs Agent {j+1}: potential conflict detected"
                )

        # Extract first 2 sentences from each response as key points
        sentences = resp.replace("\n", " ").strip().split(". ")
        for s in sentences[:2]:
            clean = s.strip()
            if len(clean) > 20 and clean not in seen_points:
                key_points.append(clean)
                seen_points.add(clean)

    # Synthesize
    synthesis_parts = []
    if key_points:
        synthesis_parts.extend(key_points[:5])
    else:
        synthesis_parts.append("Agents provided analysis on: " + goal[:100])

    synthesis = ". ".join(synthesis_parts)
    if len(synthesis) > max_summary_chars:
        synthesis = synthesis[:max_summary_chars - 3] + "..."

    return {
        "synthesis": synthesis,
        "contradictions": contradictions[:5],
        "agents_consulted": len(responses),
        "key_points_count": len(key_points),
    }
