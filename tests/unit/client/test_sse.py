"""Tests for the SSE stream parser."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
import httpx

from mimo_tui.client.schemas import ContentDelta, DoneDelta, ReasoningDelta, ToolCallDelta, UsageDelta
from mimo_tui.client.sse import parse_sse_stream


def _make_response(lines: list[str]) -> httpx.Response:
    body = "\n".join(lines) + "\n"

    async def _aiter_lines():
        for line in lines:
            yield line

    resp = MagicMock(spec=httpx.Response)
    resp.aiter_lines = _aiter_lines
    return resp


@pytest.mark.asyncio
async def test_content_delta() -> None:
    chunk = {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}]}
    resp = _make_response([f"data: {json.dumps(chunk)}", "data: [DONE]"])
    deltas = [d async for d in parse_sse_stream(resp)]
    assert any(isinstance(d, ContentDelta) and d.text == "Hello" for d in deltas)
    assert any(isinstance(d, DoneDelta) for d in deltas)


@pytest.mark.asyncio
async def test_reasoning_delta() -> None:
    chunk = {"choices": [{"delta": {"reasoning_content": "Let me think"}, "finish_reason": None}]}
    resp = _make_response([f"data: {json.dumps(chunk)}", "data: [DONE]"])
    deltas = [d async for d in parse_sse_stream(resp)]
    assert any(isinstance(d, ReasoningDelta) and d.text == "Let me think" for d in deltas)


@pytest.mark.asyncio
async def test_usage_delta() -> None:
    chunk = {
        "choices": [{"delta": {}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    }
    resp = _make_response([f"data: {json.dumps(chunk)}", "data: [DONE]"])
    deltas = [d async for d in parse_sse_stream(resp)]
    usage = [d for d in deltas if isinstance(d, UsageDelta)]
    assert usage
    assert usage[0].prompt_tokens == 10


@pytest.mark.asyncio
async def test_tool_call_delta() -> None:
    chunk1 = {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "tc1", "function": {"name": "read_file", "arguments": ""}}]}, "finish_reason": None}]}
    chunk2 = {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"path":'}}]}, "finish_reason": None}]}
    chunk3 = {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '"foo.py"}'}}]}, "finish_reason": "tool_calls"}]}
    resp = _make_response([
        f"data: {json.dumps(chunk1)}",
        f"data: {json.dumps(chunk2)}",
        f"data: {json.dumps(chunk3)}",
        "data: [DONE]",
    ])
    deltas = [d async for d in parse_sse_stream(resp)]
    tc_deltas = [d for d in deltas if isinstance(d, ToolCallDelta)]
    assert any(d.name == "read_file" for d in tc_deltas)
    assert any(d.finished for d in tc_deltas)


@pytest.mark.asyncio
async def test_skip_non_data_lines() -> None:
    resp = _make_response(["", ": keep-alive", "data: [DONE]"])
    deltas = [d async for d in parse_sse_stream(resp)]
    assert any(isinstance(d, DoneDelta) for d in deltas)


@pytest.mark.asyncio
async def test_explicit_null_fields_do_not_crash() -> None:
    """Regression: some upstream servers emit explicit nulls instead of omitting fields.

    Iterating ``None`` previously raised ``TypeError: 'NoneType' object is not iterable``.
    """
    chunk = {
        "choices": [
            {
                "delta": {
                    "content": "hi",
                    "tool_calls": None,
                    "audio": None,
                    "reasoning_content": None,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": None,
    }
    resp = _make_response([f"data: {json.dumps(chunk)}", "data: [DONE]"])
    deltas = [d async for d in parse_sse_stream(resp)]
    assert any(isinstance(d, ContentDelta) and d.text == "hi" for d in deltas)
    assert any(isinstance(d, DoneDelta) for d in deltas)


@pytest.mark.asyncio
async def test_null_choices_does_not_crash() -> None:
    """Regression: ``choices: null`` must not crash the parser."""
    chunk = {"choices": None, "usage": {"prompt_tokens": 1, "completion_tokens": 2}}
    resp = _make_response([f"data: {json.dumps(chunk)}", "data: [DONE]"])
    deltas = [d async for d in parse_sse_stream(resp)]
    assert any(isinstance(d, UsageDelta) for d in deltas)
