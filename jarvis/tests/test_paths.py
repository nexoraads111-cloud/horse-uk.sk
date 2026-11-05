from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.paths import app_dir, resource_path


def test_resource_defaults_json():
    p = resource_path("config", "defaults.json")
    assert p.exists()
    assert p.name == "defaults.json"


def test_app_dir_is_jarvis_root():
    assert (app_dir() / "main.py").exists()
