"""JEBAT SEO MCP Tools (Pawang SEO / Search Visibility).

Deterministic on-page SEO toolkit plus live checks:
- seo_audit: Score any HTML document against on-page SEO checks
  (title, meta, canonical, OG/Twitter cards, headings, alt text, keywords).
- seo_meta_generate: Generate a title, meta description, slug, canonical,
  and social tags that fit search-engine length limits.
- seo_keyword_extract: Extract primary/secondary keywords and phrases
  from text with frequency scoring and target-keyword density.
- seo_content_brief: Build a keyword-targeted content brief (intent,
  outline, FAQ block, schema type, word target).
- seo_serp_check: Live SERP position check for a domain on a query
  using JEBAT's search backend (SearXNG → Google/Bing → DuckDuckGo).
- seo_url_audit: Live audit of a URL (status, redirects, robots,
  sitemap) combined with the on-page checks.

All offline tools are pure functions — no network, no keys, fast enough
to run on every page edit.
"""

from __future__ import annotations

import html as html_mod
import re
from collections import Counter
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from jebat.tools import register_tool


# ─── Shared HTML facts ────────────────────────────────────────────────────


class _PageParser(HTMLParser):
    """Collect the on-page SEO facts a human auditor would look at first."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.metas: Dict[str, str] = {}
        self.canonical = ""
        self.lang = ""
        self.headings: List[Tuple[int, str]] = []
        self.img_total = 0
        self.img_missing_alt = 0
        self.links: List[str] = []
        self.json_ld_count = 0
        self.text_parts: List[str] = []
        self._in_title = False
        self._cur_h: Optional[int] = None
        self._cur_h_parts: List[str] = []
        self._suppress = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = d.get("lang", "").strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (d.get("name") or d.get("property") or "").lower().strip()
            if key and key not in self.metas:
                self.metas[key] = d.get("content", "").strip()
        elif tag == "link":
            rel = d.get("rel", "").lower()
            if "canonical" in rel and not self.canonical:
                self.canonical = d.get("href", "").strip()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._cur_h = int(tag[1])
            self._cur_h_parts = []
        elif tag == "img":
            self.img_total += 1
            if not d.get("alt", "").strip():
                self.img_missing_alt += 1
        elif tag == "a":
            href = d.get("href", "").strip()
            if href:
                self.links.append(href)
        elif tag == "script":
            if d.get("type", "").lower() == "application/ld+json":
                self.json_ld_count += 1
            self._suppress += 1
        elif tag in ("style", "noscript"):
            self._suppress += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._cur_h is not None:
            text = " ".join("".join(self._cur_h_parts).split())
            self.headings.append((self._cur_h, text))
            self._cur_h = None
            self._cur_h_parts = []
        elif tag in ("script", "style", "noscript") and self._suppress > 0:
            self._suppress -= 1

    def handle_data(self, data: str) -> None:
        if self._suppress > 0:
            return
        if self._in_title:
            self.title += data
            return
        if data.strip():
            self.text_parts.append(data)

    # Derived helpers -----------------------------------------------------
    @property
    def title_text(self) -> str:
        return " ".join(self.title.split())

    @property
    def body_text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())

    @property
    def word_count(self) -> int:
        return len(self.body_text.split())

    def h1s(self) -> List[str]:
        return [t for lvl, t in self.headings if lvl == 1]


def _parse_page(html: str) -> _PageParser:
    parser = _PageParser()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:
        # Malformed HTML still yields whatever was parsed before the error.
        pass
    return parser


def _kw_hits(text: str, keyword: str) -> int:
    if not keyword:
        return 0
    return len(re.findall(rf"\b{re.escape(keyword.strip())}\b", text, re.I))


# ─── Shared checks ────────────────────────────────────────────────────────


def _run_checks(page: _PageParser, target_keyword: str = "") -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(cid: str, status: str, detail: str, fix: str = "") -> None:
        checks.append({"id": cid, "status": status, "detail": detail, "fix": fix})

    title = page.title_text
    desc = page.metas.get("description", "")
    kw = target_keyword.strip()

    # Title
    if not title:
        add("title", "fail", "No <title> tag found.", "Add a unique title of 50-60 chars with the target keyword.")
    elif len(title) > 60:
        add("title", "warn", f"Title is {len(title)} chars (ideal ≤60; Google truncates ~600px).", "Shorten the title, keyword first.")
    elif len(title) < 15:
        add("title", "warn", f"Title is only {len(title)} chars.", "Use the full 50-60 char budget.")
    else:
        add("title", "pass", f"Title OK ({len(title)} chars): {title}")
    if kw and title and _kw_hits(title, kw) == 0:
        add("title_keyword", "fail", f"Target keyword '{kw}' not in title.", f"Lead the title with '{kw}'.")
    elif kw and title:
        add("title_keyword", "pass", "Target keyword present in title.")

    # Meta description
    if not desc:
        add("meta_description", "fail", "No meta description.", "Write a 140-160 char description with the keyword and a hook.")
    elif len(desc) > 160:
        add("meta_description", "warn", f"Meta description is {len(desc)} chars (truncated past ~160).", "Trim to ≤160 chars.")
    elif len(desc) < 120:
        add("meta_description", "warn", f"Meta description is {len(desc)} chars (aim 140-160).", "Expand with benefit + CTA.")
    else:
        add("meta_description", "pass", f"Meta description OK ({len(desc)} chars).")

    # Canonical / robots / viewport / lang
    add("canonical", "pass" if page.canonical else "warn",
        f"Canonical: {page.canonical}" if page.canonical else "No canonical link tag.",
        "" if page.canonical else 'Add <link rel="canonical" href="..."> to prevent duplicate-content issues.')
    add("viewport", "pass" if "viewport" in page.metas else "fail",
        "Viewport meta present." if "viewport" in page.metas else "No viewport meta (not mobile-friendly).",
        "" if "viewport" in page.metas else 'Add <meta name="viewport" content="width=device-width, initial-scale=1">.')
    add("lang", "pass" if page.lang else "warn",
        f"<html lang=\"{page.lang}\"> set." if page.lang else "Missing lang attribute on <html>.",
        "" if page.lang else 'Add lang (e.g. <html lang="en">) for accessibility + hreflang signals.')
    robots = page.metas.get("robots", "").lower()
    if robots and "noindex" in robots:
        add("robots", "fail", f"Page is NOINDEX ({robots}).", "Remove noindex if this page should rank.")

    # Social
    og_missing = [k for k in ("og:title", "og:description", "og:image") if k not in page.metas]
    if og_missing:
        add("open_graph", "warn", f"Missing Open Graph tags: {', '.join(og_missing)}.",
            "Add og:title/og:description/og:image for rich social shares.")
    else:
        add("open_graph", "pass", "Open Graph tags complete.")
    add("twitter_card", "pass" if "twitter:card" in page.metas else "warn",
        "twitter:card present." if "twitter:card" in page.metas else "No twitter:card meta.",
        "" if "twitter:card" in page.metas else 'Add <meta name="twitter:card" content="summary_large_image">.')

    # Headings
    h1s = page.h1s()
    if not h1s:
        add("h1", "fail", "No H1 on the page.", "Add exactly one H1 containing the target keyword.")
    elif len(h1s) > 1:
        add("h1", "warn", f"{len(h1s)} H1 tags found.", "Keep one H1; demote the rest to H2.")
    else:
        add("h1", "pass", f"H1: {h1s[0][:80]}")
    if kw and h1s and _kw_hits(h1s[0], kw) == 0:
        add("h1_keyword", "warn", f"H1 does not contain '{kw}'.", "Work the keyword into the H1 naturally.")
    levels = [lvl for lvl, _ in page.headings if lvl in (2, 3)]
    skipped = any(levels[i + 1] - levels[i] > 1 for i in range(len(levels) - 1))
    if skipped:
        add("heading_order", "warn", "Heading levels skip (e.g. H2 → H4).", "Use sequential heading levels.")
    elif not levels:
        add("heading_order", "warn", "No H2/H3 subheadings.", "Break content into H2/H3 sections for SERP sitelinks.")

    # Images
    if page.img_missing_alt:
        add("image_alt", "fail", f"{page.img_missing_alt} of {page.img_total} images missing alt text.",
            "Describe each image in alt text (keyword only when accurate).")
    elif page.img_total:
        add("image_alt", "pass", f"All {page.img_total} images have alt text.")

    # Content depth
    if page.word_count < 300:
        add("content_depth", "warn", f"Only {page.word_count} body words (thin content).",
            "Aim for 300+ words minimum; match the top-ranking pages.")
    else:
        add("content_depth", "pass", f"{page.word_count} body words.")

    # Structured data
    add("structured_data", "pass" if page.json_ld_count else "warn",
        f"{page.json_ld_count} JSON-LD block(s)." if page.json_ld_count else "No JSON-LD structured data.",
        "" if page.json_ld_count else "Add schema.org JSON-LD (Article/Product/FAQ) for rich results.")

    # Internal links
    internal = [lnk for lnk in page.links if lnk.startswith("/") or lnk.startswith("#")]
    if len(internal) < 3:
        add("internal_links", "warn", f"Only {len(internal)} internal links.", "Link to 3+ related pages/resources.")
    else:
        add("internal_links", "pass", f"{len(internal)} internal links.")

    # Keyword (only when a target is given)
    if kw:
        body_hits = _kw_hits(page.body_text, kw)
        density = (body_hits / page.word_count * 100) if page.word_count else 0.0
        if body_hits == 0:
            add("keyword_body", "fail", f"'{kw}' not found in body text.",
                f"Use '{kw}' in the first 100 words and 2-4 more times naturally.")
        elif density > 3.0:
            add("keyword_body", "warn", f"Keyword density {density:.1f}% — over-optimized (>3%).", "Reduce repetitions; use synonyms.")
        else:
            add("keyword_body", "pass", f"'{kw}' found {body_hits}× (density {density:.1f}%).")

    return checks


def _score(checks: List[Dict[str, Any]]) -> Tuple[int, str]:
    score = 100
    for c in checks:
        if c["status"] == "fail":
            score -= 8
        elif c["status"] == "warn":
            score -= 4
    score = max(0, score)
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    return score, grade


def _stats(page: _PageParser) -> Dict[str, Any]:
    return {
        "title": page.title_text,
        "title_length": len(page.title_text),
        "meta_description_length": len(page.metas.get("description", "")),
        "h1_count": len(page.h1s()),
        "heading_count": len(page.headings),
        "images": page.img_total,
        "images_missing_alt": page.img_missing_alt,
        "links": len(page.links),
        "word_count": page.word_count,
        "json_ld_blocks": page.json_ld_count,
        "lang": page.lang,
        "canonical": page.canonical,
    }


# ─── Tool: seo_audit ──────────────────────────────────────────────────────


@register_tool(
    "seo_audit",
    schema={
        "type": "object",
        "properties": {
            "html": {"type": "string", "description": "Full HTML of the page to audit"},
            "target_keyword": {"type": "string", "description": "Optional target keyword to check placement/density for"},
        },
        "required": ["html"],
    },
    safety_tier="auto",
    timeout=20,
    description="On-page SEO audit of an HTML document: scores title/meta/canonical/OG/headings/alt/keyword checks 0-100 with prioritized fixes.",
)
async def seo_audit(html: str, target_keyword: str = "") -> Dict[str, Any]:
    """Score a page's HTML against on-page SEO checks."""
    page = _parse_page(html)
    checks = _run_checks(page, target_keyword)
    score, grade = _score(checks)
    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    return {
        "score": score,
        "grade": grade,
        "target_keyword": target_keyword,
        "counts": {"pass": len(checks) - len(failures) - len(warnings), "warn": len(warnings), "fail": len(failures)},
        "quick_fixes": [c["fix"] for c in (failures + warnings) if c["fix"]][:3],
        "checks": checks,
        "stats": _stats(page),
    }


# ─── Tool: seo_meta_generate ──────────────────────────────────────────────


def _truncate(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    return cut[: cut.rfind(" ")].rstrip(" ,;:-") if " " in cut else cut


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:80].rstrip("-")


@register_tool(
    "seo_meta_generate",
    schema={
        "type": "object",
        "properties": {
            "page_title": {"type": "string", "description": "What the page is about (human wording)"},
            "summary": {"type": "string", "description": "1-3 sentence summary of the page's value"},
            "target_keyword": {"type": "string", "description": "Primary keyword to front-load", "default": ""},
            "site_name": {"type": "string", "description": "Brand/site name for the title suffix", "default": ""},
            "url": {"type": "string", "description": "Canonical URL of the page (for canonical/og:url)", "default": ""},
            "image_url": {"type": "string", "description": "Absolute URL of the social image (for og:image)", "default": ""},
        },
        "required": ["page_title", "summary"],
    },
    safety_tier="auto",
    timeout=10,
    description="Generate an SEO title (≤60), meta description (≤160), slug, canonical, and Open Graph/Twitter tags that fit search snippet limits.",
)
async def seo_meta_generate(
    page_title: str,
    summary: str,
    target_keyword: str = "",
    site_name: str = "",
    url: str = "",
    image_url: str = "",
) -> Dict[str, Any]:
    """Generate length-safe title, description, slug and social meta tags."""
    kw = (target_keyword or page_title).strip()
    site = site_name.strip()

    title = _truncate(f"{kw} | {site}" if site else kw, 60)
    alt_title = _truncate(f"{page_title} | {site}" if site else page_title, 60)
    if len(title) < 30 and len(alt_title) > len(title):
        title = alt_title

    desc_src = " ".join(summary.split())
    if kw.lower() not in desc_src.lower():
        desc_src = f"{kw}: {desc_src}"
    description = _truncate(desc_src, 160)
    if len(description) < 120:
        description = _truncate(f"{description} Learn more and get started today.", 160)

    slug = _slugify(target_keyword or page_title)

    esc = lambda s: html_mod.escape(s, quote=True)  # noqa: E731
    snippet_lines = [
        f"<title>{html_mod.escape(title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
    ]
    if url:
        snippet_lines.append(f'<link rel="canonical" href="{esc(url)}">')
        snippet_lines.append(f'<meta property="og:url" content="{esc(url)}">')
    snippet_lines += [
        '<meta name="robots" content="index,follow">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(description)}">',
    ]
    if image_url:
        snippet_lines.append(f'<meta property="og:image" content="{esc(image_url)}">')

    return {
        "title": title,
        "title_length": len(title),
        "title_fits": len(title) <= 60,
        "meta_description": description,
        "meta_description_length": len(description),
        "description_fits": len(description) <= 160,
        "slug": slug,
        "html_snippet": "\n".join(snippet_lines),
        "checks": {
            "keyword_in_title": _kw_hits(title, kw) > 0 if target_keyword else None,
            "keyword_in_description": _kw_hits(description, kw) > 0 if target_keyword else None,
        },
    }


# ─── Tool: seo_keyword_extract ────────────────────────────────────────────

_STOPWORDS = {
    "the", "and", "for", "you", "your", "are", "was", "with", "that", "this",
    "these", "those", "from", "have", "has", "had", "but", "not", "what",
    "when", "where", "which", "while", "will", "would", "could", "should",
    "can", "may", "might", "must", "about", "into", "over", "under", "after",
    "before", "between", "through", "during", "above", "below", "out", "off",
    "again", "more", "most", "some", "such", "than", "too", "very", "just",
    "only", "also", "then", "once", "here", "there", "their", "they", "them",
    "his", "her", "its", "our", "who", "whom", "how", "why", "all", "any",
    "each", "other", "being", "because", "until", "against", "both", "same",
    "own", "why", "doing", "does", "did", "done", "get", "got", "make",
    "made", "use", "used", "using", "via", "per", "one", "two", "new", "first",
    "last", "long", "great", "like", "even", "way", "well", "back", "much",
    "know", "want", "need", "see", "look", "come", "take", "many", "user",
    "users", "page", "pages", "site", "web", "www", "com", "http", "https",
    "html", "default", "added", "based", "following", "following", "please",
    "click", "here", "home", "menu", "search", "close", "next", "post",
    "comments", "comment", "share", "email", "name", "date", "posted",
    "entry", "continue", "reading", "article", "content", "website",
}


@register_tool(
    "seo_keyword_extract",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Body text to analyze (paste page copy or an article draft)"},
            "target_keyword": {"type": "string", "description": "Optional keyword to measure placement/density for", "default": ""},
            "top_n": {"type": "integer", "description": "How many keywords/phrases to return (default 10)", "default": 10, "minimum": 3, "maximum": 30},
        },
        "required": ["text"],
    },
    safety_tier="auto",
    timeout=10,
    description="Extract primary/secondary keywords and phrases from text with frequency scoring, plus target-keyword density when given.",
)
async def seo_keyword_extract(text: str, target_keyword: str = "", top_n: int = 10) -> Dict[str, Any]:
    """Score content terms and phrases the way an SEO would."""
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9']{3,}", text or "")]
    content_tokens = [t for t in tokens if t not in _STOPWORDS]
    if not content_tokens:
        return {"error": "No analyzable content (need at least a few words).", "keywords": [], "phrases": []}

    uni = Counter(content_tokens)
    bigrams = [
        f"{content_tokens[i]} {content_tokens[i + 1]}"
        for i in range(len(content_tokens) - 1)
    ]
    bi = Counter(bigrams)

    def uni_score(w: str, c: int) -> float:
        return round(c * (1 + 0.15 * max(0, len(w) - 4)), 2)

    def bi_score(p: str, c: int) -> float:
        return round(c * 3.0 + 0.4 * len(p), 2)

    primary = ""
    if target_keyword and target_keyword.lower() in text.lower():
        primary = target_keyword.strip().lower()
    elif uni:
        primary = uni.most_common(1)[0][0]

    keywords = [
        {"keyword": w, "count": c, "score": uni_score(w, c)}
        for w, c in uni.most_common(max(top_n * 3, 30))
        if w != primary
    ]
    keywords.sort(key=lambda x: -x["score"])
    phrases = [
        {"phrase": p, "count": c, "score": bi_score(p, c)}
        for p, c in bi.most_common(max(top_n * 3, 30))
        if c >= 2
    ]
    phrases.sort(key=lambda x: -x["score"])

    words_total = len(text.split())
    hits = _kw_hits(text, primary) if primary else 0
    density = round(hits / words_total * 100, 2) if words_total else 0.0

    return {
        "primary_keyword": primary,
        "secondary_keywords": keywords[:top_n],
        "phrases": phrases[:top_n],
        "target_keyword": {
            "keyword": target_keyword,
            "count": _kw_hits(text, target_keyword) if target_keyword else None,
            "density_pct": round(_kw_hits(text, target_keyword) / words_total * 100, 2) if target_keyword and words_total else None,
        },
        "word_count": words_total,
        "density_of_primary_pct": density,
        "guidance": [
            "Primary keyword: front-load the title, H1, first 100 words, and slug.",
            "Secondary keywords: work into H2s and body copy where they read naturally.",
            "Phrases with count ≥2 are strong internal-link anchor candidates.",
        ],
    }


# ─── Tool: seo_content_brief ──────────────────────────────────────────────


@register_tool(
    "seo_content_brief",
    schema={
        "type": "object",
        "properties": {
            "target_keyword": {"type": "string", "description": "Primary keyword/topic to rank for"},
            "audience": {"type": "string", "description": "Who the content is for", "default": ""},
            "funnel_stage": {"type": "string", "description": "informational | commercial | transactional (auto-detected if omitted)", "default": ""},
            "word_count_goal": {"type": "integer", "description": "Override the word target (0 = derive from intent)", "default": 0},
        },
        "required": ["target_keyword"],
    },
    safety_tier="auto",
    timeout=10,
    description="Build a keyword-targeted content brief: search intent, title options, H2/H3 outline, FAQ block, schema type, and word target.",
)
async def seo_content_brief(
    target_keyword: str,
    audience: str = "",
    funnel_stage: str = "",
    word_count_goal: int = 0,
) -> Dict[str, Any]:
    """Generate an on-page content brief from a target keyword."""
    kw = " ".join((target_keyword or "").split())
    if not kw:
        return {"error": "target_keyword is required"}
    low = kw.lower()

    stage = (funnel_stage or "").strip().lower()
    if stage not in ("informational", "commercial", "transactional"):
        if re.search(r"\b(best|top|vs|versus|review|comparison|compare|alternative|pricing|price|cost)\b", low):
            stage = "commercial"
        elif re.search(r"\b(buy|discount|coupon|order|shipping|signup|sign up|download|trial|demo|deal|hire)\b", low):
            stage = "transactional"
        elif re.search(r"\b(how|what|why|when|where|which|guide|tutorial|ideas|examples|meaning|definition)\b", low):
            stage = "informational"
        else:
            stage = "informational"

    word_targets = {
        "informational": (1200, 1800),
        "commercial": (1800, 2500),
        "transactional": (700, 1200),
    }
    lo, hi = word_targets[stage]
    word_target = word_count_goal if word_count_goal > 0 else (lo + hi) // 2

    title_templates = {
        "informational": [
            f"{kw.title()}: The Complete Guide",
            f"What Is {kw.title()}? Everything You Need to Know",
            f"How to Approach {kw.title()} (Step by Step)",
        ],
        "commercial": [
            f"Best {kw.title()}: Compared & Reviewed",
            f"{kw.title()}: Features, Pricing & Trade-offs",
            f"Top {kw.title()} Options Ranked",
        ],
        "transactional": [
            f"{kw.title()} — Get Started Today",
            f"Buy {kw.title()}: What You Get & Pricing",
            f"{kw.title()}: Plans, Pricing & Sign-up",
        ],
    }
    titles = [_truncate(t, 60) for t in title_templates[stage]]

    outlines = {
        "informational": [
            ("Introduction: why this matters now", []),
            (f"What {kw} actually is", ["Definition in one sentence", "How it differs from the nearest alternative"]),
            (f"Why {kw} matters", ["Concrete benefits with numbers", "Who it's for"]),
            (f"How to work with {kw}: step by step", ["Step 1", "Step 2", "Step 3"]),
            ("Common mistakes to avoid", []),
            ("FAQ", []),
            ("Conclusion + next step", []),
        ],
        "commercial": [
            ("Introduction: the decision you're facing", []),
            (f"What to look for in {kw}", ["Must-haves", "Deal-breakers"]),
            (f"Top {kw} options compared", ["Option 1", "Option 2", "Option 3"]),
            ("Pricing & value for money", []),
            ("How to choose (decision framework)", []),
            ("FAQ", []),
            ("Final verdict", []),
        ],
        "transactional": [
            (f"What you get with {kw}", ["Key outcomes", "What's included"]),
            ("Features & specifications", []),
            ("Pricing & plans", []),
            ("How to get started (3 steps)", []),
            ("FAQ: objections answered", []),
            ("CTA: start now", []),
        ],
    }
    schema_types = {
        "informational": ["Article", "FAQPage"],
        "commercial": ["Product", "Review"],
        "transactional": ["Product", "Offer"],
    }

    faq = [
        f"What is {kw}?",
        f"Why is {kw} important?",
        f"How do I get started with {kw}?",
        f"How long does {kw} take to show results?",
        f"What are the best {kw} practices?",
        f"How much does {kw} cost?",
    ]

    return {
        "target_keyword": kw,
        "intent": stage,
        "audience": audience,
        "word_target": word_target,
        "slug": _slugify(kw),
        "title_options": titles,
        "meta_description": _truncate(
            (f"A practical guide to {kw}" if stage == "informational"
             else f"Compare the top {kw} options" if stage == "commercial"
             else f"Get {kw} today") + (f" for {audience}" if audience else "") + ". Honest, updated, and built to save you time.",
            160,
        ),
        "outline": [{"h2": h2, "h3": h3s} for h2, h3s in outlines[stage]],
        "faq_block": faq,
        "schema_suggestion": schema_types[stage],
        "onpage_checklist": [
            f"Keyword '{kw}' in the title, H1, slug, and meta description",
            "Keyword in the first 100 words",
            f"Reach ~{word_target} words (current top pages set the bar)",
            "At least 3 internal links + descriptive image alts",
            "One original asset (table, screenshot, or chart) to earn snippets",
        ],
        "note": "Heuristic brief — validate word target and titles against the live SERP (see seo_serp_check).",
    }


# ─── Tool: seo_serp_check (live) ──────────────────────────────────────────


def _host(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


@register_tool(
    "seo_serp_check",
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query to check rankings for"},
            "domain": {"type": "string", "description": "Domain to look for (e.g. example.com). Omit for a competitor overview.", "default": ""},
            "top_n": {"type": "integer", "description": "Results to inspect (default 10, max 25)", "default": 10, "minimum": 5, "maximum": 25},
        },
        "required": ["query"],
    },
    safety_tier="auto",
    timeout=35,
    description="Live SERP check: run a query through JEBAT's search backend and report whether a domain ranks, its position, and the current top results.",
)
async def seo_serp_check(query: str, domain: str = "", top_n: int = 10) -> Dict[str, Any]:
    """Check live search rankings for a domain on a query."""
    from jebat.features.search.web_search import search_web

    out = await search_web(query, limit=max(5, min(int(top_n or 10), 25)))
    results = out.get("results", []) or []
    if results and isinstance(results[0], dict) and results[0].get("error"):
        return {"status": "error", "error": results[0]["error"], "query": query}

    target = _host("https://" + domain.strip()) if domain.strip() else ""
    entries = []
    for i, r in enumerate(results[:25], start=1):
        url = r.get("url", "")
        entries.append({
            "position": i,
            "title": r.get("title", ""),
            "url": url,
            "domain": _host(url),
            "snippet": (r.get("snippet") or "")[:200],
        })

    target_hits = [e for e in entries if target and (e["domain"] == target or e["domain"].endswith("." + target))]
    return {
        "status": "ok",
        "query": query,
        "checked": len(entries),
        "target_domain": target or None,
        "ranking_position": target_hits[0]["position"] if target_hits else None,
        "ranked": bool(target_hits),
        "target_entries": target_hits,
        "top_results": entries[:10],
        "competitor_domains": [e["domain"] for e in entries[:10] if e["domain"] and e["domain"] != target][:10],
        "summary": (
            f"'{query}': {target} ranks #{target_hits[0]['position']}" if target_hits
            else f"'{query}': {target or 'domain'} not in top {len(entries)} (competitors: {', '.join(sorted({e['domain'] for e in entries[:5]}))})" if target
            else f"'{query}': top {len(entries)} results collected"
        ),
    }


# ─── Tool: seo_url_audit (live) ───────────────────────────────────────────


@register_tool(
    "seo_url_audit",
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Absolute http(s) URL to audit"},
            "target_keyword": {"type": "string", "description": "Optional target keyword for placement checks", "default": ""},
        },
        "required": ["url"],
    },
    safety_tier="auto",
    timeout=30,
    description="Live audit of a URL: HTTP status, redirect chain, response time, robots.txt/sitemap availability, plus the full on-page SEO checks.",
)
async def seo_url_audit(url: str, target_keyword: str = "") -> Dict[str, Any]:
    """Fetch a URL and run the on-page audit against the live page."""
    import httpx
    from jebat.features.security.outbound import get_validated, OutboundURLBlocked

    url = (url or "").strip()
    if not url.lower().startswith(("http://", "https://")):
        return {"status": "error", "error": "url must start with http:// or https://"}

    headers = {"User-Agent": "JEBAT-SEO-Audit/1.0 (+https://github.com/jebat)"}
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await get_validated(client, url, headers=headers)
            elapsed_ms = int(resp.elapsed.total_seconds() * 1000)

            robots_status = None
            sitemap_urls: List[str] = []
            origin = f"{resp.url.scheme}://{resp.url.netloc}"
            try:
                robots = await get_validated(client, f"{origin}/robots.txt", headers=headers)
                robots_status = robots.status_code
                if robots.status_code == 200:
                    sitemap_urls = re.findall(r"(?i)^sitemap:\s*(\S+)", robots.text)[:5]
            except Exception:
                pass
    except OutboundURLBlocked as exc:
        return {"status": "error", "error": f"Blocked unsafe URL: {exc}", "url": url}
    except Exception as e:
        return {"status": "error", "error": f"Fetch failed: {e}", "url": url}
    content_type = resp.headers.get("content-type", "")
    facts: Dict[str, Any] = {
        "status_code": resp.status_code,
        "final_url": str(resp.url),
        "redirect_chain": [str(h.url) for h in resp.history],
        "redirects": len(resp.history),
        "response_ms": elapsed_ms,
        "content_type": content_type,
        "https": str(resp.url).startswith("https://"),
        "robots_txt": robots_status,
        "sitemaps_declared": sitemap_urls,
        "bytes": len(resp.content),
    }

    if resp.status_code >= 400:
        return {"status": "error", "url": url, "server": facts,
                "error": f"HTTP {resp.status_code} — fix availability before on-page work."}

    if "html" not in content_type:
        return {"status": "error", "url": url, "server": facts,
                "error": f"Content-Type is '{content_type}', not HTML — nothing to audit on-page."}

    page = _parse_page(resp.text)
    checks = _run_checks(page, target_keyword)
    score, grade = _score(checks)
    failures = [c for c in checks if c["status"] == "fail"]

    return {
        "status": "ok",
        "url": url,
        "score": score,
        "grade": grade,
        "server": facts,
        "quick_fixes": [c["fix"] for c in failures if c["fix"]][:3],
        "checks": checks,
        "stats": _stats(page),
    }
