from __future__ import annotations

import os
import subprocess
from typing import Literal

ImageProtocol = Literal["kitty", "iterm2", "sixel", "ascii"]


def detect_image_protocol() -> ImageProtocol:
    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program in ("iTerm.app", "WezTerm"):
        return "iterm2"
    if _supports_sixel():
        return "sixel"
    return "ascii"


def _supports_sixel() -> bool:
    try:
        result = subprocess.run(
            ["tput", "colors"],
            capture_output=True,
            timeout=1,
        )
        return False  # conservative; full sixel detection needs terminfo query
    except Exception:
        return False
