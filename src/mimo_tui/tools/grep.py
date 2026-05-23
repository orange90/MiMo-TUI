from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from mimo_tui.tools.base import BaseTool, ToolSpec

_HAS_RG: bool | None = None


def _has_ripgrep() -> bool:
    global _HAS_RG
    if _HAS_RG is None:
        try:
            subprocess.run(["rg", "--version"], capture_output=True, check=True)
            _HAS_RG = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            _HAS_RG = False
    return _HAS_RG


class GrepTool(BaseTool):
    spec = ToolSpec(
        name="grep",
        description="Search for a pattern in files. Uses ripgrep if available, otherwise Python re.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory or file to search", "default": "."},
                "file_pattern": {"type": "string", "description": "Glob to filter files, e.g. *.py", "default": ""},
                "context_lines": {"type": "integer", "description": "Lines of context", "default": 2},
            },
            "required": ["pattern"],
        },
        danger_level=0,
    )

    async def run(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "",
        context_lines: int = 2,
        **_: Any,
    ) -> str:
        if _has_ripgrep():
            return await self._rg(pattern, path, file_pattern, context_lines)
        return self._python_grep(pattern, path, file_pattern, context_lines)

    async def _rg(self, pattern: str, path: str, glob: str, ctx: int) -> str:
        cmd = ["rg", "--color=never", f"--context={ctx}", pattern, path]
        if glob:
            cmd += ["--glob", glob]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        return stdout.decode(errors="replace")[:50_000] or "No matches"

    def _python_grep(self, pattern: str, path: str, glob: str, ctx: int) -> str:
        import re
        base = Path(path)
        file_glob = glob or "**/*"
        results: list[str] = []
        try:
            rx = re.compile(pattern)
        except re.error as e:
            return f"Invalid regex: {e}"
        for fp in sorted(base.glob(file_glob)):
            if not fp.is_file():
                continue
            try:
                lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines):
                if rx.search(line):
                    start = max(0, i - ctx)
                    end = min(len(lines), i + ctx + 1)
                    block = "\n".join(
                        f"{fp}:{j+1}:{'>' if j==i else ' '} {lines[j]}"
                        for j in range(start, end)
                    )
                    results.append(block)
                    if len(results) >= 200:
                        break
        return "\n---\n".join(results) if results else "No matches"
