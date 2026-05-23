from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Any

import yaml

_LOCALES_DIR = Path(__file__).parent / "locales"
_catalogs: dict[str, dict[str, Any]] = {}
_current_lang: str = "en"


def _load(lang: str) -> dict[str, Any]:
    if lang not in _catalogs:
        path = _LOCALES_DIR / f"{lang}.yaml"
        if not path.exists():
            path = _LOCALES_DIR / "en.yaml"
        with open(path, encoding="utf-8") as f:
            _catalogs[lang] = yaml.safe_load(f) or {}
    return _catalogs[lang]


def set_language(lang: str) -> None:
    global _current_lang
    _current_lang = lang
    _load(lang)


def t(key: str, **kwargs: str) -> str:
    """Look up a dot-separated key in the current locale catalog."""
    parts = key.split(".")
    catalog = _load(_current_lang)
    try:
        value = reduce(lambda d, k: d[k], parts, catalog)  # type: ignore[arg-type]
    except (KeyError, TypeError):
        en = _load("en")
        try:
            value = reduce(lambda d, k: d[k], parts, en)  # type: ignore[arg-type]
        except (KeyError, TypeError):
            return key
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)
    return str(value)
