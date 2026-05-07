"""
JEBAT Services

Running services: WebUI, API Gateway, MCP Protocol Server.
"""

__all__ = ["webui_router", "APIGateway", "MCPProtocolServer"]


def __getattr__(name: str):
    if name == "APIGateway":
        from .api import APIGateway
        return APIGateway
    if name == "MCPProtocolServer":
        from .mcp import MCPProtocolServer
        return MCPProtocolServer
    if name == "webui_router":
        from .webui import webui_router
        return webui_router
    raise AttributeError(name)
