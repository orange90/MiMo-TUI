"""Model capability table and heuristic matching.

Lookups are case-insensitive so that server-provided ids (e.g. ``mimo-v2.5-pro``)
and historical config values (e.g. ``MiMo-V2.5-Pro``) both resolve to the same
capabilities entry.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelCapabilities:
    reasoning: bool = False
    vision: bool = False
    audio_out: bool = False
    tools: bool = False
    context_window: int = 32768

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


_TABLE_RAW: dict[str, ModelCapabilities] = {
    "MiMo-V2.5-Pro": ModelCapabilities(reasoning=True, tools=True, context_window=128_000),
    "MiMo-V2.5": ModelCapabilities(reasoning=True, tools=True, context_window=128_000),
    "MiMo-V2-Pro": ModelCapabilities(reasoning=True, tools=True, context_window=128_000),
    "MiMo-V2-Omni": ModelCapabilities(reasoning=True, vision=True, audio_out=True, tools=True, context_window=128_000),
    "MiMo-V2.5-TTS-VoiceClone": ModelCapabilities(audio_out=True, context_window=8_192),
    "MiMo-V2.5-TTS-VoiceDesign": ModelCapabilities(audio_out=True, context_window=8_192),
    "MiMo-V2.5-TTS": ModelCapabilities(audio_out=True, context_window=8_192),
    "MiMo-V2-TTS": ModelCapabilities(audio_out=True, context_window=8_192),
}

_TABLE: dict[str, ModelCapabilities] = {k.lower(): v for k, v in _TABLE_RAW.items()}

_HEURISTIC_PREFIXES_RAW: list[tuple[str, ModelCapabilities]] = [
    ("MiMo-V2.5-TTS", ModelCapabilities(audio_out=True, context_window=8_192)),
    ("MiMo-V2-TTS", ModelCapabilities(audio_out=True, context_window=8_192)),
    ("MiMo-V2-Omni", ModelCapabilities(reasoning=True, vision=True, audio_out=True, tools=True, context_window=128_000)),
    ("MiMo-V2.5", ModelCapabilities(reasoning=True, tools=True, context_window=128_000)),
    ("MiMo-V2", ModelCapabilities(reasoning=True, tools=True, context_window=128_000)),
    ("MiMo-7B", ModelCapabilities(reasoning=True, tools=True, context_window=32_768)),
]

_HEURISTIC_PREFIXES: list[tuple[str, ModelCapabilities]] = [
    (p.lower(), c) for p, c in _HEURISTIC_PREFIXES_RAW
]

_KNOWN_MODELS: list[str] = list(_TABLE_RAW.keys())


def get_capabilities(model_name: str) -> ModelCapabilities:
    key = (model_name or "").lower()
    if key in _TABLE:
        return _TABLE[key]
    for prefix, caps in _HEURISTIC_PREFIXES:
        if key.startswith(prefix):
            return caps
    return ModelCapabilities(tools=True)


def all_models() -> list[str]:
    return list(_KNOWN_MODELS)


def set_known_models(models: list[str]) -> None:
    """Replace the runtime list of known models (used by ModelPicker, etc.).

    Called by the CLI bootstrap after a successful ``GET /v1/models`` so that
    the rest of the app sees the live list returned by the API.
    """
    global _KNOWN_MODELS
    seen: set[str] = set()
    deduped: list[str] = []
    for m in models:
        if not m:
            continue
        key = m.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)
    if deduped:
        _KNOWN_MODELS = deduped


def is_tts_model(model_name: str) -> bool:
    caps = get_capabilities(model_name)
    return caps.audio_out and not caps.reasoning
