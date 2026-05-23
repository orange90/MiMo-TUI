from __future__ import annotations

from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec

_MAX_BYTES = 200_000


class ReadFileTool(BaseTool):
    spec = ToolSpec(
        name="read_file",
        description="Read the contents of a file. Returns the text content.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "offset": {"type": "integer", "description": "Line number to start from (1-indexed)", "default": 1},
                "limit": {"type": "integer", "description": "Max lines to return", "default": 200},
            },
            "required": ["path"],
        },
        danger_level=0,
    )

    async def run(self, path: str, offset: int = 1, limit: int = 200, **_: Any) -> str:
        p = Path(path)
        if not p.exists():
            return f"Error: file not found: {path}"
        if not p.is_file():
            return f"Error: not a file: {path}"
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return f"Error reading file: {e}"
        lines = text.splitlines()
        start = max(0, offset - 1)
        end = start + limit
        selected = lines[start:end]
        result = "\n".join(f"{start + i + 1}\t{line}" for i, line in enumerate(selected))
        if end < len(lines):
            result += f"\n… ({len(lines) - end} more lines)"
        return result
