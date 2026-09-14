"""JEBAT AGI Cognitive Core — Sovereign Multi-Domain Autonomous Engine.

Unifies:
1. Perception & Epistemic Grounding (SelfLearn + autoMimpi + Tokens)
2. Domain Classification (Build, Design, Copywriting, Database, Security)
3. Multi-Domain Reflexion Gates (Automated syntax check, Hallmark anti-slop, Pawang Jualan copy audit)
4. Dynamic Tool Synthesis (Voyager-style self-extending tools)
5. Continuous Consolidation (Durable retention + dream integration)
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DomainType(str, Enum):
    BUILD = "build"
    DESIGN = "design"
    COPYWRITING = "copywriting"
    DATABASE = "database"
    SECURITY = "security"
    AUTO = "auto"


@dataclass
class ReflexionResult:
    """Outcome of an autonomous verification & critique gate."""
    passed: bool
    domain: str
    violations: List[str] = field(default_factory=list)
    score: float = 1.0
    critique: str = ""
    actionable_feedback: str = ""


class AGICognitiveEngine:
    """Sovereign cognitive operator powering multi-domain autonomous execution."""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root or os.getcwd()).resolve()

    def classify_domain(self, prompt: str) -> DomainType:
        """Classify user intent into specialized operator domain."""
        p_lower = prompt.lower()
        words = set(re.findall(r"\b\w+\b", p_lower))

        design_keywords = {"css", "tailwind", "ui", "ux", "design", "component", "button", "styling", "card", "color", "font", "theme", "wireframe"}
        copy_keywords = {"copy", "headline", "cta", "tagline", "marketing", "pitch", "sales", "buzzword", "aida", "pas"}
        db_keywords = {"database", "sql", "postgres", "table", "schema", "migration", "query", "ghost"}
        sec_keywords = {"security", "pentest", "vulnerability", "cve", "secret", "headers", "audit"}

        if words & design_keywords:
            return DomainType.DESIGN
        if words & copy_keywords:
            return DomainType.COPYWRITING
        if words & db_keywords:
            return DomainType.DATABASE
        if words & sec_keywords:
            return DomainType.SECURITY
        return DomainType.BUILD
    def perceive(self, goal: str) -> Dict[str, Any]:
        """Ground perception across workspace, active memories, dream heuristics, and tokens."""
        domain = self.classify_domain(goal)
        perception: Dict[str, Any] = {
            "goal": goal,
            "detected_domain": domain.value,
            "workspace": str(self.workspace_root),
            "project_name": self.workspace_root.name,
            "project_facts": [],
            "dream_heuristics": [],
            "design_tokens": {},
            "copy_guidelines": [],
        }

        # 1. Recall project context from SelfLearn
        try:
            from jebat.tools.automimpi_tools import _get_memory, _recall_project_facts
            mem = _get_memory()
            facts = _recall_project_facts(mem)
            perception["project_facts"] = [f.get("content", "") for f in facts[:8]]
        except Exception:
            pass

        # 2. Retrieve autoMimpi heuristics
        try:
            from jebat.tools.automimpi_tools import _get_automimpi
            status = _get_automimpi().get_status()
            patterns = status.get("patterns", [])
            if isinstance(patterns, list):
                perception["dream_heuristics"] = [str(p) for p in patterns[:5]]
        except Exception:
            pass

        # 3. Add domain-specific grounding
        if domain in (DomainType.DESIGN, DomainType.AUTO):
            try:
                from jebat.tools.design_tools import design_preflight
                # Synchronous-safe wrapper
                import asyncio
                res = asyncio.run(design_preflight(str(self.workspace_root)))
                perception["design_tokens"] = res.get("findings", {})
            except Exception:
                pass

        if domain in (DomainType.COPYWRITING, DomainType.AUTO):
            perception["copy_guidelines"] = [
                "Mandatory CTA Formula: [Action Verb] + [What They Get]",
                "Banned AI Buzzwords: delve, testament, tapestry, seamless, game-changer, elevate",
                "Hard Rule: No unverified statistics or fabricated guarantees",
            ]

        return perception

    def reflexion_gate(
        self,
        action_name: str,
        arguments: Dict[str, Any],
        raw_output: str,
    ) -> ReflexionResult:
        """Autonomous post-execution verification & critique gate.

        Applies domain-specific sanity checks and returns actionable feedback
        for self-healing before allowing final deliverable output.
        """
        # ── Gate 1: Build & Syntax Verification ──
        if action_name == "write_file":
            path = arguments.get("path", "")
            content = arguments.get("content", "")
            if path.endswith(".py"):
                # Compile verification
                try:
                    ast.parse(content, filename=path)
                except SyntaxError as e:
                    return ReflexionResult(
                        passed=False,
                        domain="build",
                        violations=[f"Python SyntaxError in {path} at line {e.lineno}: {e.msg}"],
                        score=0.0,
                        critique="Code failed Python AST parse.",
                        actionable_feedback=(
                            f"[REFLEXION_FAILURE: Build Gate]\n"
                            f"Syntax error at line {e.lineno}: {e.msg}\n"
                            f"Text around error: {e.text}\n"
                            f"Action required: Fix the syntax error in {path} and rewrite."
                        ),
                    )

            if path.endswith((".json", ".jebatrc")):
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    return ReflexionResult(
                        passed=False,
                        domain="build",
                        violations=[f"JSONDecodeError in {path}: {e.msg}"],
                        score=0.0,
                        critique="JSON file is malformed.",
                        actionable_feedback=f"[REFLEXION_FAILURE: Build Gate] Malformed JSON in {path}: {e.msg}. Fix formatting and retry.",
                    )

        # ── Gate 2: Hallmark Design & UI/UX Verification ──
        has_ui_markup = any(tag in raw_output.lower() for tag in ("<button", "<div class=", "<h1", "<section", "tailwind"))
        if has_ui_markup:
            violations = []
            # Check for italic headers
            if re.search(r"<(h[1-6]|div)[^>]*class=[\"'][^\"']*(italic)[^\"']*[\"']", raw_output, re.I):
                violations.append("Italic header detected — Hallmark rule: headers must be roman weight.")
            # Check for fake OS chrome
            if re.search(r"(mac-dots|window-chrome|browser-header)", raw_output, re.I):
                violations.append("Fake browser/window chrome detected — represent authentic UI instead.")

            if violations:
                return ReflexionResult(
                    passed=False,
                    domain="design",
                    violations=violations,
                    score=2.0,
                    critique="Failed Hallmark anti-slop standards.",
                    actionable_feedback=(
                        "[REFLEXION_FAILURE: Hallmark Design Gate]\n"
                        + "\n".join(f"- {v}" for v in violations)
                        + "\nAction required: Remove italic headers or fake chrome and emit clean roman UI."
                    ),
                )

        # ── Gate 3: Pawang Jualan Copywriting Verification ──
        if any(keyword in raw_output.lower() for keyword in ("click here", "get started", "submit", "delve", "seamless")):
            from jebat.tools.copywriting_tools import AI_BUZZWORDS, GENERIC_CTAS
            found_ctas = [cta for cta in GENERIC_CTAS if re.search(rf"\b{re.escape(cta)}\b", raw_output.lower())]
            found_buzz = [bw for bw in AI_BUZZWORDS if re.search(rf"\b{re.escape(bw)}\b", raw_output.lower())]

            violations = []
            if found_ctas:
                violations.append(f"Generic CTAs found: {found_ctas}. Must be [Action Verb] + [What They Get].")
            if found_buzz:
                violations.append(f"AI buzzwords found: {found_buzz}. Strip fluff words.")

            if violations:
                return ReflexionResult(
                    passed=False,
                    domain="copywriting",
                    violations=violations,
                    score=2.5,
                    critique="Failed Pawang Jualan conversion standards.",
                    actionable_feedback=(
                        "[REFLEXION_FAILURE: Copywriting Gate]\n"
                        + "\n".join(f"- {v}" for v in violations)
                        + "\nAction required: Transform CTAs to Action Verb + What They Get and eliminate buzzwords."
                    ),
                )

        return ReflexionResult(passed=True, domain="general", score=5.0)

    async def consolidate_learning(self, goal: str, final_answer: str, tool_actions: List[str]) -> Dict[str, Any]:
        """Extract durable heuristics from execution and persist to memory & vector DB."""
        if not final_answer or len(final_answer) < 10:
            return {"status": "skipped"}

        # Extract lesson if substantive
        domain = self.classify_domain(goal)
        clean_fact = f"Goal '{goal[:60]}': Completed via {len(tool_actions)} tool steps."

        try:
            from jebat.tools.automimpi_tools import project_remember
            res = await project_remember(fact=clean_fact, category=domain.value, importance=0.7)
            return {"status": "consolidated", "memory": res}
        except Exception as e:
            return {"status": "error", "error": str(e)}
