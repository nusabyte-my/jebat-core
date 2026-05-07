"""
JEBAT WebSearch Skill

Multi-engine web search with no API keys required (DuckDuckGo).
Optional support for Brave Search and SearXNG with API keys.

Usage:
    from apps.api.skills.web_search import WebSearchSkill

    skill = WebSearchSkill()
    result = await skill.execute(query="Python async best practices", limit=5)
    for item in result.results:
        print(f"{item['title']}: {item['url']}")
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode

# httpx is imported lazily inside methods so the module can import without optional deps.

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15.0
MAX_RESULTS = 20
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


@dataclass
class SearchResult:
    """Result of a web search operation."""

    success: bool
    query: str
    engine: str = ""
    results: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSearchSkill:
    """
    Multi-engine web search skill.

    Engines (in priority order):
    1. DuckDuckGo HTML — no API key, always available
    2. Brave Search API — requires BRAVE_SEARCH_API_KEY
    3. SearXNG — requires SEARXNG_URL (self-hosted)

    Falls back through engines automatically.
    """

    name = "web_search"
    description = "Search the web using multiple engines"
    version = "1.0.0"

    def __init__(self, brave_api_key: str = "", searxng_url: str = ""):
        import os
        self.brave_api_key = brave_api_key or os.getenv("BRAVE_SEARCH_API_KEY", "")
        self.searxng_url = searxng_url or os.getenv("SEARXNG_URL", "")

    async def execute(
        self,
        query: str,
        limit: int = 10,
        engine: str = "auto",
        timeout: float = DEFAULT_TIMEOUT,
    ) -> SearchResult:
        """
        Search the web.

        Args:
            query: Search query string
            limit: Maximum number of results (1-20)
            engine: Engine to use: "auto", "duckduckgo", "brave", "searxng"
            timeout: Request timeout in seconds

        Returns:
            SearchResult with list of {title, url, snippet} dicts
        """
        start = time.monotonic()
        limit = min(max(limit, 1), MAX_RESULTS)

        if not query or not query.strip():
            return SearchResult(success=False, query=query, error="Empty query")

        engines_to_try = self._resolve_engines(engine)
        last_error = ""

        for eng in engines_to_try:
            try:
                if eng == "brave" and self.brave_api_key:
                    result = await self._search_brave(query, limit, timeout)
                elif eng == "searxng" and self.searxng_url:
                    result = await self._search_searxng(query, limit, timeout)
                elif eng == "duckduckgo":
                    result = await self._search_duckduckgo(query, limit, timeout)
                else:
                    continue

                if result.success and result.results:
                    result.execution_time_ms = int((time.monotonic() - start) * 1000)
                    return result
                last_error = result.error or "No results"
            except Exception as e:
                last_error = f"{eng}: {e}"
                logger.warning("Search engine %s failed: %s", eng, e)

        return SearchResult(
            success=False, query=query, error=f"All engines failed. Last: {last_error}",
            execution_time_ms=int((time.monotonic() - start) * 1000),
        )

    def _resolve_engines(self, engine: str) -> list[str]:
        """Resolve engine preference to ordered list."""
        if engine != "auto":
            return [engine, "duckduckgo"]
        # Auto: try best available first
        engines = []
        if self.brave_api_key:
            engines.append("brave")
        if self.searxng_url:
            engines.append("searxng")
        engines.append("duckduckgo")
        return engines

    # ── DuckDuckGo (HTML scraping, no API key) ──────────────────────

    async def _search_duckduckgo(
        self, query: str, limit: int, timeout: float
    ) -> SearchResult:
        """Search via DuckDuckGo HTML (no API key required)."""
        import httpx

        url = "https://html.duckduckgo.com/html/"

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(timeout),
        ) as client:
            response = await client.post(
                url,
                data={"q": query, "b": ""},
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

        if response.status_code != 200:
            return SearchResult(
                success=False, query=query, engine="duckduckgo",
                error=f"HTTP {response.status_code}",
            )

        results = self._parse_ddg_html(response.text, limit)
        return SearchResult(
            success=bool(results), query=query, engine="duckduckgo",
            results=results,
            error=None if results else "No results parsed",
        )

    def _parse_ddg_html(self, html: str, limit: int) -> list[dict[str, str]]:
        """Parse DuckDuckGo HTML results page."""
        results = []

        # Find result blocks: <a class="result__a" href="...">title</a>
        # and <a class="result__snippet">snippet</a>
        blocks = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL,
        )

        for href, title_html, snippet_html in blocks[:limit]:
            # Clean HTML from title and snippet
            title = re.sub(r"<[^>]+>", "", title_html).strip()
            snippet = re.sub(r"<[^>]+>", "", snippet_html).strip()

            # DDG wraps URLs in a redirect — extract actual URL
            if "uddg=" in href:
                from urllib.parse import parse_qs, urlparse as _urlparse
                parsed = _urlparse(href)
                qs = parse_qs(parsed.query)
                actual_url = qs.get("uddg", [href])[0]
            else:
                actual_url = href

            if title and actual_url:
                results.append({
                    "title": title,
                    "url": actual_url,
                    "snippet": snippet,
                })

        return results

    # ── Brave Search API ────────────────────────────────────────────

    async def _search_brave(
        self, query: str, limit: int, timeout: float
    ) -> SearchResult:
        """Search via Brave Search API (requires API key)."""
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": limit},
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self.brave_api_key,
                },
            )

        if response.status_code != 200:
            return SearchResult(
                success=False, query=query, engine="brave",
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )

        data = response.json()
        results = []
        for item in data.get("web", {}).get("results", [])[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
            })

        return SearchResult(
            success=bool(results), query=query, engine="brave",
            results=results,
            error=None if results else "No results",
        )

    # ── SearXNG (self-hosted) ───────────────────────────────────────

    async def _search_searxng(
        self, query: str, limit: int, timeout: float
    ) -> SearchResult:
        """Search via SearXNG instance (self-hosted, no API key)."""
        import httpx

        url = f"{self.searxng_url.rstrip('/')}/search"

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.get(
                url,
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general",
                },
            )

        if response.status_code != 200:
            return SearchResult(
                success=False, query=query, engine="searxng",
                error=f"HTTP {response.status_code}",
            )

        data = response.json()
        results = []
        for item in data.get("results", [])[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            })

        return SearchResult(
            success=bool(results), query=query, engine="searxng",
            results=results,
            error=None if results else "No results",
        )
