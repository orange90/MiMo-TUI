from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass
class ApprovalRequest:
    tool_name: str
    arguments: dict[str, object]
    danger_level: int
    call_id: str


ApprovalCallback = Callable[[ApprovalRequest], Awaitable[bool]]


async def auto_approve(_: ApprovalRequest) -> bool:
    return True


async def auto_deny(_: ApprovalRequest) -> bool:
    return False
