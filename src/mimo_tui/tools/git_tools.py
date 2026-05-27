"""Git tools — status, log, diff as independent read-only tools."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec


async def _run_git(args: list[str], cwd: str, timeout: int = 15) -> str:
    """Run a git command and return stdout or an error string."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        return f"Error: git {' '.join(args)} timed out after {timeout}s."
    except OSError as e:
        return f"Error running git: {e}"

    out = stdout.decode(errors="replace").strip()
    err = stderr.decode(errors="replace").strip()
    if proc.returncode != 0 and err:
        return f"git error: {err}"
    return out or "(no output)"


class GitStatusTool(BaseTool):
    spec = ToolSpec(
        name="git_status",
        description="Show working tree status (short format). Equivalent to 'git status --short'.",
        parameters={
            "type": "object",
            "properties": {},
        },
        danger_level=0,
    )

    def __init__(self, project_root: str = ".") -> None:
        self._project_root = str(Path(project_root).resolve())

    async def run(self, **kwargs: Any) -> str:
        return await _run_git(["status", "--short"], self._project_root)


class GitLogTool(BaseTool):
    spec = ToolSpec(
        name="git_log",
        description="Show recent commit history. Returns one-line per commit.",
        parameters={
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "description": "Number of commits to show (default 10)",
                    "default": 10,
                },
                "path": {
                    "type": "string",
                    "description": "Limit to commits touching this path",
                },
            },
        },
        danger_level=0,
    )

    def __init__(self, project_root: str = ".") -> None:
        self._project_root = str(Path(project_root).resolve())

    async def run(self, **kwargs: Any) -> str:
        n = kwargs.get("n", 10)
        path = kwargs.get("path", "")
        args = ["log", "--oneline", f"-{n}"]
        if path:
            args.append(path)
        return await _run_git(args, self._project_root)


class GitDiffTool(BaseTool):
    spec = ToolSpec(
        name="git_diff",
        description="Show git diff for working tree or staged changes.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Limit diff to this file or directory",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes (--cached)",
                    "default": False,
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines around changes",
                    "default": 3,
                },
            },
        },
        danger_level=0,
    )

    def __init__(self, project_root: str = ".") -> None:
        self._project_root = str(Path(project_root).resolve())

    async def run(self, **kwargs: Any) -> str:
        staged = kwargs.get("staged", False)
        path = kwargs.get("path", "")
        context = kwargs.get("context_lines", 3)

        args = ["diff", f"-U{context}"]
        if staged:
            args.append("--staged")
        if path:
            args.append(path)
        return await _run_git(args, self._project_root)
