"""Settings UI for mic, voice, models, shortcuts, monitoring, startup."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.settings import Settings, DATA_DIR
from voice.audio_devices import list_input_devices, list_output_devices


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, ollama_models: list[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Налаштування JARVIS")
        self.resize(620, 520)
        self.settings = settings
        self._models = ollama_models or []

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        tabs.addTab(self._voice_tab(), "Голос")
        tabs.addTab(self._models_tab(), "Моделі")
        tabs.addTab(self._apps_tab(), "Програми / Cursor")
        tabs.addTab(self._system_tab(), "Система")
        tabs.addTab(self._memory_tab(), "Пам'ять")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _voice_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("За замовчуванням", None)
        for d in list_input_devices():
            self.mic_combo.addItem(f"{d['index']}: {d['name']}", d["index"])
        cur_mic = self.settings.get("mic_device")
        if cur_mic is not None:
            idx = self.mic_combo.findData(cur_mic)
            if idx >= 0:
                self.mic_combo.setCurrentIndex(idx)

        self.spk_combo = QComboBox()
        self.spk_combo.addItem("За замовчуванням", None)
        for d in list_output_devices():
            self.spk_combo.addItem(f"{d['index']}: {d['name']}", d["index"])
        cur_spk = self.settings.get("speaker_device")
        if cur_spk is not None:
            idx = self.spk_combo.findData(cur_spk)
            if idx >= 0:
                self.spk_combo.setCurrentIndex(idx)

        self.stt_model = QComboBox()
        for m in ("tiny", "base", "small", "medium"):
            self.stt_model.addItem(m)
        self.stt_model.setCurrentText(str(self.settings.get("stt_model") or "base"))

        self.tts_engine = QComboBox()
        self.tts_engine.addItems(["piper", "fallback"])
        self.tts_engine.setCurrentText(str(self.settings.get("tts_engine") or "piper"))

        self.tts_voice = QLineEdit(str(self.settings.get("tts_voice") or ""))
        self.tts_speed = QDoubleSpinBox()
        self.tts_speed.setRange(0.5, 2.0)
        self.tts_speed.setSingleStep(0.1)
        self.tts_speed.setValue(float(self.settings.get("tts_speed") or 1.0))

        self.wake_enabled = QCheckBox("Увімкнути wake word")
        self.wake_enabled.setChecked(bool(self.settings.get("wake_word_enabled")))
        self.wake_word = QLineEdit(str(self.settings.get("wake_word") or "джарвіс"))
        self.vad_enabled = QCheckBox("VAD (автозавершення фрази)")
        self.vad_enabled.setChecked(bool(self.settings.get("vad_enabled", True)))
        self.ptt_key = QLineEdit(str(self.settings.get("push_to_talk_key") or "Ctrl+Space"))

        form.addRow("Мікрофон", self.mic_combo)
        form.addRow("Динаміки", self.spk_combo)
        form.addRow("Модель STT (Whisper)", self.stt_model)
        form.addRow("TTS рушій", self.tts_engine)
        form.addRow("Голос Piper", self.tts_voice)
        form.addRow("Швидкість мови", self.tts_speed)
        form.addRow(self.wake_enabled)
        form.addRow("Wake word", self.wake_word)
        form.addRow(self.vad_enabled)
        form.addRow("Push-to-talk", self.ptt_key)
        hint = QLabel(
            f"Моделі Piper кладіть у:\n{DATA_DIR / 'voices'}\n"
            "(файл .onnx + .json українського голосу)"
        )
        hint.setWordWrap(True)
        form.addRow(hint)
        return w

    def _models_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.ollama_url = QLineEdit(str(self.settings.get("ollama_base_url") or ""))
        self.chat_model = QComboBox()
        self.chat_model.setEditable(True)
        self.vision_model = QComboBox()
        self.vision_model.setEditable(True)
        for m in self._models or ["llama3.2", "llava", "qwen2.5", "mistral"]:
            self.chat_model.addItem(m)
            self.vision_model.addItem(m)
        self.chat_model.setCurrentText(str(self.settings.get("chat_model") or "llama3.2"))
        self.vision_model.setCurrentText(str(self.settings.get("vision_model") or "llava"))
        self.system_prompt = QTextEdit()
        self.system_prompt.setPlainText(str(self.settings.get("system_prompt") or ""))
        self.system_prompt.setMaximumHeight(160)
        form.addRow("Ollama URL", self.ollama_url)
        form.addRow("Модель чату", self.chat_model)
        form.addRow("Модель vision", self.vision_model)
        form.addRow("Системний промпт", self.system_prompt)
        return w

    def _apps_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.shortcuts = QTextEdit()
        shortcuts = self.settings.get("app_shortcuts") or {}
        self.shortcuts.setPlainText(json.dumps(shortcuts, ensure_ascii=False, indent=2))
        self.projects = QTextEdit()
        projects = self.settings.get("project_folders") or []
        self.projects.setPlainText("\n".join(projects))
        self.cursor_path = QLineEdit(str(self.settings.get("cursor_path") or ""))
        browse = QPushButton("Огляд…")
        browse.clicked.connect(self._browse_cursor)
        row = QHBoxLayout()
        row.addWidget(self.cursor_path)
        row.addWidget(browse)
        form.addRow("Ярлики програм (JSON)", self.shortcuts)
        form.addRow("Теки проєктів (по рядку)", self.projects)
        form.addRow("Шлях Cursor", row)
        return w

    def _system_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.monitor = QCheckBox("Моніторинг екрана (за замовчуванням ВИМК)")
        self.monitor.setChecked(bool(self.settings.get("screen_monitoring")))
        self.monitor_interval = QSpinBox()
        self.monitor_interval.setRange(5, 600)
        self.monitor_interval.setValue(int(self.settings.get("screen_monitor_interval_sec") or 30))
        self.confirm_destructive = QCheckBox("Підтверджувати небезпечні дії")
        self.confirm_destructive.setChecked(bool(self.settings.get("confirm_destructive", True)))
        self.confirm_shell = QCheckBox("Підтверджувати shell-команди")
        self.confirm_shell.setChecked(bool(self.settings.get("confirm_shell", True)))
        self.tray = QCheckBox("Згортати в системний трей")
        self.tray.setChecked(bool(self.settings.get("minimize_to_tray", True)))
        self.startup = QCheckBox("Запускати з Windows")
        self.startup.setChecked(bool(self.settings.get("startup_with_windows")))
        form.addRow(self.monitor)
        form.addRow("Інтервал моніторингу (с)", self.monitor_interval)
        form.addRow(self.confirm_destructive)
        form.addRow(self.confirm_shell)
        form.addRow(self.tray)
        form.addRow(self.startup)
        return w

    def _memory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.memory_enabled = QCheckBox("Зберігати довготривалу пам'ять")
        self.memory_enabled.setChecked(bool(self.settings.get("memory_enabled", True)))
        layout.addWidget(self.memory_enabled)
        layout.addWidget(QLabel(f"База даних: {DATA_DIR / 'jarvis.db'}"))
        clear_btn = QPushButton("Очистити історію чату")
        clear_btn.clicked.connect(self._clear_chat_flag)
        layout.addWidget(clear_btn)
        self._clear_chat = False
        layout.addStretch()
        return w

    def _browse_cursor(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Виберіть Cursor.exe")
        if path:
            self.cursor_path.setText(path)

    def _clear_chat_flag(self) -> None:
        self._clear_chat = True
        QMessageBox.information(self, "Пам'ять", "Історію буде очищено після збереження.")

    def _save(self) -> None:
        try:
            shortcuts = json.loads(self.shortcuts.toPlainText() or "{}")
            if not isinstance(shortcuts, dict):
                raise ValueError("shortcuts must be object")
        except Exception as exc:
            QMessageBox.warning(self, "Помилка", f"Некоректний JSON ярликів: {exc}")
            return
        projects = [ln.strip() for ln in self.projects.toPlainText().splitlines() if ln.strip()]
        self.settings.update(
            {
                "mic_device": self.mic_combo.currentData(),
                "speaker_device": self.spk_combo.currentData(),
                "stt_model": self.stt_model.currentText(),
                "tts_engine": self.tts_engine.currentText(),
                "tts_voice": self.tts_voice.text().strip(),
                "tts_speed": self.tts_speed.value(),
                "wake_word_enabled": self.wake_enabled.isChecked(),
                "wake_word": self.wake_word.text().strip().lower(),
                "vad_enabled": self.vad_enabled.isChecked(),
                "push_to_talk_key": self.ptt_key.text().strip(),
                "ollama_base_url": self.ollama_url.text().strip(),
                "chat_model": self.chat_model.currentText().strip(),
                "vision_model": self.vision_model.currentText().strip(),
                "system_prompt": self.system_prompt.toPlainText(),
                "app_shortcuts": shortcuts,
                "project_folders": projects,
                "cursor_path": self.cursor_path.text().strip(),
                "screen_monitoring": self.monitor.isChecked(),
                "screen_monitor_interval_sec": self.monitor_interval.value(),
                "confirm_destructive": self.confirm_destructive.isChecked(),
                "confirm_shell": self.confirm_shell.isChecked(),
                "minimize_to_tray": self.tray.isChecked(),
                "startup_with_windows": self.startup.isChecked(),
                "memory_enabled": self.memory_enabled.isChecked(),
            }
        )
        if sys.platform == "win32":
            self._apply_windows_startup(self.startup.isChecked())
        self.accept()

    def _apply_windows_startup(self, enable: bool) -> None:
        try:
            import winreg  # type: ignore

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    start_bat = Path(__file__).resolve().parent.parent / "start.bat"
                    winreg.SetValueEx(key, "JarvisAssistant", 0, winreg.REG_SZ, str(start_bat))
                else:
                    try:
                        winreg.DeleteValue(key, "JarvisAssistant")
                    except FileNotFoundError:
                        pass
        except Exception:
            pass

    @property
    def clear_chat_requested(self) -> bool:
        return getattr(self, "_clear_chat", False)
