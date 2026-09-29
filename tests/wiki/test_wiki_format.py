"""Tests for the shared slug/frontmatter helpers and cross-module parity.

`wiki.py` (tool surface) and `wiki_core.WikiStore` (FTS5 index) used to
carry private, slightly divergent slug and title logic. Because the index
keys pages by title and filename, a disagreement between writer and
indexer would make pages unfindable or split them across index rows —
so both modules must resolve titles identically.
"""

import pytest
from pathlib import Path

from jebat.features.wiki import wiki as wiki_mod
from jebat.features.wiki import wiki_core
from jebat.features.wiki.wiki_format import (
    build_page,
    page_filename,
    parse_frontmatter,
    slugify_title,
    title_from_file,
)

pytestmark = pytest.mark.unit


def test_slugify_ascii_titles_are_stable() -> None:
    assert slugify_title("Erawan QPOS Operational Invariants") == (
        "erawan-qpos-operational-invariants"
    )
    assert slugify_title("  Multiple   Spaces _and_ underscores  ") == (
        "multiple-spaces-and-underscores"
    )
    assert slugify_title("tags: alpha, beta") == "tags-alpha-beta"


def test_slugify_never_returns_an_empty_filename() -> None:
    assert slugify_title("!!!") == "untitled"
    assert slugify_title("") == "untitled"
    assert page_filename("???") == "untitled.md"


def test_slugify_keeps_unicode_word_characters() -> None:
    assert slugify_title("Café München") == "café-münchen"


def test_parse_and_build_roundtrip() -> None:
    original = build_page(
        "Round Trip",
        "body text",
        tags=["a", "b"],
        source="session_x",
        created="2026-01-01",
        updated="2026-02-02",
    )
    meta, body = parse_frontmatter(original)
    assert meta["title"] == "Round Trip"
    assert meta["tags"] == ["a", "b"]
    assert meta["created"] == "2026-01-01"
    assert meta["updated"] == "2026-02-02"
    assert meta["source"] == "session_x"
    assert body == "body text"


def test_parse_frontmatter_without_header_falls_back_to_h1() -> None:
    meta, body = parse_frontmatter("# My Page\n\ncontent\n")
    assert meta == {}
    assert body == "# My Page\n\ncontent"
    # ...and the indexer must still recover the title from the same text.
    assert title_from_file("# My Page\n\ncontent\n", "my-page") == "My Page"


def test_title_from_file_prefers_wiki_header_then_h1_then_filename() -> None:
    assert title_from_file("# Wiki: Explicit\n\nx\n", "ignored") == "Explicit"
    assert title_from_file("# First H1\nx\n", "fallback") == "First H1"
    assert title_from_file("no headings\n", "plain-name") == "Plain Name"


def test_writer_and_indexer_agree_on_filename() -> None:
    """wiki.py's path resolution and WikiStore's must be the same function."""
    for title in [
        "Deploy Runbook",
        "erawan-qpos-operational-invariants",
        "A. Very Odd (title)!",
        "caf\u00e9 notes",
    ]:
        expected = f"{slugify_title(title)}.md"
        assert page_filename(title) == expected
        assert wiki_mod._page_path(title).name == expected


def test_indexer_uses_the_shared_slug(tmp_path) -> None:
    """WikiStore.create_page must file the page under the shared filename."""
    store = wiki_core.WikiStore(wiki_dir=tmp_path)
    result = store.create_page("Deploy Runbook", "body")

    assert result.get("created") is True
    assert result["filename"] == page_filename("Deploy Runbook")
    assert result["filename"] == "deploy-runbook.md"
    # And the tool surface resolves the same title to the same file.
    assert wiki_mod._page_path("Deploy Runbook").name == result["filename"]


def test_wiki_modules_use_the_shared_helpers() -> None:
    """The duplicated private copies must stay deleted."""
    source = Path(wiki_mod.__file__).read_text(encoding="utf-8")
    core_source = Path(wiki_core.__file__).read_text(encoding="utf-8")
    for stale in ("def _slugify(", "def _parse_frontmatter(", "def _build_page("):
        assert stale not in source
    for stale in ("def _slug(self", "def _filename(self", "def _file_path(self"):
        assert stale not in core_source
