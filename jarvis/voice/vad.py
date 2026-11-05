"""Simple energy-based VAD for push-to-talk / end-of-utterance."""

from __future__ import annotations

import numpy as np


class SimpleVAD:
    def __init__(self, threshold: float = 0.015, silence_ms: int = 800, sample_rate: int = 16000) -> None:
        self.threshold = threshold
        self.silence_ms = silence_ms
        self.sample_rate = sample_rate
        self._silent_samples = 0
        self._speech_started = False

    def reset(self) -> None:
        self._silent_samples = 0
        self._speech_started = False

    def is_speech(self, chunk: np.ndarray) -> bool:
        if chunk.size == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(chunk.astype(np.float32)))))
        return rms >= self.threshold

    def process(self, chunk: np.ndarray) -> str:
        """
        Feed audio chunk; returns state: 'silence' | 'speech' | 'end'.
        """
        speaking = self.is_speech(chunk)
        if speaking:
            self._speech_started = True
            self._silent_samples = 0
            return "speech"
        if not self._speech_started:
            return "silence"
        self._silent_samples += len(chunk)
        silence_needed = int(self.sample_rate * (self.silence_ms / 1000.0))
        if self._silent_samples >= silence_needed:
            self.reset()
            return "end"
        return "silence"
