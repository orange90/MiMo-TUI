"""Top header bar — Xiaomi MiMo branding with session title."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

# Orange background block matching Xiaomi brand color
XIAOMI_LOGO_TEXT = "[bold white on #FF6700] MI [/]"


class HeaderBar(Horizontal):
    DEFAULT_CSS = """
    HeaderBar {
        dock: top;
        height: 1;
        background: #1a1b2e;
        color: #FF6700;
        padding: 0 1;
    }
    HeaderBar #hb-left {
        width: auto;
        content-align: left middle;
    }
    HeaderBar #hb-center {
        width: 1fr;
        content-align: center middle;
        color: #c0caf5;
    }
    HeaderBar #hb-right {
        width: auto;
        content-align: right middle;
        color: #565f89;
    }
    """

    def __init__(self, model: str = "", mode: str = "agent", title: str = "Untitled") -> None:
        super().__init__()
        self._model = model
        self._mode = mode
        self._title = title

    def compose(self) -> ComposeResult:
        yield Static(self._build_left(), id="hb-left")
        yield Static(self._build_center(), id="hb-center")
        yield Static(self._build_right(), id="hb-right")

    def _build_left(self) -> str:
        model_short = self._model.split("/")[-1] if self._model else "mimo"
        return f"{XIAOMI_LOGO_TEXT} [bold #FF6700]XiaoMiMo[/]  [dim]mimo-tui · {model_short}[/]"

    def _build_center(self) -> str:
        return f"[dim]◆[/]  {self._title}"

    def _build_right(self) -> str:
        return f"[dim]{self._mode}[/]"

    def update_model(self, model: str) -> None:
        self._model = model
        self.query_one("#hb-left", Static).update(self._build_left())

    def update_mode(self, mode: str) -> None:
        self._mode = mode
        self.query_one("#hb-right", Static).update(self._build_right())

    def update_title(self, title: str) -> None:
        self._title = title
        self.query_one("#hb-center", Static).update(self._build_center())

    def update_right(self, text: str = "") -> None:
        self.query_one("#hb-right", Static).update(text)

    def _update_right(self) -> None:
        self.query_one("#hb-right", Static).update(self._build_right())
