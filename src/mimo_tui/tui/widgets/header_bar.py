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
        self._ctx_used = 0
        self._ctx_window = 0

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
        parts = [f"[dim]{self._mode}[/]"]
        if self._ctx_used > 0 and self._ctx_window > 0:
            pct = min(100, int((self._ctx_used / self._ctx_window) * 100))
            color = "#9ece6a" if pct < 60 else "#e0af68" if pct < 85 else "#f7768e"
            parts.append(
                f"[{color}]ctx {pct}%[/] [dim]{_fmt_tok(self._ctx_used)}/{_fmt_tok(self._ctx_window)}[/]"
            )
        elif self._ctx_window > 0:
            parts.append(f"[dim]ctx 0% 0/{_fmt_tok(self._ctx_window)}[/]")
        return "  [dim]·[/]  ".join(parts)

    def update_model(self, model: str) -> None:
        self._model = model
        self.query_one("#hb-left", Static).update(self._build_left())

    def update_mode(self, mode: str) -> None:
        self._mode = mode
        self.query_one("#hb-right", Static).update(self._build_right())

    def update_title(self, title: str) -> None:
        self._title = title
        self.query_one("#hb-center", Static).update(self._build_center())

    def update_context(self, used: int = -1, window: int = -1) -> None:
        if used >= 0:
            self._ctx_used = used
        if window >= 0:
            self._ctx_window = window
        try:
            self.query_one("#hb-right", Static).update(self._build_right())
        except Exception:
            pass

    def update_right(self, text: str = "") -> None:
        self.query_one("#hb-right", Static).update(text)


def _fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)
