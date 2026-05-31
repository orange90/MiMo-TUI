from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, Field, model_validator


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: dict[str, str]


MessageContent = Union[str, list[Union[TextContent, ImageContent]]]


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: MessageContent = ""
    tool_call_id: str | None = None
    name: str | None = None


class FunctionDef(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionDef


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    tools: list[Tool] | None = None
    stream: bool = True
    max_tokens: int = 8192
    temperature: float = 0.6

    @model_validator(mode="before")
    @classmethod
    def normalize_model_name(cls, data: dict[str, Any]) -> dict[str, Any]:
        if isinstance(data, dict) and "model" in data:
            data["model"] = data["model"].lower()
        return data


# ── Typed deltas emitted by the SSE parser ──

class ContentDelta(BaseModel):
    type: Literal["content"] = "content"
    text: str


class ReasoningDelta(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    text: str


class ToolCallDelta(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    index: int
    id: str | None = None
    name: str | None = None
    args_fragment: str = ""
    finished: bool = False


class AudioDelta(BaseModel):
    type: Literal["audio"] = "audio"
    data: bytes
    mime_type: str = "audio/wav"
    finished: bool = False


class UsageDelta(BaseModel):
    type: Literal["usage"] = "usage"
    prompt_tokens: int = 0
    completion_tokens: int = 0


class DoneDelta(BaseModel):
    type: Literal["done"] = "done"
    stop_reason: str = "stop"


Delta = Union[
    ContentDelta,
    ReasoningDelta,
    ToolCallDelta,
    AudioDelta,
    UsageDelta,
    DoneDelta,
]


class ToolCallSpec(BaseModel):
    id: str
    name: str
    arguments: str
    index: int = 0


class AssistantMessage(BaseModel):
    content: str = ""
    reasoning: str = ""
    tool_calls: list[ToolCallSpec] = Field(default_factory=list)
    usage: UsageDelta = Field(default_factory=UsageDelta)
    stop_reason: str = "stop"
