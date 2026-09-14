"""JEBAT Copywriting MCP Tools (Pawang / Jurutulis Jualan).

Enforces mandatory sales copywriting gates before deliverables ship:
- copy_audit: Scans copy for generic CTAs, AI filler words, corporate fluff, and ungrounded claims.
- copy_transform_cta: Converts lazy CTAs ("Submit", "Get Started") into [Action Verb] + [What They Get].
- copy_framework: Synthesizes high-converting copy using PAS, AIDA, BAB, or Hormozi Value Stack.
"""

from __future__ import annotations
import re
from typing import Any, Dict
from pydantic import BaseModel, Field

from jebat.tools import register_tool


# ─── Prohibited AI Fluff & Buzzwords ──────────────────────────────
AI_BUZZWORDS = [
    "delve", "testament", "tapestry", "seamless", "seamlessly",
    "cutting-edge", "game-changer", "game changer", "game-changing",
    "empower", "empowers", "empowering", "revolutionize", "revolutionary",
    "unlock your potential", "elevate", "elevates", "elevating",
    "supercharge", "unleash", "in today's fast-paced world",
    "beacon", "beacon of hope", "look no further", "synergy",
]

# ─── Lazy / Generic CTAs to Flag ──────────────────────────────────
GENERIC_CTAS = [
    "click here", "get started", "learn more", "submit", "contact us",
    "read more", "sign up", "sign up now", "buy now", "continue",
]


class CopyAuditInput(BaseModel):
    text: str = Field(..., description="Copy or marketing text to audit")
    context: str = Field(default="landing_page", description="Copy context (landing_page, email, hero, pricing, ad)")


class CopyTransformCTAInput(BaseModel):
    current_cta: str = Field(..., description="Existing CTA text to improve")
    benefit: str = Field(..., description="What the user specifically receives or accomplishes")


class CopyFrameworkInput(BaseModel):
    framework: str = Field(default="PAS", description="Framework formula: PAS, AIDA, BAB, ValueStack")
    product_name: str = Field(..., description="Name of the product or service")
    target_audience: str = Field(..., description="Target buyer / ICP")
    problem: str = Field(..., description="Core pain point experienced by customer")
    solution: str = Field(..., description="How product solves pain point with tangible benefit")


@register_tool(
    "copy_audit",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text or copy to audit"},
            "context": {"type": "string", "description": "Context (landing_page, email, hero, pricing, ad)", "default": "landing_page"},
        },
        "required": ["text"],
    },
    safety_tier="auto",
    timeout=20,
    description="Audit copy against the Pawang Jualan gate: catch generic CTAs, AI filler words, buzzwords, and fake claims.",
)
async def copy_audit(text: str, context: str = "landing_page") -> Dict[str, Any]:
    """Audit marketing text for conversion blockers and corporate filler."""
    text_lower = text.lower()
    buzzwords_found = [bw for bw in AI_BUZZWORDS if bw in text_lower]
    generic_ctas_found = [cta for cta in GENERIC_CTAS if re.search(rf"\b{re.escape(cta)}\b", text_lower)]

    # Check for suspected fake statistics
    stat_pattern = r"(\b\d{1,3}%\s+(?:guaranteed|satisfaction|happiness|success)\b|\b10,000\+\s+(?:happy|trusted)\b)"
    unverified_stats = re.findall(stat_pattern, text, re.I)

    violations = []
    if generic_ctas_found:
        violations.append(f"Generic CTAs detected ({generic_ctas_found}). Transform into [Action Verb] + [What They Get].")
    if buzzwords_found:
        violations.append(f"AI filler words detected ({buzzwords_found}). Strip them in favor of concrete customer benefits.")
    if unverified_stats:
        violations.append(f"Suspected ungrounded claims detected ({unverified_stats}). Hard rule: No fabricated metrics or testimonials.")

    word_count = len(text.split())
    status = "pass" if not violations else "needs_revision"

    return {
        "status": status,
        "word_count": word_count,
        "context": context,
        "violations": violations,
        "buzzwords_found": buzzwords_found,
        "generic_ctas_found": generic_ctas_found,
        "guidelines": [
            "Every CTA must follow: [Action Verb] + [What They Get].",
            "Focus on customer outcomes, not company features.",
            "Write in active voice with zero corporate jargon.",
            "Never fabricate metrics, logos, or testimonials.",
        ],
    }


@register_tool(
    "copy_transform_cta",
    schema={
        "type": "object",
        "properties": {
            "current_cta": {"type": "string", "description": "Existing CTA text (e.g. 'Get Started')"},
            "benefit": {"type": "string", "description": "What the user receives (e.g. '14-day access to sovereign agent')"},
        },
        "required": ["current_cta", "benefit"],
    },
    safety_tier="auto",
    timeout=10,
    description="Transform generic lazy CTAs into high-converting [Action Verb] + [What They Get] CTAs.",
)
async def copy_transform_cta(current_cta: str, benefit: str) -> Dict[str, Any]:
    """Generate high-converting specific CTAs."""
    clean_benefit = benefit.strip().lstrip("a ").lstrip("an ")

    options = [
        f"Start Your {clean_benefit.title()}",
        f"Claim Your {clean_benefit.title()}",
        f"Deploy Your {clean_benefit.title()}",
        f"Get {clean_benefit.title()}",
    ]

    secondary_options = [
        "View Live Interactive Demo",
        "Inspect Architecture & Docs",
        "Explore Sample Workflows",
    ]

    return {
        "original_cta": current_cta,
        "primary_recommendation": options[0],
        "alternatives": options,
        "recommended_secondary": secondary_options[0],
        "secondary_alternatives": secondary_options,
        "conversion_rule": "Primary CTA must be prominent; secondary CTA must be low-friction / text link.",
    }


@register_tool(
    "copy_framework",
    schema={
        "type": "object",
        "properties": {
            "framework": {"type": "string", "description": "PAS, AIDA, BAB, or ValueStack", "default": "PAS"},
            "product_name": {"type": "string", "description": "Product name"},
            "target_audience": {"type": "string", "description": "ICP / Target audience"},
            "problem": {"type": "string", "description": "Customer core problem"},
            "solution": {"type": "string", "description": "How product solves it"},
        },
        "required": ["product_name", "target_audience", "problem", "solution"],
    },
    safety_tier="auto",
    timeout=15,
    description="Generate structured sales copy blueprint using PAS, AIDA, BAB, or Hormozi Value Stack.",
)
async def copy_framework(
    product_name: str,
    target_audience: str,
    problem: str,
    solution: str,
    framework: str = "PAS",
) -> Dict[str, Any]:
    """Structure sales copy according to classic direct-response frameworks."""
    fmt = framework.upper()
    if fmt == "PAS":
        structure = {
            "Problem": f"Are you tired of {problem.lower()} as a {target_audience}?",
            "CTA": f"Deploy {product_name} Today",
            "Solution": f"With {product_name}, you {solution.lower()}. Sovereign, verified, and automated.",
            "CTA": f"Deploy {product_name} Today",
        }
    elif fmt == "BAB":
        structure = {
            "Before": f"Currently, {target_audience} struggle with {problem.lower()}.",
            "CTA": f"Start Using {product_name}",
            "Bridge": f"{product_name} bridges the gap by providing {solution.lower()}.",
            "CTA": f"Start Using {product_name}",
        }
    elif fmt == "AIDA":
        structure = {
            "Attention": f"Stop wasting hours on {problem.lower()}.",
            "Interest": f"{product_name} gives {target_audience} an autonomous multi-turn operator.",
            "Desire": f"Gain immediate confidence: {solution.lower()}.",
            "Action": f"Launch {product_name} Now",
        }
    else:  # ValueStack (Hormozi)
        structure = {
            "Dream_Outcome": f"Achieve seamless {solution.lower()}.",
            "Grand_Slam_CTA": f"Claim Your {product_name} Access",
            "Time_Delay": "Zero setup friction — ready to execute immediately.",
            "Effort_and_Sacrifice": "No complex refactors; fits into your existing workflow.",
            "Grand_Slam_CTA": f"Claim Your {product_name} Access",
        }

    return {
        "framework": fmt,
        "product": product_name,
        "audience": target_audience,
        "sections": structure,
    }
