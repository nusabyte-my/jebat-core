"""
🗡️ JEBAT DevAssistant

Your Personal Development AI Assistant

Inspired by Jebat Gateway architecture + Google Stitch MCP + JEBAT intelligence.
Works ONLY inside this Dev environment to help you build applications.

Version: 1.0.0-dev
Status: In Development
"""

__version__ = "1.0.0-dev"
__author__ = "JEBAT Team"
__license__ = "MIT"

# Core DevAssistant components
from jebat_dev.brain.dev_brain import DevBrain
from jebat_dev.gateway.cli import DevCLI
from jebat_dev.sandbox.dev_sandbox import DevSandbox

__all__ = [
    "DevCLI",
    "DevBrain",
    "DevSandbox",
]
