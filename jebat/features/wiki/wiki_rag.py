"""JEBAT Wiki RAG — inject wiki pages into agent context.

Extracts keywords from user messages, searches the wiki via FTS5,
and injects the most relevant pages into the system prompt before
each agent iteration.

Usage:
    from jebat.features.wiki.wiki_rag import inject_wiki_rag

    context = inject_wiki_rag("how does delegation work")
    if context:
        system_prompt = context + "\n" + system_prompt
"""

from __future__ import annotations

import re
import os
from pathlib import Path

from jebat.features.wiki.wiki_core import WikiStore

# Singleton store, lazily initialized
_store: WikiStore | None = None

# Common stopwords to filter out of keyword extraction
_STOPWORDS: set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "and", "or", "but", "if", "then", "else", "when", "where",
    "how", "what", "why", "who", "which", "this", "that", "it",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "do", "does", "did", "can", "will", "would", "could", "should",
    "has", "have", "had", "not", "no", "yes", "so", "just",
    "its", "im", "ive", "you", "your", "we", "our", "they", "their",
    "me", "my", "i", "us", "its",
}


def _get_store() -> WikiStore:
    """Get or create the singleton wiki store."""
    global _store
    if _store is None:
        wiki_dir = os.environ.get(
            "JEBAT_WIKI_DIR",
            str(Path.home() / ".jebat" / "wiki"),
        )
        _store = WikiStore(Path(wiki_dir))
    return _store


def _extract_keywords(text: str, max_keywords: int = 8) -> list[str]:
    """Extract keyword phrases from user text for wiki search.

    Strategy:
    1. Extract multi-word phrases with $VAR, --flags, filepaths
    2. Pull out CamelCase and snake_case identifiers
    3. Fall back to individual significant words (non-stopwords, 3+ chars)
    """
    keywords: list[str] = []

    # 1. Extract technical identifiers (CamelCase, snake_case, $VAR, --flags)
    technical = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text)  # CamelCase
    technical += re.findall(r'\b([a-z]+(?:_[a-z]+)+)\b', text)           # snake_case
    technical += re.findall(r'(\$\w+)', text)                            # $VAR
    technical += re.findall(r'(--[\w-]+)', text)                         # --flags
    keywords.extend(t.lower() for t in technical)

    # 2. Extract quoted phrases
    quoted = re.findall(r'"([^"]+)"', text)
    quoted += re.findall(r"'([^']+)'", text)
    keywords.extend(q.lower() for q in quoted)

    # 3. Extract individual significant words (3+ chars, non-stopwords)
    words = re.findall(r'\b([a-zA-Z]{3,})\b', text.lower())
    significant = [w for w in words if w not in _STOPWORDS]
    keywords.extend(significant)

    # Deduplicate while preserving order, limit to max_keywords
    seen: set[str] = set()
    result: list[str] = []
    for kw in keywords:
        if kw not in seen and kw.strip():
            seen.add(kw)
            result.append(kw)
            if len(result) >= max_keywords:
                break

    return result


def search_wiki(query: str, top_k: int = 3) -> list[dict]:
    """Search wiki pages and return raw match dicts with snippets."""
    store = _get_store()
    stats = store.get_stats()
    if stats.get("page_count", 0) == 0:
        return []

    # First try: search each keyword individually, merge results
    keywords = _extract_keywords(query)
    all_matches: list[dict] = []
    seen_titles: set[str] = set()

    for kw in keywords[:5]:  # Search with top 5 keywords
        result = store.search(kw, top_k=min(top_k, 5))
        for m in result.get("matches", []):
            if m["title"] not in seen_titles:
                seen_titles.add(m["title"])
                all_matches.append(m)

    # Second try: search the full query as a phrase
    if not all_matches:
        result = store.search(query, top_k=top_k)
        all_matches = result.get("matches", [])

    return all_matches[:top_k]


def inject_wiki_rag(user_message: str, max_pages: int = 3) -> str:
    """Build a wiki context injection string for the agent system prompt.

    Args:
        user_message: The user's latest message to extract keywords from.
        max_pages: Maximum number of wiki pages to inject.

    Returns:
        A formatted string to prepend to the system prompt, or empty string
        if no relevant wiki pages were found.
    """
    matches = search_wiki(user_message, top_k=max_pages)
    if not matches:
        return ""

    lines = [
        "# Wiki Knowledge Base (auto-loaded — relevant pages)",
        "",
    ]

    for i, m in enumerate(matches, 1):
        title = m["title"]
        # Strip HTML tags from FTS5 snippet
        snippet = re.sub(r'<[^>]+>', '', m.get("snippet", "")).strip()

        # Also fetch the full page content (first 500 chars for context)
        page = _get_store().read_page(title)
        content = page.get("content", "")
        if content:
            # Truncate to reasonable context window budget (~500 chars)
            preview = content[:500]
            if len(content) > 500:
                preview += "..."

            lines.append(f"### Wiki Page {i}: {title}")
            if snippet:
                lines.append(f"  Relevance: ...{snippet}...")
            lines.append(f"  Content: {preview}")
            lines.append("")

    lines.append("Use this wiki context when relevant. If irrelevant, ignore it.")
    lines.append("")

    return "\n".join(lines)