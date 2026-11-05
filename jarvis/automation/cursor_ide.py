"""Cursor IDE integration: launch, open project, prepare prompts."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class CursorIDE:
    def __init__(self, cursor_path: str = "", project_folders: list[str] | None = None) -> None:
        self.cursor_path = cursor_path.strip()
        self.project_folders = project_folders or []
        self._pending_prompt: str | None = None

    def update(self, cursor_path: str = "", project_folders: list[str] | None = None) -> None:
        if cursor_path is not None:
            self.cursor_path = cursor_path.strip()
        if project_folders is not None:
            self.project_folders = project_folders

    def find_executable(self) -> str | None:
        if self.cursor_path and Path(self.cursor_path).exists():
            return self.cursor_path
        candidates = [
            shutil.which("cursor"),
            shutil.which("Cursor"),
        ]
        if sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA", "")
            candidates.extend(
                [
                    str(Path(local) / "Programs" / "cursor" / "Cursor.exe"),
                    str(Path(local) / "Programs" / "Cursor" / "Cursor.exe"),
                    r"C:\Program Files\Cursor\Cursor.exe",
                    r"C:\Users\{}\AppData\Local\Programs\cursor\Cursor.exe".format(
                        os.environ.get("USERNAME", "")
                    ),
                ]
            )
        else:
            candidates.extend(
                [
                    str(Path.home() / ".local" / "bin" / "cursor"),
                    "/usr/bin/cursor",
                    "/opt/Cursor/cursor",
                ]
            )
        for c in candidates:
            if c and Path(c).exists():
                return c
        return shutil.which("cursor")

    def launch(self) -> tuple[bool, str]:
        exe = self.find_executable()
        if not exe:
            return False, (
                "Cursor не знайдено. Вкажіть шлях у налаштуваннях "
                "або додайте cursor до PATH."
            )
        try:
            subprocess.Popen([exe], start_new_session=True)
            return True, f"Cursor запущено: {exe}"
        except Exception as exc:
            return False, f"Не вдалося запустити Cursor: {exc}"

    def open_project(self, path: str) -> tuple[bool, str]:
        project = Path(path).expanduser()
        if not project.exists():
            # try match configured project folders by name
            for folder in self.project_folders:
                fp = Path(folder)
                if fp.name.lower() == path.lower() or path.lower() in str(fp).lower():
                    project = fp
                    break
        if not project.exists():
            return False, f"Проєкт не знайдено: {path}"
        exe = self.find_executable()
        if not exe:
            return False, "Cursor не знайдено."
        try:
            subprocess.Popen([exe, str(project)], start_new_session=True)
            return True, f"Відкрито проєкт у Cursor: {project}"
        except Exception as exc:
            return False, f"Помилка: {exc}"

    def prepare_prompt(self, prompt: str) -> tuple[bool, str]:
        """Store prompt for clipboard insert after user confirmation."""
        if not prompt.strip():
            return False, "Порожній промпт."
        self._pending_prompt = prompt
        try:
            self._copy_to_clipboard(prompt)
            return True, (
                "Промпт скопійовано в буфер. Відкрийте чат Cursor і вставте (Ctrl+V). "
                "Вставка автоматично не виконувалась без підтвердження."
            )
        except Exception as exc:
            return False, f"Промпт збережено локально, але буфер недоступний: {exc}"

    def insert_pending_after_confirm(self) -> tuple[bool, str]:
        """Paste pending prompt into the active window (user confirmed)."""
        if not self._pending_prompt:
            return False, "Немає підготовленого промпту."
        try:
            self._copy_to_clipboard(self._pending_prompt)
            import pyautogui

            pyautogui.hotkey("ctrl", "v")
            self._pending_prompt = None
            return True, "Промпт вставлено у активне вікно."
        except Exception as exc:
            return False, f"Не вдалося вставити: {exc}"

    def verify_running(self) -> bool:
        import psutil

        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if "cursor" in name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        try:
            import pyperclip

            pyperclip.copy(text)
            return
        except Exception:
            pass
        if sys.platform == "win32":
            # PowerShell fallback
            subprocess.run(
                ["powershell", "-Command", f"Set-Clipboard -Value @'\n{text}\n'@"],
                check=False,
                capture_output=True,
            )
        else:
            if shutil.which("xclip"):
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"))
            elif shutil.which("wl-copy"):
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"))
            else:
                raise RuntimeError("Немає інструмента для буфера обміну")
