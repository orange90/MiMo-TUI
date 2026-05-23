from __future__ import annotations

from typing import Any

from mimo_tui.config.schema import AppConfig
from mimo_tui.tools.base import BaseTool, ToolSpec
from mimo_tui.tools.edit_file import EditFileTool
from mimo_tui.tools.glob import GlobTool
from mimo_tui.tools.grep import GrepTool
from mimo_tui.tools.read_file import ReadFileTool
from mimo_tui.tools.shell_exec import ShellExecTool
from mimo_tui.tools.todo_write import TodoWriteTool
from mimo_tui.tools.web_fetch import WebFetchTool
from mimo_tui.tools.write_file import WriteFileTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def to_api_tools(self) -> list[dict[str, Any]]:
        return [t.to_api_tool() for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools.keys())


def build_registry(cfg: AppConfig) -> ToolRegistry:
    reg = ToolRegistry()
    wp = cfg.sandbox.write_paths
    root = cfg.sandbox.project_root
    allow = cfg.sandbox.shell_allowlist
    timeout = cfg.sandbox.shell_timeout_s

    reg.register(ReadFileTool())
    reg.register(WriteFileTool(write_paths=wp, project_root=root))
    reg.register(EditFileTool(write_paths=wp, project_root=root))
    reg.register(GlobTool())
    reg.register(GrepTool())
    reg.register(ShellExecTool(allowlist=allow, write_paths=wp, project_root=root, timeout_s=timeout))
    reg.register(WebFetchTool())
    reg.register(TodoWriteTool())
    return reg
