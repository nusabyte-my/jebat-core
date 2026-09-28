"""Regression tests for the DuckDuckGo HTML result parser.

Current DDG markup nests every helper div (``result__extras``,
``result__extras__url``) inside the container — and each of those class
names also *starts with* "result". The old prefix-match parser reset its
title/url buffer on them and closed the result at the first nested
``</div>``, so live searches parsed to zero results (which made the whole
SearXNG → Google/Bing → DDG fallback chain report "all sources failed").
These tests pin the container/depth behavior against recorded markup.
"""

from jebat.features.search.web_search import _DDGResultParser

FIXTURE = """
<html><body>
<div class="serp__results">
  <div class="result results_links results_links-sponsored result--ad">
    <div class="links_main links_deep result__body">
      <h2 class="result__title">
        <a rel="nofollow" class="result__a" href="https://duckduckgo.com/y.js?ad_domain=spam.example&amp;u3=click">Sponsored Thing</a>
      </h2>
      <div class="result__extras">
        <div class="result__extras__url">
          <a class="result__url" href="https://spam.example/">spam.example</a>
        </div>
      </div>
      <a class="result__snippet" href="https://duckduckgo.com/y.js?ad=1">Buy it now</a>
      <div class="clear"></div>
    </div>
  </div>

  <div class="result results_links results_links_deep web-result ">
    <div class="links_main links_deep result__body">
      <h2 class="result__title">
        <a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fgithub.com%2FNandhaKishorM%2Flaya&amp;rut=abc123">GitHub - NandhaKishorM/laya: System 1</a>
      </h2>
      <div class="result__extras">
        <div class="result__extras__url">
          <a class="result__url" href="https://github.com/NandhaKishorM/laya">github.com</a>
        </div>
      </div>
      <a class="result__snippet" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fgithub.com%2FNandhaKishorM%2Flaya&amp;rut=abc123">Non-autoregressive System 1 decision engine.</a>
      <div class="clear"></div>
    </div>
  </div>

  <div class="result results_links results_links_deep web-result ">
    <div class="links_main links_deep result__body">
      <h2 class="result__title">
        <a rel="nofollow" class="result__a" href="https://laya.convaiinnovations.com/">Laya - 33ms Multilingual Decision Engine</a>
      </h2>
      <div class="result__extras">
        <div class="result__extras__url"><a class="result__url" href="https://laya.convaiinnovations.com/">laya.convaiinnovations.com</a></div>
      </div>
      <a class="result__snippet" href="https://laya.convaiinnovations.com/">Typed answers with calibrated probabilities.</a>
      <div class="clear"></div>
    </div>
  </div>
</div>
</body></html>
"""


def _parse(html: str = FIXTURE) -> list[dict[str, str]]:
    parser = _DDGResultParser()
    parser.feed(html)
    parser.close()
    return parser.results


def test_parser_extracts_organic_results_from_current_markup() -> None:
    results = _parse()
    assert len(results) == 2, "helper divs must not truncate results; ads excluded"
    assert results[0]["title"].startswith("GitHub - NandhaKishorM/laya")
    assert results[0]["url"] == "https://github.com/NandhaKishorM/laya"
    assert "System 1" in results[0]["snippet"]
    assert results[1]["url"] == "https://laya.convaiinnovations.com/"


def test_parser_skips_sponsored_ad_slots() -> None:
    results = _parse()
    urls = [r["url"] for r in results]
    assert not any("y.js" in u or "spam.example" in u for u in urls)
    assert all(r["title"] for r in results), "no empty placeholders"


def test_parser_handles_direct_links_without_redirect_wrapper() -> None:
    html = FIXTURE.replace(
        '//duckduckgo.com/l/?uddg=https%3A%2F%2Fgithub.com%2FNandhaKishorM%2Flaya&amp;rut=abc123',
        "https://github.com/NandhaKishorM/laya",
    )
    results = _parse(html)
    assert results[0]["url"] == "https://github.com/NandhaKishorM/laya"


def test_parser_returns_nothing_for_empty_page() -> None:
    assert _parse("<html><body><div class='results'></div></body></html>") == []
