"""Inline activity bar — animated horizontal indicator shown above the Composer.

Sits between the chat transcript / approval panel and the Composer. Stays
hidden when the agent is idle. While the agent is streaming (thinking,
calling a tool, or writing a reply) it renders a Knight-Rider style shimmer
that sweeps across the bar so the user has a visible heartbeat right next
to where they type.
"""
from __future__ import annotations

import time

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


BAR_WIDTH = 28
BLOCKS = ("█", "▓", "▒", "░")


class ActivityBar(Horizontal):
    DEFAULT_CSS = """
    ActivityBar {
        display: none;
        height: 1;
        background: #16213e;
        padding: 0 1;
    }
    ActivityBar.-visible {
        display: block;
    }
    ActivityBar #ab-bar {
        width: 1fr;
        color: #7aa2f7;
        content-align: left middle;
    }
    ActivityBar #ab-label {
        width: auto;
        color: #565f89;
        content-align: right middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._activity: str | None = None
        self._started_at: float = 0.0
        self._frame: int = 0
        self._timer: object | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="ab-bar")
        yield Static("", id="ab-label")

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.08, self._tick)

    def _tick(self) -> None:
        if self._activity is None:
            return
        self._frame = (self._frame + 1) % (BAR_WIDTH * 2)
        self._repaint()

    def set_activity(self, label: str | None) -> None:
        """Show the bar with a label like "thinking" / clear with None."""
        if label:
            if self._activity is None:
                self._started_at = time.monotonic()
                self._frame = 0
            self._activity = label
            self.add_class("-visible")
            self._repaint()
        else:
            self._activity = None
            self._started_at = 0.0
            self.remove_class("-visible")

    def _repaint(self) -> None:
        if self._activity is None:
            return

        head = self._frame
        if head >= BAR_WIDTH:
            head = (BAR_WIDTH * 2) - head - 1

        chars: list[str] = []
        for i in range(BAR_WIDTH):
            dist = abs(i - head)
            if dist < len(BLOCKS):
                chars.append(BLOCKS[dist])
            else:
                chars.append("·")
        bar = "".join(chars)

        elapsed = time.monotonic() - self._started_at
        try:
            self.query_one("#ab-bar", Static).update(
                f"[#7aa2f7]{bar}[/]  [#e0af68]{self._activity}[/]"
            )
            self.query_one("#ab-label", Static).update(
                f"[dim]· {elapsed:.1f}s[/]"
            )
        except Exception:
            pass
