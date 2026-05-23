from __future__ import annotations

from pathlib import Path

from mimo_tui.constants import APP_DIR, AUDIO_DIR


def ensure_app_dirs() -> None:
    for d in (APP_DIR, AUDIO_DIR):
        d.mkdir(parents=True, exist_ok=True)


def resolve_audio_save_path(filename: str, save_dir: str) -> Path:
    base = Path(save_dir).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base / filename
