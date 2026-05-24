"""Textual App entry point for MiMo TUI."""
from __future__ import annotations

from textual.app import App, ComposeResult

from mimo_tui.config.loader import save_config
from mimo_tui.config.schema import AppConfig
from mimo_tui.constants import CONFIG_FILE
from mimo_tui.i18n.translator import set_language
from mimo_tui.tui.screens.first_run import FirstRunWizard
from mimo_tui.tui.screens.main import MainScreen
from mimo_tui.tui.theme import DEFAULT_THEME, get_theme_css


class MimoApp(App):  # type: ignore[type-arg]
    TITLE = "MiMo TUI"
    CSS = """
    Screen {
        background: #1a1b2e;
    }
    """

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self._cfg = cfg
        set_language(cfg.language)

    def on_mount(self) -> None:
        if not CONFIG_FILE.exists() or not self._cfg.endpoint.api_key:
            self.push_screen(FirstRunWizard())
        else:
            self.push_screen(MainScreen(self._cfg))

    def on_first_run_wizard_wizard_complete(self, event: FirstRunWizard.WizardComplete) -> None:
        self._cfg.endpoint.api_key = event.api_key
        self._cfg.endpoint.url = event.endpoint_url
        self._cfg.model.name = event.model
        self._cfg.protocol = event.protocol  # type: ignore[assignment]
        self._cfg.language = event.language  # type: ignore[assignment]
        self._cfg.theme = event.theme
        set_language(event.language)
        save_config(self._cfg)
        self.push_screen(MainScreen(self._cfg))
