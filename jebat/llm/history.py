"""Chat history persistence using JSONL files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ChatTurn:
    role: str
    content: str


class ChatHistoryStore:
    """Append-only JSONL chat history per session."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, session_id: str, role: str, content: str) -> None:
        entry = {"session_id": session_id, "role": role, "content": content}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def load(self, session_id: str) -> List[ChatTurn]:
        turns: List[ChatTurn] = []
        if not self.path.exists():
            return turns
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("session_id") == session_id:
                    turns.append(ChatTurn(role=entry["role"], content=entry["content"]))
        return turns
