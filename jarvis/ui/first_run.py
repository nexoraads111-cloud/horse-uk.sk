"""First-run wizard — Ollama / models / voice check."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)

from config.settings import DATA_DIR, Settings
from core.ollama_client import OllamaClient


WIZARD_HTML = """
<h2 style="color:#00e5ff;">Ласкаво просимо до JARVIS</h2>
<p>Локальний український AI-асистент. Жодних хмарних API — лише ваш ПК.</p>
<ol>
<li><b>Встановіть Ollama</b> з <code>https://ollama.com</code> і запустіть її.</li>
<li>У PowerShell виконайте:<br>
<code>ollama pull llama3.2</code><br>
<code>ollama pull llava</code> (для аналізу екрана)</li>
<li>Для голосу (Piper): завантажте українську модель <code>.onnx</code>
у теку <code>{voices}</code>.</li>
<li>Мікрофон і динаміки налаштуйте в меню «Налаштування».</li>
</ol>
<p>Push-to-talk: <b>Ctrl+Space</b>. Аварійна зупинка: кнопка <b>STOP</b>.</p>
"""


class FirstRunWizard(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Перший запуск JARVIS")
        self.resize(560, 420)
        self.settings = settings
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(WIZARD_HTML.format(voices=DATA_DIR / "voices"))
        layout.addWidget(browser)

        self.status = QLabel()
        layout.addWidget(self.status)
        self._check()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._finish)
        layout.addWidget(buttons)

    def _check(self) -> None:
        client = OllamaClient(self.settings.ollama_base_url)
        if client.is_available():
            models = client.list_models()
            self.status.setText(f"✓ Ollama доступна. Моделі: {', '.join(models) or 'немає'}")
            self.status.setStyleSheet("color: #00ff9d;")
        else:
            self.status.setText("✗ Ollama недоступна — встановіть і запустіть перед роботою.")
            self.status.setStyleSheet("color: #ff3366;")

    def _finish(self) -> None:
        self.settings.set("first_run_done", True)
        self.accept()
