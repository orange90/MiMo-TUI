"""Tool approval — inline panel rendered inside the main UI (no fullscreen modal)."""
from __future__ import annotations

import asyncio
import json

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, Static

from mimo_tui.agent.approval import ApprovalRequest
from mimo_tui.i18n.translator import t


class ApprovalPanel(Vertical):
    """Inline approval panel shown above the composer.

    Stays hidden by default. When the agent loop needs approval, call
    `await panel.request(req)` from the approval callback — it will reveal
    the panel, await the user's decision, then hide itself again.
    """

    DEFAULT_CSS = """
    ApprovalPanel {
        display: none;
        height: auto;
        max-height: 14;
        background: #1a1b2e;
        border-top: solid #FF6700;
        padding: 1 2;
    }
    ApprovalPanel.-visible {
        display: block;
    }
    ApprovalPanel #ap-title {
        text-style: bold;
        color: #e0af68;
    }
    ApprovalPanel #ap-tool {
        color: #7aa2f7;
        text-style: bold;
    }
    ApprovalPanel #ap-args {
        color: #565f89;
        max-height: 5;
        overflow-y: auto;
    }
    ApprovalPanel #ap-danger {
        color: #f7768e;
        text-style: bold;
    }
    ApprovalPanel #ap-actions {
        layout: horizontal;
        height: 3;
        margin-top: 1;
    }
    ApprovalPanel #ap-actions Button {
        margin-right: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._future: asyncio.Future[bool] | None = None
        self._request: ApprovalRequest | None = None

    def compose(self) -> ComposeResult:
        yield Label("", id="ap-title")
        yield Label("", id="ap-tool")
        yield Static("", id="ap-args")
        yield Label("", id="ap-danger")
        with Horizontal(id="ap-actions"):
            yield Button(t("approval.approve"), id="ap-approve", variant="success")
            yield Button(t("approval.deny"), id="ap-deny", variant="error")

    async def request(self, req: ApprovalRequest) -> bool:
        """Show the panel and wait until the user approves or denies."""
        self._request = req
        try:
            args_str = json.dumps(req.arguments, indent=2, ensure_ascii=False)[:500]
        except Exception:
            args_str = str(req.arguments)[:500]

        self.query_one("#ap-title", Label).update(t("approval.title"))
        self.query_one("#ap-tool", Label).update(f"Tool: {req.tool_name}")
        self.query_one("#ap-args", Static).update(f"Args:\n{args_str}")
        danger_lbl = self.query_one("#ap-danger", Label)
        if req.danger_level >= 2:
            danger_lbl.update(f"\u26a0 {t('approval.danger')}")
            danger_lbl.display = True
        else:
            danger_lbl.update("")
            danger_lbl.display = False

        loop = asyncio.get_event_loop()
        self._future = loop.create_future()
        self.add_class("-visible")
        try:
            self.query_one("#ap-approve", Button).focus()
        except Exception:
            pass

        try:
            return await self._future
        finally:
            self.remove_class("-visible")
            self._future = None
            self._request = None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self._future is None or self._future.done():
            return
        if event.button.id == "ap-approve":
            self._future.set_result(True)
        elif event.button.id == "ap-deny":
            self._future.set_result(False)

    def on_key(self, event: object) -> None:
        from textual.events import Key
        if not isinstance(event, Key):
            return
        if self._future is None or self._future.done():
            return
        if event.key == "y":
            self._future.set_result(True)
            event.stop()
        elif event.key in ("n", "escape"):
            self._future.set_result(False)
            event.stop()
