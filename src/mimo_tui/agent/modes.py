from __future__ import annotations

from enum import Enum


class AgentMode(str, Enum):
    CHAT = "chat"
    PLAN = "plan"
    AGENT = "agent"
    YOLO = "yolo"

    def allows_tools(self) -> bool:
        return self in (AgentMode.AGENT, AgentMode.YOLO)

    def requires_approval(self) -> bool:
        return self == AgentMode.AGENT

    def is_planning(self) -> bool:
        return self == AgentMode.PLAN
