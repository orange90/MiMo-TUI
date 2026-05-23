"""Probe for local self-hosted inference engines."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

_PROBE_PORTS = [
    (11434, "ollama", "/api/tags"),
    (8000, "vllm", "/v1/models"),
    (9001, "sglang", "/v1/models"),
    (30000, "sglang", "/v1/models"),
]


@dataclass
class LocalEndpoint:
    engine: str
    url: str
    models: list[str]


async def _probe(port: int, engine: str, path: str) -> LocalEndpoint | None:
    url = f"http://localhost:{port}"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{url}{path}")
            if resp.status_code == 200:
                data = resp.json()
                models: list[str] = []
                if engine == "ollama":
                    models = [m["name"] for m in data.get("models", [])]
                else:
                    models = [m["id"] for m in data.get("data", [])]
                return LocalEndpoint(engine=engine, url=f"{url}/v1", models=models)
    except Exception:
        pass
    return None


async def detect_local_endpoints() -> list[LocalEndpoint]:
    tasks = [_probe(port, engine, path) for port, engine, path in _PROBE_PORTS]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
