"""Left sidebar listing sessions — hidden by default in Claude Code style."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Label, ListItem, ListView, Static


class SessionsList(Vertical):
    DEFAULT_CSS = """
    SessionsList {
        width: 22;
        border-right: solid #29a4bd;
        padding: 0;
        background: #16213e;
    }
    SessionsList.collapsed {
        width: 0;
        display: none;
    }
    SessionsList #sl-header {
        height: 1;
        padding: 0 1;
        color: #e0af68;
        text-style: bold;
        background: #1f2335;
    }
    SessionsList #sl-new {
        height: 1;
        margin: 0 1;
        background: #29a4bd;
        color: #1a1b2e;
        border: none;
    }
    SessionsList #sl-list {
        height: 1fr;
        background: #16213e;
    }
    """

    collapsed: reactive[bool] = reactive(True)

    class SessionSelected(Message):
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            super().__init__()

    class NewSessionRequested(Message):
        pass

    def __init__(self) -> None:
        super().__init__()
        self.add_class("collapsed")

    def compose(self) -> ComposeResult:
        yield Static("Sessions", id="sl-header")
        yield Button("+ New", id="sl-new", variant="success")
        yield ListView(id="sl-list")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sl-new":
            self.post_message(self.NewSessionRequested())

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        sid = event.item.id or ""
        if sid.startswith("session-"):
            self.post_message(self.SessionSelected(sid[8:]))

    def load_sessions(self, sessions: list[tuple[str, str]]) -> None:
        lv = self.query_one("#sl-list", ListView)
        lv.clear()
        for sid, title in sessions:
            item = ListItem(Label(title[:18]), id=f"session-{sid}")
            lv.append(item)

    def highlight_session(self, session_id: str) -> None:
        pass

    def toggle_collapse(self) -> None:
        if self.collapsed:
            self.remove_class("collapsed")
            self.collapsed = False
        else:
            self.add_class("collapsed")
            self.collapsed = True
