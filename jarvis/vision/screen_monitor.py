"""Optional periodic screen monitoring — OFF by default."""

from __future__ import annotations

import logging
from typing import Any, Callable

from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)


class ScreenMonitor(QObject):
    captured = Signal(str)  # path
    analyzed = Signal(str)  # summary
    status_changed = Signal(bool)

    def __init__(
        self,
        screenshot_service,
        vision: Any = None,
        interval_sec: int = 30,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.screenshot = screenshot_service
        self.vision = vision
        self.interval_sec = max(5, int(interval_sec))
        self._enabled = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.on_result: Callable[[str], None] | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_interval(self, sec: int) -> None:
        self.interval_sec = max(5, int(sec))
        if self._enabled:
            self._timer.start(self.interval_sec * 1000)

    def start(self) -> None:
        self._enabled = True
        self._timer.start(self.interval_sec * 1000)
        self.status_changed.emit(True)
        logger.info("Screen monitoring ON (%ss)", self.interval_sec)

    def stop(self) -> None:
        self._enabled = False
        self._timer.stop()
        self.status_changed.emit(False)
        logger.info("Screen monitoring OFF")

    def _tick(self) -> None:
        if not self._enabled:
            return
        try:
            path = self.screenshot.capture()
            self.captured.emit(str(path))
            if self.vision:
                summary = self.vision.analyze(
                    path,
                    "Коротко українською: що змінилось / що зараз на екрані? 1-2 речення.",
                )
                self.analyzed.emit(summary)
                if self.on_result:
                    self.on_result(summary)
        except Exception:
            logger.exception("Screen monitor tick failed")
