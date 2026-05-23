"""Tests for audio format detection and decoding."""
import base64
import struct
import wave
import io
import pytest

from mimo_tui.audio.formats import decode_base64_audio, detect_mime


def _make_wav_bytes() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00\x00" * 100)
    return buf.getvalue()


def test_detect_wav() -> None:
    wav_bytes = _make_wav_bytes()
    assert detect_mime(wav_bytes) == "audio/wav"


def test_detect_mp3() -> None:
    mp3_bytes = b"\xff\xfb" + b"\x00" * 10
    assert detect_mime(mp3_bytes) == "audio/mpeg"


def test_decode_base64() -> None:
    wav_bytes = _make_wav_bytes()
    b64 = base64.b64encode(wav_bytes).decode()
    audio = decode_base64_audio(b64, "audio/wav")
    assert audio.raw == wav_bytes
    assert audio.mime_type == "audio/wav"
