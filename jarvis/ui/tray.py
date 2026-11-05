"""System tray icon and menu."""

from __future__ import annotations

from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from ui.styles import THEME


def make_tray_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(THEME["cyan"]))
    p.setPen(QColor(THEME["bg"]))
    p.drawEllipse(4, 4, 56, 56)
    p.setPen(QColor(THEME["bg"]))
    p.drawText(pix.rect(), 0x84, "J")  # AlignCenter
    p.end()
    return QIcon(pix)


class TrayController:
    def __init__(self, window) -> None:
        self.window = window
        self.tray = QSystemTrayIcon(make_tray_icon(), window)
        self.tray.setToolTip("JARVIS AI Assistant")
        menu = QMenu()
        show_act = QAction("Показати", window)
        show_act.triggered.connect(window.showNormal)
        hide_act = QAction("Згорнути в трей", window)
        hide_act.triggered.connect(window.hide)
        stop_act = QAction("Аварійна STOP", window)
        stop_act.triggered.connect(window.on_emergency_stop)
        quit_act = QAction("Вийти", window)
        quit_act.triggered.connect(window.clean_shutdown)
        menu.addAction(show_act)
        menu.addAction(hide_act)
        menu.addSeparator()
        menu.addAction(stop_act)
        menu.addSeparator()
        menu.addAction(quit_act)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)
        self.tray.show()

    def _activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.window.showNormal()
                self.window.raise_()
                self.window.activateWindow()

    def notify(self, title: str, body: str) -> None:
        self.tray.showMessage(title, body, QSystemTrayIcon.MessageIcon.Information, 3000)
