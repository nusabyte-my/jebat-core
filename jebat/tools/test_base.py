"""Test tool registry infrastructure."""


from jebat.tools.base import BaseTool, ToolRegistry


def test_tool_registry_can_register_and_retrieve() -> None:
    """Test that the tool registry can register and retrieve a tool."""
    registry = ToolRegistry()
    tool = BaseTool(func=lambda x: x * 2)

    registry.register("test_tool", tool)
    retrieved = registry.get("test_tool")

    assert retrieved is not None
    assert retrieved is tool