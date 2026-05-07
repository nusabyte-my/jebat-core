"""
JEBAT WebUI Service

Immersive web interface for JEBAT AI Assistant.
"""

__all__ = ["webui_router"]


def __getattr__(name: str):
    if name == "webui_router":
        from .webui_server import webui_router
        return webui_router
    raise AttributeError(name)
