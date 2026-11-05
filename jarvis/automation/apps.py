"""Discover / open / switch / close applications (Windows-first)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class AppController:
    def __init__(self, shortcuts: dict[str, str] | None = None) -> None:
        self.shortcuts = {k.lower(): v for k, v in (shortcuts or {}).items()}

    def update_shortcuts(self, shortcuts: dict[str, str]) -> None:
        self.shortcuts = {k.lower(): v for k, v in shortcuts.items()}

    def list_running(self) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info["name"] or ""
                if not name or name.lower() in seen:
                    continue
                seen.add(name.lower())
                result.append({"pid": proc.info["pid"], "name": name})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(result, key=lambda x: x["name"].lower())

    def list_installed(self) -> list[dict[str, str]]:
        """Best-effort discovery of installed apps."""
        found: list[dict[str, str]] = []
        if sys.platform == "win32":
            found.extend(self._windows_start_menu())
            found.extend(self._windows_registry_hint())
        else:
            # Linux fallback for CI / development
            for name in ("firefox", "chromium", "code", "cursor", "gedit", "nautilus"):
                path = shutil.which(name)
                if path:
                    found.append({"name": name, "path": path})
        # merge shortcuts
        for name, path in self.shortcuts.items():
            found.append({"name": name, "path": path})
        # dedupe by name
        uniq: dict[str, dict[str, str]] = {}
        for item in found:
            uniq[item["name"].lower()] = item
        return sorted(uniq.values(), key=lambda x: x["name"].lower())

    def _windows_start_menu(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        roots = []
        appdata = os.environ.get("APPDATA")
        programdata = os.environ.get("PROGRAMDATA")
        if appdata:
            roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
        if programdata:
            roots.append(Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
        for root in roots:
            if not root.exists():
                continue
            for lnk in root.rglob("*.lnk"):
                items.append({"name": lnk.stem, "path": str(lnk)})
                if len(items) > 400:
                    return items
        return items

    def _windows_registry_hint(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        if sys.platform != "win32":
            return items
        try:
            import winreg  # type: ignore

            for hive, sub in (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            ):
                try:
                    with winreg.OpenKey(hive, sub) as key:
                        i = 0
                        while True:
                            try:
                                name = winreg.EnumKey(key, i)
                                i += 1
                                with winreg.OpenKey(key, name) as appkey:
                                    path, _ = winreg.QueryValueEx(appkey, None)
                                    items.append({"name": Path(name).stem, "path": str(path)})
                            except OSError:
                                break
                except OSError:
                    continue
        except ImportError:
            pass
        return items

    def resolve(self, name: str) -> str | None:
        key = name.lower().strip()
        if key in self.shortcuts:
            return self.shortcuts[key]
        for item in self.list_installed():
            if item["name"].lower() == key or key in item["name"].lower():
                return item["path"]
        which = shutil.which(name)
        return which

    def open_app(self, name: str) -> tuple[bool, str]:
        if not name.strip():
            return False, "Не вказано назву програми."
        path = self.resolve(name)
        if not path:
            # try bare name via start / shell
            if sys.platform == "win32":
                try:
                    subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
                    return True, f"Спроба відкрити «{name}» через start."
                except Exception as exc:
                    return False, f"Не вдалося відкрити: {exc}"
            return False, f"Програму «{name}» не знайдено."
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen([path], start_new_session=True)
            return True, f"Відкриваю: {path}"
        except Exception as exc:
            return False, f"Помилка відкриття: {exc}"

    def switch_app(self, name: str) -> tuple[bool, str]:
        target = name.lower().strip()
        if sys.platform == "win32":
            try:
                import win32gui  # type: ignore
                import win32con  # type: ignore

                found = []

                def enum_handler(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title and target in title.lower():
                            found.append(hwnd)

                win32gui.EnumWindows(enum_handler, None)
                if not found:
                    return False, f"Вікно «{name}» не знайдено."
                hwnd = found[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return True, f"Перемкнувся на вікно «{name}»."
            except Exception as exc:
                return False, f"Не вдалося перемкнути вікно: {exc}"
        # Linux: best-effort via wmctrl if present
        if shutil.which("wmctrl"):
            r = subprocess.run(["wmctrl", "-a", name], capture_output=True, text=True)
            if r.returncode == 0:
                return True, f"Перемкнувся на «{name}»."
        return False, "Перемикання вікон підтримується повністю лише на Windows."

    def close_app(self, name: str) -> tuple[bool, str]:
        target = name.lower().strip()
        closed = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = (proc.info["name"] or "").lower()
                if target in pname or pname.startswith(target):
                    proc.terminate()
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if closed:
            return True, f"Закрито процесів: {closed}."
        return False, f"Процес «{name}» не знайдено."

    def type_text(self, text: str) -> tuple[bool, str]:
        if not text:
            return False, "Порожній текст."
        try:
            import pyautogui

            pyautogui.typewrite(text, interval=0.02) if text.isascii() else None
            # unicode-friendly path
            try:
                import pyperclip  # optional

                pyperclip.copy(text)
                if sys.platform == "win32":
                    pyautogui.hotkey("ctrl", "v")
                else:
                    pyautogui.hotkey("ctrl", "v")
                return True, "Текст вставлено."
            except Exception:
                if text.isascii():
                    pyautogui.write(text, interval=0.02)
                    return True, "Текст введено."
                return False, "Для Unicode-тексту потрібен буфер обміну (pyperclip)."
        except Exception as exc:
            return False, f"Не вдалося ввести текст: {exc}"
