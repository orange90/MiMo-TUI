from __future__ import annotations

import asyncio
import shlex
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec


class ShellExecTool(BaseTool):
    spec = ToolSpec(
        name="shell_exec",
        description=(
            "Run a shell command. Only commands in the allowlist are permitted. "
            "Returns stdout + stderr."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run"},
                "cwd": {"type": "string", "description": "Working directory", "default": "."},
            },
            "required": ["command"],
        },
        danger_level=2,
    )

    def __init__(
        self,
        allowlist: list[str] | None = None,
        write_paths: list[str] | None = None,
        project_root: str = ".",
        timeout_s: int = 60,
    ) -> None:
        self._allowlist = set(allowlist or [])
        self._write_paths = write_paths or ["."]
        self._project_root = Path(project_root).resolve()
        self._timeout = timeout_s

    async def run(self, command: str, cwd: str = ".", **_: Any) -> str:
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return f"Error: invalid command syntax: {e}"
        if not parts:
            return "Error: empty command"
        binary = parts[0]
        if self._allowlist and binary not in self._allowlist:
            return (
                f"Error: '{binary}' is not in the shell allowlist. "
                f"Allowed: {', '.join(sorted(self._allowlist))}"
            )

        cwd_path = (self._project_root / cwd).resolve()
        if not str(cwd_path).startswith(str(self._project_root)):
            return f"Error: cwd {cwd_path} is outside project root"

        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                cwd=str(cwd_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout
            )
        except asyncio.TimeoutError:
            return f"Error: command timed out after {self._timeout}s"
        except OSError as e:
            return f"Error: {e}"

        out = stdout.decode(errors="replace")
        err = stderr.decode(errors="replace")
        combined = out + (f"\nSTDERR:\n{err}" if err else "")
        return combined[:50_000] or f"(exit {proc.returncode})"
