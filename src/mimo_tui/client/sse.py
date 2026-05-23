"""SSE stream → typed deltas (OpenAI wire format)."""
from __future__ import annotations

import json
from collections import defaultdict
from typing import AsyncGenerator

import httpx

from mimo_tui.client.schemas import (
    AudioDelta,
    ContentDelta,
    Delta,
    DoneDelta,
    ReasoningDelta,
    ToolCallDelta,
    UsageDelta,
)
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)

_DONE_SENTINEL = "[DONE]"


async def parse_sse_stream(
    response: httpx.Response,
) -> AsyncGenerator[Delta, None]:
    """Parse an OpenAI-compatible SSE response into typed Delta objects."""
    tool_arg_buffers: dict[int, str] = defaultdict(str)
    tool_finished: set[int] = set()

    async for line in response.aiter_lines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == _DONE_SENTINEL:
            yield DoneDelta()
            return

        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            log.debug("sse: could not parse json", payload=payload[:100])
            continue

        # usage-only chunk (no choices)
        if "usage" in obj and not obj.get("choices"):
            u = obj["usage"]
            yield UsageDelta(
                prompt_tokens=u.get("prompt_tokens", 0),
                completion_tokens=u.get("completion_tokens", 0),
            )
            continue

        choices = obj.get("choices", [])
        if not choices:
            continue

        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")

        # reasoning content (MiMo extension)
        rc = delta.get("reasoning_content")
        if rc:
            yield ReasoningDelta(text=rc)

        # text content
        content = delta.get("content")
        if content:
            yield ContentDelta(text=content)

        # audio (TTS models return audio field)
        audio = delta.get("audio")
        if audio:
            import base64
            raw_b64 = audio.get("data", "")
            if raw_b64:
                yield AudioDelta(
                    data=base64.b64decode(raw_b64),
                    mime_type=audio.get("mime_type", "audio/wav"),
                    finished=bool(finish_reason),
                )

        # tool calls
        tool_calls = delta.get("tool_calls", [])
        for tc in tool_calls:
            idx = tc.get("index", 0)
            tc_id = tc.get("id")
            fn = tc.get("function", {})
            name = fn.get("name")
            args_frag = fn.get("arguments", "")

            tool_arg_buffers[idx] += args_frag

            yield ToolCallDelta(
                index=idx,
                id=tc_id,
                name=name,
                args_fragment=args_frag,
                finished=False,
            )

        # signal completion of buffered tool calls
        if finish_reason in ("tool_calls", "stop") and tool_arg_buffers:
            for idx in list(tool_arg_buffers.keys()):
                if idx not in tool_finished:
                    tool_finished.add(idx)
                    yield ToolCallDelta(index=idx, finished=True)

        # usage on final chunk
        if "usage" in obj:
            u = obj["usage"]
            yield UsageDelta(
                prompt_tokens=u.get("prompt_tokens", 0),
                completion_tokens=u.get("completion_tokens", 0),
            )

        if finish_reason:
            yield DoneDelta(stop_reason=finish_reason or "stop")
