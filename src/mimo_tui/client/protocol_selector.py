"""Choose OpenAI or Anthropic client based on config and model capabilities."""
from __future__ import annotations

from typing import Union

from mimo_tui.client.anthropic_client import AnthropicClient
from mimo_tui.client.openai_client import OpenAIClient
from mimo_tui.config.schema import AppConfig

AnyClient = Union[OpenAIClient, AnthropicClient]


def get_client(cfg: AppConfig) -> AnyClient:
    if cfg.protocol == "anthropic":
        return AnthropicClient(cfg)
    return OpenAIClient(cfg)
