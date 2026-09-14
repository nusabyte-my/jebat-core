from __future__ import annotations


import pytest
from jebat.core.agi_core import AGICognitiveEngine, DomainType
from jebat.tools.dynamic_synthesis import tool_synthesize
from jebat.tools import TOOL_REGISTRY


def test_domain_classification():
    """Verify that intent is routed to the correct sovereign specialist domain."""
    engine = AGICognitiveEngine()
    assert engine.classify_domain("Build a FastAPI route for authentication") == DomainType.BUILD
    assert engine.classify_domain("Design a dark-mode button with Tailwind and hover state") == DomainType.DESIGN
    assert engine.classify_domain("Write high-converting headline and CTA for our landing page") == DomainType.COPYWRITING
    assert engine.classify_domain("Inspect postgres table schema and run migrations") == DomainType.DATABASE
    assert engine.classify_domain("Audit security headers and run CVE port scan") == DomainType.SECURITY


def test_perception_grounding():
    """Verify that perception generates a grounded context frame."""
    engine = AGICognitiveEngine()
    perception = engine.perceive("Design a pricing table with high-converting CTAs")
    assert "goal" in perception
    assert perception["detected_domain"] in ("design", "copywriting")
    assert "workspace" in perception
    assert "project_name" in perception


def test_reflexion_gate_build_catches_syntax_error():
    """Verify that the Reflexion Gate intercepts broken Python syntax."""
    engine = AGICognitiveEngine()
    broken_code = "def broken_func(:\n  return 'fail'"
    result = engine.reflexion_gate("write_file", {"path": "test.py", "content": broken_code}, "File written")
    assert not result.passed
    assert result.domain == "build"
    assert "Syntax error" in result.actionable_feedback or "SyntaxError" in result.violations[0]


def test_reflexion_gate_design_catches_hallmark_violations():
    """Verify that the Reflexion Gate intercepts Hallmark anti-slop violations."""
    engine = AGICognitiveEngine()
    slop_markup = "<h1 class='text-4xl font-bold italic'>AI Landing Page</h1><div class='mac-dots'></div>"
    result = engine.reflexion_gate("generate_ui", {"markup": slop_markup}, slop_markup)
    assert not result.passed
    assert result.domain == "design"
    assert any("italic header" in v.lower() for v in result.violations)
    assert any("fake browser" in v.lower() for v in result.violations)


def test_reflexion_gate_copy_catches_generic_ctas_and_buzzwords():
    """Verify that the Reflexion Gate intercepts lazy CTAs and AI buzzwords."""
    engine = AGICognitiveEngine()
    buzzword_copy = "Click here to delve into our revolutionary seamless platform."
    result = engine.reflexion_gate("write_copy", {"text": buzzword_copy}, buzzword_copy)
    assert not result.passed
    assert result.domain == "copywriting"
    assert any("generic cta" in v.lower() for v in result.violations)
    assert any("buzzword" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_dynamic_tool_synthesis():
    """Verify Voyager-style dynamic tool synthesis, registration, and live execution."""
    tool_code = """
async def calculate_roi(revenue: float, cost: float) -> str:
    roi = ((float(revenue) - float(cost)) / float(cost)) * 100
    return f"ROI: {roi:.1f}%"
"""
    res = await tool_synthesize(
        name="calculate_roi",
        code=tool_code,
        description="Calculate return on investment percentage from revenue and cost.",
        parameters={"revenue": "Total revenue", "cost": "Total cost"},
    )
    assert res["status"] == "registered"
    assert "calculate_roi" in TOOL_REGISTRY

    # Test live execution of the dynamically synthesized tool
    handler = TOOL_REGISTRY["calculate_roi"].handler
    assert callable(handler)
    output = await handler(revenue=150.0, cost=50.0)


def test_agi_execute_meta_tool_registered():
    """Verify that agi_execute is registered in TOOL_REGISTRY."""
    from jebat.features.mcp.mcp_server import MCPServer
    MCPServer()._ensure_tools_loaded()
    assert "agi_execute" in TOOL_REGISTRY
    tool = TOOL_REGISTRY["agi_execute"]
    assert "goal" in tool.schema["properties"]
    assert "domain" in tool.schema["properties"]
