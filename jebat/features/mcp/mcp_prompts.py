"""Guided workflow prompt catalog for the MCP prompts surface.

Extracted from mcp_server.py (P2-4 monolith split). `prompts_list` serves
prompts/list; `prompts_get` serves prompts/get. Pure payload builders — no
JSON-RPC or transport concerns.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

def prompts_list(terse: bool = False) -> Dict:
    """Return reusable prompts for governed agent workflows."""
    raw_prompts = [
        {
            "name": "plan-act-verify-remember",
            "description": "Run a governed JEBAT task from intent through durable memory.",
            "arguments": [
                {"name": "task", "description": "The task to perform", "required": True},
                {"name": "scope", "description": "Files, services, or systems in scope", "required": False},
            ],
        },
        {
            "name": "hallmark-design-audit",
            "description": "Audit UI markup against Hallmark 6-axis anti-slop gates and 8-state interaction rules.",
            "arguments": [
                {"name": "markup", "description": "UI component markup or code", "required": True},
                {"name": "component_type", "description": "Type of component (button, card, hero, pricing)", "required": False},
            ],
        },
        {
            "name": "sales-copy-review",
            "description": "Mandatory copywriting conversion review: strip AI buzzwords and transform generic CTAs.",
            "arguments": [
                {"name": "copy", "description": "Sales or marketing text to audit", "required": True},
                {"name": "benefit", "description": "Specific tangible benefit the customer achieves", "required": False},
            ],
        },
        {
            "name": "project-onboard",
            "description": "Auto-scan project files and SelfLearn memory to produce a comprehensive project context snapshot.",
            "arguments": [
                {"name": "root", "description": "Project root directory", "required": False},
            ],
        },
        {
            "name": "kb-review",
            "description": "Review JEBAT knowledge base: analyze strong areas, stale memories, knowledge gaps, and suggested consolidation actions.",
            "arguments": [
                {"name": "focus_area", "description": "Optional focus area or topic to evaluate", "required": False},
            ],
        },
        {
            "name": "debug-this",
            "description": "Structured 5-step debugging workflow for diagnosing and fixing errors.",
            "arguments": [
                {"name": "error_message", "description": "The error message or traceback to debug", "required": True},
                {"name": "file", "description": "File or module where the error occurred", "required": False},
                {"name": "context", "description": "Additional context, reproducer, or logs", "required": False},
            ],
        },
    ]
    if terse:
        terse_prompts = []
        for p in raw_prompts:
            tp: Dict[str, Any] = {"name": p["name"]}
            req_args = [a for a in p.get("arguments", []) if a.get("required")]
            if req_args:
                tp["arguments"] = req_args
            terse_prompts.append(tp)
        return {"prompts": terse_prompts}
    return {"prompts": raw_prompts}

def prompts_get(params: Dict) -> Dict:
    """Return the requested guided workflow prompt."""
    name = params.get("name", "")
    arguments = params.get("arguments", {})

    if name == "plan-act-verify-remember":
        task = arguments.get("task", "the requested task")
        scope = arguments.get("scope", "the current workspace")
        text = (
            f"Perform this task: {task}\nScope: {scope}\n\n"
            "First plan the smallest reversible change. Before each CONFIRM or "
            "DANGEROUS action, return the exact operation and wait for approval. "
            "After execution, verify the user-visible result and remember only "
            "durable non-secret project facts."
        )
        return {
            "description": "Governed JEBAT task workflow",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }

    if name == "hallmark-design-audit":
        markup = arguments.get("markup", "")
        c_type = arguments.get("component_type", "generic")
        text = (
            f"Audit this {c_type} markup against Hallmark standards:\n\n{markup}\n\n"
            "Evaluate against:\n"
            "1. 6-Axis Scoring (Philosophy, Hierarchy, Execution, Specificity, Restraint, Variety)\n"
            "2. 8-State Interactive Discipline (default, hover, focus-visible, active, disabled, loading, error, success)\n"
            "3. Hard Rules: No italic headers, no re-drawn browser chrome, responsive at 320/375/768px.\n"
            "Provide the Hallmark score stamp: /* Hallmark · pre-emit critique: P# H# E# S# R# V# */ and concrete fixes."
        )
        return {
            "description": "Hallmark anti-slop design audit prompt",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }

    if name == "sales-copy-review":
        copy = arguments.get("copy", "")
        benefit = arguments.get("benefit", "clear value proposition")
        text = (
            f"Perform a sales copywriting review on this text:\n\n{copy}\n\n"
            f"Target Benefit: {benefit}\n\n"
            "Requirements:\n"
            "1. Transform any generic CTA into [Action Verb] + [What They Get].\n"
            "2. Strip banned AI buzzwords (delve, testament, tapestry, seamless, game-changer).\n"
            "3. Ensure benefits over features, customer language, and active voice.\n"
            "4. Enforce: No fabricated statistics, testimonials, or claims."
        )
        return {
            "description": "Sales copywriting conversion review prompt",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }
    if name == "project-onboard":
        root_arg = arguments.get("root")
        root_dir = Path(root_arg).resolve() if root_arg else Path(os.getcwd()).resolve()

        snippets = []
        common_files = ["package.json", "pyproject.toml", "tsconfig.json", ".jebat/memory.json", "README.md"]
        for rel_name in common_files:
            target_file = root_dir / rel_name
            try:
                if target_file.is_file():
                    content = target_file.read_text(encoding="utf-8", errors="replace")
                    snippet = content[:4000] + ("\n... [truncated]" if len(content) > 4000 else "")
                    snippets.append(f"--- {rel_name} ---\n{snippet}")
            except Exception as e:
                logger.debug(f"Could not read {target_file} for project-onboard prompt: {e}")

        files_context = "\n\n".join(snippets) if snippets else "No common project configuration files found."

        prompt_text = (
            f"You are onboarding to the project located at '{root_dir}'.\n\n"
            f"Project configuration and context files detected:\n\n{files_context}\n\n"
            "Please analyze this project:\n"
            "1. Identify the tech stack, languages, frameworks, and architecture.\n"
            "2. Note key conventions, build/test commands, and entry points.\n"
            "3. Check for any prior project memory or gotchas.\n"
            "4. Produce a comprehensive project context snapshot summarizing your findings."
        )
        return {
            "description": "Auto-scan project files and SelfLearn memory to produce a comprehensive project context snapshot.",
            "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}],
        }



    if name == "kb-review":
        focus_area = arguments.get("focus_area", "all domains")
        stats_text = "Memory stats unavailable."
        try:
            from jebat.tools.automimpi_tools import _get_memory, _get_automimpi
            memory = _get_memory()
            automimpi = _get_automimpi()
            total = len(memory.traces)
            profile = automimpi._build_learning_profile()
            strong = ", ".join(profile.strong_areas) if profile.strong_areas else "none"
            weak = ", ".join(profile.weak_areas) if profile.weak_areas else "none"
            gaps = ", ".join(profile.knowledge_gaps) if profile.knowledge_gaps else "none"
            patterns = len(getattr(memory, "extracted_patterns", []))
            stats_text = (
                f"Total memories: {total}\n"
                f"Strong areas: {strong}\n"
                f"Weak areas: {weak}\n"
                f"Knowledge gaps: {gaps}\n"
                f"Consolidated patterns: {patterns}\n"
                f"Consolidation health: {profile.consolidation_health:.2f}"
            )
        except Exception as e:
            stats_text = f"Could not load memory stats: {e}"

        text = (
            f"Perform a comprehensive review of the JEBAT knowledge base for focus area: {focus_area}.\n\n"
            f"Current Knowledge Base Statistics:\n{stats_text}\n\n"
            "Please review the knowledge base and address:\n"
            "1. What is strong: Identify domains with solid, high-strength memory coverage.\n"
            "2. What is stale: Identify weak or decaying memories that need refreshing or pruning.\n"
            "3. What is missing: Highlight critical knowledge gaps or unrepresented skills.\n"
            "4. Suggested actions: Recommend concrete consolidation steps, practice areas, or facts to remember."
        )
        return {
            "description": "JEBAT knowledge base review prompt",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }

    if name == "debug-this":
        error_message = arguments.get("error_message", "")
        file_path = arguments.get("file", "unknown")
        context = arguments.get("context", "")

        text = (
            f"Debug the following error:\n\n"
            f"Error: {error_message}\n"
            f"File: {file_path}\n"
            + (f"Context: {context}\n\n" if context else "\n")
            + "Follow this structured 5-step debugging workflow:\n"
            "1. Reproduce the error: State the minimal conditions or command that reproduce the issue.\n"
            "2. Identify the root cause: Trace execution to find the underlying bug, not just the crash point.\n"
            "3. Fix the source, not the symptom: Implement a clean fix addressing the actual cause.\n"
            "4. Verify the fix: Test and prove that the error is resolved and no regressions are introduced.\n"
            "5. Store the pattern as a memory: Record the bug pattern and solution in JEBAT memory to avoid recurrence."
        )
        return {
            "description": "Structured 5-step debugging workflow",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }
    return {"description": "Unknown prompt", "messages": []}
