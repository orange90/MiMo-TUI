"""Tests for the agent loop with mocked streaming."""
from __future__ import annotations

from typing import AsyncGenerator
import pytest

from mimo_tui.agent.loop import AgentLoop, DoneEvent, TextEvent
from mimo_tui.agent.modes import AgentMode
from mimo_tui.agent.registry import ToolRegistry
from mimo_tui.client.schemas import ContentDelta, Delta, DoneDelta


class MockClient:
    async def stream(self, request: object) -> AsyncGenerator[Delta, None]:
        yield ContentDelta(text="Hello")
        yield ContentDelta(text=" world")
        yield DoneDelta(stop_reason="stop")


@pytest.mark.asyncio
async def test_basic_chat(test_cfg) -> None:
    client = MockClient()
    registry = ToolRegistry()
    loop = AgentLoop(cfg=test_cfg, client=client, registry=registry, mode=AgentMode.CHAT)

    events = [e async for e in loop.run("hi")]
    text_events = [e for e in events if isinstance(e, TextEvent)]
    done_events = [e for e in events if isinstance(e, DoneEvent)]

    assert text_events[0].text == "Hello"
    assert done_events


@pytest.mark.asyncio
async def test_history_accumulates(test_cfg) -> None:
    client = MockClient()
    registry = ToolRegistry()
    loop = AgentLoop(cfg=test_cfg, client=client, registry=registry, mode=AgentMode.CHAT)

    _ = [e async for e in loop.run("first message")]
    assert len(loop._history) >= 2  # user + assistant


@pytest.mark.asyncio
async def test_reset_clears_history(test_cfg) -> None:
    client = MockClient()
    registry = ToolRegistry()
    loop = AgentLoop(cfg=test_cfg, client=client, registry=registry, mode=AgentMode.CHAT)
    _ = [e async for e in loop.run("test")]
    loop.reset()
    assert loop._history == []
