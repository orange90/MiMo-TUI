"""Python exec tool — run Python code snippets in a subprocess."""
from __future__ import annotations

import asyncio
import contextlib
import sys
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec


class PythonExecTool(BaseTool):
    spec = ToolSpec(
        name="python_exec",
        description=(
            "Execute a Python code snippet and return stdout + stderr. "
            "Runs in a subprocess with a timeout. Useful for calculations, "
            "data processing, and quick prototyping."
        ),
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 30)",
                    "default": 30,
                },
            },
            "required": ["code"],
        },
        danger_level=1,
    )

    def __init__(self, project_root: str = ".") -> None:
        self._project_root = Path(project_root).resolve()
        self._python = sys.executable

    async def run(self, **kwargs: Any) -> str:
        code = kwargs.get("code", "")
        if not code.strip():
            return "Error: code is required."

        timeout = kwargs.get("timeout", 30)
        if timeout < 1 or timeout > 120:
            timeout = 30

        try:
            proc = await asyncio.create_subprocess_exec(
                self._python, "-c", code,
                cwd=str(self._project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            return f"Error: execution timed out after {timeout}s."
        except OSError as e:
            return f"Error: {e}"

        out = stdout.decode(errors="replace")
        err = stderr.decode(errors="replace")

        parts: list[str] = []
        if out:
            parts.append(out.rstrip())
        if err:
            parts.append(f"STDERR:\n{err.rstrip()}")

        result = "\n".join(parts) if parts else f"(exit code {proc.returncode})"
        return result[:50_000]
