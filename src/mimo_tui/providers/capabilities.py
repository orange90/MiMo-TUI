"""Model capability table and heuristic matching."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelCapabilities:
    reasoning: bool = False
    vision: bool = False
    audio_out: bool = False
    tools: bool = False

    def badge_str(self) -> str:
        badges = []
        if self.reasoning:
            badges.append("think")
        if self.vision:
            badges.append("vision")
        if self.audio_out:
            badges.append("tts")
        if self.tools:
            badges.append("tools")
        return " ".join(f"[{b}]" for b in badges)


_TABLE: dict[str, ModelCapabilities] = {
    "MiMo-V2.5-Pro": ModelCapabilities(reasoning=True, tools=True),
    "MiMo-V2.5": ModelCapabilities(reasoning=True, tools=True),
    "MiMo-V2-Pro": ModelCapabilities(reasoning=True, tools=True),
    "MiMo-V2-Omni": ModelCapabilities(reasoning=True, vision=True, audio_out=True, tools=True),
    "MiMo-V2.5-TTS-VoiceClone": ModelCapabilities(audio_out=True),
    "MiMo-V2.5-TTS-VoiceDesign": ModelCapabilities(audio_out=True),
    "MiMo-V2.5-TTS": ModelCapabilities(audio_out=True),
    "MiMo-V2-TTS": ModelCapabilities(audio_out=True),
}

_HEURISTIC_PREFIXES: list[tuple[str, ModelCapabilities]] = [
    ("MiMo-V2.5-TTS", ModelCapabilities(audio_out=True)),
    ("MiMo-V2-TTS", ModelCapabilities(audio_out=True)),
    ("MiMo-V2-Omni", ModelCapabilities(reasoning=True, vision=True, audio_out=True, tools=True)),
    ("MiMo-V2.5", ModelCapabilities(reasoning=True, tools=True)),
    ("MiMo-V2", ModelCapabilities(reasoning=True, tools=True)),
    ("MiMo-7B", ModelCapabilities(reasoning=True, tools=True)),
]

_KNOWN_MODELS: list[str] = list(_TABLE.keys())


def get_capabilities(model_name: str) -> ModelCapabilities:
    if model_name in _TABLE:
        return _TABLE[model_name]
    for prefix, caps in _HEURISTIC_PREFIXES:
        if model_name.startswith(prefix):
            return caps
    return ModelCapabilities(tools=True)


def all_models() -> list[str]:
    return _KNOWN_MODELS


def is_tts_model(model_name: str) -> bool:
    return get_capabilities(model_name).audio_out and not get_capabilities(model_name).reasoning
