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
        self._context_window = 0

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
        context_window: int = 0,
        reset_tokens: bool = False,
    ) -> None:
        if model:
            self._model = model
        if mode:
            self._mode = mode
        if reset_tokens:
            self._prompt_tokens = 0
            self._completion_tokens = 0
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
        if context_window:
            self._context_window = context_window
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
        ctx_used = self._prompt_tokens + self._completion_tokens
        if ctx_used > 0 and self._context_window > 0:
            pct = min(100, int((ctx_used / self._context_window) * 100))
            color = "#9ece6a" if pct < 60 else "#e0af68" if pct < 85 else "#f7768e"
            right_parts.append(
                f"[{color}]ctx {pct}%[/] [dim]({_fmt_tok(ctx_used)}/{_fmt_tok(self._context_window)})[/]"
            )
        elif ctx_used > 0:
            right_parts.append(f"ctx {_fmt_tok(ctx_used)}")
        if self._latency_ms:
            right_parts.append(f"{self._latency_ms:.0f}ms")
        right_parts.append(self._lang)

        try:
            self.query_one("#sb-left", Static).update(left)
            self.query_one("#sb-right", Static).update(" [dim]·[/] ".join(right_parts))
        except Exception:
            pass


def _fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)
