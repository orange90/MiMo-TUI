from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import tomllib
import tomli_w

from mimo_tui.config.schema import AppConfig
from mimo_tui.constants import APP_DIR, CONFIG_FILE

_DEFAULTS_PATH = Path(__file__).parent / "defaults.toml"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config() -> AppConfig:
    defaults = _load_toml(_DEFAULTS_PATH)
    user = _load_toml(CONFIG_FILE)
    local = _load_toml(Path(".mimo") / "config.toml")

    merged = _deep_merge(_deep_merge(defaults, user), local)

    api_key = os.environ.get("MIMO_API_KEY", "")
    if api_key and not merged.get("endpoint", {}).get("api_key"):
        merged.setdefault("endpoint", {})["api_key"] = api_key

    return AppConfig.model_validate(merged)


def save_config(cfg: AppConfig) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    data = cfg.model_dump(exclude_none=True)
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)
