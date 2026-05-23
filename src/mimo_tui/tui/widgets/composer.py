"""Multi-line input with slash-command autocomplete."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Button, Input, Static

from mimo_tui.tui.commands import completions_for


class Composer(Static):
    DEFAULT_CSS = """
    Composer {
        height: 5;
        border-top: solid $border;
        background: $surface-darken-1;
        padding: 0 1;
    }
    Composer #compose-input {
        height: 3;
        border: none;
        background: $surface;
    }
    Composer #compose-hint {
        height: 1;
        color: $text-muted;
        text-style: italic;
    }
    Composer #compose-send {
        dock: right;
        height: 3;
        width: 8;
    }
    """

    class MessageSubmitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class StopRequested(Message):
        pass

    def __init__(self, placeholder: str = "Type a message… (/help for commands)") -> None:
        super().__init__()
        self._placeholder = placeholder
        self._streaming = False

    def compose(self) -> ComposeResult:
        yield Input(placeholder=self._placeholder, id="compose-input")
        yield Static("", id="compose-hint")
        yield Button("Send", id="compose-send", variant="primary")

    def on_input_changed(self, event: Input.Changed) -> None:
        text = event.value
        if text.startswith("/"):
            completions = completions_for(text)
            hint = "  ".join(completions[:5]) if completions else ""
            self.query_one("#compose-hint", Static).update(hint)
        else:
            self.query_one("#compose-hint", Static).update("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "compose-send":
            if self._streaming:
                self.post_message(self.StopRequested())
            else:
                self._submit()

    def _submit(self) -> None:
        inp = self.query_one("#compose-input", Input)
        text = inp.value.strip()
        if not text:
            return
        inp.value = ""
        self.query_one("#compose-hint", Static).update("")
        self.post_message(self.MessageSubmitted(text=text))

    def set_streaming(self, streaming: bool) -> None:
        self._streaming = streaming
        btn = self.query_one("#compose-send", Button)
        btn.label = "Stop" if streaming else "Send"
        btn.variant = "error" if streaming else "primary"
        inp = self.query_one("#compose-input", Input)
        inp.disabled = streaming

    def focus_input(self) -> None:
        self.query_one("#compose-input", Input).focus()
