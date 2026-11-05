"""Speech-to-text via faster-whisper (Ukrainian)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class SpeechToText:
    def __init__(
        self,
        model_size: str = "base",
        language: str = "uk",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded: %s", self.model_size)
        except Exception as exc:
            logger.error("Failed to load Whisper: %s", exc)
            raise

    @property
    def ready(self) -> bool:
        return self._model is not None

    def transcribe_array(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._model is None:
            self.load()
        assert self._model is not None
        # faster-whisper expects float32 mono
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        # normalize if int-like range leaked in
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 1.0:
            audio = audio / peak
        segments, _info = self._model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,
        )
        parts = [seg.text.strip() for seg in segments if seg.text.strip()]
        return " ".join(parts).strip()

    def transcribe_file(self, path: Path | str) -> str:
        if self._model is None:
            self.load()
        assert self._model is not None
        segments, _ = self._model.transcribe(str(path), language=self.language)
        return " ".join(s.text.strip() for s in segments if s.text.strip()).strip()

    def record_and_transcribe(
        self,
        duration_sec: float = 5.0,
        sample_rate: int = 16000,
        device: int | None = None,
        vad=None,
        max_sec: float = 30.0,
    ) -> str:
        """Record from mic until VAD end or duration, then transcribe."""
        try:
            import sounddevice as sd
        except Exception as exc:
            raise RuntimeError(f"sounddevice недоступний: {exc}") from exc

        chunks: list[np.ndarray] = []
        if vad is not None:
            vad.reset()

        block = int(sample_rate * 0.1)

        def callback(indata, frames, time_info, status):  # noqa: ARG001
            mono = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
            chunks.append(mono)
            if vad is not None and vad.process(mono) == "end":
                raise sd.CallbackStop()

        try:
            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block,
                device=device,
                callback=callback,
            ):
                if vad is not None:
                    sd.sleep(int(max_sec * 1000))
                else:
                    sd.sleep(int(duration_sec * 1000))
        except Exception as exc:
            # CallbackStop ends recording normally
            if "CallbackStop" not in type(exc).__name__ and "CallbackStop" not in str(exc):
                logger.debug("record end: %s", exc)

        if not chunks:
            return ""
        audio = np.concatenate(chunks)
        return self.transcribe_array(audio, sample_rate=sample_rate)
