"""Tool approval modal — shown before executing dangerous tools in agent mode."""
from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from mimo_tui.agent.approval import ApprovalRequest
from mimo_tui.i18n.translator import t


class ApprovalModal(ModalScreen[bool]):
    DEFAULT_CSS = """
    ApprovalModal {
        align: center middle;
    }
    ApprovalModal > * {
        width: 70;
        height: auto;
        min-height: 10;
        background: $surface;
        border: solid $border;
        padding: 2 4;
    }
    ApprovalModal #ap-title { text-style: bold; color: $warning; }
    ApprovalModal #ap-tool { color: $accent; text-style: bold; margin-top: 1; }
    ApprovalModal #ap-args { color: $text-muted; margin-top: 1; }
    ApprovalModal #ap-danger { color: $error; text-style: bold; }
    ApprovalModal #ap-actions { layout: horizontal; height: 3; margin-top: 2; }
    ApprovalModal #ap-actions Button { margin-right: 1; }
    """

    def __init__(self, request: ApprovalRequest) -> None:
        super().__init__()
        self._request = request

    def compose(self) -> ComposeResult:
        r = self._request
        with Static():
            yield Label(t("approval.title"), id="ap-title")
            yield Label(f"Tool: {r.tool_name}", id="ap-tool")
            try:
                args_str = json.dumps(r.arguments, indent=2)[:500]
            except Exception:
                args_str = str(r.arguments)[:500]
            yield Label(f"Args:\n{args_str}", id="ap-args")
            if r.danger_level >= 2:
                yield Label(f"⚠ {t('approval.danger')}", id="ap-danger")
            with Static(id="ap-actions"):
                yield Button(t("approval.approve"), id="ap-approve", variant="success")
                yield Button(t("approval.deny"), id="ap-deny", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ap-approve":
            self.dismiss(True)
        elif event.button.id == "ap-deny":
            self.dismiss(False)

    def on_key(self, event: object) -> None:
        from textual.events import Key
        if isinstance(event, Key):
            if event.key == "y":
                self.dismiss(True)
            elif event.key in ("n", "escape"):
                self.dismiss(False)
