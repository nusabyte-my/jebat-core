"""JEBAT Autonomous Agent Tool — MCP & CLI integration.

Exposes the multi-turn ReAct agent harness (Hermes reasoning + Atomic tools)
as an MCP tool callable by IDEs and API clients.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from jebat.tools import register_tool


class AgentExecuteInput(BaseModel):
    task: str = Field(..., description="Goal, query, or coding task for autonomous multi-step execution")
    max_iterations: int = Field(default=8, ge=1, le=20, description="Max ReAct execution cycles")
    yolo: bool = Field(default=True, description="Skip interactive confirmation prompts in autonomous mode")
    model: Optional[str] = Field(default=None, description="Model to use (default: active LLM)")
    provider: Optional[str] = Field(default=None, description="Provider to use (default: active provider)")


@register_tool(
    "agent_execute",
    schema={
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Goal, query, or coding task for autonomous multi-step execution"},
            "max_iterations": {"type": "integer", "description": "Max ReAct execution cycles", "default": 8},
            "yolo": {"type": "boolean", "description": "Skip interactive confirmation in autonomous mode", "default": True},
            "model": {"type": "string", "description": "Optional model override"},
            "provider": {"type": "string", "description": "Optional provider override"},
        },
        "required": ["task"],
    },
    safety_tier="auto",
    timeout=300,
    description="Autonomous multi-turn ReAct coding agent powered by OpenManus, Hermes reasoning, and Atomic tools.",
)
async def agent_execute(
    task: str,
    max_iterations: int = 8,
    yolo: bool = True,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a task autonomously using the multi-turn ReAct agent harness."""
    from jebat_cli_new.agent import AgentLoop
    from jebat_cli_new.providers import ProviderRegistry
    from jebat.llm.config import load_llm_config

    config = load_llm_config()
    chosen_provider = provider or config.provider
    chosen_model = model or config.model

    registry = ProviderRegistry()
    loop = AgentLoop(
        registry=registry,
        default_provider=chosen_provider,
        model=chosen_model,
        yolo=yolo,
        context_window=config.context_window,
    )
    loop.max_iterations = max_iterations

    # Run step in thread to keep async event loop responsive
    step = await asyncio.to_thread(loop.step, task, provider=chosen_provider, model=chosen_model)

    return {
        "success": True,
        "task": task,
        "answer": step.response.text,
        "tool_actions": step.tool_actions,
        "tokens_used": step.response.tokens_used,
        "latency_ms": step.response.latency_ms,
        "model": step.response.model,
        "provider": step.response.provider,
    }


class AGIExecuteInput(BaseModel):
    goal: str = Field(..., description="High-level goal across Build, Design, Copywriting, or Fullstack")
    domain: Optional[str] = Field(default="auto", description="Domain focus: 'auto', 'build', 'design', 'copywriting', 'database'")
    max_iterations: int = Field(default=8, ge=1, le=20, description="Max autonomous ReAct iterations")


@register_tool(
    "agi_execute",
    schema={
        "type": "object",
        "properties": {
            "goal": {"type": "string", "description": "High-level goal across Build, Design, Copywriting, or Fullstack"},
            "domain": {"type": "string", "enum": ["auto", "build", "design", "copywriting", "database"], "default": "auto"},
            "max_iterations": {"type": "integer", "default": 8},
        },
        "required": ["goal"],
    },
    safety_tier="auto",
    timeout=300,
    description="Autonomous Sovereign AGI Engine: executes goal through Perception -> Reason -> Act -> Reflexion (Build/Hallmark/Copy) -> Consolidate.",
)
async def agi_execute(
    goal: str,
    domain: str = "auto",
    max_iterations: int = 8,
) -> Dict[str, Any]:
    """Execute a goal using the sovereign AGI multi-domain cognitive architecture."""
    from jebat.core.agi_core import AGICognitiveEngine
    from jebat_cli_new.agent import AgentLoop
    from jebat_cli_new.providers import ProviderRegistry
    from jebat.llm.config import load_llm_config

    engine = AGICognitiveEngine()
    perception = engine.perceive(goal)
    config = load_llm_config()

    # Enrich prompt with grounded epistemic perception frame
    context_frame = (
        f"Target Domain: {perception['detected_domain'].upper()}\n"
        f"Project: {perception['project_name']}\n"
    )
    if perception.get("project_facts"):
        context_frame += "Known Project Facts:\n" + "\n".join(f"- {f}" for f in perception["project_facts"][:5]) + "\n"
    if perception.get("copy_guidelines"):
        context_frame += "Copywriting Conversion Invariants:\n" + "\n".join(f"- {g}" for g in perception["copy_guidelines"]) + "\n"

    full_prompt = f"GOAL: {goal}\n\n[AGI_PERCEPTION_FRAME]\n{context_frame}\nExecute with full autonomous ReAct reasoning. Self-correct on any Reflexion Gate failure."

    registry = ProviderRegistry()
    loop = AgentLoop(
        registry=registry,
        default_provider=config.provider,
        model=config.model,
        yolo=True,
        context_window=config.context_window,
    )
    loop.max_iterations = max_iterations

    step = await asyncio.to_thread(loop.step, full_prompt)

    return {
        "status": "completed",
        "goal": goal,
        "domain": perception["detected_domain"],
        "deliverable": step.response.text,
        "actions_taken": step.tool_actions,
        "iterations_used": len(step.tool_actions) + 1,
        "tokens_used": step.response.tokens_used,
        "latency_ms": step.response.latency_ms,
        "guidance": "Delivered through sovereign multi-domain Reflexion gates.",
    }
