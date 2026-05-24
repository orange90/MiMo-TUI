"""Top header bar — Claude Code style with Xiaomi branding."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


XIAOMI_LOGO = "小米"


class HeaderBar(Horizontal):
    DEFAULT_CSS = """
    HeaderBar {
        dock: top;
        height: 1;
        background: #1a1b2e;
        color: #7aa2f7;
        padding: 0 1;
    }
    HeaderBar #hb-left {
        width: 1fr;
        content-align: left middle;
    }
    HeaderBar #hb-right {
        width: auto;
        content-align: right middle;
        color: #565f89;
    }
    """

    def __init__(self, model: str = "", mode: str = "agent") -> None:
        super().__init__()
        self._model = model
        self._mode = mode

    def compose(self) -> ComposeResult:
        yield Static(self._build_left(), id="hb-left")
        yield Static("", id="hb-right")

    def _build_left(self) -> str:
        model_short = self._model.split("/")[-1] if self._model else "mimo"
        return f"[bold #ff6700]{XIAOMI_LOGO}[/] [bold]Agent[/]  [dim]mimo-tui[/] [dim]·[/] {model_short}"

    def update_model(self, model: str) -> None:
        self._model = model
        self.query_one("#hb-left", Static).update(self._build_left())

    def update_mode(self, mode: str) -> None:
        self._mode = mode
        self._update_right()

    def update_right(self, text: str = "") -> None:
        self.query_one("#hb-right", Static).update(text)

    def _update_right(self) -> None:
        self.query_one("#hb-right", Static).update(f"[dim]{self._mode}[/]")
