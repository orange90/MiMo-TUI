from __future__ import annotations

import asyncio
from typing import AsyncGenerator, TypeVar

import httpx

from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)

T = TypeVar("T")

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class MimoAPIError(Exception):
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body
        super().__init__(f"API error {status}: {body[:200]}")


class MimoNetworkError(Exception):
    pass


async def with_retry(
    coro_fn: object,
    *args: object,
    max_attempts: int = 4,
    **kwargs: object,
) -> object:
    import inspect
    delays = [2, 4, 8, 16]
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            result = coro_fn(*args, **kwargs)  # type: ignore[operator]
            if inspect.isawaitable(result):
                return await result
            return result
        except MimoAPIError as e:
            if e.status not in _RETRYABLE_STATUS:
                raise
            last_exc = e
        except (httpx.NetworkError, httpx.TimeoutException) as e:
            last_exc = MimoNetworkError(str(e))
        if attempt < max_attempts - 1:
            delay = delays[attempt]
            log.warning("retrying after error", attempt=attempt + 1, delay=delay)
            await asyncio.sleep(delay)
    raise last_exc or MimoNetworkError("max retries exceeded")
