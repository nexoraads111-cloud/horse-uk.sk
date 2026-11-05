"""Animated circular audio visualizer."""

from __future__ import annotations

import math
import random

from PySide6.QtCore import QTimer, Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient, QBrush
from PySide6.QtWidgets import QWidget

from ui.styles import THEME


class CircularVisualizer(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self._level = 0.08
        self._phase = 0.0
        self._state = "idle"  # idle | listening | speaking | thinking
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_state(self, state: str) -> None:
        self._state = state

    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(1.0, float(level)))

    def _tick(self) -> None:
        speed = {"idle": 0.04, "listening": 0.12, "speaking": 0.18, "thinking": 0.09}.get(
            self._state, 0.04
        )
        self._phase += speed
        if self._state == "idle":
            self._level = 0.08 + 0.03 * math.sin(self._phase)
        elif self._state == "thinking":
            self._level = 0.25 + 0.1 * abs(math.sin(self._phase * 2))
        elif self._state == "listening":
            self._level = max(self._level * 0.85, 0.2 + random.random() * 0.35)
        elif self._state == "speaking":
            self._level = 0.35 + 0.4 * abs(math.sin(self._phase * 3))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) * 0.35

        # glow
        glow_r = radius * (1.2 + self._level * 0.6)
        grad = QRadialGradient(cx, cy, glow_r)
        cyan = QColor(THEME["cyan"])
        cyan.setAlpha(40 + int(80 * self._level))
        grad.setColorAt(0.0, cyan)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # rings
        for i in range(3):
            r = radius * (0.7 + i * 0.18) * (1 + self._level * 0.15)
            pen = QPen(QColor(THEME["cyan"]))
            pen.setWidthF(1.5 + self._level * 2)
            alpha = 180 - i * 40
            c = QColor(THEME["cyan"])
            c.setAlpha(alpha)
            pen.setColor(c)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # arc sweep
        pen = QPen(QColor(THEME["cyan"]))
        pen.setWidth(3)
        painter.setPen(pen)
        sweep = 60 + int(self._level * 100)
        start = int((self._phase * 57.3) % 360) * 16
        r = radius * (1.05 + self._level * 0.2)
        painter.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), start, sweep * 16)

        # core
        core = radius * 0.35
        core_grad = QRadialGradient(cx, cy, core)
        core_grad.setColorAt(0.0, QColor(THEME["cyan"]))
        core_grad.setColorAt(1.0, QColor(THEME["bg_panel"]))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - core, cy - core, core * 2, core * 2))
