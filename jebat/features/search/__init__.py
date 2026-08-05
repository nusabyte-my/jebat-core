"""JEBAT Web Search feature package.

Exports search_web and web_extract tools for registration
in the JEBAT tool registry. Import this package to make
web search tools available.
"""

from jebat.features.search.web_search import (
    search_web,
    web_extract,
)

__all__ = [
    "search_web",
    "web_extract",
]