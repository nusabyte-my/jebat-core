"""
JEBAT DevAssistant Gateway

Local environment interface:
- CLI commands
- File watcher
- WebSocket server
"""

from .cli import DevCLI

__all__ = ["DevCLI"]
