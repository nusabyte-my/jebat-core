"""JEBAT Creative MCP: product-specific, anti-slop design direction."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jebat.tools import register_tool

SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "jebat-creative"
DOMAINS = {
    "media-studio": ("Open Higgsfield", "Studio canvas, model-aware settings, generation history, compare/inspect"),
    "voice-production": ("VoiceStudio", "Script, cast, waveform, timeline, playback, export"),
    "seo-analytics": ("OpenSEO", "Question, evidence, prioritized action"),
    "workspace": ("AppFlowy", "Document canvas, semantic navigation, content-first"),
    "dictation": ("OpenWhispr", "Voice presence, transcript, edit/export, privacy state"),
    "project-management": ("OpenProject", "Work hierarchy, schedule, dependencies, state"),
    "scheduling": ("Cal.diy", "Availability, time zone, conflicts, booking state"),
    "support": ("Chatwoot", "Conversation queue, dialogue, customer context, composer"),
    "recording": ("Cap", "Capture setup, recording state, preview, trim/share"),
}


def _reference(name: str) -> str:
    path = SKILL_ROOT / "references" / name
    if not path.is_file():
        raise RuntimeError(f"JEBAT Creative reference missing: {path}")
    return path.read_text(encoding="utf-8")


@register_tool(
    "creative_brief",
    schema={
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "User and primary product job"},
            "domain": {"type": "string", "enum": sorted(DOMAINS)},
            "include_research": {"type": "boolean", "default": False},
        },
        "required": ["task", "domain"],
    },
    safety_tier="auto",
    timeout=30,
    description="Return JEBAT Creative anti-slop direction for a product-specific UI: task model, domain grammar, required proof, and strict quality gates. Does not copy reference branding or generate generic gradient/card templates.",
)
async def creative_brief(task: str, domain: str, include_research: bool = False) -> Dict[str, Any]:
    task = task.strip()
    if not task:
        raise ValueError("task must not be empty")
    if domain not in DOMAINS:
        raise ValueError(f"unknown creative domain {domain!r}")
    reference, grammar = DOMAINS[domain]
    result: Dict[str, Any] = {
        "skill": "jebat-creative",
        "version": "2.0.0",
        "task": task,
        "domain": domain,
        "reference": reference,
        "structure": grammar,
        "required_direction": [
            "State one primary action and one signature interaction justified by the product task.",
            "Use semantic tokens and preserve the host project's design system.",
            "Design real empty, loading, error, success, and recovery states.",
            "Do not invent metrics, product output, screenshots, or customer proof.",
        ],
        "quality_gates": _reference("quality-gates.md"),
        "verification": {
            "widths": [320, 375, 414, 768, "desktop"],
            "required": ["actual surface", "keyboard/focus", "reduced motion", "primary workflow", "no horizontal overflow"],
            "rule": "Unexercised checks are unknown, not passed.",
        },
    }
    if include_research:
        result["research"] = _reference("product-grammar.md")
    return result
