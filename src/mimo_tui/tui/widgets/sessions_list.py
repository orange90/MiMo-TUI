"""Left sidebar listing sessions."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Label, ListItem, ListView, Static


class SessionsList(Static):
    DEFAULT_CSS = """
    SessionsList {
        width: 20;
        border-right: solid $border;
        padding: 0;
        background: $surface-darken-2;
    }
    SessionsList #sl-header {
        height: 1;
        padding: 0 1;
        color: $text-muted;
        text-style: bold;
    }
    SessionsList #sl-new {
        height: 1;
        margin: 0 1;
        background: $success;
        color: $on-success;
        border: none;
    }
    SessionsList #sl-list {
        height: 1fr;
    }
    """

    class SessionSelected(Message):
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            super().__init__()

    class NewSessionRequested(Message):
        pass

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
        pass  # future: scroll to and highlight active session
