"""Collapsible reasoning-trace pane — styled for Claude Code look."""
from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import RichLog, Static


class ReasoningPane(Vertical):
    """Side panel streaming the model's reasoning tokens."""

    DEFAULT_CSS = """
    ReasoningPane {
        width: 30%;
        border-left: solid #29a4bd;
        padding: 0 1;
        background: #16213e;
    }
    ReasoningPane.collapsed {
        width: 0;
        display: none;
    }
    ReasoningPane #rp-header {
        height: 1;
        color: #e0af68;
        text-style: bold;
    }
    ReasoningPane #rp-log {
        height: 1fr;
        background: #16213e;
    }
    ReasoningPane #rp-stats {
        height: 1;
        color: #565f89;
        text-style: italic;
    }
    """

    collapsed: reactive[bool] = reactive(False)

    def __init__(self, collapsed: bool = False) -> None:
        super().__init__()
        self._token_count = 0
        self._turn_count = 0
        if collapsed:
            self.add_class("collapsed")
            self.collapsed = True

    def compose(self) -> ComposeResult:
        yield Static("Reasoning", id="rp-header")
        yield RichLog(highlight=False, markup=False, wrap=True, id="rp-log")
        yield Static("", id="rp-stats")

    def begin_turn(self) -> None:
        self._token_count = 0
        self._turn_count += 1
        log_widget = self.query_one("#rp-log", RichLog)
        log_widget.write(Text(f"\n-- Turn {self._turn_count} --", style="dim #7aa2f7"))

    def append_reasoning(self, text: str) -> None:
        self._token_count += len(text.split())
        log_widget = self.query_one("#rp-log", RichLog)
        log_widget.write(Text(text, style="dim #565f89"), shrink=False)
        stats = self.query_one("#rp-stats", Static)
        stats.update(f"~{self._token_count} tokens")

    def clear(self) -> None:
        log_widget = self.query_one("#rp-log", RichLog)
        log_widget.clear()
        stats = self.query_one("#rp-stats", Static)
        stats.update("")
        self._token_count = 0
        self._turn_count = 0

    def toggle_collapse(self) -> None:
        if self.collapsed:
            self.remove_class("collapsed")
            self.collapsed = False
        else:
            self.add_class("collapsed")
            self.collapsed = True
