"""Optional simple wake-word detection for «Джарвіс» via STT snippets."""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Callable

import numpy as np

logger = logging.getLogger(__name__)


class WakeWordListener:
    """Lightweight wake-word: short STT windows looking for the phrase."""

    def __init__(
        self,
        stt,
        phrase: str = "джарвіс",
        sample_rate: int = 16000,
        device: int | None = None,
        on_detect: Callable[[], None] | None = None,
    ) -> None:
        self.stt = stt
        self.phrase = phrase.lower().strip()
        self.sample_rate = sample_rate
        self.device = device
        self.on_detect = on_detect
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._enabled = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._enabled = False
        self._stop.set()

    def _normalize(self, text: str) -> str:
        t = text.lower().replace("'", "'")
        t = re.sub(r"[^\wа-яіїєґ\s]", " ", t, flags=re.IGNORECASE)
        # common STT variants
        t = t.replace("jarvis", "джарвіс").replace("джервіс", "джарвіс")
        return " ".join(t.split())

    def _loop(self) -> None:
        try:
            import sounddevice as sd
        except Exception:
            logger.error("sounddevice required for wake word")
            self._enabled = False
            return

        window = int(self.sample_rate * 1.5)
        while not self._stop.is_set():
            try:
                audio = sd.rec(
                    window,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    device=self.device,
                )
                sd.wait()
                if self._stop.is_set():
                    break
                mono = audio[:, 0] if audio.ndim > 1 else audio
                if float(np.max(np.abs(mono))) < 0.01:
                    continue
                text = self.stt.transcribe_array(mono, sample_rate=self.sample_rate)
                norm = self._normalize(text)
                if self.phrase in norm:
                    logger.info("Wake word detected: %s", text)
                    if self.on_detect:
                        self.on_detect()
                    time.sleep(1.0)
            except Exception:
                logger.exception("Wake word loop error")
                time.sleep(1.0)
        self._enabled = False
