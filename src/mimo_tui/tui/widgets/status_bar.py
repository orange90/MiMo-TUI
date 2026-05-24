"""Bottom status bar — Claude Code style with mode and cost display."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class StatusBar(Horizontal):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #16213e;
        padding: 0 1;
    }
    StatusBar #sb-left {
        width: 1fr;
        color: #565f89;
        content-align: left middle;
    }
    StatusBar #sb-right {
        width: auto;
        color: #565f89;
        content-align: right middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._model = ""
        self._mode = "agent"
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._latency_ms = 0.0
        self._endpoint = ""
        self._lang = "en"
        self._audio_playing = False
        self._cache_pct = 0

    def compose(self) -> ComposeResult:
        yield Static("", id="sb-left")
        yield Static("", id="sb-right")

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
        self._render_bar()

    def set_audio_playing(self, playing: bool) -> None:
        self._audio_playing = playing
        self._render_bar()

    def _render_bar(self) -> None:
        model_short = self._model.split("/")[-1] if self._model else "mimo"
        left_parts = [self._mode, model_short]
        if self._audio_playing:
            left_parts.append("playing")
        left = " [dim]·[/] ".join(left_parts)

        right_parts: list[str] = []
        if self._prompt_tokens or self._completion_tokens:
            total = self._prompt_tokens + self._completion_tokens
            if total > 0 and self._prompt_tokens > 0:
                self._cache_pct = min(99, int((self._prompt_tokens / (total + 1)) * 100))
            right_parts.append(f"cache {self._cache_pct}%")
        if self._latency_ms:
            right_parts.append(f"{self._latency_ms:.0f}ms")
        right_parts.append(self._lang)

        try:
            self.query_one("#sb-left", Static).update(left)
            self.query_one("#sb-right", Static).update(" [dim]·[/] ".join(right_parts))
        except Exception:
            pass
