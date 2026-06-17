"""Catalyst Integration — Inference.net observability and tracing for JEBAT."""

from jebat.features.catalyst.catalyst_integration import (
    CatalystClient,
    CatalystSpan,
    CatalystTrace,
    create_catalyst_client,
)
from jebat.features.catalyst.catalyst_tools import (
    CatalystToolRegistry,
    catalyst_tool_registry,
)

__all__ = [
    "CatalystClient",
    "CatalystSpan",
    "CatalystTrace",
    "create_catalyst_client",
    "CatalystToolRegistry",
    "catalyst_tool_registry",
]
