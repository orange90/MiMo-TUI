"""Diff tool — compare two files or show git diff."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec


class DiffTool(BaseTool):
    spec = ToolSpec(
        name="diff",
        description=(
            "Show differences between files or git changes. "
            "Mode 'files' compares two file paths. "
            "Mode 'git' shows git diff output (optionally for a specific path)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["files", "git"],
                    "description": "Comparison mode: 'files' to compare two files, 'git' for git diff",
                },
                "file_a": {
                    "type": "string",
                    "description": "First file path (required when mode='files')",
                },
                "file_b": {
                    "type": "string",
                    "description": "Second file path (required when mode='files')",
                },
                "path": {
                    "type": "string",
                    "description": "Path to diff (optional, for mode='git')",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes instead of working tree (for mode='git')",
                    "default": False,
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines around changes",
                    "default": 3,
                },
            },
            "required": ["mode"],
        },
        danger_level=0,
    )

    def __init__(self, project_root: str = ".") -> None:
        self._project_root = Path(project_root).resolve()

    async def run(self, **kwargs: Any) -> str:
        mode = kwargs.get("mode", "")
        context = kwargs.get("context_lines", 3)

        if mode == "files":
            return await self._diff_files(
                kwargs.get("file_a", ""),
                kwargs.get("file_b", ""),
                context,
            )
        elif mode == "git":
            return await self._diff_git(
                kwargs.get("path", ""),
                kwargs.get("staged", False),
                context,
            )
        else:
            return f"Error: unknown mode '{mode}'. Use 'files' or 'git'."

    async def _diff_files(self, file_a: str, file_b: str, context: int) -> str:
        if not file_a or not file_b:
            return "Error: both file_a and file_b are required for mode='files'."

        path_a = (self._project_root / file_a).resolve()
        path_b = (self._project_root / file_b).resolve()

        if not str(path_a).startswith(str(self._project_root)):
            return f"Error: file_a '{file_a}' is outside project root."
        if not str(path_b).startswith(str(self._project_root)):
            return f"Error: file_b '{file_b}' is outside project root."
        if not path_a.exists():
            return f"Error: file_a '{file_a}' does not exist."
        if not path_b.exists():
            return f"Error: file_b '{file_b}' does not exist."

        try:
            import difflib
            text_a = path_a.read_text(encoding="utf-8", errors="replace").splitlines()
            text_b = path_b.read_text(encoding="utf-8", errors="replace").splitlines()
            diff = difflib.unified_diff(
                text_a,
                text_b,
                fromfile=file_a,
                tofile=file_b,
                lineterm="",
                n=context,
            )
            result = "\n".join(diff)
            return result or "(files are identical)"
        except Exception as e:
            return f"Error computing diff: {e}"

    async def _diff_git(self, path: str, staged: bool, context: int) -> str:
        cmd = ["git", "diff", f"-U{context}"]
        if staged:
            cmd.append("--staged")
        if path:
            resolved = (self._project_root / path).resolve()
            if not str(resolved).startswith(str(self._project_root)):
                return f"Error: path '{path}' is outside project root."
            cmd.append(path)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self._project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        except asyncio.TimeoutError:
            return "Error: git diff timed out after 15s."
        except OSError as e:
            return f"Error running git diff: {e}"

        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        if err:
            return f"git diff error: {err}"
        return out or "(no changes)"
