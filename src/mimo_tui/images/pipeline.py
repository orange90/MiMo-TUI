"""Image → base64 encoding for multimodal API requests."""
from __future__ import annotations

import base64
import io
from pathlib import Path


def image_to_b64(path: Path, max_dim: int = 1568) -> tuple[str, str]:
    """Return (base64_string, mime_type) for the given image path."""
    from PIL import Image  # type: ignore[import-untyped]

    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)

    fmt = img.format or "JPEG"
    mime = f"image/{fmt.lower()}"
    buf = io.BytesIO()
    img.save(buf, format=fmt if fmt in ("JPEG", "PNG", "GIF", "WEBP") else "JPEG")
    return base64.b64encode(buf.getvalue()).decode(), mime


def build_image_content(path: Path) -> dict[str, object]:
    """Build an OpenAI-style image_url content block."""
    b64, mime = image_to_b64(path)
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}"},
    }
