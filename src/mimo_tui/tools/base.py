from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    danger_level: int = 0  # 0=safe, 1=moderate, 2=dangerous


class BaseTool(ABC):
    spec: ToolSpec

    @abstractmethod
    async def run(self, **kwargs: Any) -> str:
        ...

    def to_api_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.spec.name,
                "description": self.spec.description,
                "parameters": self.spec.parameters,
            },
        }
