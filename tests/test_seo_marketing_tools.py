"""Contract tests for the JEBAT marketing + SEO MCP tool suites."""

import pytest

from jebat.tools import TOOL_REGISTRY, call_tool
from jebat.tools import marketing_tools, seo_tools  # noqa: F401  (registers tools)

NEW_TOOLS = {
    "seo_audit",
    "seo_meta_generate",
    "seo_keyword_extract",
    "seo_content_brief",
    "seo_serp_check",
    "seo_url_audit",
    "marketing_plan",
    "marketing_positioning",
    "marketing_metrics",
    "marketing_icp",
}

_KEYWORD = "team analytics"


def _good_html() -> str:
    body_words = " ".join(
        ["analytics"] * 40 + ["dashboards"] * 30 + ["teams"] * 30 + ["ship"] * 30
        + ["aligned"] * 20 + ["progress"] * 20 + ["weekly"] * 20 + ["goals"] * 20
        + ["reports"] * 20 + ["insights"] * 20 + ["metrics"] * 20 + ["focus"] * 20
        + ["grows"] * 20 + ["faster"] * 20 + ["clear"] * 20 + ["simple"] * 20
        + ["works"] * 20 + ["better"] * 20 + ["value"] * 30 + ["daily"] * 30
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Team analytics for fast teams | AcmeCo</title>
  <meta name="description" content="AcmeCo gives teams live analytics and dashboards that turn weekly progress into clear decisions, so every team ships aligned and grows faster.">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://acmeco.example/team-analytics">
  <meta property="og:title" content="Team analytics for fast teams">
  <meta property="og:description" content="Live analytics and dashboards for teams.">
  <meta property="og:image" content="https://acmeco.example/og.png">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article"}}</script>
</head>
<body>
  <h1>Team analytics that keeps every team aligned</h1>
  <p>{body_words}</p>
  <h2>Why it matters</h2>
  <p>More detail about how { _KEYWORD } helps.</p>
  <img src="/shot.png" alt="Analytics dashboard screenshot">
  <a href="/pricing">Pricing</a>
  <a href="/docs">Docs</a>
  <a href="/blog">Blog</a>
</body>
</html>"""


@pytest.mark.anyio
async def test_all_new_tools_registered() -> None:
    missing = NEW_TOOLS - set(TOOL_REGISTRY)
    assert not missing, f"unregistered tools: {sorted(missing)}"


@pytest.mark.anyio
async def test_seo_audit_separates_good_and_bad_pages() -> None:
    bad_html = "<html><body><div>tiny page with nothing</div></body></html>"
    bad = await call_tool("seo_audit", html=bad_html, target_keyword=_KEYWORD)
    good = await call_tool("seo_audit", html=_good_html(), target_keyword=_KEYWORD)

    assert bad["score"] < good["score"]
    assert good["score"] >= 90
    assert good["grade"] in ("A", "B")
    assert bad["grade"] in ("D", "F")
    assert bad["quick_fixes"], "a failing page must surface prioritized fixes"
    assert any(c["id"] == "title" and c["status"] == "fail" for c in bad["checks"])
    assert good["stats"]["word_count"] >= 300


@pytest.mark.anyio
async def test_seo_audit_flags_noindex_and_keyword_density() -> None:
    html = (
        '<html lang="en"><head><title>spam keyword keyword keyword tool</title>'
        '<meta name="robots" content="noindex"></head>'
        "<body><h1>keyword keyword</h1>"
        + f"<p>{'keyword ' * 200}</p>"
        + "</body></html>"
    )
    result = await call_tool("seo_audit", html=html, target_keyword="keyword")
    statuses = {c["id"]: c["status"] for c in result["checks"]}
    assert statuses.get("robots") == "fail"
    assert statuses.get("keyword_body") in ("warn", "fail")  # over-optimized
    assert result["score"] < 70


@pytest.mark.anyio
async def test_seo_meta_generate_fits_snippet_limits() -> None:
    result = await call_tool(
        "seo_meta_generate",
        page_title="The complete guide to incident checklists",
        summary="A checklist that helps on-call engineers detect, triage, and resolve incidents without missing a step.",
        target_keyword="incident checklist",
        site_name="AcmeCo",
        url="https://acmeco.example/incident-checklist",
        image_url="https://acmeco.example/og.png",
    )
    assert result["title_length"] <= 60
    assert result["meta_description_length"] <= 160
    assert result["title_fits"] and result["description_fits"]
    assert result["slug"] == "incident-checklist"
    assert '<meta name="description"' in result["html_snippet"]
    assert 'rel="canonical"' in result["html_snippet"]
    assert "og:image" in result["html_snippet"]


@pytest.mark.anyio
async def test_seo_keyword_extract_scores_terms_and_phrases() -> None:
    text = (
        "Incident checklists reduce alert fatigue. Incident checklists also speed up "
        "triage. On-call engineers rely on incident checklists during peak traffic, "
        "and dashboards confirm recovery time."
    )
    result = await call_tool("seo_keyword_extract", text=text, target_keyword="incident checklists")
    assert result["primary_keyword"]
    assert result["phrases"], "repeated bigrams should surface as phrases"
    assert all(p["count"] >= 2 for p in result["phrases"])
    assert result["target_keyword"]["count"] >= 3


@pytest.mark.anyio
async def test_seo_content_brief_classifies_commercial_intent() -> None:
    result = await call_tool("seo_content_brief", target_keyword="best incident tools", audience="SREs")
    assert result["intent"] == "commercial"
    assert 1800 <= result["word_target"] <= 2500
    assert result["outline"] and result["faq_block"]
    assert all(len(t) <= 60 for t in result["title_options"])
    assert "FAQPage" in result["schema_suggestion"] or "Product" in result["schema_suggestion"]


@pytest.mark.anyio
async def test_seo_url_audit_rejects_non_http_urls_without_fetching() -> None:
    result = await call_tool("seo_url_audit", url="example.com/no-scheme")
    assert result["status"] == "error"
    assert "http" in result["error"]


# ─── Marketing ────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_marketing_plan_covers_every_goal() -> None:
    for goal in ("launch", "growth", "retention", "leads", "awareness"):
        result = await call_tool(
            "marketing_plan",
            goal=goal,
            product="AcmeCo",
            audience="SRE teams at 10-100 person startups",
            budget=1000,
            horizon_days=30,
        )
        assert result["status"] == "ok", goal
        assert result["budget_pct_total"] == 100, goal
        amounts = [c["budget_amount"] for c in result["channels"]]
        assert abs(sum(amounts) - 1000) < 0.01, goal
        assert len(result["phases"]) == 4, goal
        assert result["risks"] and result["north_star_kpi"], goal


@pytest.mark.anyio
async def test_marketing_plan_rejects_unknown_goal() -> None:
    result = await call_tool("marketing_plan", goal="vibes", product="x", audience="y")
    assert result["status"] == "error"
    assert "launch" in result["available_goals"]


@pytest.mark.anyio
async def test_marketing_positioning_builds_statement_and_pillars() -> None:
    result = await call_tool(
        "marketing_positioning",
        product="AcmeCo",
        audience="on-call engineers",
        problem="they drown in alert noise",
        differentiators=["noise budgeting per service", "one-click rollback"],
        category="incident tool",
        competitors="PagerDuty, spreadsheets",
    )
    assert result["status"] == "ok"
    assert "AcmeCo" in result["positioning_statement"]
    assert "on-call engineers" in result["positioning_statement"]
    assert len(result["pillars"]) == 2
    assert result["tagline_options"] and len(result["objection_handling"]) == 3


@pytest.mark.anyio
async def test_marketing_positioning_requires_differentiators() -> None:
    result = await call_tool(
        "marketing_positioning",
        product="AcmeCo",
        audience="engineers",
        problem="alert fatigue",
        differentiators=[],
    )
    assert result["status"] == "error"


@pytest.mark.anyio
async def test_marketing_metrics_covers_all_models() -> None:
    for model in ("saas", "ecommerce", "marketplace", "content", "leadgen", "app"):
        result = await call_tool("marketing_metrics", goal="growth", business_model=model, stage="growth")
        assert result["status"] == "ok", model
        assert result["north_star"], model
        assert len(result["input_metrics"]) >= 3, model
        assert all(m["formula"] for m in result["input_metrics"]), model
        assert result["guardrails"] and result["thresholds"], model


@pytest.mark.anyio
async def test_marketing_icp_reports_missing_inputs() -> None:
    result = await call_tool("marketing_icp", product="AcmeCo", audience_hint="CTOs at B2B startups")
    assert result["status"] == "ok"
    assert set(result["missing_inputs"]) == {"pains", "goals", "objections"}
    assert result["reach_channels"], "channel hints derive from the audience hint"

    filled = await call_tool(
        "marketing_icp",
        product="AcmeCo",
        audience_hint="CTOs at B2B startups",
        pains=["alert fatigue", "flaky deploys"],
        goals=["ship daily"],
        objections=["too expensive"],
    )
    assert filled["missing_inputs"] == []
    assert filled["pains"] == ["alert fatigue", "flaky deploys"]
