from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voice.vad import SimpleVAD


def test_vad_end_of_speech():
    vad = SimpleVAD(threshold=0.01, silence_ms=100, sample_rate=1000)
    speech = np.ones(100, dtype=np.float32) * 0.5
    silence = np.zeros(100, dtype=np.float32)
    assert vad.process(speech) == "speech"
    # 100ms silence needed; one chunk of 100 samples at 1000Hz = 100ms
    assert vad.process(silence) == "end"


def test_vad_idle_silence():
    vad = SimpleVAD(threshold=0.01, silence_ms=100, sample_rate=1000)
    silence = np.zeros(100, dtype=np.float32)
    assert vad.process(silence) == "silence"
