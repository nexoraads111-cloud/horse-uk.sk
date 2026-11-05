#!/usr/bin/env python3
"""JARVIS AI Assistant — entry point."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Ensure package root is on sys.path when launched as script / from .bat / frozen
if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent
    # PyInstaller extracts pure-Python packages into _MEIPASS
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and meipass not in sys.path:
        sys.path.insert(0, meipass)
else:
    ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config.settings import get_settings
from database.db import Database
from core.assistant import JarvisAssistant
from ui.main_window import MainWindow
from ui.styles import STYLESHEET


def setup_logging() -> None:
    settings = get_settings()
    log_dir = settings.db_path.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "jarvis.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    # HiDPI
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    setup_logging()
    log = logging.getLogger("jarvis")

    settings = get_settings()
    settings.ensure_dirs()

    db = Database(settings.db_path)
    stored = db.load_settings()
    if stored:
        settings.update(stored)

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setOrganizationName("JarvisAssistant")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    # Keep running when last window hidden (tray)
    app.setQuitOnLastWindowClosed(False)

    assistant = JarvisAssistant(settings, db)
    window = MainWindow(settings, db, assistant)
    window.show()
    log.info("JARVIS started")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
