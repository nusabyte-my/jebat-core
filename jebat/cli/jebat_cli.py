"""JEBAT CLI interface."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from jebat.llm.config import load_llm_config
from jebat.llm.providers import list_supported_providers


class JEBATCLI:
    """Main JEBAT CLI class."""

    def __init__(self):
        self.print = print

    async def cmd_doctor(self) -> None:
        config = load_llm_config()
        providers = {p["name"] for p in list_supported_providers()}
        self.print(f"Configured Provider: {config.provider}")
        self.print(f"Best Available Provider: {config.provider}")
        self.print(f"Model: {config.model}")
        self.print(f"Supported Providers: {', '.join(sorted(providers))}")
