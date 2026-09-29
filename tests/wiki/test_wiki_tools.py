"""Tests that the wiki tool surface keeps `index.db` in step with pages/*.md.

`wiki.py` owns the page files and `WikiStore` owns the FTS5 index that
`inject_wiki_rag` searches. Before the index bridge, the two drifted: writes
went to disk only, so a page created through the tools stayed unsearchable until
something happened to construct a fresh `WikiStore` — and since the RAG store is
a process-lifetime singleton, that could mean the whole session.
"""

import pytest

import jebat.features.wiki.wiki as wiki_mod

pytestmark = pytest.mark.unit


@pytest.fixture
def wiki_env(tmp_path, monkeypatch):
    """Point the tool module at an isolated wiki and drop its cached store."""
    monkeypatch.setattr(wiki_mod, "WIKI_DIR", tmp_path)
    monkeypatch.setattr(wiki_mod, "PAGES_DIR", tmp_path / "pages")
    monkeypatch.setattr(wiki_mod, "INDEX_DIR", tmp_path / "index")
    monkeypatch.setattr(wiki_mod, "_index_store", None)
    # Keep the vector cache out of the test: loading a sentence-transformers
    # model here would dominate the run and is not what is under test.
    monkeypatch.setattr(wiki_mod, "_update_embedding", lambda slug, text: None)
    return wiki_mod


@pytest.mark.anyio
async def test_create_is_searchable_immediately(wiki_env):
    """The same store instance must see the page with no reload or reindex."""
    store = wiki_env._get_index_store()  # built while the pages dir is empty
    assert store.get_stats()["page_count"] == 0

    result = await wiki_env.wiki_create(
        "Indexed Page", "A zzqwiki marker lives here.", tags=["demo"]
    )

    assert result["status"] == "created"
    assert store.get_stats()["page_count"] == 1
    assert store.search("zzqwiki")["count"] == 1
    read = store.read_page("Indexed Page")
    assert read["content"].startswith("# Wiki: Indexed Page")
    assert "**Tags**: demo" in read["content"]


@pytest.mark.anyio
async def test_edit_replaces_the_indexed_content(wiki_env):
    await wiki_env.wiki_create("Editable", "first zzqalpha body")
    store = wiki_env._get_index_store()
    assert store.search("zzqalpha")["count"] == 1

    await wiki_env.wiki_edit("Editable", "second zzqbeta body")

    assert store.search("zzqbeta")["count"] == 1
    assert store.search("zzqalpha")["count"] == 0
    assert store.get_stats()["page_count"] == 1


@pytest.mark.anyio
async def test_delete_drops_the_index_row(wiki_env):
    await wiki_env.wiki_create("Deletable", "doomed zzqgamma body")
    store = wiki_env._get_index_store()
    assert store.search("zzqgamma")["count"] == 1

    result = await wiki_env.wiki_delete("Deletable")

    assert result["status"] == "deleted"
    assert store.search("zzqgamma")["count"] == 0
    assert store.get_stats()["page_count"] == 0
    # A hard delete leaves no file, so nothing can re-adopt it later either.
    assert not (wiki_env.PAGES_DIR / "deletable.md").exists()


@pytest.mark.anyio
async def test_auto_save_is_searchable_immediately(wiki_env):
    await wiki_env.wiki_create("Filler", "filler body")
    store = wiki_env._get_index_store()

    result = await wiki_env.wiki_auto_save("zzqepsilon auto-saved note\nmore detail")

    assert result["status"] == "auto_saved"
    assert store.search("zzqepsilon")["count"] == 1
    assert store.get_stats()["page_count"] == 2


def test_direct_file_writes_are_still_adopted(wiki_env):
    """The reindex remains the safety net for writers that bypass the bridge."""
    from jebat.features.wiki.wiki_core import WikiStore

    pages = wiki_env.PAGES_DIR
    pages.mkdir(parents=True, exist_ok=True)
    (pages / "direct.md").write_text("# Wiki: Direct\n\nzzqdelta\n", encoding="utf-8")

    store = WikiStore(wiki_dir=wiki_env.WIKI_DIR)

    assert store.search("zzqdelta")["count"] == 1
