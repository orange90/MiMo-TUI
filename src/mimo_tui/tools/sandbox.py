from __future__ import annotations

from pathlib import Path


class SandboxViolation(Exception):
    pass


def check_path_allowed(path: str | Path, write_paths: list[str], project_root: str) -> None:
    resolved = Path(path).resolve()
    root = Path(project_root).resolve()
    allowed = [Path(p).resolve() for p in write_paths] + [root]
    if not any(str(resolved).startswith(str(a)) for a in allowed):
        raise SandboxViolation(f"Path {resolved} is outside allowed write paths")
