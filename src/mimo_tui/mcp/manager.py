"""MCP server manager — connects to stdio/http MCP servers and bridges their tools."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from mimo_tui.config.schema import MCPServer
from mimo_tui.tools.base import BaseTool, ToolSpec
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)


class MCPToolBridge(BaseTool):
    """Wraps an MCP server tool as a BaseTool for the agent registry."""

    def __init__(self, server_name: str, tool_name: str, schema: dict[str, Any], session: Any) -> None:
        self.spec = ToolSpec(
            name=f"mcp__{server_name}__{tool_name}",
            description=schema.get("description", ""),
            parameters=schema.get("inputSchema", {"type": "object", "properties": {}}),
            danger_level=1,
        )
        self._session = session
        self._raw_name = tool_name

    async def run(self, **kwargs: Any) -> str:
        try:
            result = await self._session.call_tool(self._raw_name, kwargs)
            return str(result.content) if hasattr(result, "content") else str(result)
        except Exception as e:
            return f"MCP tool error: {e}"


class MCPManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Any] = {}
        self._tools: list[MCPToolBridge] = []
        self._tasks: dict[str, asyncio.Task[None]] = {}

    async def start_server(self, server_cfg: MCPServer) -> None:
        if not server_cfg.enabled:
            return
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=server_cfg.command,
                args=server_cfg.args,
            )
            # Start the transport in a background task
            task = asyncio.create_task(self._run_server(server_cfg.name, params))
            self._tasks[server_cfg.name] = task
        except ImportError:
            log.warning("mcp package not installed; MCP support disabled")
        except Exception as e:
            log.error("failed to start MCP server", server=server_cfg.name, error=str(e))

    async def _run_server(self, name: str, params: Any) -> None:
        import asyncio
        backoff = 2
        while True:
            try:
                from mcp import ClientSession
                from mcp.client.stdio import stdio_client
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        self._sessions[name] = session
                        tools_resp = await session.list_tools()
                        for tool in tools_resp.tools:
                            bridge = MCPToolBridge(
                                server_name=name,
                                tool_name=tool.name,
                                schema=tool.model_dump() if hasattr(tool, "model_dump") else {},
                                session=session,
                            )
                            self._tools.append(bridge)
                            log.info("mcp tool registered", name=bridge.spec.name)
                        await asyncio.sleep(3600)  # keep alive
            except Exception as e:
                log.warning("MCP server crashed, retrying", server=name, error=str(e), backoff=backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    def get_tools(self) -> list[MCPToolBridge]:
        return list(self._tools)

    async def stop_all(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        self._sessions.clear()
        self._tools.clear()
