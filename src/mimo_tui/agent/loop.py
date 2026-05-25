"""Core agent loop — yields typed UI events from a streaming conversation."""
from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from mimo_tui.agent.approval import ApprovalCallback, ApprovalRequest, auto_approve
from mimo_tui.agent.modes import AgentMode
from mimo_tui.agent.prompts import get_system_prompt
from mimo_tui.agent.registry import ToolRegistry
from mimo_tui.client.protocol_selector import AnyClient
from mimo_tui.client.schemas import (
    AudioDelta,
    ChatRequest,
    ContentDelta,
    DoneDelta,
    Message,
    ReasoningDelta,
    Tool,
    ToolCallDelta,
    ToolCallSpec,
    UsageDelta,
)
from mimo_tui.config.schema import AppConfig
from mimo_tui.constants import AGENT_MAX_ITERATIONS
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)


# ── UI events ──

@dataclass
class TextEvent:
    text: str
    role: str = "assistant"


@dataclass
class ReasoningEvent:
    text: str


@dataclass
class AudioEvent:
    data: bytes
    mime_type: str
    finished: bool = False


@dataclass
class ToolCallStartEvent:
    call_id: str
    tool_name: str
    index: int


@dataclass
class ToolCallArgFragEvent:
    index: int
    fragment: str


@dataclass
class ToolCallResultEvent:
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: str
    approved: bool


@dataclass
class UsageEvent:
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


@dataclass
class ErrorEvent:
    message: str


@dataclass
class DoneEvent:
    stop_reason: str = "stop"


AgentEvent = (
    TextEvent
    | ReasoningEvent
    | AudioEvent
    | ToolCallStartEvent
    | ToolCallArgFragEvent
    | ToolCallResultEvent
    | UsageEvent
    | ErrorEvent
    | DoneEvent
)


class AgentLoop:
    def __init__(
        self,
        cfg: AppConfig,
        client: AnyClient,
        registry: ToolRegistry,
        mode: AgentMode = AgentMode.AGENT,
        approval_cb: ApprovalCallback | None = None,
    ) -> None:
        self._cfg = cfg
        self._client = client
        self._registry = registry
        self._mode = mode
        self._approval_cb = approval_cb or auto_approve
        self._history: list[Message] = []
        self._pending_call_ids: dict[int, str] = {}  # index → call_id

    def reset(self) -> None:
        self._history.clear()

    def load_history(self, messages: list[Message]) -> None:
        self._history = list(messages)

    def history_size(self) -> int:
        return len(self._history)

    async def compact(self, focus: str = "") -> str:
        """Summarize current history via the model, then replace history with the recap.

        Returns the summary text. Raises if there is nothing to compact or the
        model fails to respond.
        """
        if not self._history:
            return ""

        focus_line = (
            f"Focus areas requested by the user: {focus}\n" if focus else ""
        )
        instruction = (
            "Produce a concise structured recap of the conversation above so "
            "we can continue in a fresh context window. Cover: (1) user goal "
            "and key decisions, (2) facts discovered or established, (3) work "
            "completed, (4) work still pending or open questions. Be specific "
            "with file paths, identifiers, numbers, and API names — do not "
            "invent details. Keep under ~400 words.\n" + focus_line
        )

        req = ChatRequest(
            model=self._cfg.model.name,
            messages=(
                [Message(role="system", content="You summarize conversations.")]
                + self._history
                + [Message(role="user", content=instruction)]
            ),
            tools=None,
            max_tokens=min(2048, self._cfg.model.max_tokens),
            temperature=0.3,
        )

        summary = ""
        async for delta in self._client.stream(req):
            if isinstance(delta, ContentDelta):
                summary += delta.text

        summary = summary.strip()
        if not summary:
            raise RuntimeError("compact: empty summary from model")

        recap_header = "[Compacted conversation summary]\n"
        self._history = [
            Message(role="user", content=recap_header + summary),
            Message(
                role="assistant",
                content="Got it — I have the recap and will continue from here.",
            ),
        ]
        return summary

    async def run(self, user_text: str) -> AsyncGenerator[AgentEvent, None]:
        self._history.append(Message(role="user", content=user_text))
        system = get_system_prompt(self._mode.value)

        tools_api = (
            [Tool(**t) for t in self._registry.to_api_tools()]
            if self._mode.allows_tools() and self._cfg.model.tools
            else None
        )

        for iteration in range(AGENT_MAX_ITERATIONS):
            req = ChatRequest(
                model=self._cfg.model.name,
                messages=[Message(role="system", content=system)] + self._history,
                tools=tools_api,
                max_tokens=self._cfg.model.max_tokens,
                temperature=self._cfg.model.temperature,
            )

            content_buf = ""
            reasoning_buf = ""
            audio_buf = b""
            audio_mime = "audio/wav"
            # tool_calls: index → {id, name, args_buf}
            tool_buffers: dict[int, dict[str, Any]] = defaultdict(lambda: {"id": None, "name": None, "args": ""})
            usage = UsageDelta()
            t_start = time.monotonic()

            try:
                async for delta in self._client.stream(req):
                    if isinstance(delta, ContentDelta):
                        content_buf += delta.text
                        yield TextEvent(text=delta.text)

                    elif isinstance(delta, ReasoningDelta):
                        reasoning_buf += delta.text
                        yield ReasoningEvent(text=delta.text)

                    elif isinstance(delta, AudioDelta):
                        audio_buf += delta.data
                        audio_mime = delta.mime_type
                        yield AudioEvent(data=delta.data, mime_type=delta.mime_type, finished=delta.finished)

                    elif isinstance(delta, ToolCallDelta):
                        tb = tool_buffers[delta.index]
                        if delta.id:
                            tb["id"] = delta.id
                            call_id = delta.id
                            self._pending_call_ids[delta.index] = call_id
                        if delta.name:
                            tb["name"] = delta.name
                            yield ToolCallStartEvent(
                                call_id=tb.get("id") or f"tc_{delta.index}",
                                tool_name=delta.name,
                                index=delta.index,
                            )
                        if delta.args_fragment:
                            tb["args"] += delta.args_fragment
                            yield ToolCallArgFragEvent(index=delta.index, fragment=delta.args_fragment)

                    elif isinstance(delta, UsageDelta):
                        usage = delta

                    elif isinstance(delta, DoneDelta):
                        latency = (time.monotonic() - t_start) * 1000
                        yield UsageEvent(
                            prompt_tokens=usage.prompt_tokens,
                            completion_tokens=usage.completion_tokens,
                            latency_ms=latency,
                        )

            except Exception as e:
                log.error("stream error", error=str(e))
                yield ErrorEvent(message=str(e))
                return

            # Append assistant message to history
            assembled_calls = [
                ToolCallSpec(
                    id=tb.get("id") or f"tc_{i}",
                    name=tb.get("name") or "",
                    arguments=tb["args"],
                    index=i,
                )
                for i, tb in sorted(tool_buffers.items())
                if tb.get("name")
            ]

            assistant_msg = Message(
                role="assistant",
                content=content_buf,
            )
            self._history.append(assistant_msg)

            if not assembled_calls:
                yield DoneEvent()
                return

            # Execute tool calls
            any_executed = False
            for tc in assembled_calls:
                tool = self._registry.get(tc.name)
                if tool is None:
                    result = f"Error: unknown tool '{tc.name}'"
                    approved = False
                else:
                    try:
                        args = json.loads(tc.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}

                    approved = True
                    if self._mode.requires_approval():
                        req_approval = ApprovalRequest(
                            tool_name=tc.name,
                            arguments=args,
                            danger_level=tool.spec.danger_level,
                            call_id=tc.id,
                        )
                        auto_allow_names = set(self._cfg.approval.auto_allow)
                        if tc.name not in auto_allow_names:
                            approved = await self._approval_cb(req_approval)

                    if approved:
                        try:
                            result = await tool.run(**args)
                        except Exception as e:
                            result = f"Error executing {tc.name}: {e}"
                    else:
                        result = f"Tool call '{tc.name}' was denied by user."

                yield ToolCallResultEvent(
                    call_id=tc.id,
                    tool_name=tc.name,
                    arguments=args if approved else {},
                    result=result,
                    approved=approved,
                )

                self._history.append(Message(
                    role="tool",
                    content=result,
                    tool_call_id=tc.id,
                    name=tc.name,
                ))
                any_executed = True

            if not any_executed:
                yield DoneEvent()
                return

        yield ErrorEvent(message=f"Agent loop exceeded {AGENT_MAX_ITERATIONS} iterations")
