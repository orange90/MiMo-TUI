from __future__ import annotations

from typing import Any

import httpx

from mimo_tui.tools.base import BaseTool, ToolSpec


class WebFetchTool(BaseTool):
    spec = ToolSpec(
        name="web_fetch",
        description="Fetch a URL and return its text content (HTML stripped to plain text).",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_chars": {"type": "integer", "description": "Max characters to return", "default": 20000},
            },
            "required": ["url"],
        },
        danger_level=0,
    )

    async def run(self, url: str, max_chars: int = 20_000, **_: Any) -> str:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "MiMo-TUI/0.1"})
                text = resp.text
        except Exception as e:
            return f"Error fetching {url}: {e}"
        # strip HTML tags naively
        import re
        plain = re.sub(r"<[^>]+>", "", text)
        plain = re.sub(r"\s{3,}", "\n\n", plain)
        return plain[:max_chars]
