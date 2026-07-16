"""JEBAT Web Search — multi-source web search and page extraction.

Provides search_web (SearXNG / Google / Bing API / DuckDuckGo HTML)
and web_extract (httpx + HTML-to-text) tools for the JEBAT CLI agent.
Uses the tool registry decorator pattern from jebat.tools.
"""

from __future__ import annotations

import os
import re
import json
from typing import Any
from html.parser import HTMLParser

import httpx

from jebat.tools import register_tool
from jebat.config import load_config
from jebat.features.security.outbound import OutboundURLBlocked, get_validated
from jebat.features.security.trust_boundary import mark_untrusted_content

# ── Constants ─────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 30
DEFAULT_LIMIT = 10
DEFAULT_SEARXNG_URL = "http://localhost:8888/search"


# ── Config helpers ───────────────────────────────────────────────────────

def _get_searxng_url() -> str:
    """Read SearXNG base URL from config, with env override."""
    env_val = os.environ.get("JEBAT_SEARXNG_URL")
    if env_val:
        return env_val.rstrip("/")
    cfg = load_config()
    return cfg.get("search.searxng_url", DEFAULT_SEARXNG_URL).rstrip("/")


def _get_google_api_key() -> str | None:
    """Read Google Custom Search API key from config / env."""
    return os.environ.get("JEBAT_GOOGLE_API_KEY") or load_config().get("search.google_api_key")


def _get_google_cx() -> str | None:
    """Read Google Custom Search CX (site-restricted) from config / env."""
    return os.environ.get("JEBAT_GOOGLE_CX") or load_config().get("search.google_cx")


def _get_bing_api_key() -> str | None:
    """Read Bing Search API key from config / env."""
    return os.environ.get("JEBAT_BING_API_KEY") or load_config().get("search.bing_api_key")


# ── SearXNG search ───────────────────────────────────────────────────────

async def _search_searxng(query: str, limit: int) -> list[dict[str, str]]:
    """Search via a local/self-hosted SearXNG instance (JSON API)."""
    base = _get_searxng_url()
    url = f"{base}/search"
    params = {
        "q": query,
        "format": "json",
        "pageno": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url, params=params, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()

        results: list[dict[str, str]] = []
        for item in data.get("results", [])[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            })
        return results
    except Exception as exc:
        return [{"error": f"SearXNG search failed: {exc}"}]


# ── Google Custom Search API ─────────────────────────────────────────────

async def _search_google(query: str, limit: int) -> list[dict[str, str]]:
    """Search via Google Custom Search JSON API (requires API key + CX)."""
    api_key = _get_google_api_key()
    cx = _get_google_cx()
    if not api_key or not cx:
        return [{"error": "Google API key or CX not configured"}]

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(limit, 10),
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results: list[dict[str, str]] = []
        for item in data.get("items", [])[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        return results
    except Exception as exc:
        return [{"error": f"Google search failed: {exc}"}]


# ── Bing Search API ──────────────────────────────────────────────────────

async def _search_bing(query: str, limit: int) -> list[dict[str, str]]:
    """Search via Bing Web Search API (requires subscription key)."""
    api_key = _get_bing_api_key()
    if not api_key:
        return [{"error": "Bing API key not configured"}]

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": min(limit, 50),
        "responseFilter": "Webpages",
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        results: list[dict[str, str]] = []
        for page in data.get("webPages", {}).get("value", [])[:limit]:
            results.append({
                "title": page.get("name", ""),
                "url": page.get("url", ""),
                "snippet": page.get("snippet", ""),
            })
        return results
    except Exception as exc:
        return [{"error": f"Bing search failed: {exc}"}]


# ── DuckDuckGo HTML scrape ──────────────────────────────────────────────

class _DDGResultParser(HTMLParser):
    """Minimal HTML parser to extract search results from DuckDuckGo HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_result = False
        self._in_title = False
        self._in_snippet = False
        self._current_url = ""
        self._current_title = ""
        self._current_snippet = ""
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "div" and attrs_dict.get("class", "").startswith("result"):
            self._in_result = True
            self._current_title = ""
            self._current_snippet = ""
            self._current_url = ""
        if self._in_result and tag == "a" and "result__a" in attrs_dict.get("class", ""):
            self._in_title = True
            url = attrs_dict.get("href", "")
            # DDG uses redirect URLs; strip the wrapper if present
            if url.startswith("//duckduckgo.com/l/?uddg="):
                from urllib.parse import unquote
                # Extract the actual URL from DDG redirect parameter
                redirect_part = url.split("uddg=", 1)
                if len(redirect_part) > 1:
                    actual_url = unquote(redirect_part[1].split("&", 1)[0])
                    self._current_url = actual_url
            elif url:
                self._current_url = url
        if self._in_result and tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
            self._in_snippet = True
        self._tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()
        if tag == "a" and self._in_title:
            self._in_title = False
        if tag == "a" and self._in_snippet:
            self._in_snippet = False
        if tag == "div" and self._in_result:
            if self._current_title or self._current_url:
                self.results.append({
                    "title": self._current_title.strip(),
                    "url": self._current_url.strip(),
                    "snippet": self._current_snippet.strip(),
                })
            self._in_result = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._current_title += data
        if self._in_snippet:
            self._current_snippet += data


async def _search_duckduckgo(query: str, limit: int) -> list[dict[str, str]]:
    """Search via DuckDuckGo HTML endpoint (no API key needed)."""
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query, "kl": "wt-wt"}  # worldwide, no region bias
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.post(url, data=params, headers=headers)
            resp.raise_for_status()
            html_text = resp.text

        parser = _DDGResultParser()
        parser.feed(html_text)
        results = parser.results[:limit]
        return results
    except Exception as exc:
        return [{"error": f"DuckDuckGo search failed: {exc}"}]


# ── Fallback chain ───────────────────────────────────────────────────────

def _is_error_list(results: list[dict[str, str]]) -> bool:
    """Check if a result list consists only of error entries."""
    if not results:
        return True
    return all("error" in r for r in results)


async def _search_with_fallback(query: str, limit: int) -> list[dict[str, str]]:
    """Try SearXNG → Google → Bing → DuckDuckGo in order, return first success."""
    # 1. SearXNG (primary, self-hosted)
    results = await _search_searxng(query, limit)
    if not _is_error_list(results):
        return results

    # 2. Google API (if keys available)
    if _get_google_api_key() and _get_google_cx():
        results = await _search_google(query, limit)
        if not _is_error_list(results):
            return results

    # 3. Bing API (if key available)
    if _get_bing_api_key():
        results = await _search_bing(query, limit)
        if not _is_error_list(results):
            return results

    # 4. DuckDuckGo HTML (always available, no key needed)
    results = await _search_duckduckgo(query, limit)
    if not _is_error_list(results):
        return results

    # All sources failed — collect error messages
    return [{"error": f"All search sources failed for query: '{query}'"}]


# ── Tool: search_web ─────────────────────────────────────────────────────

@register_tool(
    "search_web",
    schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default 10)",
                "default": 10,
                "minimum": 1,
                "maximum": 50,
            },
        },
        "required": ["query"],
    },
    safety_tier="auto",
    timeout=30,
    max_output=50_000,
    description="Search the web using SearXNG (primary), Google/Bing API, or DuckDuckGo fallback. Returns title, url, and snippet for each result.",
)
async def search_web(query: str, limit: int = DEFAULT_LIMIT, engine: str | None = None) -> dict[str, Any]:
    """Search the web for a query, returning title/url/snippet results.
    
    engine: 'searxng', 'google', 'bing', 'duckduckgo', or None for fallback
    """
    results = await _search_with_fallback(query, limit)
    return {
        "query": query,
        "count": len(results),
        "results": results,
    }


# ── HTML-to-text extraction ──────────────────────────────────────────────

class _HTMLTextExtractor(HTMLParser):
    """Extract readable text from HTML, stripping tags and collapsing whitespace."""

    # Tags whose content should be suppressed entirely
    SUPPRESS_TAGS = {"script", "style", "noscript", "iframe", "svg", "head"}

    # Tags that act as block-level separators (insert newline)
    BLOCK_TAGS = {
        "p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "ul", "ol", "table", "tr", "td", "th", "section",
        "article", "header", "footer", "nav", "aside", "main",
        "blockquote", "pre", "hr", "dl", "dt", "dd",
    }

    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._suppress_depth = 0
        self._current_suppress_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SUPPRESS_TAGS and self._suppress_depth == 0:
            self._suppress_depth = 1
            self._current_suppress_tag = tag
        elif self._suppress_depth > 0:
            self._suppress_depth += 1

        if self._suppress_depth == 0:
            if tag in self.BLOCK_TAGS:
                self._text_parts.append("\n")
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self._text_parts.append("\n## ")

    def handle_endtag(self, tag: str) -> None:
        if self._suppress_depth > 0:
            self._suppress_depth -= 1
            if self._suppress_depth == 0:
                self._current_suppress_tag = None

        if self._suppress_depth == 0:
            if tag in self.BLOCK_TAGS:
                self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._suppress_depth == 0:
            self._text_parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._suppress_depth == 0:
            common = {
                "amp": "&", "lt": "<", "gt": ">", "quot": '"',
                "nbsp": " ", "mdash": "—", "ndash": "–",
                "copy": "©", "reg": "®",
            }
            self._text_parts.append(common.get(name, f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if self._suppress_depth == 0:
            try:
                if name.startswith("x"):
                    char = chr(int(name[1:], 16))
                else:
                    char = chr(int(name))
                self._text_parts.append(char)
            except (ValueError, OverflowError):
                self._text_parts.append(f"&#{name};")

    def get_text(self) -> str:
        """Return the extracted text with collapsed whitespace."""
        raw = "".join(self._text_parts)
        # Collapse multiple spaces (but preserve newlines)
        lines = raw.split("\n")
        cleaned = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
        # Remove consecutive blank lines
        text = "\n".join(cleaned)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _extract_main_content(text: str, max_chars: int = 100_000) -> str:
    """Try to identify the main content area of extracted text.

    Simple heuristic: find the longest contiguous block of non-trivial text
    (lines with >40 chars average), bounded by short/empty lines.
    Falls back to the full text if no clear main block is found.
    """
    if len(text) <= max_chars:
        return text

    lines = text.split("\n")
    # Find blocks of consecutive "long" lines
    best_start = 0
    best_end = len(lines)
    best_len = 0

    current_start: int | None = None
    current_len = 0

    for i, line in enumerate(lines):
        if len(line) > 40:
            if current_start is None:
                current_start = i
            current_len += len(line)
        else:
            if current_start is not None and current_len > best_len:
                best_start = current_start
                best_end = i
                best_len = current_len
            current_start = None
            current_len = 0

    # Check final block
    if current_start is not None and current_len > best_len:
        best_start = current_start
        best_end = len(lines)

    main_block = "\n".join(lines[best_start:best_end])
    if len(main_block) > max_chars:
        return main_block[:max_chars] + "\n... (truncated)"
    return main_block


# ── Tool: web_extract ────────────────────────────────────────────────────

@register_tool(
    "web_extract",
    schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL of the web page to extract content from",
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters of extracted text to return (default 100000)",
                "default": 100000,
                "minimum": 500,
                "maximum": 500_000,
            },
        },
        "required": ["url"],
    },
    safety_tier="auto",
    timeout=30,
    max_output=200_000,
    description="Extract plain text content from a web page URL. Returns title, url, and extracted text content.",
)
async def web_extract(url: str, max_chars: int = 100_000) -> dict[str, Any]:
    """Fetch a web page and extract its main text content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await get_validated(client, url, headers=headers)
            resp.raise_for_status()
            html_text = resp.text

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # Extract main text content
        extractor = _HTMLTextExtractor()
        extractor.feed(html_text)
        full_text = extractor.get_text()
        content = _extract_main_content(full_text, max_chars=max_chars)

        char_count = len(content)
        truncated = char_count >= max_chars

        return {
            "url": url,
            "title": title,
            "content": mark_untrusted_content(content, source=str(resp.url)),
            "char_count": char_count,
            "truncated": truncated,
        }
    except OutboundURLBlocked as exc:
        return {"error": f"Blocked unsafe URL: {exc}", "url": url}
    except httpx.TimeoutException:
        return {"error": f"Timeout fetching {url}", "url": url}
    except httpx.HTTPStatusError as exc:
        return {
            "error": f"HTTP {exc.response.status_code} for {url}",
            "url": url,
            "status_code": exc.response.status_code,
        }
    except Exception as exc:
        return {"error": f"Failed to extract content from {url}: {exc}", "url": url}
