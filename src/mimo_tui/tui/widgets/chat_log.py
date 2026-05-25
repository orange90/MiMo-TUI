"""Chat transcript widget — Claude Code style with thinking display."""
from __future__ import annotations

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from textual.widgets import RichLog


class ChatLog(RichLog):
    """Scrollable chat transcript with markdown rendering and thinking blocks."""

    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        border: none;
        padding: 0 1;
        background: #1a1b2e;
        scrollbar-size: 1 1;
    }
    """

    def __init__(self) -> None:
        super().__init__(highlight=True, markup=True, wrap=True)
        self._current_role: str | None = None
        self._current_buf: str = ""
        self._streaming = False
        self._reasoning_buf: str = ""
        self._reasoning_active = False

    def begin_user_message(self, text: str) -> None:
        self._flush_current()
        self.write(Text(""))
        self.write(Text("You ", style="bold #FF8C33"), shrink=False)
        self.write(Markdown(text))
        self._current_role = None

    def begin_assistant_message(self) -> None:
        self._flush_current()
        self.write(Text(""))
        self.write(Text("MiMo ", style="bold #ff6700"), shrink=False)
        self._current_role = "assistant"
        self._current_buf = ""
        self._streaming = True

    def begin_thinking(self) -> None:
        """Start a thinking/reasoning block inline in chat."""
        self._reasoning_buf = ""
        self._reasoning_active = True

    def append_thinking(self, text: str, elapsed: float = 0.0) -> None:
        """Append text to the inline thinking block."""
        self._reasoning_buf += text

    def end_thinking(self, elapsed: float = 0.0) -> None:
        """Finish the thinking block and render it."""
        if self._reasoning_buf:
            elapsed_str = f"{elapsed:.1f}s" if elapsed else ""
            header = f"[dim #e0af68]o thinking[/] [dim]done · {elapsed_str}[/]" if elapsed_str else "[dim #e0af68]o thinking[/]"
            self.write(Text.from_markup(header), shrink=False)
            lines = self._reasoning_buf.strip().split("\n")
            for line in lines[:6]:
                self.write(Text(f"  | {line.strip()}", style="dim #565f89"), shrink=False)
            if len(lines) > 6:
                self.write(Text(f"  | ... ({len(lines) - 6} more lines)", style="dim #565f89"), shrink=False)
        self._reasoning_active = False
        self._reasoning_buf = ""

    def append_assistant_chunk(self, text: str) -> None:
        self._current_buf += text

    def flush_assistant_stream(self) -> None:
        if self._current_buf:
            self.write(Markdown(self._current_buf))
            self._current_buf = ""
        self._current_role = None
        self._streaming = False

    def _flush_current(self) -> None:
        if self._current_role == "assistant" and self._current_buf:
            self.write(Markdown(self._current_buf))
            self._current_buf = ""
            self._current_role = None

    def write_tool_call(self, tool_name: str, args_preview: str, result: str, approved: bool) -> None:
        self._flush_current()
        status = "[bold #9ece6a]v[/]" if approved else "[bold #f7768e]x[/]"
        header_text = f"  {status} [bold #e0af68]{tool_name}[/]"
        self.write(Text.from_markup(header_text), shrink=False)
        if args_preview:
            self.write(Text(f"    {args_preview[:120]}", style="dim #565f89"), shrink=False)
        if result:
            preview = result[:300] + ("..." if len(result) > 300 else "")
            result_style = "dim #9ece6a" if approved else "dim #f7768e"
            self.write(Text(f"    -> {preview}", style=result_style), shrink=False)

    def write_system_message(self, text: str, style: str = "dim italic") -> None:
        self._flush_current()
        self.write(Text(f"  {text}", style=style))

    def write_audio_card(self, audio_id: str) -> None:
        self._flush_current()
        self.write(Text.from_markup(f"  [bold #FF8C33]>> Audio response[/] [dim][id={audio_id}][/]"), shrink=False)

    def write_error(self, text: str) -> None:
        self._flush_current()
        self.write(Text(f"  x Error: {text}", style="bold #f7768e"))
