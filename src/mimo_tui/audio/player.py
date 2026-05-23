"""Async audio playback via sounddevice (optional dependency)."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from mimo_tui.audio.formats import AudioData, to_numpy
from mimo_tui.utils.logging import get_logger

log = get_logger(__name__)


class AudioPlayer:
    """Thread-safe async audio player wrapping sounddevice."""

    def __init__(self, on_state_change: Callable[[bool], None] | None = None) -> None:
        self._stop_event = threading.Event()
        self._playing = False
        self._on_state_change = on_state_change

    @property
    def is_playing(self) -> bool:
        return self._playing

    def stop(self) -> None:
        self._stop_event.set()
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._playing = False
        if self._on_state_change:
            self._on_state_change(False)

    async def play(self, audio: AudioData) -> None:
        import anyio
        await anyio.to_thread.run_sync(self._play_sync, audio)

    def _play_sync(self, audio: AudioData) -> None:
        try:
            import sounddevice as sd  # type: ignore[import-untyped]
            data, sr = to_numpy(audio)
            self._stop_event.clear()
            self._playing = True
            if self._on_state_change:
                self._on_state_change(True)
            sd.play(data, samplerate=sr)
            sd.wait()
        except ImportError:
            log.warning("sounddevice not installed; audio playback unavailable")
        except Exception as e:
            log.error("audio playback error", error=str(e))
        finally:
            self._playing = False
            if self._on_state_change:
                self._on_state_change(False)

    def save(self, audio: AudioData, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio.raw)
        log.info("audio saved", path=str(path))
