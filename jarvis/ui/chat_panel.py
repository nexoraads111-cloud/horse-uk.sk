"""Chat history panel (left)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QTextEdit, QVBoxLayout

from ui.styles import THEME


class ChatPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        title = QLabel("ІСТОРІЯ ЧАТУ")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.view = QTextEdit()
        self.view.setReadOnly(True)
        self.view.setPlaceholderText("Тут з'явиться розмова з Джарвісом…")
        layout.addWidget(self.view)

    def clear(self) -> None:
        self.view.clear()

    def append_message(self, role: str, text: str) -> None:
        if role == "user":
            color = THEME["cyan"]
            label = "Ви"
        elif role == "system":
            color = THEME["warn"]
            label = "Система"
        else:
            color = THEME["ok"]
            label = "Джарвіс"
        safe = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        html = (
            f'<p style="margin:8px 0;">'
            f'<span style="color:{color};font-weight:700;">{label}:</span> '
            f'<span style="color:{THEME["text"]};">{safe}</span></p>'
        )
        self.view.append(html)
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def append_streaming(self, chunk: str) -> None:
        # simple: append plain to end for streaming tokens
        cursor = self.view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.view.setTextCursor(cursor)
        self.view.insertPlainText(chunk)
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())
