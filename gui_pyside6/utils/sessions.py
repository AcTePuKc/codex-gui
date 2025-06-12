from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import List


@dataclass
class SessionMeta:
    path: str
    timestamp: str
    user_messages: int
    tool_calls: int
    first_message: str


def load_sessions() -> List[SessionMeta]:
    """Load saved sessions from ~/.codex/sessions."""
    root = Path.home() / ".codex" / "sessions"
    sessions: List[SessionMeta] = []
    if not root.exists():
        return sessions

    for entry in root.glob("*.json"):
        try:
            with entry.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        items = data.get("items", [])
        first_user = next(
            (i for i in items if i.get("type") == "message" and i.get("role") == "user"),
            None,
        )
        first_text = ""
        if first_user:
            content = first_user.get("content") or []
            if content and isinstance(content, list):
                part = content[0]
                if isinstance(part, dict):
                    first_text = str(part.get("text", "")).replace("\n", " ")[:16]
        user_messages = sum(
            1 for i in items if i.get("type") == "message" and i.get("role") == "user"
        )
        tool_calls = sum(1 for i in items if i.get("type") == "function_call")
        timestamp = data.get("session", {}).get("timestamp", "")
        sessions.append(
            SessionMeta(
                path=str(entry),
                timestamp=timestamp,
                user_messages=user_messages,
                tool_calls=tool_calls,
                first_message=first_text,
            )
        )
    sessions.sort(key=lambda s: s.timestamp, reverse=True)
    return sessions
