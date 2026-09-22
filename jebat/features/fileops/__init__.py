"""JEBAT File Operations — read, write, patch, search, tree, undo.

The implementations live in :mod:`jebat.features.fileops.file_ops` and register
themselves into the tool registry via @register_tool at import time. This
package must import that submodule, otherwise `import jebat.features.fileops`
(a no-op package init) registers nothing and the MCP server silently exposes
no file tools at all.
"""

from __future__ import annotations

from .file_ops import (
    file_patch,
    file_read,
    file_search,
    file_tree,
    file_undo,
    file_write,
)

__all__ = [
    "file_patch",
    "file_read",
    "file_search",
    "file_tree",
    "file_undo",
    "file_write",
]
