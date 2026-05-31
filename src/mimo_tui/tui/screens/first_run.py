"""First-run wizard: API key → model → protocol → lang/theme."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from mimo_tui.constants import OFFICIAL_ANTHROPIC_URL, OFFICIAL_API_URL
from mimo_tui.i18n.translator import t
from mimo_tui.providers.capabilities import all_models
from mimo_tui.tui.theme import THEMES


class FirstRunWizard(ModalScreen[None]):
    """Multi-step first-run setup modal."""

    DEFAULT_CSS = """
    FirstRunWizard {
        align: center middle;
    }
    FirstRunWizard > * {
        width: 70;
        height: auto;
        background: $surface;
        border: solid $border;
        padding: 2 4;
    }
    FirstRunWizard .wizard-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    FirstRunWizard .wizard-label {
        margin-top: 1;
    }
    FirstRunWizard .wizard-actions {
        margin-top: 2;
        layout: horizontal;
        height: 3;
    }
    FirstRunWizard .wizard-actions Button {
        margin-right: 1;
    }
    """

    class WizardComplete(Message):
        def __init__(
            self,
            api_key: str,
            endpoint_url: str,
            model: str,
            protocol: str,
            language: str,
            theme: str,
        ) -> None:
            self.api_key = api_key
            self.endpoint_url = endpoint_url
            self.model = model
            self.protocol = protocol
            self.language = language
            self.theme = theme
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self._step = 0
        # Values entered on each step are captured here before the step's
        # widgets are torn down, so the final collection isn't limited to the
        # widgets that happen to be mounted on the last step.
        self._values: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Static():
            yield Static(t("first_run.title"), classes="wizard-title")
            yield Static(id="wizard-step-label")
            yield Static(id="wizard-body")
            with Static(classes="wizard-actions"):
                yield Button("Next →", id="wizard-next", variant="primary")
                yield Button("Skip", id="wizard-skip", variant="default")

    def on_mount(self) -> None:
        self._render_step()

    def _render_step(self) -> None:
        body = self.query_one("#wizard-body", Static)
        step_label = self.query_one("#wizard-step-label", Static)

        if self._step == 0:
            step_label.update(f"Step 1/4 — {t('first_run.step_api')}")
            body.remove_children()
            body.mount(Label(t("first_run.api_key_label"), classes="wizard-label"))
            body.mount(Input(placeholder=t("first_run.api_key_placeholder"), id="wiz-api-key", password=True))
            body.mount(Label(t("first_run.self_hosted_label"), classes="wizard-label"))
            body.mount(Input(value=OFFICIAL_API_URL, id="wiz-endpoint"))

        elif self._step == 1:
            step_label.update(f"Step 2/4 — {t('first_run.step_model')}")
            body.remove_children()
            options = [(m, m) for m in all_models()]
            body.mount(Label("Model", classes="wizard-label"))
            body.mount(Select(options, id="wiz-model", value="MiMo-V2.5-Pro"))  # type: ignore[arg-type]

        elif self._step == 2:
            step_label.update(f"Step 3/4 — {t('first_run.step_protocol')}")
            body.remove_children()
            body.mount(Label(t("first_run.step_protocol"), classes="wizard-label"))
            body.mount(Select(
                [
                    (t("first_run.protocol_openai"), "openai"),
                    (t("first_run.protocol_anthropic"), "anthropic"),
                ],
                id="wiz-protocol",
                value="openai",  # type: ignore[arg-type]
            ))

        elif self._step == 3:
            step_label.update(f"Step 4/4 — {t('first_run.step_prefs')}")
            body.remove_children()
            body.mount(Label(t("first_run.language_label"), classes="wizard-label"))
            body.mount(Select([("English", "en"), ("中文", "zh_CN")], id="wiz-lang", value="en"))  # type: ignore[arg-type]
            body.mount(Label(t("first_run.theme_label"), classes="wizard-label"))
            theme_opts = [(k, k) for k in THEMES]
            body.mount(Select(theme_opts, id="wiz-theme", value="tokyonight"))  # type: ignore[arg-type]

            next_btn = self.query_one("#wizard-next", Button)
            next_btn.label = t("first_run.finish")

    def _capture_step(self) -> None:
        """Store the values of the currently-mounted widgets.

        Each step replaces the body's children, so values must be captured
        before navigating away or they are lost.
        """
        for widget_id in ("wiz-api-key", "wiz-endpoint", "wiz-model",
                           "wiz-protocol", "wiz-lang", "wiz-theme"):
            try:
                w = self.query_one(f"#{widget_id}")
            except Exception:
                continue
            if isinstance(w, Input):
                self._values[widget_id] = w.value
            elif isinstance(w, Select):
                v = w.value
                if v is not None and v is not Select.BLANK:
                    self._values[widget_id] = str(v)

    def _collect_and_finish(self) -> None:
        self._capture_step()

        def _get(widget_id: str, default: str = "") -> str:
            return self._values.get(widget_id) or default

        self.app.post_message(self.WizardComplete(
            api_key=_get("wiz-api-key"),
            endpoint_url=_get("wiz-endpoint", OFFICIAL_API_URL),
            model=_get("wiz-model", "MiMo-V2.5-Pro"),
            protocol=_get("wiz-protocol", "openai"),
            language=_get("wiz-lang", "en"),
            theme=_get("wiz-theme", "tokyonight"),
        ))
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wizard-skip":
            self.dismiss(None)
            return
        if event.button.id == "wizard-next":
            if self._step < 3:
                self._capture_step()
                self._step += 1
                self._render_step()
            else:
                self._collect_and_finish()
