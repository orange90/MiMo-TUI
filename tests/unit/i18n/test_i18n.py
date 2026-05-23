"""Tests for the i18n translator."""
import pytest
from mimo_tui.i18n.translator import set_language, t


def test_english_key() -> None:
    set_language("en")
    assert t("app_title") == "MiMo TUI"


def test_chinese_key() -> None:
    set_language("zh_CN")
    result = t("app_title")
    assert "MiMo" in result
    set_language("en")


def test_nested_key() -> None:
    set_language("en")
    assert t("chat.placeholder") != "chat.placeholder"


def test_missing_key_fallback() -> None:
    set_language("en")
    result = t("this.key.does.not.exist")
    assert result == "this.key.does.not.exist"


def test_format_kwargs() -> None:
    set_language("en")
    result = t("commands.model_set", model="MiMo-V2.5-Pro")
    assert "MiMo-V2.5-Pro" in result
