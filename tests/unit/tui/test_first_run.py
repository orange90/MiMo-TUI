"""Tests for the first-run wizard value capture across steps."""
from __future__ import annotations

import pytest
from textual.app import App
from textual.widgets import Input, Select

from mimo_tui.tui.screens.first_run import FirstRunWizard


class _WizardApp(App):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__()
        self.completed: FirstRunWizard.WizardComplete | None = None

    def on_mount(self) -> None:
        self.push_screen(FirstRunWizard())

    def on_first_run_wizard_wizard_complete(
        self, event: FirstRunWizard.WizardComplete
    ) -> None:
        self.completed = event


@pytest.mark.asyncio
async def test_wizard_captures_values_across_steps() -> None:
    app = _WizardApp()
    async with app.run_test() as pilot:
        wizard = app.screen
        assert isinstance(wizard, FirstRunWizard)

        async def advance() -> None:
            # Let any programmatic widget value changes settle first.
            for _ in range(3):
                await pilot.pause()
            await pilot.click("#wizard-next")
            # Each step tears down and remounts the body; let the mount settle.
            for _ in range(5):
                await pilot.pause()

        # Step 1: API key + endpoint
        wizard.query_one("#wiz-api-key", Input).value = "sk-my-key"
        wizard.query_one("#wiz-endpoint", Input).value = "https://example.com/v1"
        await advance()

        # Step 2: model
        wizard.query_one("#wiz-model", Select).value = "MiMo-V2.5-Pro"
        await advance()

        # Step 3: protocol
        wizard.query_one("#wiz-protocol", Select).value = "anthropic"
        await advance()

        # Step 4: language + theme, then finish
        wizard.query_one("#wiz-lang", Select).value = "zh_CN"
        await advance()

    assert app.completed is not None
    assert app.completed.api_key == "sk-my-key"
    assert app.completed.endpoint_url == "https://example.com/v1"
    assert app.completed.model == "MiMo-V2.5-Pro"
    assert app.completed.protocol == "anthropic"
    assert app.completed.language == "zh_CN"
