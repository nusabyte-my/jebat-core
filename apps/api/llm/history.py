from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class ChatTurn:
    role: str
    content: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatHistoryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, session_id: str, role: str, content: str) -> None:
        record = {"session_id": session_id, **asdict(ChatTurn(role=role, content=content))}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def load(self, session_id: str, limit: int = 20) -> list[ChatTurn]:
        if not self.path.exists():
            return []
        rows: list[ChatTurn] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("session_id") != session_id:
                continue
            rows.append(
                ChatTurn(
                    role=str(item.get("role", "user")),
                    content=str(item.get("content", "")),
                    created_at=str(item.get("created_at", "")),
                )
            )
        return rows[-limit:]
