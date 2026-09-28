"""JEBAT Marketing MCP Tools (Pawang Pemasaran).

Strategy-side playbooks that complement the copywriting tools (Pawang
Jualan, which handles the words). These structure the plan instead:
- marketing_plan: 30-day channel plan with budget split, phased actions,
  per-channel KPIs, and risks for launch/growth/retention/leads/awareness.
- marketing_positioning: Moore-style positioning statement, messaging
  pillars, tagline options, and objection/rebuttal table.
- marketing_metrics: north-star metric + input metric tree with formulas,
  RYG thresholds, guardrails, and review cadence per goal/model/stage.
- marketing_icp: structured ICP one-pager (jobs, pains, gains, channels,
  disqualifiers) from product + audience inputs.

All tools are deterministic playbooks — they structure what you give
them and never invent metrics or claims about your market.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from jebat.tools import register_tool


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in re.split(r"[,;\n]+", str(value)) if p.strip()]


# ─── Tool: marketing_plan ─────────────────────────────────────────────────

_GOAL_PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "launch": {
        "channels": [
            ("Content / SEO", 25, "medium", "Organic sessions → signup", "Compounds; you keep the traffic you earn."),
            ("Email list", 20, "medium", "Subscriber → activation rate", "Own the audience — algorithm-proof."),
            ("Paid ads (small tests)", 20, "high", "CAC per channel", "Buys data fast; only after the message converts."),
            ("Communities (Reddit/HN/Discord)", 15, "medium", "Qualified signups", "Where early adopters already gather."),
            ("Launch platforms (PH/directories)", 10, "low", "Launch-day signups", "One-shot spike + backlinks."),
            ("Partnerships / cross-promo", 10, "medium", "Partner-sourced signups", "Borrowed trust converts best."),
        ],
        "phases": [
            ("Ship the foundation", "Positioning page, analytics + event tracking, email capture, 3 cornerstone pieces of content."),
            ("Build pre-launch audience", "Teaser posts 3×/wk, waitlist loop, engage in 3 communities daily, collect 10 problem interviews."),
            ("Launch push", "Launch on 2 platforms + directories, email the list, partner embargo day, run paid message tests."),
            ("Read & iterate", "Kill channels above 2× target CAC, double down on the winner, turn launch feedback into content."),
        ],
        "risks": [
            ("Building in silence", "Start community + email capture in week 1, before the product is 'ready'."),
            ("Paid before message-market fit", "Cap paid at test budget until conversion beats 3% on the landing page."),
            ("Launch day = endpoint", "Treat launch as week 3 of 4; the compounding channels start after it."),
        ],
    },
    "growth": {
        "channels": [
            ("Content / SEO", 30, "high", "Non-branded clicks → trials", "Cheapest compounding acquisition at scale."),
            ("Lifecycle email", 20, "low", "Activation & expansion rate", "Cheapest revenue you already earned."),
            ("Paid acquisition", 20, "high", "Blended CAC / payback months", "Scales what already converts."),
            ("Referral / word of mouth", 15, "medium", "Invites per active user", "Best CAC when the product loops."),
            ("Social / community", 15, "medium", "Reach → assisted signups", "Distribution for everything else."),
        ],
        "phases": [
            ("Instrument the funnel", "Fix tracking, define activation, baseline every step conversion before touching spend."),
            ("Remove the biggest leak", "Attack the worst-converting step (usually signup→activation) for 2 weeks straight."),
            ("Scale the winner", "Raise budget/Output on the channel with proven CAC < payback target."),
            ("Systemize", "Document the loop, automate lifecycle flows, set monthly growth experiments cadence."),
        ],
        "risks": [
            ("Scaling a leaky funnel", "No channel spend until step conversions are instrumented and stable."),
            ("Channel myopia", "Keep one exploratory channel at 10% of budget every quarter."),
            ("Vanity metrics", "Rank by revenue per channel, not clicks or followers."),
        ],
    },
    "retention": {
        "channels": [
            ("Lifecycle email", 30, "low", "Week-4 retention", "Win-back and habit loops at near-zero cost."),
            ("In-app messaging", 25, "medium", "Feature adoption rate", "Right message at the value moment."),
            ("Community", 20, "medium", "DAU/WAU ratio", "Peers retain better than product alone."),
            ("Support loop", 15, "low", "Time-to-first-value for new users", "Support tickets are churn signals."),
            ("Loyalty / rewards", 10, "medium", "Repeat purchase / renewal rate", "Gives the engaged a reason to stay."),
        ],
        "phases": [
            ("Find the churn cause", "Exit interviews + cohort churn analysis: list the top 3 reasons users leave."),
            ("Fix time-to-value", "Onboarding rewrite targeting the 'aha' moment; measure day-1 activation lift."),
            ("Build the habit loop", "Trigger-based lifecycle emails + in-app nudges at the core action."),
            ("Close the loop", "Win-back flow for churned cohort; track recovered revenue monthly."),
        ],
        "risks": [
            ("Discounting to retain", "Price cuts train churn — fix value delivery before touching price."),
            ("Emailing inactive users hard", "Suppress beyond 90 days; protect deliverability and brand."),
            ("Measuring retention too late", "Track week-1 behavior proxies; monthly retention arrives a month late."),
        ],
    },
    "leads": {
        "channels": [
            ("SEO / content", 30, "high", "MQLs per 1k sessions", "Compounds and qualifies intent."),
            ("Outbound", 25, "high", "Meetings per 100 contacts", "Predictable volume while SEO ramps."),
            ("Webinars / live sessions", 15, "medium", "Attendee → opportunity rate", "High-intent leads self-select."),
            ("Paid search", 15, "medium", "Cost per qualified lead", "Captures existing demand now."),
            ("Partnerships", 15, "medium", "Partner-sourced pipeline", "Warm intros convert at 2-4× cold."),
        ],
        "phases": [
            ("Define qualification", "Write ICP + MQL criteria; align sales/marketing on what counts as a lead."),
            ("Build the bait", "One high-value asset (calculator/template/teardown) behind a short form."),
            ("Turn on two channels", "SEO cornerstone content + one always-on channel (outbound or paid)."),
            ("Score & prune", "Kill sources with MQL→opportunity below the bar; feed wins back into targeting."),
        ],
        "risks": [
            ("Volume over fit", "Measure pipeline dollars, not lead count — gated PDFs attract tourists."),
            ("Slow handoff", "Speed-to-lead under 5 minutes multiplies conversion; automate the routing."),
            ("Single-channel dependence", "Two live channels minimum before optimizing either."),
        ],
    },
    "awareness": {
        "channels": [
            ("Social (owned)", 30, "medium", "Branded search lift", "Frequency builds memory; post 4-5×/wk."),
            ("PR / earned", 20, "medium", "Mentions + referral spikes", "Third-party credibility you can't buy."),
            ("Creators / influencers", 20, "high", "Share of voice in niche", "Borrow an audience that already trusts them."),
            ("Community", 15, "medium", "Community growth + activity", "Awareness that turns into belonging."),
            ("Events / sponsorships", 15, "high", "Qualified conversations", "High-cost, high-recall moments."),
        ],
        "phases": [
            ("Sharpen the story", "One sentence anyone can repeat; visual/verbal identity locked."),
            ("Show up consistently", "4-5 posts/wk across 1-2 platforms; engage 30 min/day where the niche talks."),
            ("Borrow attention", "3 creator collabs + 1 earned-media push aimed at the same story."),
            ("Measure memory", "Track branded search, direct traffic, and mention volume — not impressions alone."),
        ],
        "risks": [
            ("Platform rent", "Move the audience to email/community within 90 days of every spike."),
            ("Story drift", "Repeat the same core story for a full quarter before changing it."),
            ("Impressions as success", "Awareness counts only when branded search and direct traffic move."),
        ],
    },
}


@register_tool(
    "marketing_plan",
    schema={
        "type": "object",
        "properties": {
            "goal": {
                "type": "string",
                "enum": ["launch", "growth", "retention", "leads", "awareness"],
                "description": "Primary marketing goal",
            },
            "product": {"type": "string", "description": "What you're marketing"},
            "audience": {"type": "string", "description": "Who you're trying to reach (ICP)"},
            "budget": {"type": "number", "description": "Total budget in your currency for the horizon (0 = effort-only plan)", "default": 0},
            "horizon_days": {"type": "integer", "description": "Planning horizon in days (default 30)", "default": 30, "minimum": 7, "maximum": 365},
        },
        "required": ["goal", "product", "audience"],
    },
    safety_tier="auto",
    timeout=10,
    description="Build a phased marketing plan for launch/growth/retention/leads/awareness: channel mix with budget split, phased actions, per-channel KPIs, and risks.",
)
async def marketing_plan(
    goal: str,
    product: str,
    audience: str,
    budget: float = 0.0,
    horizon_days: int = 30,
) -> Dict[str, Any]:
    """Structure a phased channel plan for a named goal."""
    key = (goal or "").strip().lower()
    if key not in _GOAL_PLAYBOOKS:
        return {"status": "error", "error": f"Unknown goal '{goal}'", "available_goals": sorted(_GOAL_PLAYBOOKS)}

    book = _GOAL_PLAYBOOKS[key]
    horizon_days = max(7, min(int(horizon_days or 30), 365))

    channels = []
    pct_total = 0
    for i, (name, pct, effort, kpi, why) in enumerate(book["channels"]):
        pct_total += pct
        entry = {
            "name": name,
            "budget_pct": pct,
            "effort": effort,
            "primary_kpi": kpi,
            "why": why,
        }
        if budget > 0:
            amount = round(budget * pct / 100, 2)
            if i == len(book["channels"]) - 1:  # rounding safety: last absorbs remainder
                amount = round(budget - sum(c.get("budget_amount", 0.0) for c in channels), 2)
            entry["budget_amount"] = amount
        channels.append(entry)

    bounds = [round(horizon_days * f) for f in (0, 0.25, 0.5, 0.75, 1.0)]
    phases = [
        {
            "phase": i + 1,
            "window": f"Days {bounds[i] + 1}-{bounds[i + 1]}",
            "focus": focus,
            "actions": [a.strip() for a in actions.split(";") if a.strip()],
        }
        for i, ((focus, actions)) in enumerate(book["phases"])
    ]

    return {
        "status": "ok",
        "goal": key,
        "product": product,
        "audience": audience,
        "horizon_days": horizon_days,
        "budget_total": budget if budget > 0 else None,
        "channels": channels,
        "budget_pct_total": pct_total,
        "phases": phases,
        "north_star_kpi": book["channels"][0][3],
        "risks": [{"risk": r, "mitigation": m} for r, m in book["risks"]],
        "first_actions": [a for p in phases[:1] for a in p["actions"]],
    }


# ─── Tool: marketing_positioning ──────────────────────────────────────────


@register_tool(
    "marketing_positioning",
    schema={
        "type": "object",
        "properties": {
            "product": {"type": "string", "description": "Product/brand name"},
            "audience": {"type": "string", "description": "Specific target segment (the narrower the better)"},
            "problem": {"type": "string", "description": "The painful problem you solve, in the customer's words"},
            "differentiators": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2-4 real, provable differentiators (not adjectives)",
            },
            "category": {"type": "string", "description": "Category you want to be read in (e.g. 'developer tool', 'CRM for clinics')", "default": ""},
            "competitors": {"type": "string", "description": "Alternatives customers use today (comma-separated), default: status quo", "default": ""},
        },
        "required": ["product", "audience", "problem", "differentiators"],
    },
    safety_tier="auto",
    timeout=10,
    description="Generate a positioning statement (Moore template), 3 messaging pillars with proof prompts, tagline options, and an objection/rebuttal table.",
)
async def marketing_positioning(
    product: str,
    audience: str,
    problem: str,
    differentiators: List[str],
    category: str = "",
    competitors: str = "",
) -> Dict[str, Any]:
    """Build a positioning statement and messaging pillars."""
    diffs = _listify(differentiators)
    if not diffs:
        return {"status": "error", "error": "Provide at least one real differentiator."}
    cat = category.strip() or "solution"
    rivals = [c.strip() for c in competitors.split(",") if c.strip()] or ["the status quo"]

    statement = (
        f"For {audience} who {problem.lstrip('Aa ').lstrip()}, {product} is the "
        f"{cat} that {diffs[0].rstrip('.')}. Unlike {', '.join(rivals[:2])}, {product} "
        + (f"{diffs[1].rstrip('.')}." if len(diffs) > 1 else "delivers it without the usual trade-offs.")
    )

    pillars = []
    for i, d in enumerate(diffs[:3], start=1):
        pillars.append({
            "pillar": f"Pillar {i}",
            "claim": d.rstrip("."),
            "proof_prompt": f"What evidence proves '{d.rstrip('.')}'? (number, demo, customer quote, benchmark)",
            "so_what": f"So {audience.split(',')[0]} gets: connect '{d.rstrip('.')}' to the outcome they pay for.",
        })

    taglines = [
        f"{product}: solve {problem.split(' without ')[0][:40].rstrip(',.')} — properly.",
        f"The {cat} built for {audience.split(',')[0]}",
        f"{product} — {diffs[0][:45].rstrip('.')}",
    ]

    objections = [
        {"objection": f"Why {product} instead of {rivals[0]}?",
         "rebuttal_slot": f"Lead with '{diffs[0]}' — then show the proof."},
        {"objection": "Is it worth switching / what's the risk?",
         "rebuttal_slot": f"Offer a low-friction trial plan; quantify the cost of '{problem[:60]}' staying unsolved."},
        {"objection": "We tried something like this before and it failed.",
         "rebuttal_slot": f"Name what changed: {diffs[-1]} — plus onboarding that lands value in the first session."},
    ]

    return {
        "status": "ok",
        "positioning_statement": statement,
        "category": cat,
        "pillars": pillars,
        "tagline_options": taglines,
        "competitive_frame": [
            {"vs": rival, "angle": diffs[i % len(diffs)]} for i, rival in enumerate(rivals[:3])
        ],
        "objection_handling": objections,
        "note": "Pillars are only as strong as the proof behind them — fill proof_prompt before publishing.",
    }


# ─── Tool: marketing_metrics ──────────────────────────────────────────────

_NORTH_STAR: Dict[str, str] = {
    "saas": "Weekly accounts reaching the core value action",
    "ecommerce": "Revenue from new customers (first-order)",
    "marketplace": "Completed transactions between members",
    "content": "Returning readers subscribed to owned channels",
    "leadgen": "Qualified opportunities created",
    "app": "Weekly active users completing the core action",
}

_INPUT_METRICS: Dict[str, List[Dict[str, str]]] = {
    "saas": [
        {"metric": "Signup → activation rate", "formula": "activated_users / signups", "why": "The gate to every downstream conversion."},
        {"metric": "Activation → paid rate", "formula": "paid_accounts / activated_accounts", "why": "Proves the aha moment sells."},
        {"metric": "Net revenue retention", "formula": "(start_mrr + expansion - contraction - churn) / start_mrr", "why": "Compounding growth or a leaky bucket."},
    ],
    "ecommerce": [
        {"metric": "Conversion rate", "formula": "orders / sessions", "why": "Multiplies the value of every traffic source."},
        {"metric": "Average order value", "formula": "revenue / orders", "why": "Cheapest lever on paid-back campaigns."},
        {"metric": "Repeat purchase rate", "formula": "customers_with_2plus_orders / customers", "why": "Determines whether CAC ever pays back."},
    ],
    "marketplace": [
        {"metric": "Liquidity", "formula": "transactions / active_listings (or search success %)", "why": "The marketplace health number."},
        {"metric": "GMV per active user", "formula": "gmv / monthly_active_users", "why": "Tracks engagement quality, not just size."},
        {"metric": "Supply-demand balance", "formula": "demand_queries / available_supply", "why": "Where liquidity breaks first."},
    ],
    "content": [
        {"metric": "Owned audience growth", "formula": "net_new_subscribers / week", "why": "Rented reach doesn't compound."},
        {"metric": "Return rate", "formula": "returning_visitors / unique_visitors", "why": "Signals content worth returning for."},
        {"metric": "Content → conversion", "formula": "conversions / content_sessions", "why": "Connects editorial effort to revenue."},
    ],
    "leadgen": [
        {"metric": "MQL → opportunity rate", "formula": "opportunities / mqls", "why": "The real quality score of a lead."},
        {"metric": "Cost per qualified lead", "formula": "channel_spend / qualified_leads", "why": "Keeps scale affordable."},
        {"metric": "Speed to lead", "formula": "minutes(first_contact) - minutes(form_submit)", "why": "First 5 minutes multiply conversion."},
    ],
    "app": [
        {"metric": "Day-1 / Day-7 retention", "formula": "returning_users_dayN / cohort_size", "why": "The shelf-life of your install spike."},
        {"metric": "Core action frequency", "formula": "core_actions / WAU", "why": "Habit depth, not just reach."},
        {"metric": "Session → value time", "formula": "seconds_until_core_action", "why": "Shorter = stickier."},
    ],
}

_STAGE_NOTES = {
    "early": "Optimize for learning speed: pick one input metric and move it weekly; ignore ±20% noise in samples under 100.",
    "growth": "Set RYG thresholds from your own 4-week baseline, then scale budget only while green.",
    "scale": "Add cohort splits (channel × segment) and watch blended CAC plus NRR; leading indicators before board metrics move.",
}


@register_tool(
    "marketing_metrics",
    schema={
        "type": "object",
        "properties": {
            "goal": {
                "type": "string",
                "enum": ["launch", "growth", "retention", "leads", "awareness"],
                "description": "Primary goal",
            },
            "business_model": {
                "type": "string",
                "enum": ["saas", "ecommerce", "marketplace", "content", "leadgen", "app"],
                "description": "Business model",
            },
            "stage": {"type": "string", "enum": ["early", "growth", "scale"], "description": "Company stage", "default": "early"},
        },
        "required": ["goal", "business_model"],
    },
    safety_tier="auto",
    timeout=10,
    description="Pick a north-star metric plus the input-metric tree (formulas included) for a goal/business model/stage, with guardrails, RYG thresholds, and review cadence.",
)
async def marketing_metrics(goal: str, business_model: str, stage: str = "early") -> Dict[str, Any]:
    """Define the metric tree for a goal and business model."""
    model = business_model.lower().strip()
    if model not in _INPUT_METRICS:
        return {"status": "error", "error": f"Unknown business_model '{business_model}'", "available": sorted(_INPUT_METRICS)}
    stg = stage if stage in _STAGE_NOTES else "early"

    north_star = _NORTH_STAR[model]
    goal_focus = {
        "launch": "Weight signup→activation hardest; acquisition volume is secondary until activation is stable.",
        "growth": "Optimize the input metric with the largest gap to benchmark — usually activation or paid conversion.",
        "retention": "Retention is the north star input: report week-over-week cohort curves, not totals.",
        "leads": "Optimize MQL→opportunity rate before optimizing lead volume.",
        "awareness": "Track branded search and direct traffic; impressions alone prove nothing.",
    }.get(goal, "")

    return {
        "status": "ok",
        "north_star": north_star,
        "goal_focus": goal_focus,
        "input_metrics": _INPUT_METRICS[model],
        "guardrails": [
            "Churn / refund rate (never buy growth that refunds out)",
            "Unsubscribe + spam-complaint rate (email health)",
            "Support tickets per active user (growth that creates load isn't growth)",
        ],
        "thresholds": {
            "green": "At or above plan (≥100% of target)",
            "yellow": "80-99% of target — investigate this week",
            "red": "<80% of target two weeks running — reallocate effort",
        },
        "cadence": {
            "daily": ["revenue, conversion, core-action volume"],
            "weekly": ["the full input-metric tree + one experiment verdict"],
            "monthly": ["cohort retention, CAC payback, channel mix"],
        },
        "stage_note": _STAGE_NOTES[stg],
        "note": "Thresholds are planning conventions — recalibrate against your own first 4 weeks of data.",
    }


# ─── Tool: marketing_icp ──────────────────────────────────────────────────


@register_tool(
    "marketing_icp",
    schema={
        "type": "object",
        "properties": {
            "product": {"type": "string", "description": "What you sell"},
            "audience_hint": {"type": "string", "description": "Free-form description of who buys today (role, company, context)", "default": ""},
            "pains": {"type": "array", "items": {"type": "string"}, "description": "Known pains, comma- or array-provided", "default": []},
            "goals": {"type": "array", "items": {"type": "string"}, "description": "What they're trying to achieve", "default": []},
            "objections": {"type": "array", "items": {"type": "string"}, "description": "Obections you hear in sales", "default": []},
        },
        "required": ["product"],
    },
    safety_tier="auto",
    timeout=10,
    description="Structure an ICP one-pager from product + audience inputs: jobs, pains, gains, messaging angles, reach channels, objection hooks, and disqualifiers.",
)
async def marketing_icp(
    product: str,
    audience_hint: str = "",
    pains: List[str] | None = None,
    goals: List[str] | None = None,
    objections: List[str] | None = None,
) -> Dict[str, Any]:
    """Structure an ICP one-pager from supplied inputs."""
    pain_list = _listify(pains)
    goal_list = _listify(goals)
    obj_list = _listify(objections)
    hint = audience_hint.strip()

    profile = hint or "[Describe the buyer: role, company size, context where the pain shows up]"
    hint_low = hint.lower()

    channel_guesses = []
    if any(k in hint_low for k in ("developer", "engineer", "cto", "technical", "devops")):
        channel_guesses = ["GitHub / dev communities", "Hacker News", "Technical blogs + newsletters", "Dev conferences/meetups"]
    elif any(k in hint_low for k in ("designer", "agency", "creative")):
        channel_guesses = ["Dribbble / Behance", "Design Twitter/X", "Designer newsletters", "Figma communities"]
    elif any(k in hint_low for k in ("marketing", "growth", "founder", "startup", "smb")):
        channel_guesses = ["LinkedIn", "X / indie communities", "Industry newsletters", "Podcast guesting"]
    elif any(k in hint_low for k in ("enterprise", "procurement", "b2b", "manager", "director")):
        channel_guesses = ["LinkedIn outbound", "Industry events", "Analyst/review sites", "Partner referrals"]
    if not channel_guesses:
        channel_guesses = ["Where they already gather: 2 communities + 1 industry newsletter + LinkedIn/X search by pain quotes"]

    jobs = goal_list or [
        "[JTBD: what they're hiring the product to do — start with 'When I ___, I want to ___, so I can ___']",
    ]
    pains_out = pain_list or ["[Top pain, in their exact words — mine your support tickets and sales calls]"]
    gains_out = [
        "Outcome they'd pay for: measurable result tied to the job",
        "How they'd describe success to their boss",
        "Fastest acceptable time-to-value",
    ]

    messages = []
    if goal_list:
        messages.append(f"Outcome-first: lead with '{goal_list[0]}' — the product is the vehicle.")
    if pain_list:
        messages.append(f"Problem-first: name '{pain_list[0]}' louder than they do.")
    messages.append(f"Proof-first: show '{(obj_list or ['risk'])[0]}' being removed with evidence.")

    return {
        "status": "ok",
        "product": product,
        "profile": profile,
        "jobs_to_be_done": jobs,
        "pains": pains_out,
        "gains": gains_out,
        "messaging_angles": messages,
        "reach_channels": channel_guesses,
        "objection_hooks": (
            [{"objection": o, "hook": f"Answer with proof of '{diffs_label}'" if (diffs_label := "the differentiator that removes it") else ""} for o in obj_list]
            if obj_list else
            [{"objection": "[Ask sales: what stops the deal?]", "hook": "Map each objection to one proof asset"}]
        ),
        "disqualifiers": [
            "No access to the person who feels the pain (buyer ≠ user and no bridge)",
            "The pain costs them less than your price to fix",
            "They need a feature roadmap, not the outcome you already deliver",
        ],
        "missing_inputs": [name for name, val in (("pains", pain_list), ("goals", goal_list), ("objections", obj_list)) if not val],
        "note": "Fill missing_inputs from real customer language — verbatim quotes beat adjectives.",
    }
