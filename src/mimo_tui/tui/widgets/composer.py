"""Claude Code style composer — bottom input with label."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input, Static

from mimo_tui.tui.commands import completions_for


class Composer(Vertical):
    DEFAULT_CSS = """
    Composer {
        height: 4;
        background: #16213e;
        padding: 0 1;
        border-top: solid #29a4bd;
    }
    Composer #compose-label {
        height: 1;
        color: #565f89;
    }
    Composer #compose-input {
        height: 1;
        border: none;
        background: #1a1b2e;
        color: #c0caf5;
        padding: 0 1;
    }
    Composer #compose-hint {
        height: 1;
        color: #565f89;
        text-style: italic;
    }
    """

    class MessageSubmitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class StopRequested(Message):
        pass

    def __init__(self, placeholder: str = "Write a task or use /.") -> None:
        super().__init__()
        self._placeholder = placeholder
        self._streaming = False

    def compose(self) -> ComposeResult:
        yield Static("[dim]Composer[/]", id="compose-label")
        yield Input(placeholder=self._placeholder, id="compose-input")
        yield Static("", id="compose-hint")

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

    def _submit(self) -> None:
        if self._streaming:
            self.post_message(self.StopRequested())
            return
        inp = self.query_one("#compose-input", Input)
        text = inp.value.strip()
        if not text:
            return
        inp.value = ""
        self.query_one("#compose-hint", Static).update("")
        self.post_message(self.MessageSubmitted(text=text))

    def set_streaming(self, streaming: bool) -> None:
        self._streaming = streaming
        inp = self.query_one("#compose-input", Input)
        if streaming:
            inp.placeholder = "Press Enter to stop..."
        else:
            inp.placeholder = self._placeholder
        inp.disabled = streaming

    def focus_input(self) -> None:
        self.query_one("#compose-input", Input).focus()
