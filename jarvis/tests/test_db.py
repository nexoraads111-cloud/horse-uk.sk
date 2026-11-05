"""SQLite persistence tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.db import Database
from database.memory import MemoryStore


def test_settings_roundtrip(tmp_path):
    db = Database(tmp_path / "t.db")
    db.save_settings({"chat_model": "llama3.2", "tts_speed": 1.2})
    loaded = db.load_settings()
    assert loaded["chat_model"] == "llama3.2"
    assert loaded["tts_speed"] == 1.2


def test_messages_and_memory(tmp_path):
    db = Database(tmp_path / "t.db")
    db.add_message("user", "Привіт")
    db.add_message("assistant", "Вітаю")
    msgs = db.get_messages()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"

    mem = MemoryStore(db)
    mem.remember("ім'я", "Укстав", "profile")
    assert mem.recall("ім'я") == "Укстав"
    snippet = mem.context_snippet()
    assert "Укстав" in snippet
    assert mem.forget("ім'я") is True
    assert mem.recall("ім'я") is None


def test_tasks(tmp_path):
    db = Database(tmp_path / "t.db")
    tid = db.add_task("Перевірити Ollama")
    db.update_task(tid, "done")
    tasks = db.list_tasks()
    assert tasks[0]["status"] == "done"
