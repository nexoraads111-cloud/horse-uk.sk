"""Main JARVIS orchestrator — chat, voice, actions."""

from __future__ import annotations

import logging
from typing import Any, Callable

from automation.apps import AppController
from automation.cursor_ide import CursorIDE
from automation.files import FileController
from automation.safety import ActionExecutor, ActionResult
from automation.screenshot import ScreenshotService
from config.settings import Settings
from core.actions import action_help_for_prompt, parse_actions_from_reply
from core.ollama_client import OllamaClient, OllamaError
from database.db import Database
from database.memory import MemoryStore
from vision.analyzer import VisionAnalyzer

logger = logging.getLogger(__name__)

TokenCallback = Callable[[str], None]
ReplyCallback = Callable[[str], None]


class JarvisAssistant:
    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings = settings
        self.db = db
        self.memory = MemoryStore(db)
        self.ollama = OllamaClient(settings.ollama_base_url)
        self.apps = AppController(settings.get("app_shortcuts") or {})
        self.files = FileController()
        self.screenshot = ScreenshotService()
        self.cursor_ide = CursorIDE(
            settings.get("cursor_path") or "",
            settings.get("project_folders") or [],
        )
        self.vision = VisionAnalyzer(
            self.ollama, model=str(settings.get("vision_model") or "llava")
        )
        self.executor = ActionExecutor(
            confirm_destructive=bool(settings.get("confirm_destructive", True)),
            confirm_shell=bool(settings.get("confirm_shell", True)),
            apps=self.apps,
            files=self.files,
            screenshot=self.screenshot,
            cursor_ide=self.cursor_ide,
            memory=self.memory,
            vision=self.vision,
            tasks_db=db,
        )
        self._history: list[dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        for msg in self.db.get_messages(limit=40):
            self._history.append({"role": msg["role"], "content": msg["content"]})

    def reload_settings(self) -> None:
        self.ollama = OllamaClient(self.settings.ollama_base_url)
        self.vision.set_model(str(self.settings.get("vision_model") or "llava"))
        self.apps.update_shortcuts(self.settings.get("app_shortcuts") or {})
        self.cursor_ide.update(
            self.settings.get("cursor_path") or "",
            self.settings.get("project_folders") or [],
        )
        self.executor.confirm_destructive = bool(
            self.settings.get("confirm_destructive", True)
        )
        self.executor.confirm_shell = bool(self.settings.get("confirm_shell", True))

    def set_confirm_callback(self, cb) -> None:
        self.executor.confirm_callback = cb

    def emergency_stop(self) -> None:
        self.executor.emergency_stop()

    def clear_stop(self) -> None:
        self.executor.clear_stop()

    def status(self) -> dict[str, Any]:
        return {
            "ollama": self.ollama.is_available(),
            "models": self.ollama.list_models() if self.ollama.is_available() else [],
            "monitoring": bool(self.settings.get("screen_monitoring")),
            "stopped": self.executor.stopped,
            "memory_count": len(self.memory.list_all()),
        }

    def _system_message(self) -> dict[str, str]:
        base = str(self.settings.get("system_prompt") or "")
        mem = ""
        if self.settings.get("memory_enabled", True):
            mem = self.memory.context_snippet()
        help_txt = action_help_for_prompt()
        content = "\n\n".join(x for x in (base, mem, help_txt) if x)
        return {"role": "system", "content": content}

    def chat(
        self,
        user_text: str,
        *,
        on_token: TokenCallback | None = None,
        execute_actions: bool = True,
    ) -> tuple[str, list[ActionResult]]:
        user_text = user_text.strip()
        if not user_text:
            return "", []

        self.db.add_message("user", user_text)
        self._history.append({"role": "user", "content": user_text})

        messages = [self._system_message()] + self._history[-20:]
        model = str(self.settings.get("chat_model") or "llama3.2")

        try:
            reply = self.ollama.chat(
                messages,
                model=model,
                stream=on_token is not None,
                on_token=on_token,
            )
        except OllamaError as exc:
            err = str(exc)
            self.db.add_message("assistant", err)
            self._history.append({"role": "assistant", "content": err})
            return err, []

        clean, actions = parse_actions_from_reply(reply)
        if not clean and reply:
            clean = reply

        self.db.add_message("assistant", clean)
        self._history.append({"role": "assistant", "content": clean})

        results: list[ActionResult] = []
        if execute_actions:
            for act in actions:
                result = self.executor.execute(act)
                results.append(result)
                self.db.log_action(
                    act.name,
                    detail=str(act.params),
                    approved=True,
                    success=result.success,
                )
                if result.message:
                    note = f"[Дія {act.name}] {result.message}"
                    self.db.add_message("assistant", note)
                    self._history.append({"role": "assistant", "content": note})
                    clean = (clean + "\n\n" + note).strip()

        return clean, results

    def clear_chat(self) -> None:
        self._history.clear()
        self.db.clear_messages()
