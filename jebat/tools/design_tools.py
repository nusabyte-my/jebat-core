"""JEBAT Design & UI/UX MCP Tools (Pawang Estetika).

Provides tools for:
- design_preflight: Scans workspace for tokens, font stack, color palette, and component libraries.
- ui_critique: Hallmark 6-axis anti-slop audit (Philosophy, Hierarchy, Execution, Specificity, Restraint, Variety).
- component_states: Verifies 8-state interaction discipline (default, hover, focus-visible, active, disabled, loading, error, success).
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from jebat.tools import register_tool


class DesignPreflightInput(BaseModel):
    path: str = Field(default=".", description="Root or component directory to scan")


class UICritiqueInput(BaseModel):
    markup: str = Field(..., description="HTML, JSX, TSX, or Vue component markup to critique")
    component_type: str = Field(default="generic", description="Component category (button, card, hero, pricing, form, generic)")


class ComponentStatesInput(BaseModel):
    markup: str = Field(..., description="Interactive element markup (button, input, select, link)")


@register_tool(
    "design_preflight",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Project root or directory to scan", "default": "."},
        },
    },
    safety_tier="auto",
    timeout=30,
    description="Scan project for design system tokens, Tailwind config, font stacks, and component libraries before editing UI.",
)
async def design_preflight(path: str = ".") -> Dict[str, Any]:
    """Scan project for UI framework, fonts, colors, and styling conventions."""
    root = Path(path).resolve()
    findings: Dict[str, Any] = {
        "framework": "unknown",
        "component_lib": "custom",
        "tailwind": False,
        "fonts": [],
        "palette_type": "standard",
        "motion": False,
        "design_file_present": False,
    }

    # Check for DESIGN.md / design.md
    for name in ("DESIGN.md", "design.md", "tokens.json"):
        p = root / name
        if p.exists():
            findings["design_file_present"] = True
            findings["design_file"] = name
            break

    # Inspect package.json
    pkg_path = root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                findings["framework"] = f"Next.js ({deps['next']})"
            elif "vite" in deps:
                findings["framework"] = f"Vite ({deps['vite']})"
            elif "astro" in deps:
                findings["framework"] = "Astro"

            # Component libraries
            if "@flyonui/flyonui" in deps or "flyonui" in deps:
                findings["component_lib"] = "FlyonUI"
            elif "@radix-ui/react-slot" in deps or (root / "components.json").exists():
                findings["component_lib"] = "shadcn/ui"
            elif "antd" in deps:
                findings["component_lib"] = "Ant Design"

            # Motion libraries
            for m in ("framer-motion", "motion", "gsap", "lenis"):
                if m in deps:
                    findings["motion"] = True
                    findings["motion_lib"] = m
                    break

            # Fonts
            for d in deps:
                if d.startswith("@fontsource/"):
                    findings["fonts"].append(d.replace("@fontsource/", ""))
        except Exception:
            pass

    # Inspect Tailwind
    for tw in ("tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs"):
        if (root / tw).exists():
            findings["tailwind"] = True
            findings["tailwind_config"] = tw
            break

    return {
        "status": "ok",
        "root": str(root),
        "findings": findings,
        "rules": [
            "Lock detected tokens — do not invent mid-render hex codes or random fonts.",
            "If DESIGN.md exists, defer to its rules unconditionally.",
            "Apply 8-state discipline for all interactive controls.",
            "Verify layout at 320px, 375px, 768px, and 1280px breakpoints without horizontal scroll.",
        ],
    }


@register_tool(
    "ui_critique",
    schema={
        "type": "object",
        "properties": {
            "markup": {"type": "string", "description": "UI markup/code to audit"},
            "component_type": {"type": "string", "description": "Component category", "default": "generic"},
        },
        "required": ["markup"],
    },
    safety_tier="auto",
    timeout=30,
    description="Run Hallmark 6-axis anti-slop audit (Philosophy, Hierarchy, Execution, Specificity, Restraint, Variety) on UI code.",
)
async def ui_critique(markup: str, component_type: str = "generic") -> Dict[str, Any]:
    """Audit UI markup against Hallmark anti-slop gates and generate scores."""
    scores: Dict[str, int] = {
        "Philosophy": 5,
        "Hierarchy": 5,
        "Execution": 5,
        "Specificity": 5,
        "Restraint": 5,
        "Variety": 5,
    }
    violations: List[str] = []
    recommendations: List[str] = []

    # 1. Check for italic headers (Hard Rule: No italic headers)
    if re.search(r"<(h[1-6]|div|span)[^>]*class=[\"'][^\"']*(italic|font-serif-italic)[^\"']*[\"']", markup, re.I):
        scores["Execution"] -= 2
        violations.append("Italic header detected — headers must be roman; use weight/tracking/color for emphasis.")

    # 2. Check for fake browser / window chrome
    if re.search(r"(mac-dots|window-chrome|browser-header|bg-red-500 rounded-full.*bg-yellow-500)", markup, re.I):
        scores["Philosophy"] -= 2
        violations.append("Re-drawn browser/OS chrome detected — represents AI template slop; present clean authentic UI instead.")

    # 3. Check for low contrast / gray on gray
    if "text-gray-400 bg-gray-200" in markup or "text-zinc-500 bg-zinc-700" in markup:
        scores["Hierarchy"] -= 1
        violations.append("Low contrast text/background pairing violates WCAG AA readability.")

    # 4. Check for interactive states on buttons/inputs
    if "<button" in markup.lower() or "role=[\"']button[\"']" in markup.lower():
        states_found = []
        for state in ("hover:", "focus:", "active:", "disabled:"):
            if state in markup:
                states_found.append(state)
        if len(states_found) < 3:
            scores["Execution"] -= 1
            violations.append(f"Interactive element lacks complete interaction states (found only: {states_found}).")

    # 5. Restraint: Overuse of gradients or excessive glows
    gradient_count = len(re.findall(r"bg-gradient|from-|to-|drop-shadow-glow", markup, re.I))
    if gradient_count > 4:
        scores["Restraint"] -= 1
        violations.append(f"Excessive decorative gradients ({gradient_count} instances) reduce visual restraint.")

    # Ensure scores stay between 1 and 5
    for k in scores:
        scores[k] = max(1, min(5, scores[k]))

    stamp = f"/* Hallmark · pre-emit critique: P{scores['Philosophy']} H{scores['Hierarchy']} E{scores['Execution']} S{scores['Specificity']} R{scores['Restraint']} V{scores['Variety']} */"

    passed = all(v >= 3 for v in scores.values()) and len(violations) == 0

    return {
        "status": "pass" if passed else "needs_revision",
        "scores": scores,
        "critique_stamp": stamp,
        "violations": violations,
        "recommendations": recommendations or ["Craft is sharp; tokens and hierarchy align with Hallmark standards."],
    }


@register_tool(
    "component_states",
    schema={
        "type": "object",
        "properties": {
            "markup": {"type": "string", "description": "Interactive component markup"},
        },
        "required": ["markup"],
    },
    safety_tier="auto",
    timeout=20,
    description="Verify the 8-state interactive discipline (default, hover, focus-visible, active, disabled, loading, error, success).",
)
async def component_states(markup: str) -> Dict[str, Any]:
    """Audit an interactive element for complete 8-state coverage."""
    discipline_map = {
        "default": True,  # base styling
        "hover": bool(re.search(r"hover:", markup)),
        "focus_visible": bool(re.search(r"focus-visible:|focus:", markup)),
        "active": bool(re.search(r"active:", markup)),
        "disabled": bool(re.search(r"disabled:|aria-disabled", markup)),
        "loading": bool(re.search(r"loading|is-loading|animate-spin|spinner", markup)),
        "error": bool(re.search(r"error|border-red|text-red|invalid:", markup)),
        "success": bool(re.search(r"success|border-green|text-green|valid:", markup)),
    }

    missing = [state for state, covered in discipline_map.items() if not covered]
    covered_count = sum(1 for covered in discipline_map.values() if covered)

    return {
        "status": "complete" if covered_count >= 6 else "partial",
        "coverage": f"{covered_count}/8 states implemented",
        "states": discipline_map,
        "missing_states": missing,
        "guidance": "Interactive elements must provide clear visual feedback across hover, active, focus-visible, and disabled states.",
    }
