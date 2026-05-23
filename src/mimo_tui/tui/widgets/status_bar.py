"""Bottom status bar — model, mode, tokens, latency, endpoint, audio indicator."""
from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary-darken-2;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__("")
        self._model = ""
        self._mode = ""
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._latency_ms = 0.0
        self._endpoint = ""
        self._lang = "en"
        self._audio_playing = False

    def update_all(
        self,
        model: str = "",
        mode: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        endpoint: str = "",
        lang: str = "en",
        audio_playing: bool = False,
    ) -> None:
        if model:
            self._model = model
        if mode:
            self._mode = mode
        if prompt_tokens:
            self._prompt_tokens = prompt_tokens
        if completion_tokens:
            self._completion_tokens = completion_tokens
        if latency_ms:
            self._latency_ms = latency_ms
        if endpoint:
            self._endpoint = endpoint
        if lang:
            self._lang = lang
        self._audio_playing = audio_playing
        self._render()

    def set_audio_playing(self, playing: bool) -> None:
        self._audio_playing = playing
        self._render()

    def _render(self) -> None:
        parts: list[str] = []
        if self._model:
            parts.append(self._model)
        if self._mode:
            parts.append(f"[{self._mode}]")
        if self._prompt_tokens or self._completion_tokens:
            parts.append(f"↑{self._prompt_tokens} ↓{self._completion_tokens}")
        if self._latency_ms:
            parts.append(f"{self._latency_ms:.0f}ms")
        if self._endpoint:
            host = self._endpoint.split("/")[2] if "://" in self._endpoint else self._endpoint
            parts.append(host[:30])
        if self._lang:
            parts.append(self._lang)
        if self._audio_playing:
            parts.append("🔊")
        self.update("  ·  ".join(parts))
