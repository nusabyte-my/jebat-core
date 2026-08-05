"""Test wiki / knowledge base."""

import os
import tempfile

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