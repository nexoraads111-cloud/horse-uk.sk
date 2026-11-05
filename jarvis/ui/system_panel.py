"""System status and tasks panel (right)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ui.styles import THEME


class SystemPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)

        title = QLabel("СИСТЕМА / ЗАДАЧІ")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.ollama_lbl = QLabel("Ollama: …")
        self.ollama_lbl.setObjectName("statusDim")
        self.model_lbl = QLabel("Модель: —")
        self.model_lbl.setObjectName("statusDim")
        self.mic_lbl = QLabel("Мікрофон: готовий")
        self.mic_lbl.setObjectName("statusDim")
        self.monitor_lbl = QLabel("Моніторинг екрана: ВИМК")
        self.monitor_lbl.setObjectName("statusDim")
        self.stop_lbl = QLabel("STOP: неактивний")
        self.stop_lbl.setObjectName("statusDim")

        for w in (
            self.ollama_lbl,
            self.model_lbl,
            self.mic_lbl,
            self.monitor_lbl,
            self.stop_lbl,
        ):
            layout.addWidget(w)

        tasks_title = QLabel("ЗАДАЧІ")
        tasks_title.setObjectName("sectionTitle")
        layout.addWidget(tasks_title)
        self.tasks = QListWidget()
        layout.addWidget(self.tasks)

    def set_ollama(self, ok: bool, models: list[str] | None = None) -> None:
        if ok:
            self.ollama_lbl.setText("Ollama: підключено")
            self.ollama_lbl.setStyleSheet(f"color: {THEME['ok']};")
        else:
            self.ollama_lbl.setText("Ollama: недоступна")
            self.ollama_lbl.setStyleSheet(f"color: {THEME['danger']};")
        if models:
            self.model_lbl.setText("Моделі: " + ", ".join(models[:5]))

    def set_mic(self, text: str, active: bool = False) -> None:
        self.mic_lbl.setText(f"Мікрофон: {text}")
        color = THEME["ok"] if active else THEME["text_dim"]
        self.mic_lbl.setStyleSheet(f"color: {color};")

    def set_monitor(self, on: bool) -> None:
        if on:
            self.monitor_lbl.setText("Моніторинг екрана: УВІМК ●")
            self.monitor_lbl.setStyleSheet(f"color: {THEME['warn']}; font-weight:700;")
        else:
            self.monitor_lbl.setText("Моніторинг екрана: ВИМК")
            self.monitor_lbl.setStyleSheet(f"color: {THEME['text_dim']};")

    def set_stop(self, active: bool) -> None:
        if active:
            self.stop_lbl.setText("STOP: АКТИВНИЙ")
            self.stop_lbl.setStyleSheet(f"color: {THEME['danger']}; font-weight:800;")
        else:
            self.stop_lbl.setText("STOP: неактивний")
            self.stop_lbl.setStyleSheet(f"color: {THEME['text_dim']};")

    def set_tasks(self, tasks: list[dict]) -> None:
        self.tasks.clear()
        for t in tasks:
            item = QListWidgetItem(f"[{t.get('status','?')}] {t.get('title','')}")
            self.tasks.addItem(item)

    def set_model_name(self, name: str) -> None:
        self.model_lbl.setText(f"Модель чату: {name}")
