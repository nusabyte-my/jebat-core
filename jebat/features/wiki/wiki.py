"""JEBAT Wiki / Knowledge Base — persistent markdown wiki with hybrid search.

Provides CRUD operations for wiki pages stored as markdown with YAML-style
frontmatter, plus full-text (ripgrep) and semantic (sentence-transformers)
search with rank-fusion.  Includes a WikiRAG helper for prompt injection.
"""

from __future__ import annotations

import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jebat.tools import register_tool

# ── Paths ────────────────────────────────────────────────────────────────────

WIKI_DIR = Path.home() / ".jebat" / "wiki"
PAGES_DIR = WIKI_DIR / "pages"
INDEX_DIR = WIKI_DIR / "index"


def _ensure_dirs() -> None:
    """Create wiki directories if they don't exist."""
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _slugify(title: str) -> str:
    """Convert a title to a filesystem-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _page_path(title_or_slug: str) -> Path:
    """Resolve a title or slug to its page path."""
    slug = _slugify(title_or_slug)
    return PAGES_DIR / f"{slug}.md"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse our simple header-based frontmatter from markdown text.

    Returns (metadata_dict, body_content).
    """
    meta: dict[str, Any] = {}
    lines = text.split("\n")
    body_start = 0

    # First line: # Wiki: Title
    if lines and lines[0].startswith("# Wiki:"):
        meta["title"] = lines[0].replace("# Wiki:", "").strip()
        body_start = 1

    # Subsequent metadata lines: **Key**: value
    for i in range(body_start, len(lines)):
        m = re.match(r"^\*\*(\w+)\*\*:\s*(.+)$", lines[i])
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key == "tags":
                meta["tags"] = [t.strip() for t in val.split(",") if t.strip()]
            else:
                meta[key] = val
            body_start = i + 1
        elif lines[i].strip() == "":
            body_start = i + 1
        else:
            break

    body = "\n".join(lines[body_start:]).strip()
    return meta, body


def _build_page(title: str, content: str, tags: list[str] | None = None,
                source: str | None = None, created: str | None = None,
                updated: str | None = None) -> str:
    """Build a full wiki page string with header metadata."""
    tags_str = ", ".join(tags) if tags else ""
    created = created or _today()
    updated = updated or _today()
    source = source or ""

    header = f"# Wiki: {title}\n"
    if tags_str:
        header += f"**Tags**: {tags_str}\n"
    header += f"**Created**: {created}\n"
    header += f"**Updated**: {updated}\n"
    if source:
        header += f"**Source**: {source}\n"
    header += "\n"
    return header + content


def _read_page_raw(path: Path) -> str | None:
    """Read raw page content or return None if missing."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _all_pages() -> list[Path]:
    """Return sorted list of all wiki page paths."""
    _ensure_dirs()
    return sorted(PAGES_DIR.glob("*.md"))


# ── Embedding helpers (lazy-loaded) ─────────────────────────────────────────

_model = None
_tokenizer = None


def _get_model():
    """Lazy-load sentence-transformers model."""
    global _model, _tokenizer
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is required for semantic search. "
                "Install with: pip install sentence-transformers"
            )
    return _model


def _embed_texts(texts: list[str]):
    """Encode a list of texts into numpy embeddings."""
    import numpy as np
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(embeddings)


def _cosine_similarity(query_emb, doc_embs):
    """Compute cosine similarity between query embedding and document embeddings."""
    import numpy as np
    # Already normalized, so dot product = cosine similarity
    return np.dot(doc_embs, query_emb)


def _embedding_cache_path(slug: str) -> Path:
    return INDEX_DIR / f"{slug}.npy"


def _update_embedding(slug: str, text: str) -> None:
    """Compute and cache embedding for a single page."""
    import numpy as np
    emb = _embed_texts([text])
    np.save(str(_embedding_cache_path(slug)), emb[0])


def _load_all_embeddings() -> tuple[list[str], Any]:
    """Load all cached embeddings. Returns (slugs, matrix)."""
    import numpy as np
    slugs: list[str] = []
    vecs: list[Any] = []
    for p in sorted(INDEX_DIR.glob("*.npy")):
        slug = p.stem
        slugs.append(slug)
        vecs.append(np.load(str(p)))
    if not vecs:
        return [], np.array([])
    return slugs, np.vstack(vecs)


def _rebuild_index() -> None:
    """Rebuild the entire embedding index from current pages."""
    _ensure_dirs()
    pages = _all_pages()
    if not pages:
        return
    slugs: list[str] = []
    texts: list[str] = []
    for p in pages:
        raw = _read_page_raw(p)
        if raw:
            slugs.append(p.stem)
            texts.append(raw)
    if texts:
        embs = _embed_texts(texts)
        import numpy as np
        for slug, emb in zip(slugs, embs):
            np.save(str(_embedding_cache_path(slug)), emb)


# ── Full-text search via ripgrep/grep ────────────────────────────────────────

def _fts_search(query: str) -> list[tuple[str, float]]:
    """Full-text search using grep -rli over wiki pages.

    Returns list of (slug, score) tuples. Score is based on match count.
    """
    _ensure_dirs()
    results: list[tuple[str, float]] = []

    # Try ripgrep first, fall back to grep
    rg_cmd = ["rg", "-li", "--glob", "*.md", query, str(PAGES_DIR)]
    grep_cmd = ["grep", "-rli", query, str(PAGES_DIR)]

    matched_files: list[str] = []
    for cmd in [rg_cmd, grep_cmd]:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if proc.returncode == 0 and proc.stdout.strip():
                matched_files = proc.stdout.strip().split("\n")
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # Score by counting occurrences
    for fpath in matched_files:
        fpath = fpath.strip()
        if not fpath:
            continue
        p = Path(fpath)
        slug = p.stem
        try:
            content = p.read_text(encoding="utf-8", errors="replace").lower()
            count = content.count(query.lower())
            score = min(count / 5.0, 1.0)  # Normalize: 5+ matches = 1.0
            results.append((slug, max(score, 0.1)))
        except Exception:
            results.append((slug, 0.1))

    return results


def _semantic_search(query: str, top_k: int = 10) -> list[tuple[str, float]]:
    """Semantic search using sentence-transformers embeddings."""
    import numpy as np
    _ensure_dirs()

    # Check if index exists; rebuild if empty
    npy_files = list(INDEX_DIR.glob("*.npy"))
    if not npy_files:
        _rebuild_index()
        npy_files = list(INDEX_DIR.glob("*.npy"))
        if not npy_files:
            return []

    slugs, doc_matrix = _load_all_embeddings()
    if len(slugs) == 0:
        return []

    query_emb = _embed_texts([query])[0]
    scores = _cosine_similarity(query_emb, doc_matrix)

    # Get top_k indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        s = float(scores[idx])
        if s > 0.0:
            results.append((slugs[idx], s))
    return results


def _hybrid_search(query: str, top_k: int = 10) -> list[tuple[str, float]]:
    """Combine FTS and semantic search with Reciprocal Rank Fusion."""
    fts_results = _fts_search(query)
    sem_results = _semantic_search(query, top_k=top_k * 2)

    # RRF scoring
    rrf_scores: dict[str, float] = {}
    k = 60  # RRF constant

    for rank, (slug, _) in enumerate(fts_results):
        rrf_scores[slug] = rrf_scores.get(slug, 0.0) + 1.0 / (k + rank + 1)

    for rank, (slug, _) in enumerate(sem_results):
        rrf_scores[slug] = rrf_scores.get(slug, 0.0) + 1.0 / (k + rank + 1)

    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return ranked


# ── Tool: wiki_create ────────────────────────────────────────────────────────

@register_tool(
    "wiki_create",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title"},
            "content": {"type": "string", "description": "Markdown content"},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of tags",
            },
        },
        "required": ["title", "content"],
    },
    safety_tier="auto",
    timeout=30,
    description="Create a new wiki page with markdown content and optional tags.",
)
async def wiki_create(title: str, content: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Create a new wiki page."""
    _ensure_dirs()
    slug = _slugify(title)
    path = PAGES_DIR / f"{slug}.md"

    if path.exists():
        return {"error": f"Page already exists: {title}", "slug": slug}

    page_text = _build_page(title, content, tags=tags)
    path.write_text(page_text, encoding="utf-8")

    # Update embedding index
    try:
        _update_embedding(slug, page_text)
    except Exception:
        pass  # Non-critical; index can be rebuilt later

    return {"status": "created", "slug": slug, "path": str(path), "title": title}


# ── Tool: wiki_read ──────────────────────────────────────────────────────────

@register_tool(
    "wiki_read",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title or slug"},
        },
        "required": ["title"],
    },
    safety_tier="auto",
    timeout=10,
    description="Read a wiki page by title or slug.",
)
async def wiki_read(title: str) -> dict[str, Any]:
    """Read a wiki page."""
    _ensure_dirs()
    path = _page_path(title)

    raw = _read_page_raw(path)
    if raw is None:
        # Try fuzzy match
        slug = _slugify(title)
        candidates = [p for p in _all_pages() if slug in p.stem]
        if len(candidates) == 1:
            path = candidates[0]
            raw = _read_page_raw(path)
        elif len(candidates) > 1:
            return {
                "error": f"Ambiguous title '{title}'. Matches: {[p.stem for p in candidates]}"
            }
        else:
            return {"error": f"Page not found: {title}"}

    meta, body = _parse_frontmatter(raw)
    return {
        "title": meta.get("title", title),
        "slug": path.stem,
        "tags": meta.get("tags", []),
        "created": meta.get("created", ""),
        "updated": meta.get("updated", ""),
        "source": meta.get("source", ""),
        "content": body,
        "raw": raw,
    }


# ── Tool: wiki_edit ──────────────────────────────────────────────────────────

@register_tool(
    "wiki_edit",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title or slug"},
            "content": {"type": "string", "description": "New markdown content"},
        },
        "required": ["title", "content"],
    },
    safety_tier="auto",
    timeout=30,
    description="Edit an existing wiki page, preserving metadata and updating timestamp.",
)
async def wiki_edit(title: str, content: str) -> dict[str, Any]:
    """Edit an existing wiki page."""
    _ensure_dirs()
    path = _page_path(title)

    raw = _read_page_raw(path)
    if raw is None:
        return {"error": f"Page not found: {title}. Use wiki_create instead."}

    meta, _old_body = _parse_frontmatter(raw)
    page_title = meta.get("title", title)
    tags = meta.get("tags", [])
    created = meta.get("created", _today())
    source = meta.get("source", "")

    page_text = _build_page(page_title, content, tags=tags,
                            source=source, created=created, updated=_today())
    path.write_text(page_text, encoding="utf-8")

    # Update embedding
    try:
        _update_embedding(path.stem, page_text)
    except Exception:
        pass

    return {"status": "updated", "slug": path.stem, "title": page_title, "updated": _today()}


# ── Tool: wiki_delete ────────────────────────────────────────────────────────

@register_tool(
    "wiki_delete",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title or slug to delete"},
        },
        "required": ["title"],
    },
    safety_tier="confirm",
    timeout=10,
    description="Delete a wiki page.",
)
async def wiki_delete(title: str) -> dict[str, Any]:
    """Delete a wiki page."""
    _ensure_dirs()
    path = _page_path(title)

    if not path.exists():
        return {"error": f"Page not found: {title}"}

    slug = path.stem
    path.unlink()

    # Remove cached embedding
    emb_path = _embedding_cache_path(slug)
    if emb_path.exists():
        emb_path.unlink()

    return {"status": "deleted", "slug": slug, "title": title}


# ── Tool: wiki_list ──────────────────────────────────────────────────────────

@register_tool(
    "wiki_list",
    schema={
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by tags (AND logic)",
            },
            "limit": {"type": "integer", "default": 50, "description": "Max results"},
        },
    },
    safety_tier="auto",
    timeout=15,
    description="List wiki pages, optionally filtered by tags.",
)
async def wiki_list(tags: list[str] | None = None, limit: int = 50) -> dict[str, Any]:
    """List wiki pages."""
    _ensure_dirs()
    pages = _all_pages()
    results: list[dict[str, Any]] = []

    for p in pages:
        raw = _read_page_raw(p)
        if raw is None:
            continue
        meta, _ = _parse_frontmatter(raw)
        page_tags = meta.get("tags", [])

        # Filter by tags (AND logic)
        if tags:
            if not all(t in page_tags for t in tags):
                continue

        results.append({
            "slug": p.stem,
            "title": meta.get("title", p.stem),
            "tags": page_tags,
            "created": meta.get("created", ""),
            "updated": meta.get("updated", ""),
        })

        if len(results) >= limit:
            break

    return {"count": len(results), "pages": results}


# ── Tool: wiki_search ────────────────────────────────────────────────────────

@register_tool(
    "wiki_search",
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "mode": {
                "type": "string",
                "enum": ["fulltext", "semantic", "hybrid"],
                "default": "hybrid",
                "description": "Search mode",
            },
            "top_k": {"type": "integer", "default": 10, "description": "Max results"},
        },
        "required": ["query"],
    },
    safety_tier="auto",
    timeout=60,
    description="Search wiki pages using fulltext, semantic, or hybrid mode.",
)
async def wiki_search(query: str, mode: str = "hybrid", top_k: int = 10) -> dict[str, Any]:
    """Search wiki pages."""
    _ensure_dirs()

    if mode == "fulltext":
        raw_results = _fts_search(query)
    elif mode == "semantic":
        raw_results = _semantic_search(query, top_k=top_k)
    else:  # hybrid
        raw_results = _hybrid_search(query, top_k=top_k)

    results: list[dict[str, Any]] = []
    for slug, score in raw_results[:top_k]:
        path = PAGES_DIR / f"{slug}.md"
        raw = _read_page_raw(path)
        if raw is None:
            continue
        meta, body = _parse_frontmatter(raw)
        # Truncate body for search results
        preview = body[:300] + ("..." if len(body) > 300 else "")
        results.append({
            "slug": slug,
            "title": meta.get("title", slug),
            "score": round(score, 4),
            "tags": meta.get("tags", []),
            "preview": preview,
        })

    return {"query": query, "mode": mode, "count": len(results), "results": results}


# ── Tool: wiki_auto_save ─────────────────────────────────────────────────────

@register_tool(
    "wiki_auto_save",
    schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Content to auto-save as a wiki page"},
        },
        "required": ["content"],
    },
    safety_tier="auto",
    timeout=30,
    description="Auto-create a wiki page from conversation context.",
)
async def wiki_auto_save(content: str) -> dict[str, Any]:
    """Auto-create a wiki page from conversation context."""
    _ensure_dirs()

    # Generate a title from the first line or first 60 chars
    first_line = content.strip().split("\n")[0].strip("# ").strip()
    if not first_line:
        first_line = "Auto-saved Note"
    title = first_line[:80]

    slug = _slugify(title)
    path = PAGES_DIR / f"{slug}.md"

    # If slug collision, append short uuid
    if path.exists():
        suffix = uuid.uuid4().hex[:6]
        slug = f"{slug}-{suffix}"
        title = f"{title} ({suffix})"
        path = PAGES_DIR / f"{slug}.md"

    session_id = os.environ.get("JEBAT_SESSION_ID", f"session_{uuid.uuid4().hex[:8]}")
    page_text = _build_page(title, content, tags=["auto-saved"], source=session_id)
    path.write_text(page_text, encoding="utf-8")

    try:
        _update_embedding(slug, page_text)
    except Exception:
        pass

    return {"status": "auto_saved", "slug": slug, "title": title, "path": str(path)}


# ── Tool: wiki_suggest ───────────────────────────────────────────────────────

@register_tool(
    "wiki_suggest",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=30,
    description="Scan recent pages and suggest new wiki pages from notable facts.",
)
async def wiki_suggest() -> dict[str, Any]:
    """Scan recent pages and suggest new pages from notable facts."""
    _ensure_dirs()
    pages = _all_pages()

    suggestions: list[dict[str, str]] = []
    seen_titles: set[str] = set()

    # Collect existing titles for dedup
    for p in pages:
        seen_titles.add(p.stem.lower())

    # Scan pages for potential new topics
    fact_patterns = [
        (r"(?:important|key|note):\s*(.+)", "Notable fact"),
        (r"(?:TODO|FIXME|HACK):\s*(.+)", "Action item"),
        (r"(?:see also|related):\s*(.+)", "Related topic"),
        (r"(?:definition|concept):\s*(.+)", "Concept definition"),
    ]

    for p in pages[-20:]:  # Only scan last 20 pages
        raw = _read_page_raw(p)
        if raw is None:
            continue
        meta, body = _parse_frontmatter(raw)

        for pattern, category in fact_patterns:
            for match in re.finditer(pattern, body, re.IGNORECASE):
                fact = match.group(1).strip()[:100]
                suggested_slug = _slugify(fact[:50])
                if suggested_slug and suggested_slug not in seen_titles:
                    suggestions.append({
                        "suggested_title": fact[:80],
                        "category": category,
                        "source_page": meta.get("title", p.stem),
                        "excerpt": fact,
                    })
                    seen_titles.add(suggested_slug)

    return {"suggestions_count": len(suggestions), "suggestions": suggestions[:20]}


# ── Tool: wiki_consolidate ───────────────────────────────────────────────────

@register_tool(
    "wiki_consolidate",
    schema={
        "type": "object",
        "properties": {
            "dry_run": {"type": "boolean", "default": True,
                        "description": "If true, only report duplicates without merging"},
        },
    },
    safety_tier="confirm",
    timeout=120,
    description="Find and merge similar or duplicate wiki pages.",
)
async def wiki_consolidate(dry_run: bool = True) -> dict[str, Any]:
    """Find and merge similar/duplicate wiki pages."""
    _ensure_dirs()
    pages = _all_pages()

    if len(pages) < 2:
        return {"status": "nothing_to_consolidate", "merged": 0}

    # Load all page contents for comparison
    page_data: list[tuple[Path, str, str]] = []
    for p in pages:
        raw = _read_page_raw(p)
        if raw:
            meta, body = _parse_frontmatter(raw)
            page_data.append((p, meta.get("title", p.stem), body))

    # Find near-duplicates using simple Jaccard similarity on word sets
    duplicates: list[tuple[str, str, float]] = []
    for i in range(len(page_data)):
        for j in range(i + 1, len(page_data)):
            _, title_a, body_a = page_data[i]
            _, title_b, body_b = page_data[j]

            words_a = set(body_a.lower().split())
            words_b = set(body_b.lower().split())

            if not words_a or not words_b:
                continue

            intersection = words_a & words_b
            union = words_a | words_b
            jaccard = len(intersection) / len(union) if union else 0.0

            if jaccard > 0.7:
                duplicates.append((title_a, title_b, round(jaccard, 3)))

    merged_count = 0
    merge_details: list[dict[str, Any]] = []

    if not dry_run:
        for title_a, title_b, sim in duplicates:
            path_a = _page_path(title_a)
            path_b = _page_path(title_b)

            raw_a = _read_page_raw(path_a)
            raw_b = _read_page_raw(path_b)
            if raw_a is None or raw_b is None:
                continue

            meta_a, body_a = _parse_frontmatter(raw_a)
            meta_b, body_b = _parse_frontmatter(raw_b)

            # Merge: keep A, append unique content from B
            combined_tags = list(set(meta_a.get("tags", []) + meta_b.get("tags", [])))
            combined_body = body_a
            if body_b.strip() and body_b.strip() != body_a.strip():
                combined_body += f"\n\n---\n\n*Merged from: {meta_b.get('title', title_b)}*\n\n{body_b}"

            merged_text = _build_page(
                meta_a.get("title", title_a),
                combined_body,
                tags=combined_tags,
                created=meta_a.get("created", _today()),
                updated=_today(),
                source=meta_a.get("source", ""),
            )
            path_a.write_text(merged_text, encoding="utf-8")
            path_b.unlink()

            # Update embedding
            try:
                _update_embedding(path_a.stem, merged_text)
                emb_b = _embedding_cache_path(_slugify(title_b))
                if emb_b.exists():
                    emb_b.unlink()
            except Exception:
                pass

            merged_count += 1
            merge_details.append({
                "kept": meta_a.get("title", title_a),
                "merged_in": meta_b.get("title", title_b),
                "similarity": sim,
            })

    return {
        "dry_run": dry_run,
        "duplicates_found": len(duplicates),
        "merged": merged_count,
        "details": merge_details if not dry_run else [
            {"page_a": a, "page_b": b, "similarity": s} for a, b, s in duplicates
        ],
    }


# ── Tool: wiki_stats ─────────────────────────────────────────────────────────

@register_tool(
    "wiki_stats",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    timeout=15,
    description="Get wiki statistics: page count, total tokens, freshness.",
)
async def wiki_stats() -> dict[str, Any]:
    """Get wiki statistics."""
    _ensure_dirs()
    pages = _all_pages()

    total_chars = 0
    total_tokens = 0
    all_tags: dict[str, int] = {}
    dates: list[str] = []
    oldest = None
    newest = None

    for p in pages:
        raw = _read_page_raw(p)
        if raw is None:
            continue
        meta, body = _parse_frontmatter(raw)

        total_chars += len(raw)
        # Rough token estimate: ~4 chars per token
        total_tokens += len(raw) // 4

        for tag in meta.get("tags", []):
            all_tags[tag] = all_tags.get(tag, 0) + 1

        updated = meta.get("updated", "")
        if updated:
            dates.append(updated)

    if dates:
        oldest = min(dates)
        newest = max(dates)

    top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "page_count": len(pages),
        "total_characters": total_chars,
        "estimated_tokens": total_tokens,
        "unique_tags": len(all_tags),
        "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
        "oldest_page": oldest,
        "newest_page": newest,
        "wiki_dir": str(WIKI_DIR),
    }


# ── WikiRAG Class ────────────────────────────────────────────────────────────

class WikiRAG:
    """Retrieval-Augmented Generation helper for the JEBAT wiki.

    Usage:
        rag = WikiRAG()
        pages = rag.retrieve("how does authentication work?", top_k=3)
        # Inject pages into your prompt context
    """

    def __init__(self, wiki_dir: Path | None = None):
        self.wiki_dir = wiki_dir or WIKI_DIR
        self.pages_dir = self.wiki_dir / "pages"
        self.index_dir = self.wiki_dir / "index"

    def retrieve(self, query: str, top_k: int = 3, mode: str = "hybrid") -> list[dict[str, Any]]:
        """Retrieve relevant wiki pages for a query.

        Args:
            query: The search query.
            top_k: Number of pages to return.
            mode: 'fulltext', 'semantic', or 'hybrid'.

        Returns:
            List of dicts with keys: title, slug, content, score, tags.
        """
        _ensure_dirs()

        if mode == "fulltext":
            raw_results = _fts_search(query)
        elif mode == "semantic":
            raw_results = _semantic_search(query, top_k=top_k)
        else:
            raw_results = _hybrid_search(query, top_k=top_k)

        results: list[dict[str, Any]] = []
        for slug, score in raw_results[:top_k]:
            path = self.pages_dir / f"{slug}.md"
            raw = _read_page_raw(path)
            if raw is None:
                continue
            meta, body = _parse_frontmatter(raw)
            results.append({
                "title": meta.get("title", slug),
                "slug": slug,
                "content": body,
                "score": round(score, 4),
                "tags": meta.get("tags", []),
                "created": meta.get("created", ""),
                "updated": meta.get("updated", ""),
            })

        return results

    def format_for_prompt(self, results: list[dict[str, Any]]) -> str:
        """Format retrieved pages into a prompt-injectable string."""
        if not results:
            return ""

        sections = []
        for r in results:
            section = f"## Wiki: {r['title']}\n"
            if r.get("tags"):
                section += f"Tags: {', '.join(r['tags'])}\n"
            section += f"\n{r['content']}\n"
            sections.append(section)

        return "--- WIKI CONTEXT ---\n" + "\n---\n".join(sections) + "\n--- END WIKI CONTEXT ---"


# ── Module-level exports ─────────────────────────────────────────────────────

__all__ = [
    "WikiRAG",
    "wiki_create",
    "wiki_read",
    "wiki_edit",
    "wiki_delete",
    "wiki_list",
    "wiki_search",
    "wiki_auto_save",
    "wiki_suggest",
    "wiki_consolidate",
    "wiki_stats",
    "WIKI_DIR",
    "PAGES_DIR",
    "INDEX_DIR",
]
