from __future__ import annotations

import base64
import io
from dataclasses import dataclass


@dataclass
class AudioData:
    raw: bytes
    mime_type: str
    sample_rate: int = 22050
    channels: int = 1


def decode_base64_audio(b64_str: str, mime_type: str = "audio/wav") -> AudioData:
    raw = base64.b64decode(b64_str)
    return AudioData(raw=raw, mime_type=mime_type)


def detect_mime(data: bytes) -> str:
    if data[:4] == b"RIFF":
        return "audio/wav"
    if data[:3] == b"ID3" or data[:2] == b"\xff\xfb":
        return "audio/mpeg"
    if data[:4] == b"OggS":
        return "audio/ogg"
    return "audio/wav"


def to_numpy(audio: AudioData) -> "tuple[object, int]":
    """Decode audio bytes to numpy array + sample_rate for sounddevice."""
    import numpy as np

    mime = audio.mime_type or detect_mime(audio.raw)
    if mime in ("audio/wav", "audio/x-wav"):
        import scipy.io.wavfile as wav  # type: ignore[import-untyped]
        sr, data = wav.read(io.BytesIO(audio.raw))
        if data.dtype.kind == "i":
            data = data.astype(np.float32) / np.iinfo(data.dtype).max
        return data, sr
    # fallback: try soundfile
    try:
        import soundfile as sf  # type: ignore[import-untyped]
        data, sr = sf.read(io.BytesIO(audio.raw))
        return data, sr
    except Exception:
        raise ValueError(f"Cannot decode audio format: {mime}")
