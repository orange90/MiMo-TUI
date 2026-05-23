from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec


class GlobTool(BaseTool):
    spec = ToolSpec(
        name="glob",
        description="Find files matching a glob pattern. Returns a list of matching paths.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern, e.g. src/**/*.py"},
                "cwd": {"type": "string", "description": "Directory to search from", "default": "."},
            },
            "required": ["pattern"],
        },
        danger_level=0,
    )

    async def run(self, pattern: str, cwd: str = ".", **_: Any) -> str:
        base = Path(cwd)
        matches = sorted(str(p) for p in base.glob(pattern))
        if not matches:
            return f"No files matched: {pattern}"
        return "\n".join(matches[:500])
