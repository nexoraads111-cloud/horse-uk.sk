"""Assistant reply parsing integration (mocked Ollama)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import Settings
from core.assistant import JarvisAssistant
from database.db import Database


class FakeOllama:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.base_url = "http://test"

    def is_available(self) -> bool:
        return True

    def list_models(self):
        return ["llama3.2"]

    def chat(self, messages, model, stream=False, on_token=None):
        if on_token:
            on_token(self.reply)
        return self.reply


def test_chat_executes_safe_action(tmp_path):
    db = Database(tmp_path / "a.db")
    settings = Settings({"chat_model": "llama3.2", "memory_enabled": False})
    assistant = JarvisAssistant(settings, db)
    assistant.ollama = FakeOllama(
        'Відкриваю.\n```json\n{"action":"open_app","name":"x"}\n```'
    )

    class Apps:
        def open_app(self, name):
            return True, f"ok:{name}"

        def list_installed(self):
            return []

        def list_running(self):
            return []

        def update_shortcuts(self, *_):
            pass

    assistant.apps = Apps()
    assistant.executor.apps = assistant.apps

    reply, results = assistant.chat("відкрий x", execute_actions=True)
    assert results and results[0].success
    assert "ok:x" in results[0].message
