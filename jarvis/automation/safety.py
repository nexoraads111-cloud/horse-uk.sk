"""Central action executor with confirmation hooks."""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable

from core.actions import ProposedAction, RiskLevel, needs_confirmation

logger = logging.getLogger(__name__)

ConfirmCallback = Callable[[ProposedAction, str], bool]


@dataclass
class ActionResult:
    success: bool
    message: str
    data: Any = None


class ActionExecutor:
    """Dispatches restricted actions. Shell never runs without approval."""

    def __init__(
        self,
        *,
        confirm_callback: ConfirmCallback | None = None,
        confirm_destructive: bool = True,
        confirm_shell: bool = True,
        apps=None,
        files=None,
        screenshot=None,
        cursor_ide=None,
        memory=None,
        vision=None,
        tasks_db=None,
    ) -> None:
        self.confirm_callback = confirm_callback
        self.confirm_destructive = confirm_destructive
        self.confirm_shell = confirm_shell
        self.apps = apps
        self.files = files
        self.screenshot = screenshot
        self.cursor_ide = cursor_ide
        self.memory = memory
        self.vision = vision
        self.tasks_db = tasks_db
        self._emergency_stop = False

    def emergency_stop(self) -> None:
        self._emergency_stop = True
        logger.warning("Emergency STOP engaged")

    def clear_stop(self) -> None:
        self._emergency_stop = False

    @property
    def stopped(self) -> bool:
        return self._emergency_stop

    def execute(self, action: ProposedAction, *, pre_approved: bool = False) -> ActionResult:
        if self._emergency_stop:
            return ActionResult(False, "Аварійна зупинка активна. Дії заблоковано.")

        if not pre_approved and needs_confirmation(
            action, self.confirm_destructive, self.confirm_shell
        ):
            reason = f"Дія «{action.name}» потребує підтвердження (ризик: {action.risk.value})."
            if self.confirm_callback is None or not self.confirm_callback(action, reason):
                return ActionResult(False, f"Відхилено: {reason}")

        try:
            return self._dispatch(action)
        except Exception as exc:
            logger.exception("Action failed: %s", action.name)
            return ActionResult(False, f"Помилка виконання: {exc}")

    def _dispatch(self, action: ProposedAction) -> ActionResult:
        name = action.name
        p = action.params

        if name == "list_apps":
            items = self.apps.list_installed() if self.apps else []
            running = self.apps.list_running() if self.apps else []
            return ActionResult(True, f"Знайдено {len(items)} програм, запущено {len(running)}.", {
                "installed": items[:50],
                "running": running[:50],
            })

        if name == "open_app":
            ok, msg = self.apps.open_app(str(p.get("name", "")))
            return ActionResult(ok, msg)

        if name == "switch_app":
            ok, msg = self.apps.switch_app(str(p.get("name", "")))
            return ActionResult(ok, msg)

        if name == "close_app":
            ok, msg = self.apps.close_app(str(p.get("name", "")))
            return ActionResult(ok, msg)

        if name == "open_path":
            ok, msg = self.files.open_path(str(p.get("path", "")))
            return ActionResult(ok, msg)

        if name == "screenshot":
            path = self.screenshot.capture()
            return ActionResult(True, f"Знімок збережено: {path}", {"path": str(path)})

        if name == "analyze_screen":
            path = self.screenshot.capture()
            question = str(p.get("question") or "Опиши, що видно на екрані українською.")
            answer = self.vision.analyze(path, question)
            return ActionResult(True, answer, {"path": str(path)})

        if name == "type_text":
            ok, msg = self.apps.type_text(str(p.get("text", "")))
            return ActionResult(ok, msg)

        if name == "remember":
            self.memory.remember(str(p.get("key", "")), str(p.get("value", "")))
            return ActionResult(True, f"Запам'ятав: {p.get('key')}")

        if name == "recall":
            val = self.memory.recall(str(p.get("key", "")))
            return ActionResult(True, val or "Нічого не знайдено.")

        if name == "cursor_launch":
            ok, msg = self.cursor_ide.launch()
            return ActionResult(ok, msg)

        if name == "cursor_open_project":
            ok, msg = self.cursor_ide.open_project(str(p.get("path", "")))
            return ActionResult(ok, msg)

        if name == "cursor_prepare_prompt":
            ok, msg = self.cursor_ide.prepare_prompt(str(p.get("prompt", "")))
            return ActionResult(ok, msg)

        if name == "set_task":
            tid = self.tasks_db.add_task(str(p.get("title", "Задача")))
            return ActionResult(True, f"Задачу додано (#{tid}).")

        if name == "run_shell":
            return self._run_shell_approved(str(p.get("command", "")))

        return ActionResult(False, f"Невідома дія: {name}")

    def _run_shell_approved(self, command: str) -> ActionResult:
        """Only called after explicit user approval."""
        if not command.strip():
            return ActionResult(False, "Порожня команда.")
        # Hard block obviously dangerous patterns even after approve prompt
        blocked = ["format ", "rm -rf /", "del /s /q c:\\", ":(){", "mkfs", "shutdown /s"]
        lower = command.lower()
        for b in blocked:
            if b in lower:
                return ActionResult(False, f"Команду заблоковано політикою безпеки: {b}")

        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=creationflags,
            )
            out = (completed.stdout or "")[-2000:]
            err = (completed.stderr or "")[-1000:]
            ok = completed.returncode == 0
            msg = out or err or f"Код виходу: {completed.returncode}"
            return ActionResult(ok, msg.strip() or "Готово.")
        except subprocess.TimeoutExpired:
            return ActionResult(False, "Таймаут команди (60с).")
