"""Chat transcript widget — streams markdown text, tool-call cards, audio cards."""
from __future__ import annotations

import time
from typing import Any

from rich.markdown import Markdown
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import RichLog, Static


class ChatLog(RichLog):
    """Scrollable chat transcript with markdown rendering."""

    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        border: none;
        padding: 0 1;
        background: $surface;
    }
    """

    def __init__(self) -> None:
        super().__init__(highlight=True, markup=True, wrap=True)
        self._current_role: str | None = None
        self._current_buf: str = ""
        self._streaming = False

    def begin_user_message(self, text: str) -> None:
        self._flush_current()
        self.write(Text(""))
        self.write(Text("You", style="bold cyan"))
        self.write(Markdown(text))
        self._current_role = None

    def begin_assistant_message(self) -> None:
        self._flush_current()
        self.write(Text(""))
        self.write(Text("MiMo", style="bold magenta"))
        self._current_role = "assistant"
        self._current_buf = ""
        self._streaming = True

    def append_text(self, text: str) -> None:
        if self._current_role == "assistant":
            self._current_buf += text
            # Re-render the growing buffer as markdown
            self._refresh_current()

    def finish_assistant_message(self) -> None:
        self._flush_current()
        self._streaming = False

    def _refresh_current(self) -> None:
        pass  # optimized: write incremental only on done

    def _flush_current(self) -> None:
        if self._current_role == "assistant" and self._current_buf:
            self.write(Markdown(self._current_buf))
            self._current_buf = ""
            self._current_role = None

    def append_assistant_chunk(self, text: str) -> None:
        """Append a streaming text chunk. Final flush via finish_assistant_message."""
        self._current_buf += text

    def flush_assistant_stream(self) -> None:
        """Flush the accumulated buffer as rendered markdown."""
        if self._current_buf:
            self.write(Markdown(self._current_buf))
            self._current_buf = ""
        self._current_role = None
        self._streaming = False

    def write_tool_call(self, tool_name: str, args_preview: str, result: str, approved: bool) -> None:
        self._flush_current()
        status = "✓" if approved else "✗"
        header = Text(f"  {status} {tool_name}", style="bold yellow" if approved else "bold red")
        self.write(header)
        if args_preview:
            self.write(Text(f"    {args_preview[:120]}", style="dim"))
        if result:
            preview = result[:300] + ("…" if len(result) > 300 else "")
            self.write(Text(f"    → {preview}", style="dim green" if approved else "dim red"))

    def write_system_message(self, text: str, style: str = "dim italic") -> None:
        self._flush_current()
        self.write(Text(f"  {text}", style=style))

    def write_audio_card(self, audio_id: str) -> None:
        self._flush_current()
        self.write(Text(f"  🔊 Audio response [id={audio_id}]", style="bold cyan"))

    def write_error(self, text: str) -> None:
        self._flush_current()
        self.write(Text(f"  ✗ Error: {text}", style="bold red"))
