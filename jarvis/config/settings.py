"""Application settings loaded from SQLite + defaults.json."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import app_dir as _app_dir
from .paths import resource_path as _resource_path

APP_DIR = _app_dir()


def _default_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "JarvisAssistant"
    return Path.home() / ".jarvis_assistant"


DATA_DIR = Path(os.environ.get("JARVIS_DATA_DIR", str(_default_data_dir())))
DEFAULTS_PATH = _resource_path("config", "defaults.json")
if not DEFAULTS_PATH.exists():
    # Dev / package-local fallback
    DEFAULTS_PATH = Path(__file__).with_name("defaults.json")


def _load_defaults() -> dict[str, Any]:
    with DEFAULTS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


class Settings:
    """Mutable settings backed by a dict; persist via database layer."""

    def __init__(self, values: dict[str, Any] | None = None) -> None:
        self._values = _load_defaults()
        if values:
            self._values.update(values)

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value

    def update(self, mapping: dict[str, Any]) -> None:
        self._values.update(mapping)

    def as_dict(self) -> dict[str, Any]:
        return deepcopy(self._values)

    def ensure_dirs(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "screenshots").mkdir(exist_ok=True)
        (DATA_DIR / "voices").mkdir(exist_ok=True)
        (DATA_DIR / "models").mkdir(exist_ok=True)
        (DATA_DIR / "logs").mkdir(exist_ok=True)

    @property
    def db_path(self) -> Path:
        return DATA_DIR / "jarvis.db"

    @property
    def ollama_base_url(self) -> str:
        return str(self._values.get("ollama_base_url", "http://127.0.0.1:11434")).rstrip("/")


_settings: Settings | None = None


def get_settings(reload: bool = False) -> Settings:
    global _settings
    if _settings is None or reload:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings
