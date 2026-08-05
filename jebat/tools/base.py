"""Tool registry infrastructure."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class BaseTool:
    """Base tool class."""

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func

    async def run(self, **kwargs: Any) -> Any:
        """Run the tool with given arguments."""
        return self.func(**kwargs)


class ToolRegistry:
    """Registry for tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, name: str, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)