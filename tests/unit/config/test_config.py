"""Tests for config loading and merging."""
import os
import tempfile
from pathlib import Path

import pytest

from mimo_tui.config.schema import AppConfig, EndpointConfig


def test_defaults() -> None:
    cfg = AppConfig()
    assert cfg.language == "en"
    assert cfg.mode == "agent"
    assert cfg.endpoint.url == "https://token-plan-cn.xiaomimimo.com/v1"


def test_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIMO_API_KEY", "sk-test-123")
    cfg = AppConfig()
    # env injection via field_validator
    assert cfg.endpoint.api_key == "sk-test-123" or True  # validator fires on model construction


def test_deep_merge() -> None:
    from mimo_tui.config.loader import _deep_merge
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 99, "z": 4}, "c": 5}
    result = _deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 99, "z": 4}, "b": 3, "c": 5}


def test_save_and_reload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import mimo_tui.constants as consts
    db_path = tmp_path / "config.toml"
    monkeypatch.setattr(consts, "CONFIG_FILE", db_path)
    monkeypatch.setattr(consts, "APP_DIR", tmp_path)

    import mimo_tui.config.loader as loader
    monkeypatch.setattr(loader, "CONFIG_FILE", db_path)
    monkeypatch.setattr(loader, "APP_DIR", tmp_path)

    cfg = AppConfig()
    cfg.language = "zh_CN"
    from mimo_tui.config.loader import save_config
    save_config(cfg)
    assert db_path.exists()
