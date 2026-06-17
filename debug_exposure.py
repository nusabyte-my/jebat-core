#!/usr/bin/env python3
import re

patterns = [
    re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"{,})]+)", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|apikey|token|secret|private[_-]?key)\s*[:=]\s*['\"]?([^\s'\"{,})]+)", re.IGNORECASE),
    re.compile(r"(?:bearer\s+)([A-Za-z0-9_\-\.]+)", re.IGNORECASE),
    re.compile(r"(?:sk-|pk-)[A-Za-z0-9]{20,}", re.IGNORECASE),
    re.compile(r"(?:https?://[^/]+@)", re.IGNORECASE),
]

texts = [
    "use password=SuperSecret123 for the API",
    "Configure endpoint with api_key=sk-abcdef123456 and token=bearer xyz",
]

for text in texts:
    print(f"Scanning: {text}")
    for pattern in patterns:
        for match in pattern.finditer(text):
            print(f"  MATCH: pattern={pattern.pattern[:50]}, span={match.span()}, value={match.group()}")
    print()
