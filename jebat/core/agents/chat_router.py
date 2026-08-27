"""
Prompt-to-swarm routing helpers for JEBAT chat surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .orchestrator import AgentTask, ExecutionMode

SWARM_MODEL_ALIASES = {"jebat-swarm", "jebat-consensus", "jebat-research"}
LEGENDARY_MODEL_ALIASES = {"jebat-legend", "jebat-tuah", "jebat-nadim"}


@dataclass(frozen=True, slots=True)
class HangNadimClassification:
    """First-pass routing decision made by the Hang Nadim classifier."""

    route: str
    reason: str
    required_capabilities: list[str]
    execution_mode: ExecutionMode
    enable_search: bool = False


def should_route_prompt_to_swarm(prompt: str, requested_model: str | None = None) -> bool:
    """Return True when a prompt is a better fit for the swarm path."""
    decision = classify_prompt_with_hang_nadim(prompt, requested_model=requested_model)
    return decision.route in {"swarm", "legendary_swarm"}


def classify_prompt_with_hang_nadim(
    prompt: str,
    requested_model: str | None = None,
) -> HangNadimClassification:
    """Classify a prompt into normal chat, standard swarm, or legendary swarm."""
    requested = (requested_model or "").strip().lower()
    text = prompt.lower()

    if requested in LEGENDARY_MODEL_ALIASES:
        return HangNadimClassification(
            route="legendary_swarm",
            reason="Explicit legendary swarm model requested.",
            required_capabilities=["strategy", "reconnaissance", "defense"],
            execution_mode=ExecutionMode.CONSENSUS,
            enable_search=True,
        )

    if requested in SWARM_MODEL_ALIASES:
        execution_mode = ExecutionMode.SWARM if requested == "jebat-research" else ExecutionMode.CONSENSUS
        return HangNadimClassification(
            route="swarm",
            reason="Explicit swarm model requested.",
            required_capabilities=["research", "review"],
            execution_mode=execution_mode,
            enable_search=True,
        )

    research_terms = (
        "research",
        "investigate",
        "look up",
        "find out",
        "compare",
        "evaluate",
        "analyze",
        "search",
    )
    judgment_terms = (
        "judge",
        "decide",
        "recommend",
        "best approach",
        "best option",
        "what should we do",
        "which should",
        "safest way",
        "tradeoff",
    )
    legendary_terms = {
        "strategy": ("strategy", "direction", "best path", "tradeoff"),
        "reconnaissance": ("recon", "discovery", "map the terrain", "inventory", "find every"),
        "defense": ("protect", "defend", "guardrail", "hardening", "resilience", "safest"),
        "stability": ("stability", "reliability", "release confidence", "rollback", "support"),
        "intelligence": ("route intelligently", "classify intent", "triage", "intelligence", "orchestrated"),
    }

    has_research = any(term in text for term in research_terms)
    has_judgment = any(term in text for term in judgment_terms)
    matched_legendary_caps = [
        capability
        for capability, keywords in legendary_terms.items()
        if any(keyword in text for keyword in keywords)
    ]

    if matched_legendary_caps and (has_research or has_judgment):
        capabilities = _dedupe_preserve_order(
            ["strategy", "reconnaissance", "defense", *matched_legendary_caps]
        )
        return HangNadimClassification(
            route="legendary_swarm",
            reason="Prompt needs strategic judgment with legendary specialist routing.",
            required_capabilities=capabilities,
            execution_mode=ExecutionMode.CONSENSUS,
            enable_search=True,
        )

    if has_research and has_judgment:
        return HangNadimClassification(
            route="swarm",
            reason="Prompt requires research plus judgment.",
            required_capabilities=["research", "review"],
            execution_mode=ExecutionMode.CONSENSUS,
            enable_search=True,
        )

    explicit_patterns = (
        "research and decide",
        "compare options",
        "make a judgment",
        "make judgement",
        "decide what to do",
        "find the best way",
        "evaluate the best",
    )
    if any(pattern in text for pattern in explicit_patterns):
        return HangNadimClassification(
            route="swarm",
            reason="Prompt matches a swarm-oriented decision pattern.",
            required_capabilities=["research", "review"],
            execution_mode=ExecutionMode.CONSENSUS,
            enable_search=True,
        )

    return HangNadimClassification(
        route="chat",
        reason="Prompt is a normal single-model chat request.",
        required_capabilities=[],
        execution_mode=ExecutionMode.SINGLE,
        enable_search=False,
    )


def infer_swarm_task(
    prompt: str,
    *,
    user_id: str = "default",
    requested_model: str | None = None,
    orchestrator=None,
) -> AgentTask:
    """Infer a swarm task from a chat prompt."""
    text = prompt.lower()
    decision = classify_prompt_with_hang_nadim(prompt, requested_model=requested_model)
    execution_mode = decision.execution_mode
    require_consensus = execution_mode == ExecutionMode.CONSENSUS

    task = AgentTask(
        description=prompt,
        user_id=user_id,
        execution_mode=execution_mode,
        enable_search=decision.enable_search,
        max_agents=5,
        require_consensus=require_consensus,
        parameters={
            "hang_nadim_reason": decision.reason,
            "hang_nadim_route": decision.route,
            "required_capabilities": list(decision.required_capabilities),
        },
    )

    if orchestrator is not None and hasattr(orchestrator, "_extract_task_capabilities"):
        extracted_capabilities = sorted(orchestrator._extract_task_capabilities(task))
        if decision.required_capabilities:
            task.required_capabilities = _dedupe_preserve_order(
                [*decision.required_capabilities, *extracted_capabilities]
            )
        else:
            task.required_capabilities = extracted_capabilities

    if not task.required_capabilities:
        task.required_capabilities = decision.required_capabilities or _fallback_capabilities(text)

    if decision.route == "legendary_swarm":
        task.max_agents = max(task.max_agents, min(5, len(task.required_capabilities)))

    return task


def format_swarm_result_text(result: Dict[str, Any]) -> str:
    """Format a swarm result payload into readable assistant text."""
    if not isinstance(result, dict):
        return "No consensus decision available."

    reducer_result = ((result.get("reducer") or {}).get("result") or {}) if isinstance(result, dict) else {}
    doctrine_result = ((result.get("doctrine") or {}).get("result") or {}) if isinstance(result, dict) else {}
    consensus = result.get("consensus", {})

    decision = (
        reducer_result.get("synthesized_decision")
        or reducer_result.get("decision")
        or consensus.get("decision")
        or result.get("summary")
        or "No consensus decision available."
    )
    confidence = reducer_result.get("confidence", consensus.get("agreement"))
    actions = reducer_result.get("recommended_next_actions") or result.get("recommended_next_actions", [])
    doctrine_checks = doctrine_result.get("doctrine_checks", [])
    conflicts = reducer_result.get("conflicts", [])

    lines = [decision]
    if confidence is not None:
        lines.append(f"Confidence: {float(confidence):.2f}")
    if actions:
        lines.append("")
        lines.append("Next actions:")
        for action in actions[:5]:
            lines.append(f"- {action}")
    if doctrine_checks:
        lines.append("")
        lines.append("Doctrine checks:")
        for check in doctrine_checks[:3]:
            lines.append(f"- {check}")
    if conflicts:
        lines.append("")
        lines.append("Conflicts observed:")
        for conflict in conflicts[:3]:
            decision_text = str(conflict.get("decision", "")).strip()
            votes = conflict.get("votes")
            if decision_text:
                suffix = f" ({votes} vote)" if votes == 1 else (f" ({votes} votes)" if votes else "")
                lines.append(f"- {decision_text}{suffix}")
    return "\n".join(lines)


def _fallback_capabilities(text: str) -> list[str]:
    """Infer capabilities when the orchestrator is not available."""
    capability_keywords = {
        "database": ("database", "sql", "migration", "schema", "query"),
        "operations": ("deploy", "rollout", "ops", "infrastructure", "rollback"),
        "review": ("review", "validate", "regression", "verify"),
        "security": ("security", "harden", "vulnerability", "risk"),
        "design": ("ui", "ux", "design", "frontend"),
        "research": ("research", "search", "investigate", "compare"),
        "development": ("implement", "refactor", "code", "fix"),
    }

    capabilities: list[str] = []
    for capability, keywords in capability_keywords.items():
        if any(keyword in text for keyword in keywords):
            capabilities.append(capability)

    if not capabilities:
        return ["research", "review"]
    return capabilities


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    output: list[str] = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        output.append(value)
        seen.add(value)
    return output
