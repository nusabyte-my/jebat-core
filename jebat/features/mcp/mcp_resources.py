"""Skill and wiki index builders for MCP resource surfaces.

Extracted from mcp_server.py (P2-4 monolith split): the skill:// and wiki://
index machinery — filesystem discovery, frontmatter parsing, TTL caches.
Protocol handling (JSON-RPC handlers) stays in mcp_server.py, which imports
these helpers. No behavioral change.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, List, Optional

# ── Skills as MCP resources (skill://) ─────────────────────────────────────
# Every SKILL.md the workspace knows about is exposed as a resource instead
# of one tool per skill: MCP tool-selection accuracy degrades sharply past
# ~30-40 tools, while resources scale for free and stay readable by any
# conforming client (resources/list + resources/read).

_SKILL_INDEX: Optional[Dict[str, Dict[str, str]]] = None
_SKILL_INDEX_AT = 0.0
_SKILL_INDEX_TTL = 5.0  # seconds; skill_manage can add/remove skills at runtime


def _skill_roots() -> List[tuple]:
    """(store_key, path) pairs for every skill store JEBAT reads from."""
    home = Path.home()
    pkg_root = Path(__file__).resolve().parents[3]
    cwd = Path.cwd()
    candidates = [
        ("tokguru", os.getenv("JEBAT_SKILLS_DIR", "") or str(home / ".jebat" / "tokguru")),
        ("home", str(home / ".jebat" / "skills")),
        ("bundle", str(pkg_root / "jebat-tokguru" / "skills")),
        ("workspace", str(pkg_root / "skills")),
        ("bundle", str(cwd / "jebat-tokguru" / "skills")),
        ("workspace", str(cwd / "skills")),
    ]
    roots: List[tuple] = []
    seen = set()
    for store, raw in candidates:
        if not raw:
            continue
        try:
            path = Path(raw).expanduser().resolve()
        except OSError:
            continue
        if path in seen or not path.is_dir():
            continue
        seen.add(path)
        roots.append((store, path))
    return roots


def _skill_meta(content: str) -> Dict[str, str]:
    """Extract name/description/category from SKILL.md YAML frontmatter."""
    meta: Dict[str, str] = {}
    if not content.startswith("---"):
        return meta
    end = content.find("---", 3)
    if end == -1:
        return meta
    for line in content[3:end].splitlines():
        line = line.strip()
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        key = key.strip()
        if key in ("name", "description", "category") and key not in meta:
            meta[key] = value.strip().strip("\"'")
    return meta


def _skill_index(refresh: bool = False) -> Dict[str, Dict[str, str]]:
    """Map skill://<store>/<name> → {name, description, category, store, path}."""
    global _SKILL_INDEX, _SKILL_INDEX_AT
    now = time.monotonic()
    if (
        not refresh
        and _SKILL_INDEX is not None
        and (now - _SKILL_INDEX_AT) < _SKILL_INDEX_TTL
    ):
        return _SKILL_INDEX

    index: Dict[str, Dict[str, str]] = {}
    for store, root in _skill_roots():
        try:
            skill_files = sorted(root.rglob("SKILL.md"))
        except OSError:
            continue
        for skill_file in skill_files:
            try:
                rel = skill_file.parent.relative_to(root).as_posix()
            except ValueError:
                continue
            uri = f"skill://{store}/{rel}"
            if uri in index:
                continue
            try:
                content = skill_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta = _skill_meta(content)
            index[uri] = {
                "name": meta.get("name") or skill_file.parent.name,
                "description": meta.get("description", ""),
                "category": meta.get("category", ""),
                "store": store,
                "path": str(skill_file),
            }

    _SKILL_INDEX = index
    _SKILL_INDEX_AT = now
    return index


# ── Wiki pages as MCP resources (wiki://) ──────────────────────────────────
# Mirrors the skill:// surface: one resource per page, plus a URI template.
# Pages are read from the markdown files themselves rather than through
# WikiStore's SQLite index, because the tool surface (`wiki.py`) writes those
# same files without updating that index — the files are the only view that is
# guaranteed to match what is actually on disk.

_WIKI_INDEX: Optional[Dict[str, Dict[str, str]]] = None
_WIKI_INDEX_AT = 0.0
_WIKI_INDEX_TTL = 5.0  # seconds; the wiki_* tools can write pages at runtime


def _wiki_roots() -> List[Path]:
    """The `pages/` directory holding wiki markdown.

    `JEBAT_WIKI_DIR` *replaces* the default wiki root, matching how
    `wiki_rag` resolves the same variable — adding to it instead would mean the
    variable could never point a caller at a self-contained store.
    """
    env_dir = os.getenv("JEBAT_WIKI_DIR", "")
    base = Path(env_dir).expanduser() if env_dir else Path.home() / ".jebat" / "wiki"
    candidates = [base / "pages"]
    roots: List[Path] = []
    seen = set()
    for raw in candidates:
        try:
            path = raw.resolve()
        except OSError:
            continue
        if path in seen or not path.is_dir():
            continue
        seen.add(path)
        roots.append(path)
    return roots


def _wiki_meta(content: str, stem: str) -> Dict[str, str]:
    """Title/tags/updated from a page header (`# Wiki:` then `**Key**: value`)."""
    lines = content.split("\n")
    meta: Dict[str, str] = {}
    if lines and lines[0].strip().startswith("# Wiki:"):
        meta["title"] = lines[0].split("# Wiki:", 1)[1].strip()
    for line in lines[:12]:
        line = line.strip()
        if not line.startswith("**") or ": " not in line:
            continue
        key, value = line.split(": ", 1)
        key = key.strip("*").strip().lower()
        if key in ("tags", "updated") and key not in meta:
            meta[key] = value.strip()
    if not meta.get("title"):
        for line in lines[:10]:
            line = line.strip()
            if line.startswith("# "):
                meta["title"] = line[2:].strip()
                break
    meta.setdefault(
        "title", stem.replace("-", " ").replace("_", " ").strip().title() or stem
    )
    return meta


def _wiki_index(refresh: bool = False) -> Dict[str, Dict[str, str]]:
    """Map wiki://<slug> → {slug, title, description, tags, updated, path}."""
    global _WIKI_INDEX, _WIKI_INDEX_AT
    now = time.monotonic()
    if (
        not refresh
        and _WIKI_INDEX is not None
        and (now - _WIKI_INDEX_AT) < _WIKI_INDEX_TTL
    ):
        return _WIKI_INDEX

    index: Dict[str, Dict[str, str]] = {}
    for root in _wiki_roots():
        try:
            page_files = sorted(root.glob("*.md"))
        except OSError:
            continue
        for page_file in page_files:
            slug = page_file.stem
            uri = f"wiki://{slug}"
            if uri in index:
                continue
            try:
                content = page_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta = _wiki_meta(content, slug)
            tags = meta.get("tags", "")
            updated = meta.get("updated", "")
            description = f"JEBAT wiki page · tags: {tags}" if tags else "JEBAT wiki page"
            if updated:
                description += f" · updated {updated}"
            index[uri] = {
                "slug": slug,
                "title": meta["title"],
                "description": description,
                "tags": tags,
                "updated": updated,
                "path": str(page_file),
            }

    _WIKI_INDEX = index
    _WIKI_INDEX_AT = now
    return index


