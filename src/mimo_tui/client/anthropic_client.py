"""Anthropic-SDK client pointing at MiMo's /anthropic endpoint."""
from __future__ import annotations

from typing import AsyncGenerator, Any

from mimo_tui.client.schemas import (
    ChatRequest,
    ContentDelta,
    Delta,
    DoneDelta,
    ReasoningDelta,
    ToolCallDelta,
    UsageDelta,
)
from mimo_tui.config.schema import AppConfig
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)


def _to_anthropic_messages(request: ChatRequest) -> tuple[list[dict[str, Any]], str]:
    """Convert internal ChatRequest messages to Anthropic format.

    Returns (messages_list, system_prompt).
    """
    system = ""
    messages: list[dict[str, Any]] = []
    for msg in request.messages:
        if msg.role == "system":
            system = msg.content if isinstance(msg.content, str) else ""
            continue
        if msg.role == "tool":
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id or "",
                    "content": msg.content if isinstance(msg.content, str) else "",
                }],
            })
        else:
            if isinstance(msg.content, str):
                content: Any = msg.content
            else:
                content = [
                    {"type": c.type, **({"text": c.text} if hasattr(c, "text") else {})}
                    for c in msg.content
                ]
            messages.append({"role": msg.role, "content": content})
    return messages, system


def _to_anthropic_tools(request: ChatRequest) -> list[dict[str, Any]]:
    if not request.tools:
        return []
    return [
        {
            "name": t.function.name,
            "description": t.function.description,
            "input_schema": t.function.parameters,
        }
        for t in request.tools
    ]


class AnthropicClient:
    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        import anthropic  # lazy import — optional dep path
        self._client = anthropic.AsyncAnthropic(
            api_key=cfg.endpoint.api_key,
            base_url=cfg.endpoint.anthropic_url,
        )

    async def stream(self, request: ChatRequest) -> AsyncGenerator[Delta, None]:
        messages, system = _to_anthropic_messages(request)
        tools = _to_anthropic_tools(request)

        kwargs: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        # Enable extended thinking for reasoning models
        if self._cfg.model.reasoning:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": min(request.max_tokens // 2, 4096),
            }

        log.debug("anthropic stream", model=request.model, n_messages=len(messages))

        async with self._client.messages.stream(**kwargs) as stream:
            tool_index = 0
            async for event in stream:
                event_type = type(event).__name__

                if event_type == "ContentBlockStartEvent":
                    block = event.content_block
                    if block.type == "thinking":
                        pass  # text flows via delta
                    elif block.type == "tool_use":
                        yield ToolCallDelta(
                            index=tool_index,
                            id=block.id,
                            name=block.name,
                        )
                        tool_index += 1

                elif event_type == "ContentBlockDeltaEvent":
                    delta = event.delta
                    if delta.type == "thinking_delta":
                        yield ReasoningDelta(text=delta.thinking)
                    elif delta.type == "text_delta":
                        yield ContentDelta(text=delta.text)
                    elif delta.type == "input_json_delta":
                        yield ToolCallDelta(
                            index=tool_index - 1,
                            args_fragment=delta.partial_json,
                        )

                elif event_type == "ContentBlockStopEvent":
                    pass

                elif event_type == "MessageDeltaEvent":
                    if hasattr(event, "usage"):
                        yield UsageDelta(
                            completion_tokens=getattr(event.usage, "output_tokens", 0),
                        )
                    stop = getattr(event.delta, "stop_reason", None)
                    if stop:
                        if tool_index > 0:
                            for i in range(tool_index):
                                yield ToolCallDelta(index=i, finished=True)
                        yield DoneDelta(stop_reason=stop)

    async def aclose(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AnthropicClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
