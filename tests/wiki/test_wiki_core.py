"""Test wiki / knowledge base."""

import os
import tempfile
from pathlib import Path

from jebat.features.wiki.wiki_core import WikiStore

import pytest

pytestmark = pytest.mark.unit


def test_create_and_read_page() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        result = wiki.create_page("test-page", "Hello world content")
        assert result.get("created") is True

        read = wiki.read_page("test-page")
        assert read["title"] == "test-page"
        assert "Hello world" in read["content"]


def test_create_duplicate_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("dupe", "first")
        result = wiki.create_page("dupe", "second")
        assert "error" in result
        assert "already exists" in result["error"]


def test_update_page_preserves_data() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("updatable", "original content")
        wiki.update_page("updatable", "updated content")

        read = wiki.read_page("updatable")
        assert read["content"] == "updated content"


def test_delete_page() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("deletable", "content")
        result = wiki.delete_page("deletable")
        assert result.get("deleted") is True

        read = wiki.read_page("deletable")
        assert "error" in read


def test_list_pages() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("alpha", "first")
        wiki.create_page("beta", "second")
        wiki.create_page("gamma", "third")

        result = wiki.list_pages()
        assert result["count"] == 3
        titles = [p["title"] for p in result["pages"]]
        assert "alpha" in titles
        assert "beta" in titles

        # Prefix filter
        result_a = wiki.list_pages(prefix="a")
        assert result_a["count"] == 1


def test_search_finds_page_by_content() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("api-docs", "The REST API uses JWT tokens for authentication")
        wiki.create_page("deploy", "Deploy using Docker compose on Ubuntu server")

        result = wiki.search("JWT authentication")
        assert result["count"] >= 1
        assert any("JWT" in m["snippet"] for m in result["matches"])


def test_search_returns_empty_no_match() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("x", "plain text")
        result = wiki.search("nonexistent_xyz")
        assert result["count"] == 0


def test_read_nonexistent_page_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        result = wiki.read_page("does-not-exist")
        assert "error" in result


def test_get_stats() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki = WikiStore(wiki_dir=os.path.join(tmp, "wiki"))
        wiki.create_page("a", "content a")
        wiki.create_page("b", "content b")

        stats = wiki.get_stats()
        assert stats["page_count"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["last_updated"]["title"] in ("a", "b")


# ── Index drift: pages written outside the index ─────────────────────────────
# `jebat.features.wiki.wiki` (the tool surface the MCP server loads) writes
# `pages/*.md` directly and never touches index.db, so FTS5 — and therefore
# `inject_wiki_rag` — could not see those pages. On the live store that meant 20
# page files and 3 index rows.


def _write_page_file(wiki_dir: str, slug: str, text: str) -> Path:
    """Write a page the way wiki.py does: straight to disk, bypassing the DB."""
    pages = Path(wiki_dir) / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    path = pages / f"{slug}.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_reindex_adopts_pages_written_outside_the_index() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki_dir = os.path.join(tmp, "wiki")
        WikiStore(wiki_dir=wiki_dir)  # create the database
        _write_page_file(
            wiki_dir,
            "erawan-qpos-operational-invariants",
            "# Wiki: Erawan QPOS Operational Invariants\n"
            "**Tags**: erawan-qsys, invariants\n"
            "**Updated**: 2026-09-23\n\n"
            "Group checkout uses a running number.\n",
        )

        wiki = WikiStore(wiki_dir=wiki_dir)

        assert wiki.get_stats()["page_count"] == 1
        assert wiki.search("running number")["count"] == 1
        read = wiki.read_page("Erawan QPOS Operational Invariants")
        assert read["content"].startswith("# Wiki: Erawan QPOS")


def test_reindex_falls_back_to_the_first_markdown_heading() -> None:
    """Pages without the `# Wiki:` header still get a real title, not a slug."""
    with tempfile.TemporaryDirectory() as tmp:
        wiki_dir = os.path.join(tmp, "wiki")
        WikiStore(wiki_dir=wiki_dir)
        _write_page_file(
            wiki_dir,
            "erawan-qsys-2026-09-28-session",
            "# Erawan-QSys — 2026-09-28 Session\n\n## Gantt Timeline Overhaul\n",
        )

        wiki = WikiStore(wiki_dir=wiki_dir)

        titles = [p["title"] for p in wiki.list_pages()["pages"]]
        assert titles == ["Erawan-QSys — 2026-09-28 Session"]


def test_reindex_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki_dir = os.path.join(tmp, "wiki")
        WikiStore(wiki_dir=wiki_dir)
        _write_page_file(wiki_dir, "once", "# Wiki: Once\n\nbody\n")

        assert WikiStore(wiki_dir=wiki_dir).get_stats()["page_count"] == 1
        assert WikiStore(wiki_dir=wiki_dir).get_stats()["page_count"] == 1


def test_reindex_does_not_resurrect_soft_deleted_page() -> None:
    """`delete_page` keeps the .md file, so adoption needs the tombstone."""
    with tempfile.TemporaryDirectory() as tmp:
        wiki_dir = os.path.join(tmp, "wiki")
        wiki = WikiStore(wiki_dir=wiki_dir)
        wiki.create_page("doomed", "secret content")
        wiki.delete_page("doomed")
        # Soft delete: the file is deliberately left on disk.
        assert (Path(wiki_dir) / "pages" / "doomed.md").exists()

        reopened = WikiStore(wiki_dir=wiki_dir)

        assert reopened.get_stats()["page_count"] == 0
        assert "error" in reopened.read_page("doomed")
        assert reopened.search("secret")["count"] == 0


def test_recreating_a_soft_deleted_page_indexes_it_again() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wiki_dir = os.path.join(tmp, "wiki")
        wiki = WikiStore(wiki_dir=wiki_dir)
        wiki.create_page("phoenix", "first")
        wiki.delete_page("phoenix")
        wiki.create_page("phoenix", "second")

        reopened = WikiStore(wiki_dir=wiki_dir)

        assert reopened.get_stats()["page_count"] == 1
        assert reopened.read_page("phoenix")["content"] == "second"