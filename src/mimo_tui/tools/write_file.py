from __future__ import annotations

from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec
from mimo_tui.tools.sandbox import SandboxViolation, check_path_allowed


class WriteFileTool(BaseTool):
    spec = ToolSpec(
        name="write_file",
        description="Write content to a file, creating it or replacing it entirely.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
        danger_level=1,
    )

    def __init__(self, write_paths: list[str] = None, project_root: str = ".") -> None:  # type: ignore[assignment]
        self._write_paths = write_paths or ["."]
        self._project_root = project_root

    async def run(self, path: str, content: str, **_: Any) -> str:
        try:
            check_path_allowed(path, self._write_paths, self._project_root)
        except SandboxViolation as e:
            return f"Error: {e}"
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {path}"
