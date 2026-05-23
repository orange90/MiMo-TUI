from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec
from mimo_tui.tools.sandbox import SandboxViolation, check_path_allowed


class EditFileTool(BaseTool):
    spec = ToolSpec(
        name="edit_file",
        description="Replace an exact string in a file. The old_string must match exactly.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_string": {"type": "string", "description": "Exact text to find and replace"},
                "new_string": {"type": "string", "description": "Text to replace it with"},
            },
            "required": ["path", "old_string", "new_string"],
        },
        danger_level=1,
    )

    def __init__(self, write_paths: list[str] = None, project_root: str = ".") -> None:  # type: ignore[assignment]
        self._write_paths = write_paths or ["."]
        self._project_root = project_root

    async def run(self, path: str, old_string: str, new_string: str, **_: Any) -> str:
        try:
            check_path_allowed(path, self._write_paths, self._project_root)
        except SandboxViolation as e:
            return f"Error: {e}"
        p = Path(path)
        if not p.exists():
            return f"Error: file not found: {path}"
        original = p.read_text(encoding="utf-8")
        if old_string not in original:
            return f"Error: old_string not found in {path}"
        updated = original.replace(old_string, new_string, 1)
        p.write_text(updated, encoding="utf-8")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
        return "".join(diff) or "No visible changes"
