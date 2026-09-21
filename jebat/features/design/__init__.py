"""JEBAT Design & UI/UX Feature Package.

Exports curated design pattern corpus, modern design trends, and resource helpers.
"""

from __future__ import annotations
import json
from typing import Any, Dict

from .corpus import PATTERNS
from .trends import TRENDS


def design_reference_resource() -> Dict[str, Any]:
    """Expose the curated design pattern corpus as an MCP resource."""
    return {
        "uri": "design://reference/corpus",
        "mimeType": "application/json",
        "text": json.dumps(PATTERNS, separators=(",", ":"), ensure_ascii=False),
    }


def design_trends_resource() -> Dict[str, Any]:
    """Expose current design trends as an MCP resource."""
    return {
        "uri": "design://trends",
        "mimeType": "application/json",
        "text": json.dumps(TRENDS, separators=(",", ":"), ensure_ascii=False),
    }


__all__ = [
    "PATTERNS",
    "TRENDS",
    "design_reference_resource",
    "design_trends_resource",
]
