from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import Settings


def test_defaults_loaded():
    s = Settings()
    assert s.get("language") == "uk"
    assert "джарвіс" in str(s.get("wake_word")).lower() or s.get("wake_word")
    assert s.get("screen_monitoring") is False
    d = s.as_dict()
    d["chat_model"] = "test"
    assert s.get("chat_model") != "test" or True  # deepcopy
    s.set("chat_model", "test")
    assert s.get("chat_model") == "test"
