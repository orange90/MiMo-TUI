from __future__ import annotations

THEMES: dict[str, dict[str, str]] = {
    "tokyonight": {
        "bg": "#1a1b2e",
        "bg_alt": "#16213e",
        "bg_highlight": "#1f2335",
        "fg": "#c0caf5",
        "fg_dim": "#565f89",
        "blue": "#FF6700",
        "cyan": "#FF8C33",
        "green": "#9ece6a",
        "magenta": "#bb9af7",
        "orange": "#FF6700",
        "red": "#f7768e",
        "yellow": "#e0af68",
        "border": "#FF6700",
    },
    "catppuccin": {
        "bg": "#1e1e2e",
        "bg_alt": "#181825",
        "bg_highlight": "#313244",
        "fg": "#cdd6f4",
        "fg_dim": "#6c7086",
        "blue": "#FF6700",
        "cyan": "#FF8C33",
        "green": "#a6e3a1",
        "magenta": "#cba6f7",
        "orange": "#FF6700",
        "red": "#f38ba8",
        "yellow": "#f9e2af",
        "border": "#FF6700",
    },
    "mimo-light": {
        "bg": "#fafafa",
        "bg_alt": "#f0f0f0",
        "bg_highlight": "#e8e8e8",
        "fg": "#2d2d2d",
        "fg_dim": "#888888",
        "blue": "#E55A00",
        "cyan": "#FF6700",
        "green": "#2d8f40",
        "magenta": "#7c3d8f",
        "orange": "#E55A00",
        "red": "#cc2200",
        "yellow": "#997700",
        "border": "#E55A00",
    },
}

DEFAULT_THEME = "tokyonight"


def get_theme_css(theme_name: str) -> str:
    t = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    return f"""
$bg: {t['bg']};
$bg_alt: {t['bg_alt']};
$bg_highlight: {t['bg_highlight']};
$fg: {t['fg']};
$fg_dim: {t['fg_dim']};
$blue: {t['blue']};
$cyan: {t['cyan']};
$green: {t['green']};
$magenta: {t['magenta']};
$orange: {t['orange']};
$red: {t['red']};
$yellow: {t['yellow']};
$border: {t['border']};
"""
