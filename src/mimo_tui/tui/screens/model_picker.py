"""Model picker modal — shows capability badges, allows fuzzy filter."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from mimo_tui.i18n.translator import t
from mimo_tui.providers.capabilities import ModelCapabilities, all_models, get_capabilities


class ModelPicker(ModalScreen[str | None]):
    DEFAULT_CSS = """
    ModelPicker {
        align: center middle;
    }
    ModelPicker > * {
        width: 60;
        height: 30;
        background: $surface;
        border: solid $border;
        padding: 1 2;
    }
    ModelPicker #mp-title { text-style: bold; color: $accent; }
    ModelPicker #mp-search { margin-top: 1; }
    ModelPicker #mp-list { height: 1fr; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Static():
            yield Static(t("model_picker.title"), id="mp-title")
            yield Input(placeholder=t("model_picker.search"), id="mp-search")
            yield ListView(id="mp-list")

    def on_mount(self) -> None:
        self._populate(all_models())
        self.query_one("#mp-search", Input).focus()

    def _populate(self, models: list[str]) -> None:
        lv = self.query_one("#mp-list", ListView)
        lv.clear()
        for m in models:
            caps = get_capabilities(m)
            badge = caps.badge_str()
            text = f"{m}  {badge}"
            lv.append(ListItem(Label(text), id=f"model-{m}"))

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower()
        filtered = [m for m in all_models() if q in m.lower()]
        self._populate(filtered)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("model-"):
            self.dismiss(item_id[6:])

    def on_key(self, event: object) -> None:
        from textual.events import Key
        if isinstance(event, Key) and event.key == "escape":
            self.dismiss(None)
