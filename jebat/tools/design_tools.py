"""JEBAT Design & UI/UX MCP Tools (Pawang Estetika).

Provides tools for:
- design_preflight: Scans workspace for tokens, font stack, color palette, and component libraries.
- ui_critique: Hallmark 6-axis anti-slop audit (Philosophy, Hierarchy, Execution, Specificity, Restraint, Variety).
- component_states: Verifies 8-state interaction discipline (default, hover, focus-visible, active, disabled, loading, error, success).
"""

from __future__ import annotations
from collections import Counter
import json
import re
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from jebat.tools import register_tool


SUPPORTED_COMPONENT_TYPES = {
    "button", "card", "hero", "pricing", "form", "generic",
    "landing", "dashboard", "navigation", "modal", "table",
    "section", "page", "dialog", "list"
}

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

    is_terse = False
    try:
        from jebat.features.mcp.mcp_server import mcp_terse_mode
        is_terse = mcp_terse_mode()
    except Exception:
        pass

    if is_terse:
        return {
            "status": "ok",
            "findings": findings,
        }

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
    axes_evaluated: List[str] = []

    comp_type = (component_type or "generic").lower().strip()

    # Determine which axes can actually be evaluated
    has_tags = bool(re.search(r"<[a-zA-Z]", markup))
    is_supported = comp_type in SUPPORTED_COMPONENT_TYPES and has_tags and len(markup.strip()) >= 15

    if is_supported:
        axes_evaluated.extend(["Philosophy", "Hierarchy", "Execution", "Restraint", "Specificity"])
        if comp_type != "button" or len(re.findall(r"<[a-zA-Z]", markup)) > 1:
            axes_evaluated.append("Variety")
    elif has_tags:
        # Unsupported component type or very minimal snippet: evaluate only Execution / Restraint
        if "<button" in markup.lower() or "role=" in markup.lower() or "<h" in markup.lower():
            axes_evaluated.append("Execution")
        if "bg-" in markup or "gradient" in markup or "style=" in markup:
            axes_evaluated.append("Restraint")

    # 1. Check for italic headers (Hard Rule: No italic headers) [Execution]
    if "Execution" in axes_evaluated:
        if re.search(r"<(h[1-6]|div|span)[^>]*class=[\"'][^\"']*(italic|font-serif-italic)[^\"']*[\"']", markup, re.I):
            scores["Execution"] -= 2
            violations.append("Italic header detected — headers must be roman; use weight/tracking/color for emphasis.")
            recommendations.append("Remove italic styling from headers; use font-weight, tracking, or color contrast for emphasis.")

    # 2. Check for fake browser / window chrome [Philosophy]
    if "Philosophy" in axes_evaluated:
        if re.search(r"(mac-dots|window-chrome|browser-header|bg-red-500 rounded-full.*bg-yellow-500)", markup, re.I):
            scores["Philosophy"] -= 2
            violations.append("Re-drawn browser/OS chrome detected — represents AI template slop; present clean authentic UI instead.")
            recommendations.append("Remove simulated browser/OS window controls and present authentic product interface directly.")

    # 3. Check for low contrast / gray on gray [Hierarchy]
    if "Hierarchy" in axes_evaluated:
        if "text-gray-400 bg-gray-200" in markup or "text-zinc-500 bg-zinc-700" in markup:
            scores["Hierarchy"] -= 1
            violations.append("Low contrast text/background pairing violates WCAG AA readability.")
            recommendations.append("Ensure text-to-background contrast ratio meets WCAG AA standards (minimum 4.5:1 for normal text, 3:1 for large text).")

    # 4. Check for interactive states on buttons/inputs [Execution]
    if "Execution" in axes_evaluated:
        if "<button" in markup.lower() or "role=[\"']button[\"']" in markup.lower():
            states_found = []
            for state in ("hover:", "focus:", "active:", "disabled:"):
                if state in markup:
                    states_found.append(state)
            if len(states_found) < 3:
                scores["Execution"] -= 1
                violations.append(f"Interactive element lacks complete interaction states (found only: {states_found}).")
                recommendations.append("Implement complete interactive states: hover, focus-visible, active, and disabled.")

    # 5. Restraint: Overuse of gradients or excessive glows [Restraint]
    if "Restraint" in axes_evaluated:
        gradient_count = len(re.findall(r"bg-gradient|from-|to-|drop-shadow-glow", markup, re.I))
        if gradient_count > 4:
            scores["Restraint"] -= 1
            violations.append(f"Excessive decorative gradients ({gradient_count} instances) reduce visual restraint.")
            recommendations.append("Reduce decorative gradients; limit to subtle single-color accents or solid surface backgrounds.")

    # 6. Specificity: Check for placeholder text, generic claims, buzzwords, empty data, generic alt [Specificity]
    if "Specificity" in axes_evaluated:
        spec_classes_found = 0

        # Class 1: Placeholder / lorem ipsum text
        placeholders = re.findall(r"\b(lorem\s+ipsum|lorem|ipsum|placeholder\s+text|your\s+text\s+here|sample\s+text)\b", markup, re.I)
        if placeholders:
            spec_classes_found += 1
            violations.append(f"Placeholder text detected ({', '.join(sorted(set(placeholders[:3])))}) — replace with authentic, domain-specific content.")
            recommendations.append("Replace placeholder and lorem ipsum copy with realistic, context-specific domain content.")

        # Class 2: Generic unqualified numeric claims
        claims = re.findall(r"\b(99\.9%|10x\s+faster|24/7)\b", markup, re.I)
        if claims:
            spec_classes_found += 1
            violations.append(f"Unqualified generic marketing claims ({', '.join(sorted(set(claims)))}) weaken credibility.")
            recommendations.append("Replace generic marketing numbers (e.g. 99.9%, 10x faster) with verifiable product evidence or remove them.")

        # Class 3: Stock feature copy patterns
        buzzwords = re.findall(r"\b(innovative\s+solutions|cutting-edge|seamless\s+integration|unlock\s+the\s+power|take\s+your\s+[^<\n\r]+?to\s+the\s+next\s+level)\b", markup, re.I)
        if buzzwords:
            spec_classes_found += 1
            violations.append(f"Stock feature buzzwords detected ({', '.join(sorted(set(buzzwords[:3])))}) — AI marketing filler.")
            recommendations.append("Eliminate stock buzzwords (e.g. 'cutting-edge', 'seamless integration'); describe specific user workflows.")

        # Class 4: Empty/absent real data in a data-bearing component
        is_data_component = comp_type in ("pricing", "card") or bool(re.search(r"\b(pricing|price|plan|tier|subscription|billing)\b", markup, re.I))
        if is_data_component:
            has_data_tokens = bool(re.search(r"(\$|€|£|¥|RM|USD|EUR|GBP|/mo|/yr|/month|/year|\b\d+(\.\d+)?\s*(%|k|m|users|seats|gb|tb|credits)?\b)", markup, re.I))
            if not has_data_tokens:
                spec_classes_found += 1
                violations.append("Data-bearing component lacks concrete data tokens (no price, currency, or metric values).")
                recommendations.append("Provide realistic sample values (e.g., '$49/mo', '1,240 users') in data-bearing cards and pricing components.")

        # Class 5: Generic or empty alt text on content images
        img_alts = re.findall(r"<img[^>]*\balt=[\"'](.*?)[\"']", markup, re.I)
        generic_alts = [alt for alt in img_alts if alt.strip().lower() in ("", "image", "logo", "placeholder", "photo", "picture", "icon")]
        if generic_alts:
            spec_classes_found += 1
            violations.append(f"Generic or empty image alt attribute detected ({', '.join(generic_alts[:3]) or 'alt=\"\"'}) — violates accessibility standards.")
            recommendations.append("Provide meaningful descriptive alt text describing the image content or function (WCAG 1.1.1).")

        if spec_classes_found > 0:
            scores["Specificity"] -= spec_classes_found

    # 7. Variety: Detect structural monotony [Variety]
    if "Variety" in axes_evaluated:
        variety_issues = 0

        # Pattern 1: 3+ sibling elements with an identical class-string signature
        class_matches = [c.strip() for c in re.findall(r'''class=["']([^"']+)["']''', markup) if len(c.strip().split()) >= 2]
        class_counts = Counter(class_matches)
        repeated_sigs = [(c, count) for c, count in class_counts.items() if count >= 3]
        if repeated_sigs:
            sample_sig, n_identical_blocks = max(repeated_sigs, key=lambda x: x[1])
            short_sig = sample_sig[:40] + ("..." if len(sample_sig) > 40 else "")
            violations.append(f"Structural monotony: {n_identical_blocks} elements share identical class signature '{short_sig}'.")
            recommendations.append("Vary card/element structure, introduce visual hierarchy or featured items instead of identical repeated blocks.")
            variety_issues += 1

        # Pattern 2: Component is only centered text stacked vertically (text-center on >=4 block elements with no grid/flex layout)
        centered_blocks = re.findall(r'''<(?:div|section|p|h[1-6]|article|header|main)[^>]*class=["'][^"']*\btext-center\b[^"']*["']''', markup, re.I)
        has_layout = bool(re.search(r'\b(grid|flex|flex-row|grid-cols-\d+)\b', markup, re.I))
        if len(centered_blocks) >= 4 and not has_layout:
            violations.append(f"Structural monotony: all-centered vertical stack ({len(centered_blocks)} centered elements) without grid/flex layout.")
            recommendations.append("Break up centered text stacks with left-aligned content, multi-column grids, or horizontal flex layouts.")
            variety_issues += 1

        # Pattern 3: Identical heading + paragraph + button triplet repeated
        triplets = re.findall(r'<h[1-6][^>]*>.*?<\/h[1-6]>\s*<p[^>]*>.*?<\/p>\s*<(?:button|a)[^>]*>.*?<\/(?:button|a)>', markup, re.I | re.S)
        if len(triplets) >= 2:
            violations.append(f"Repetitive layout: {len(triplets)} identical heading + paragraph + button triplets repeated.")
            recommendations.append("Vary content rhythm by mixing media, varied CTA styles, testimonial quotes, or data callouts.")
            variety_issues += 1

        # Pattern 4: Absence of any layout variety signal in complex containers
        if len(markup) > 200 and comp_type != "button":
            has_variety_signal = bool(re.search(r'\b(grid|flex|gap-\d+|col-span-\d+|row-span-\d+|bg-(?:gray|zinc|slate|neutral|white|black|surface)-\d+.*bg-(?:gray|zinc|slate|neutral|white|black|surface)-\d+)\b', markup, re.I | re.S))
            if not has_variety_signal:
                violations.append("Monolithic layout: lacks structural variety signals (no grid, flex, gap spacing, or section alternation).")
                recommendations.append("Introduce responsive grid/flex layouts with consistent gap spacing and contrasting section surfaces.")
                variety_issues += 1

        if variety_issues > 0:
            scores["Variety"] -= variety_issues

    # Ensure scores stay between 1 and 5
    for k in scores:
        scores[k] = max(1, min(5, scores[k]))

    stamp = f"/* Hallmark · pre-emit critique: P{scores['Philosophy']} H{scores['Hierarchy']} E{scores['Execution']} S{scores['Specificity']} R{scores['Restraint']} V{scores['Variety']} */"

    # Status determination
    if len(axes_evaluated) < 4:
        status = "insufficient_signal"
        if not recommendations:
            recommendations.append(
                f"Component type '{component_type}' or markup structure has insufficient signal for full Hallmark 6-axis audit (evaluated: {axes_evaluated}). Provide fuller container markup or use a supported component type."
            )
    else:
        passed = all(v >= 3 for v in scores.values()) and len(violations) == 0
        status = "pass" if passed else "needs_revision"
        if passed and not recommendations:
            recommendations.append("Craft is sharp; tokens, specificity, variety, and hierarchy align with Hallmark standards.")

    # Terse mode check
    is_terse = False
    try:
        from jebat.features.mcp.mcp_server import mcp_terse_mode
        is_terse = mcp_terse_mode()
    except Exception:
        pass

    if is_terse:
        return {
            "status": status,
            "scores": scores,
            "violations": violations,
        }

    return {
        "status": status,
        "scores": scores,
        "axes_evaluated": axes_evaluated,
        "critique_stamp": stamp,
        "violations": violations,
        "recommendations": recommendations,
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

    is_terse = False
    try:
        from jebat.features.mcp.mcp_server import mcp_terse_mode
        is_terse = mcp_terse_mode()
    except Exception:
        pass

    if is_terse:
        return {
            "status": "complete" if covered_count >= 6 else "partial",
            "coverage": f"{covered_count}/8 states implemented",
            "missing_states": missing,
        }

    return {
        "status": "complete" if covered_count >= 6 else "partial",
        "coverage": f"{covered_count}/8 states implemented",
        "states": discipline_map,
        "missing_states": missing,
        "guidance": "Interactive elements must provide clear visual feedback across hover, active, focus-visible, and disabled states.",
    }
