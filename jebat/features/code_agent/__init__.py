"""JEBAT Coding Agent — Hermes-style autonomous coding assistant with multi-agent orchestration.

Usage:
    jebat code "build a login page with JWT auth"
    jebat code                                    # interactive mode
    jebat code --model gpt-4o "refactor the API"
"""

from .code_agent import CodeAgent
from .agent_prompt import CODING_AGENT_PROMPT, get_agent_prompt

__all__ = ["CodeAgent", "CODING_AGENT_PROMPT", "get_agent_prompt"]
