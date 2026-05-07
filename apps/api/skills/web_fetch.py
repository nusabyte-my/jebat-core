"""
JEBAT WebFetch Skill

Fetches content from URLs and converts HTML to clean readable text.

Usage:
    from apps.api.skills.web_fetch import WebFetchSkill

    skill = WebFetchSkill()
    result = await skill.execute(url="https://example.com")
    print(result.data["text"])
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# httpx is imported lazily in execute() so the package can import without optional deps.

logger = logging.getLogger(__name__)

# Max content size to process (5MB)
MAX_CONTENT_BYTES = 5 * 1024 * 1024
# Max text output length (chars)
MAX_TEXT_LENGTH = 50_000
# Request timeout
DEFAULT_TIMEOUT = 30.0

# Common user agent
USER_AGENT = "Mozilla/5.0 (compatible; JEBATBot/2.0; +https://jebat.online)"


@dataclass
class FetchResult:
    """Result of a web fetch operation."""

    success: bool
    url: str
    text: str = ""
    title: str = ""
    status_code: int = 0
    content_type: str = ""
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


def _html_to_text(html: str) -> tuple[str, str]:
    """
    Convert HTML to readable plain text. Returns (text, title).
    No external dependencies — pure regex-based extraction.
    """
    # Extract title
    title = ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()

    # Remove script, style, nav, footer, header tags and their content
    for tag in ("script", "style", "nav", "footer", "header", "aside", "noscript", "svg"):
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", html, flags=re.IGNORECASE | re.DOTALL)

    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)

    # Convert block elements to newlines
    for tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "blockquote", "article", "section"):
        html = re.sub(rf"</?{tag}[^>]*>", "\n", html, flags=re.IGNORECASE)

    # Convert list items
    html = re.sub(r"<li[^>]*>", "\n• ", html, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", html)

    # Decode common HTML entities
    entities = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
        "&apos;": "'", "&nbsp;": " ", "&mdash;": "—", "&ndash;": "–",
        "&hellip;": "…", "&copy;": "©", "&reg;": "®",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    # Numeric entities
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text, title


class WebFetchSkill:
    """
    Fetches web pages and extracts readable text content.

    Supports:
    - HTML pages → clean text extraction
    - Plain text / JSON / XML → raw content
    - Configurable timeout and max size
    - Automatic redirect following
    - HTTP/HTTPS URL validation
    """

    name = "web_fetch"
    description = "Fetch content from a URL and extract readable text"
    version = "1.0.0"

    async def execute(
        self,
        url: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_length: int = MAX_TEXT_LENGTH,
        include_metadata: bool = False,
    ) -> FetchResult:
        """
        Fetch a URL and return extracted text content.

        Args:
            url: The URL to fetch (must be http:// or https://)
            timeout: Request timeout in seconds
            max_length: Maximum text output length
            include_metadata: Include response headers in metadata

        Returns:
            FetchResult with extracted text
        """
        start = time.monotonic()

        # Validate URL (no deps needed)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return FetchResult(
                success=False, url=url,
                error=f"Invalid URL scheme: {parsed.scheme}. Only http/https supported.",
            )
        if not parsed.netloc:
            return FetchResult(success=False, url=url, error="Invalid URL: no host")

        # Upgrade http to https
        if parsed.scheme == "http":
            url = "https" + url[4:]

        import httpx  # lazy import — only needed for actual HTTP calls

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(timeout),
                limits=httpx.Limits(max_connections=5),
            ) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )

            elapsed_ms = int((time.monotonic() - start) * 1000)
            content_type = response.headers.get("content-type", "")

            # Check content size
            content = response.text
            if len(content.encode("utf-8", errors="ignore")) > MAX_CONTENT_BYTES:
                content = content[:MAX_CONTENT_BYTES]

            # Extract text based on content type
            if "html" in content_type:
                text, title = _html_to_text(content)
            else:
                text = content
                title = ""

            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length] + "\n\n[... truncated]"

            metadata = {"content_length": len(content)}
            if include_metadata:
                metadata["headers"] = dict(response.headers)
                metadata["final_url"] = str(response.url)

            return FetchResult(
                success=True,
                url=url,
                text=text,
                title=title,
                status_code=response.status_code,
                content_type=content_type,
                execution_time_ms=elapsed_ms,
                metadata=metadata,
            )

        except httpx.TimeoutException:
            return FetchResult(
                success=False, url=url, error=f"Request timed out after {timeout}s",
                execution_time_ms=int((time.monotonic() - start) * 1000),
            )
        except httpx.ConnectError as e:
            return FetchResult(
                success=False, url=url, error=f"Connection failed: {e}",
                execution_time_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            logger.error("WebFetch error for %s: %s", url, e)
            return FetchResult(
                success=False, url=url, error=f"Fetch failed: {type(e).__name__}: {e}",
                execution_time_ms=int((time.monotonic() - start) * 1000),
            )
