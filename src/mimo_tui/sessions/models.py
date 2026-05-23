from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionRow:
    id: str
    title: str
    model: str
    mode: str
    created_at: int
    updated_at: int


@dataclass
class MessageRow:
    id: str
    session_id: str
    role: str
    content: str
    reasoning: str
    created_at: int


@dataclass
class ToolCallRow:
    id: str
    message_id: str
    tool_name: str
    arguments: str
    result: str
    created_at: int
