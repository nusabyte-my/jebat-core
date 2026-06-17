#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jebat.core.agents.orchestrator import AgentOrchestrator

async def test():
    orchestrator = AgentOrchestrator()
    test_payload = {
        "decision": "use password=SuperSecret123 for the API",
        "summary": "Configure endpoint with api_key=sk-abcdef123456 and token=bearer xyz",
        "recommended_next_actions": ["set password=admin", "deploy"],
    }
    sanitized, findings = orchestrator._sanitize_payload(test_payload)
    print("Original:", test_payload)
    print("Sanitized:", sanitized)
    print("Findings:", findings)

import asyncio
asyncio.run(test())
