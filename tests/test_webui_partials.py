"""WebUI routing coverage — every sidebar page must resolve to a partial + title.

Regression guard for the class of bug where a sidebar link silently fell back
to the dashboard because PAGE_TITLES (or the partial file) was missing.
Run: pytest tests/test_webui_partials.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "jebat" / "services" / "webui" / "static"
INDEX = STATIC / "index.html"
PARTIALS = STATIC / "partials"


def _sidebar_pages() -> set[str]:
    html = INDEX.read_text(encoding="utf-8")
    return set(re.findall(r'data-page="([a-z0-9_-]+)"', html))


def _page_titles() -> set[str]:
    html = INDEX.read_text(encoding="utf-8")
    match = re.search(r"const PAGE_TITLES = \{(.*?)\};", html, re.S)
    assert match, "PAGE_TITLES block not found in index.html"
    return set(re.findall(r"([a-z0-9_-]+)\s*:", match.group(1)))


def _partial_names() -> set[str]:
    return {p.stem for p in PARTIALS.glob("*.html")}


@pytest.fixture(scope="module")
def pages() -> set[str]:
    return _sidebar_pages()


def test_sidebar_has_pages(pages: set[str]) -> None:
    assert pages, "no data-page links found in the sidebar"


def test_every_sidebar_page_resolves_to_a_partial(pages: set[str]) -> None:
    missing = pages - _partial_names()
    assert not missing, f"sidebar pages without a partial file: {sorted(missing)}"


def test_every_sidebar_page_has_a_title(pages: set[str]) -> None:
    missing = pages - _page_titles()
    assert not missing, (
        f"sidebar pages missing from PAGE_TITLES (they silently load Dashboard): {sorted(missing)}"
    )


def test_every_partial_is_reachable(pages: set[str]) -> None:
    orphans = _partial_names() - pages
    assert not orphans, f"partials no one can navigate to: {sorted(orphans)}"


def test_partials_are_non_trivial(pages: set[str]) -> None:
    thin = [name for name in pages if (PARTIALS / f"{name}.html").stat().st_size < 400]
    assert not thin, f"partials too small to render anything useful: {sorted(thin)}"
