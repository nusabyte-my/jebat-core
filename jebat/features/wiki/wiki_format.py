"""Shared slug and frontmatter helpers for the wiki package.

`wiki.py` (the tool surface) and `wiki_core.WikiStore` (the FTS5 index)
used to carry private, slightly divergent copies of the slug and title
logic. That mattered: the index keys pages by title and filename, so a
slug disagreement between writer and indexer would make a page
unfindable, and a title-parsing disagreement would split one page across
two index rows. Both sides now call the functions in this module.

Only stdlib dependencies — this module must stay importable everywhere
`wiki_core` is, including the segfault-prone test chain.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "WIKI_HEADER",
    "build_page",
    "page_filename",
    "parse_frontmatter",
    "slugify_title",
    "title_from_file",
    "today_utc",
]

WIKI_HEADER = "# Wiki:"


def slugify_title(title: str) -> str:
    """Convert a title to a filesystem-safe slug.

    Keeps unicode word characters (so non-ASCII titles stay readable) and
    collapses whitespace/underscores/runs of hyphens into single hyphens.
    Returns "untitled" for titles that slugify to nothing, so a filename
    is never empty or just ".md".
    """
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or "untitled"


def page_filename(title: str) -> str:
    """Filename for a page title: `<slug>.md`."""
    return f"{slugify_title(title)}.md"


def today_utc() -> str:
    """Today's date in the `YYYY-MM-DD` form used by page metadata."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse our simple header-based frontmatter from markdown text.

    Returns (metadata_dict, body_content). The header is a `# Wiki:`
    title line followed by `**Key**: value` lines (tags are
    comma-separated); body is everything after the header block.
    """
    meta: dict[str, Any] = {}
    lines = text.split("\n")
    body_start = 0

    # First line: # Wiki: Title
    if lines and lines[0].startswith(WIKI_HEADER):
        meta["title"] = lines[0][len(WIKI_HEADER):].strip()
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


def build_page(title: str, content: str, tags: list[str] | None = None,
               source: str | None = None, created: str | None = None,
               updated: str | None = None) -> str:
    """Build a full wiki page string with header metadata."""
    tags_str = ", ".join(tags) if tags else ""
    created = created or today_utc()
    updated = updated or today_utc()
    source = source or ""

    header = f"{WIKI_HEADER} {title}\n"
    if tags_str:
        header += f"**Tags**: {tags_str}\n"
    header += f"**Created**: {created}\n"
    header += f"**Updated**: {updated}\n"
    if source:
        header += f"**Source**: {source}\n"
    header += "\n"
    return header + content


def title_from_file(content: str, stem: str) -> str:
    """Page title: `# Wiki: <title>`, else the first markdown H1, else filename.

    `wiki.py` writes the `# Wiki:` header, but pages that predate it (or were
    written by hand) start at the body, so fall back to their own H1 before
    degrading to a title-cased filename.
    """
    lines = content.split("\n")
    first = lines[0].strip() if lines else ""
    if first.startswith(WIKI_HEADER):
        title = first[len(WIKI_HEADER):].strip()
        if title:
            return title
    for line in lines[:10]:
        line = line.strip()
        if line.startswith("# "):
            candidate = line[2:].strip()
            if candidate and not candidate.lower().startswith("wiki:"):
                return candidate
    return stem.replace("-", " ").replace("_", " ").strip().title() or stem
