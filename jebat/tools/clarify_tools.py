"""JEBAT Clarify Tool — structured user interaction mid-task.

When the agent needs clarification, feedback, or a decision before proceeding,
it invokes clarify(question="...", choices=["A", "B"]). The tool blocks until
the user responds via stdin, then returns their choice. This replaces raw
input() calls with a structured, documented interaction path.
"""

from __future__ import annotations

import sys
from typing import Any

from jebat.tools import register_tool


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------

async def clarify(question: str, choices: list[str] | None = None) -> dict[str, Any]:
    """Present a structured question to the user and block until a response arrives.

    Two modes:
    1. Multiple choice — choices=[...], up to 5 options. User picks by letter or
       types their own free-text answer.
    2. Open-ended — no choices. User types a free-form response.

    Returns {"response": <user's answer>, "choice_index": <int or None>}
    """
    # Build prompt
    lines: list[str] = []
    lines.append("")
    lines.append("─" * 40)
    lines.append(f"  JEBAT wants to clarify:")
    lines.append(f"  {question}")
    lines.append("")

    if choices:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, choice in enumerate(choices[:5]):
            letter = letters[i]
            lines.append(f"  [{letter}] {choice}")
        lines.append("  [Write] Type your own answer")
        lines.append("")
        prompt_text = "  Your choice (letter or free text) > "
    else:
        prompt_text = "  Your answer > "

    prompt = "\n".join(lines)

    # Write prompt to stderr so it won't be captured by output
    print(prompt, file=sys.stderr, flush=True)
    print(prompt_text, file=sys.stderr, end="", flush=True)

    # Block on input
    try:
        response = input().strip()
    except (EOFError, KeyboardInterrupt):
        response = ""

    # Clear the prompt line
    print("", file=sys.stderr, flush=True)

    # Determine choice index
    choice_index: int | None = None
    if choices:
        response_upper = response.upper()
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, choice in enumerate(choices):
            if response_upper == letters[i]:
                choice_index = i
                response = choice
                break
            if response.lower() == choice.lower():
                choice_index = i
                break

    # Summary line
    if choice_index is not None:
        summary = f"User picked [{chr(65 + choice_index)}] {response}"
    elif response:
        summary = f"User answered: {response}"
    else:
        summary = "User provided no answer (empty/EOF)"

    print(f"  → {summary}", file=sys.stderr, flush=True)

    return {"response": response, "choice_index": choice_index}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    "clarify",
    schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to present to the user.",
            },
            "choices": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": (
                    "Up to 5 answer choices. Letter A-E assigned automatically. "
                    "Omit this parameter for an open-ended question."
                ),
            },
        },
        "required": ["question"],
    },
    safety_tier="auto",
    timeout=300,  # User may take time to think
    description=(
        "Ask the user a structured question when you need clarification, "
        "feedback, or a decision before proceeding. Supports multiple-choice "
        "(up to 5 options) or open-ended questions. BLOCKS until the user "
        "responds — use when you genuinely need user input, not for low-stakes "
        "decisions you can make yourself."
    ),
)(clarify)