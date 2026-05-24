"""CLI entry points: mimo, mimo doctor."""
from __future__ import annotations

import os
import sys
from typing import Annotated, Optional

import typer

app = typer.Typer(name="mimo", help="MiMo TUI — terminal UI for Xiaomi MiMo")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug logging")] = False,
    api_key: Annotated[Optional[str], typer.Option("--api-key", help="Override MIMO_API_KEY")] = None,
    model: Annotated[Optional[str], typer.Option("--model", help="Override model name")] = None,
    mode: Annotated[Optional[str], typer.Option("--mode", help="Override mode (chat/plan/agent/yolo)")] = None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    from mimo_tui.config.loader import load_config
    from mimo_tui.utils.logging import configure_logging

    configure_logging(debug=debug)

    if api_key:
        os.environ["MIMO_API_KEY"] = api_key

    cfg = load_config()

    if model:
        cfg.model.name = model
    if mode and mode in ("chat", "plan", "agent", "yolo"):
        cfg.mode = mode  # type: ignore[assignment]

    _sync_available_models(cfg)

    from mimo_tui.app import MimoApp
    MimoApp(cfg).run()


def _sync_available_models(cfg) -> None:  # type: ignore[no-untyped-def]
    """Refresh the cached list of API-supported models on every startup.

    Best-effort: any network/parse error is silently ignored so the TUI still
    starts when offline. On success we:
      * update the in-memory KNOWN_MODELS list (used by ModelPicker, etc.)
      * persist ``[models] available`` + ``synced_at`` back to config.toml
      * if ``cfg.model.name`` is not in the live list, switch to the first
        live model so requests don't 400 with "Not supported model …"
    """
    if not cfg.endpoint.api_key:
        return

    import asyncio
    from datetime import datetime

    from mimo_tui.client.openai_client import OpenAIClient
    from mimo_tui.config.loader import save_config
    from mimo_tui.providers.capabilities import set_known_models

    async def _fetch() -> list[str]:
        async with OpenAIClient(cfg) as client:
            return await client.list_models()

    try:
        models = asyncio.run(_fetch())
    except Exception:
        return

    if not models:
        return

    set_known_models(models)

    cfg.models.available = list(models)
    cfg.models.synced_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    available_lower = {m.lower() for m in models}
    if cfg.model.name.lower() not in available_lower:
        cfg.model.name = models[0]

    try:
        save_config(cfg)
    except Exception:
        pass


@app.command(name="doctor", help="Check configuration and connectivity")
def doctor(
    api_key: Annotated[Optional[str], typer.Option("--api-key")] = None,
) -> None:
    import asyncio
    from mimo_tui.i18n.translator import t

    async def _check() -> None:
        if api_key:
            os.environ["MIMO_API_KEY"] = api_key

        from mimo_tui.config.loader import load_config
        cfg = load_config()

        typer.echo(t("doctor.title"))
        typer.echo("─" * 40)

        typer.echo(t("doctor.checking_api"))
        try:
            from mimo_tui.client.openai_client import OpenAIClient
            async with OpenAIClient(cfg) as client:
                models = await client.list_models()
            typer.echo(f"  ✓ {t('doctor.api_ok')}")
            typer.echo(f"  ✓ {t('doctor.models_ok', count=str(len(models)))}")
            for m in models[:8]:
                typer.echo(f"      • {m}")
        except Exception as e:
            typer.echo(f"  ✗ {t('doctor.api_fail', error=str(e))}", err=True)

        try:
            import sounddevice  # noqa: F401
            typer.echo(f"  ✓ {t('doctor.audio_ok')}")
        except (ImportError, OSError):
            typer.echo(f"  ⚠ {t('doctor.audio_fail')}")

        typer.echo("─" * 40)

    asyncio.run(_check())


@app.command(name="serve-detect", help="Probe for local self-hosted inference engines")
def serve_detect() -> None:
    import asyncio
    from mimo_tui.providers.detect import detect_local_endpoints

    async def _detect() -> None:
        typer.echo("Probing for local inference engines…")
        endpoints = await detect_local_endpoints()
        if not endpoints:
            typer.echo("No local engines found.")
            return
        for ep in endpoints:
            typer.echo(f"  [{ep.engine}] {ep.url}")
            for m in ep.models[:5]:
                typer.echo(f"      • {m}")

    asyncio.run(_detect())


if __name__ == "__main__":
    app()
