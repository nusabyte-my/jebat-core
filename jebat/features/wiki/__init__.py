"""Wiki module — persistent knowledge base with FTS5 search.

The @register_tool decorators that expose the wiki tools live in
:mod:`.wiki`, so this package has to import it. Previously only WikiStore was
imported, which left the MCP server with zero wiki tools.
"""

from __future__ import annotations

from . import wiki  # noqa: F401  (registers wiki_* tools on import)
from .wiki_core import WikiStore

__all__ = ["WikiStore", "wiki"]
