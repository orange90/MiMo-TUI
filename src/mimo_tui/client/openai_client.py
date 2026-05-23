"""OpenAI-compatible streaming client for the MiMo API."""
from __future__ import annotations

from typing import AsyncGenerator

import httpx

from mimo_tui.client.errors import MimoAPIError
from mimo_tui.client.schemas import ChatRequest, Delta
from mimo_tui.client.sse import parse_sse_stream
from mimo_tui.config.schema import AppConfig
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)


class OpenAIClient:
    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._base_url = cfg.endpoint.url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {cfg.endpoint.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(cfg.endpoint.timeout_s, connect=10.0),
            http2=True,
        )

    async def stream(self, request: ChatRequest) -> AsyncGenerator[Delta, None]:
        payload = request.model_dump(exclude_none=True)
        log.debug("openai stream", model=request.model, n_messages=len(request.messages))

        async with self._client.stream(
            "POST",
            "/chat/completions",
            json=payload,
        ) as resp:
            if resp.status_code >= 400:
                body = await resp.aread()
                raise MimoAPIError(resp.status_code, body.decode())
            async for delta in parse_sse_stream(resp):
                yield delta

    async def list_models(self) -> list[str]:
        resp = await self._client.get("/models")
        if resp.status_code >= 400:
            raise MimoAPIError(resp.status_code, resp.text)
        data = resp.json()
        return [m["id"] for m in data.get("data", [])]

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "OpenAIClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
