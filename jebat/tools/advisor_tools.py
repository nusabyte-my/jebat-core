"""JEBAT Advisor Tools — System One typed decisions as MCP tools.

Exposes the /api/advisor endpoints as registered JEBAT tools so they
appear in the MCP tool listing alongside ghost, memory, design, etc.
"""

from __future__ import annotations

import json
from typing import Any, List

from jebat.tools import register_tool


@register_tool(
    "advisor_classify",
    description="Classify text into one of N categories using a fast typed decision (Jev-style System One). Returns the chosen category with confidence and per-category probabilities. ~100ms, near-zero cost.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to classify"},
            "categories": {"type": "array", "items": {"type": "string"}, "description": "List of category labels (2-255)"},
            "instructions": {"type": "string", "description": "Classification instructions"},
        },
        "required": ["text", "categories"],
    },
)
async def advisor_classify(text: str, categories: List[str], instructions: str = "Classify this text into the most fitting category.") -> str:
    from routers.advisor import _decide
    questions = {
        "category": {
            "type": "Choice",
            "instructions": instructions,
            "candidates": categories,
        }
    }
    answers, backend = await _decide(text, questions)
    result = answers.get("category", {})
    return json.dumps({
        "category": result.get("answer", "unknown"),
        "confidence": result.get("confidence", 0.0),
        "probabilities": result.get("probabilities", {}),
        "backend": backend,
    }, indent=2)


@register_tool(
    "advisor_verify",
    description="Yes/no verification of a claim against text using a typed decision (Jev-style System One). Returns boolean result with calibrated probability. ~100ms.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Context/evidence text"},
            "claim": {"type": "string", "description": "The claim to verify against the text"},
        },
        "required": ["text", "claim"],
    },
)
async def advisor_verify(text: str, claim: str) -> str:
    from routers.advisor import _decide
    questions = {
        "check": {
            "type": "Noul",
            "instructions": claim,
        }
    }
    answers, backend = await _decide(text, questions)
    result = answers.get("check", {})
    return json.dumps({
        "result": result.get("answer", False),
        "probability": result.get("probability", 0.5),
        "backend": backend,
    }, indent=2)


@register_tool(
    "advisor_score",
    description="Rate text on a scale using a typed decision (Jev-style System One). Returns the score index, level label, and confidence. ~100ms.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to score"},
            "criteria": {"type": "array", "items": {"type": "string"}, "description": "Scale levels from lowest to highest"},
            "instructions": {"type": "string", "description": "Scoring instructions"},
        },
        "required": ["text", "criteria"],
    },
)
async def advisor_score(text: str, criteria: List[str], instructions: str = "Rate this text on the given scale.") -> str:
    from routers.advisor import _decide
    questions = {
        "rating": {
            "type": "Score",
            "instructions": instructions,
            "criteria": criteria,
        }
    }
    answers, backend = await _decide(text, questions)
    result = answers.get("rating", {})
    score_idx = result.get("answer", 0)
    return json.dumps({
        "score": score_idx,
        "level": criteria[score_idx] if score_idx < len(criteria) else "unknown",
        "confidence": result.get("confidence", 0.0),
        "backend": backend,
    }, indent=2)


@register_tool(
    "advisor_decide",
    description="Full typed-decision endpoint — send unstructured state + multiple typed questions (Noul/Choice/Score) and get all answers with calibrated probabilities in a single parallel pass. Jev-compatible.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "state": {"type": "string", "description": "Unstructured context/state to judge"},
            "questions": {"type": "object", "description": "Named typed questions: {key: {type: 'Noul'|'Choice'|'Score', ...}}"},
        },
        "required": ["state", "questions"],
    },
)
async def advisor_decide(state: str, questions: Any) -> str:
    from routers.advisor import _decide
    if isinstance(questions, str):
        questions = json.loads(questions)
    answers, backend = await _decide(state, questions)
    return json.dumps({
        "answers": answers,
        "backend": backend,
    }, indent=2)


@register_tool(
    "advisor_gate",
    description="Pre-flight safety check for destructive operations. Classifies the operation risk level and returns go/no-go.",
    safety_tier="auto",
    schema={
        "type": "object",
        "properties": {
            "operation": {"type": "string", "description": "Description of the operation to evaluate"},
            "tool_name": {"type": "string", "description": "Name of the tool to be called"},
            "arguments_summary": {"type": "string", "description": "Summary of arguments"},
        },
        "required": ["operation"],
    },
)
async def advisor_gate(operation: str, tool_name: str = "", arguments_summary: str = "") -> str:
    from routers.advisor import _decide
    state = f"Operation: {operation}\nTool: {tool_name}\nArgs: {arguments_summary}"
    questions = {
        "risk": {
            "type": "Choice",
            "instructions": "Assess the risk level of this operation",
            "candidates": ["safe", "risky", "dangerous"],
        }
    }
    answers, backend = await _decide(state, questions)
    result = answers.get("risk", {})
    risk_level = result.get("answer", "unknown")
    return json.dumps({
        "risk_level": risk_level,
        "confidence": result.get("confidence", 0),
        "probabilities": result.get("probabilities", {}),
        "recommendation": "proceed" if risk_level == "safe" else "verify",
        "backend": backend,
    }, indent=2)
