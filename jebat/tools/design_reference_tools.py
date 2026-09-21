"""JEBAT Design Reference, Trends & Visual Critique Tools (Pawang Estetika).

Provides tools for:
- design_reference: Pull curated real-world UI/UX patterns for a screen/component category.
- design_trends: Retrieve current (2025-2026) UI/UX design trends and conventions.
- design_visual_critique: Render UI markup or URL in headless Chromium, capture screenshot,
  measure layout/contrast facts, and run Hallmark visual critique.
"""

from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from jebat.tools import register_tool
from jebat.features.design.corpus import PATTERNS
from jebat.features.design.trends import TRENDS
from jebat.features.design.visual import run_visual_critique


class DesignReferenceInput(BaseModel):
    category: str = Field(default="", description="Pattern category (e.g. hero, landing, pricing, dashboard, data_display, auth, signup, onboarding, ecommerce_product, navigation, settings_configuration, empty_error_states, mobile_patterns)")
    query: str = Field(default="", description="Optional search filter over name, structure, or use_when")
    limit: int = Field(default=3, description="Maximum number of patterns to return")


class DesignTrendsInput(BaseModel):
    surface: str = Field(default="web", description="Target surface (web, mobile, desktop, or all)")


class DesignVisualCritiqueInput(BaseModel):
    markup: str = Field(default="", description="Raw HTML/CSS markup to render and critique")
    url: str = Field(default="", description="Live URL to navigate to and critique")
    viewport: str = Field(default="desktop", description="Viewport size preset: desktop, tablet, mobile")


@register_tool(
    "design_reference",
    schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Pattern category (e.g. hero, landing, pricing, dashboard, data_display, auth, signup, onboarding, ecommerce_product, navigation, settings_configuration, empty_error_states, mobile_patterns)",
                "default": "",
            },
            "query": {
                "type": "string",
                "description": "Optional search filter over name, structure, or use_when",
                "default": "",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of patterns to return",
                "default": 3,
            },
        },
    },
    safety_tier="auto",
    timeout=20,
    description="Pull curated real-world UI/UX patterns for a screen/component category.",
)
async def design_reference(category: str = "", query: str = "", limit: int = 3) -> Dict[str, Any]:
    """Pull curated real-world UI/UX patterns for a screen/component category."""
    cat = (category or "").lower().strip()
    q = (query or "").lower().strip()

    available_categories = sorted(PATTERNS.keys())

    # Terse mode check
    is_terse = False
    try:
        from jebat.features.mcp.mcp_server import mcp_terse_mode
        is_terse = mcp_terse_mode()
    except Exception:
        pass

    if not cat or cat not in PATTERNS:
        return {
            "status": "category_required" if not cat else "unknown_category",
            "message": f"Please select a category from available categories: {available_categories}",
            "categories": available_categories,
        }

    raw_patterns = PATTERNS.get(cat, [])
    if q:
        filtered = [
            p for p in raw_patterns
            if q in p.get("name", "").lower()
            or q in p.get("structure", "").lower()
            or q in p.get("use_when", "").lower()
        ]
    else:
        filtered = raw_patterns

    selected = filtered[:max(1, limit)]

    if is_terse:
        return {
            "status": "ok",
            "category": cat,
            "patterns": [
                {"name": p["name"], "structure": p["structure"]}
                for p in selected
            ],
        }

    return {
        "status": "ok",
        "category": cat,
        "count": len(selected),
        "total_in_category": len(raw_patterns),
        "patterns": selected,
    }


@register_tool(
    "design_trends",
    schema={
        "type": "object",
        "properties": {
            "surface": {
                "type": "string",
                "description": "Target surface (web, mobile, desktop, or all)",
                "default": "web",
            },
        },
    },
    safety_tier="auto",
    timeout=20,
    description="Retrieve current (2025-2026) UI/UX design trends and conventions.",
)
async def design_trends(surface: str = "web") -> Dict[str, Any]:
    """Retrieve current (2025-2026) UI/UX design trends and conventions."""
    surf = (surface or "web").lower().strip()

    # Terse mode check
    is_terse = False
    try:
        from jebat.features.mcp.mcp_server import mcp_terse_mode
        is_terse = mcp_terse_mode()
    except Exception:
        pass

    if surf in ("all", ""):
        matched = TRENDS
    else:
        matched = [t for t in TRENDS if t.get("surface", "web") == surf or surf == "web"]

    if is_terse:
        return {
            "status": "ok",
            "surface": surf,
            "trends": [
                {"name": t["name"], "convention": t["convention"]}
                for t in matched
            ],
        }

    return {
        "status": "ok",
        "surface": surf,
        "count": len(matched),
        "trends": matched,
    }


@register_tool(
    "design_visual_critique",
    schema={
        "type": "object",
        "properties": {
            "markup": {
                "type": "string",
                "description": "Raw HTML/CSS markup to render and critique",
                "default": "",
            },
            "url": {
                "type": "string",
                "description": "Live URL to navigate to and critique",
                "default": "",
            },
            "viewport": {
                "type": "string",
                "enum": ["desktop", "tablet", "mobile"],
                "description": "Viewport size preset",
                "default": "desktop",
            },
        },
    },
    safety_tier="auto",
    timeout=60,
    description="Render UI markup or URL in headless Chromium, capture screenshot, measure layout/contrast metrics, and run Hallmark visual critique.",
)
async def design_visual_critique(
    markup: str = "",
    url: str = "",
    viewport: str = "desktop",
) -> Dict[str, Any]:
    """Render UI markup or URL in headless Chromium, capture screenshot, and run critique."""
    return await run_visual_critique(markup=markup, url=url, viewport=viewport)
