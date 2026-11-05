"""Main JARVIS window — dark futuristic desktop UI."""

from __future__ import annotations

import logging
import threading
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from config.settings import Settings
from core.assistant import JarvisAssistant
from core.actions import ProposedAction
from database.db import Database
from ui.chat_panel import ChatPanel
from ui.system_panel import SystemPanel
from ui.visualizer import CircularVisualizer
from ui.settings_dialog import SettingsDialog
from ui.first_run import FirstRunWizard
from ui.tray import TrayController
from ui.styles import STYLESHEET, THEME
from vision.screen_monitor import ScreenMonitor
from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from voice.vad import SimpleVAD
from voice.wake_word import WakeWordListener

logger = logging.getLogger(__name__)


class ChatWorker(QObject):
    finished = Signal(str)
    token = Signal(str)
    error = Signal(str)

    def __init__(self, assistant: JarvisAssistant, text: str) -> None:
        super().__init__()
        self.assistant = assistant
        self.text = text

    def run(self) -> None:
        try:
            reply, _ = self.assistant.chat(
                self.text,
                on_token=lambda t: self.token.emit(t),
                execute_actions=True,
            )
            self.finished.emit(reply)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    voice_result = Signal(str)
    wake_detected = Signal()

    def __init__(self, settings: Settings, db: Database, assistant: JarvisAssistant) -> None:
        super().__init__()
        self.settings = settings
        self.db = db
        self.assistant = assistant
        self.setWindowTitle("JARVIS — Локальний AI-асистент")
        self.resize(1200, 740)
        self.setStyleSheet(STYLESHEET)

        self._muted = bool(settings.get("mute"))
        self._listening = False
        self._chat_thread: Optional[QThread] = None
        self._streaming_started = False

        self.stt = SpeechToText(
            model_size=str(settings.get("stt_model") or "base"),
            language=str(settings.get("stt_language") or "uk"),
        )
        self.tts = TextToSpeech(
            engine=str(settings.get("tts_engine") or "piper"),
            voice=str(settings.get("tts_voice") or ""),
            speed=float(settings.get("tts_speed") or 1.0),
            output_device=settings.get("speaker_device"),
        )
        self.tts.set_muted(self._muted)
        self.vad = SimpleVAD(silence_ms=int(settings.get("vad_silence_ms") or 800))
        self.wake: WakeWordListener | None = None

        self.monitor = ScreenMonitor(
            self.assistant.screenshot,
            vision=self.assistant.vision,
            interval_sec=int(settings.get("screen_monitor_interval_sec") or 30),
            parent=self,
        )
        self.monitor.analyzed.connect(self._on_monitor_result)
        self.monitor.status_changed.connect(self._on_monitor_status)

        self.assistant.set_confirm_callback(self._confirm_action)

        self._build_ui()
        self.tray = TrayController(self)
        self._setup_shortcuts()
        self.voice_result.connect(self._on_voice_text)
        self.wake_detected.connect(self.toggle_listen)

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self.refresh_status)
        self._status_timer.start(5000)

        self._load_history()
        self.refresh_status()

        if settings.get("screen_monitoring"):
            self.monitor.start()
        if settings.get("wake_word_enabled"):
            self._start_wake_word()

        QTimer.singleShot(200, self._maybe_first_run)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # header
        header = QHBoxLayout()
        brand = QLabel("JARVIS")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.monitor_indicator = QLabel("● MONITOR OFF")
        self.monitor_indicator.setStyleSheet(f"color: {THEME['text_dim']}; font-weight:700;")
        header.addWidget(self.monitor_indicator)
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.clicked.connect(self.on_emergency_stop)
        header.addWidget(self.stop_btn)
        self.settings_btn = QPushButton("Налаштування")
        self.settings_btn.clicked.connect(self.open_settings)
        header.addWidget(self.settings_btn)
        root.addLayout(header)

        # body: chat | center | system
        body = QHBoxLayout()
        self.chat_panel = ChatPanel()
        body.addWidget(self.chat_panel, 3)

        center = QVBoxLayout()
        self.visualizer = CircularVisualizer()
        center.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.mic_status = QLabel("Мікрофон: готовий")
        self.mic_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mic_status.setObjectName("statusDim")
        center.addWidget(self.mic_status)
        body.addLayout(center, 2)

        self.system_panel = SystemPanel()
        body.addWidget(self.system_panel, 2)
        root.addLayout(body, 1)

        # input row
        input_row = QHBoxLayout()
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Напишіть повідомлення українською… (Enter — надіслати, Shift+Enter — новий рядок)")
        self.input.setFixedHeight(72)
        self.input.installEventFilter(self)
        input_row.addWidget(self.input, 1)

        self.mic_btn = QPushButton("🎙 Мікрофон")
        self.mic_btn.setCheckable(True)
        self.mic_btn.clicked.connect(self.toggle_listen)
        input_row.addWidget(self.mic_btn)

        self.mute_btn = QPushButton("🔇 Mute" if self._muted else "🔊 Звук")
        self.mute_btn.clicked.connect(self.toggle_mute)
        input_row.addWidget(self.mute_btn)

        self.send_btn = QPushButton("Надіслати")
        self.send_btn.setObjectName("primary")
        self.send_btn.clicked.connect(self.send_text)
        input_row.addWidget(self.send_btn)
        root.addLayout(input_row)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Готовий")

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent

        if obj is self.input and event.type() == QEvent.Type.KeyPress:
            assert isinstance(event, QKeyEvent)
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                self.send_text()
                return True
        return super().eventFilter(obj, event)

    def _setup_shortcuts(self) -> None:
        # Push-to-talk Ctrl+Space
        QShortcut(QKeySequence("Ctrl+Space"), self, activated=self.toggle_listen)
        QShortcut(QKeySequence("Ctrl+."), self, activated=self.on_emergency_stop)
        QShortcut(QKeySequence("Ctrl+M"), self, activated=self.toggle_mute)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_settings)
        QShortcut(QKeySequence("Escape"), self, activated=self._interrupt_tts)

    def _maybe_first_run(self) -> None:
        if not self.settings.get("first_run_done"):
            wiz = FirstRunWizard(self.settings, self)
            wiz.exec()
            self.db.save_settings(self.settings.as_dict())

    def _load_history(self) -> None:
        for msg in self.db.get_messages(limit=50):
            self.chat_panel.append_message(msg["role"], msg["content"])
        self.system_panel.set_tasks(self.db.list_tasks())

    def refresh_status(self) -> None:
        try:
            st = self.assistant.status()
            self.system_panel.set_ollama(st["ollama"], st.get("models"))
            self.system_panel.set_model_name(str(self.settings.get("chat_model")))
            self.system_panel.set_monitor(self.monitor.enabled)
            self.system_panel.set_stop(st["stopped"])
            self.system_panel.set_tasks(self.db.list_tasks())
            if st["ollama"]:
                self.statusBar().showMessage("Ollama онлайн")
            else:
                self.statusBar().showMessage("Ollama офлайн — запустіть ollama serve")
        except Exception:
            logger.exception("status refresh failed")

    def send_text(self) -> None:
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self._start_chat(text)

    def _start_chat(self, text: str) -> None:
        self.tts.stop()  # interrupt speech when new request
        self.chat_panel.append_message("user", text)
        self.visualizer.set_state("thinking")
        self.send_btn.setEnabled(False)
        self._streaming_started = False

        self._chat_thread = QThread()
        worker = ChatWorker(self.assistant, text)
        worker.moveToThread(self._chat_thread)
        self._chat_thread.started.connect(worker.run)

        def on_token(t: str) -> None:
            if not self._streaming_started:
                self.chat_panel.append_message("assistant", "")
                self._streaming_started = True
            # streaming into last bubble is imperfect; collect and speak at end

        worker.token.connect(on_token)

        def on_done(reply: str) -> None:
            if not self._streaming_started:
                self.chat_panel.append_message("assistant", reply)
            else:
                # refresh last by appending clean full reply marker
                self.chat_panel.append_message("assistant", reply)
            self.visualizer.set_state("speaking")
            self.tts.speak(reply)
            QTimer.singleShot(50, lambda: self.visualizer.set_state("idle"))
            self.send_btn.setEnabled(True)
            self.refresh_status()
            self._chat_thread.quit()

        def on_err(msg: str) -> None:
            self.chat_panel.append_message("system", msg)
            self.visualizer.set_state("idle")
            self.send_btn.setEnabled(True)
            self._chat_thread.quit()

        worker.finished.connect(on_done)
        worker.error.connect(on_err)
        self._chat_thread.start()
        # keep ref
        self._worker = worker

    def toggle_listen(self) -> None:
        if self._listening:
            self._listening = False
            self.mic_btn.setChecked(False)
            self.mic_btn.setObjectName("")
            self.mic_btn.setStyle(self.mic_btn.style())
            self.mic_status.setText("Мікрофон: готовий")
            self.system_panel.set_mic("готовий", False)
            self.visualizer.set_state("idle")
            return

        self._listening = True
        self.mic_btn.setChecked(True)
        self.mic_btn.setObjectName("micActive")
        self.mic_btn.setStyle(self.mic_btn.style())
        self.mic_status.setText("Мікрофон: слухаю…")
        self.system_panel.set_mic("слухаю", True)
        self.visualizer.set_state("listening")
        self.tts.stop()

        def record() -> None:
            try:
                try:
                    self.stt.load()
                except Exception as exc:
                    self.voice_result.emit(f"__ERROR__Не вдалося завантажити Whisper: {exc}")
                    return
                vad = self.vad if self.settings.get("vad_enabled", True) else None
                text = self.stt.record_and_transcribe(
                    duration_sec=6.0,
                    device=self.settings.get("mic_device"),
                    vad=vad,
                    max_sec=20.0,
                )
                self.voice_result.emit(text or "")
            except Exception as exc:
                self.voice_result.emit(f"__ERROR__{exc}")

        threading.Thread(target=record, daemon=True).start()

    def _on_voice_text(self, text: str) -> None:
        self._listening = False
        self.mic_btn.setChecked(False)
        self.mic_btn.setObjectName("")
        self.mic_btn.setStyle(self.mic_btn.style())
        self.mic_status.setText("Мікрофон: готовий")
        self.system_panel.set_mic("готовий", False)
        self.visualizer.set_state("idle")
        if text.startswith("__ERROR__"):
            self.chat_panel.append_message("system", text[9:])
            return
        if not text.strip():
            self.chat_panel.append_message("system", "Не розпізнано мову. Спробуйте ще.")
            return
        self._start_chat(text)

    def toggle_mute(self) -> None:
        self._muted = not self._muted
        self.tts.set_muted(self._muted)
        self.settings.set("mute", self._muted)
        self.db.set_setting("mute", self._muted)
        self.mute_btn.setText("🔇 Mute" if self._muted else "🔊 Звук")

    def _interrupt_tts(self) -> None:
        self.tts.stop()
        self.visualizer.set_state("idle")

    def on_emergency_stop(self) -> None:
        self.assistant.emergency_stop()
        self.tts.stop()
        if self.monitor.enabled:
            self.monitor.stop()
        self._listening = False
        self.system_panel.set_stop(True)
        self.visualizer.set_state("idle")
        self.chat_panel.append_message("system", "Аварійна STOP — усі дії зупинено.")
        self.tray.notify("JARVIS", "Аварійна зупинка активна")

        # allow resume via second confirmation
        reply = QMessageBox.question(
            self,
            "STOP",
            "Аварійну зупинку активовано.\nЗняти блокування зараз?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.assistant.clear_stop()
            self.system_panel.set_stop(False)

    def _confirm_action(self, action: ProposedAction, reason: str) -> bool:
        # Must run on GUI thread — use BlockingQueued if needed; here usually same thread via chat worker
        # Chat worker is background — use invoke via signal would be better; simple sync message box from worker is unsafe.
        # Store pending and ask on main thread using a threading Event.
        result = {"ok": False}
        event = threading.Event()

        def ask() -> None:
            detail = f"{reason}\n\nДія: {action.name}\nПараметри: {action.params}"
            box = QMessageBox.question(
                self,
                "Підтвердження дії",
                detail,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            result["ok"] = box == QMessageBox.StandardButton.Yes
            event.set()

        QTimer.singleShot(0, ask)
        event.wait(timeout=120)
        return bool(result["ok"])

    def open_settings(self) -> None:
        models = []
        try:
            if self.assistant.ollama.is_available():
                models = self.assistant.ollama.list_models()
        except Exception:
            pass
        dlg = SettingsDialog(self.settings, models, self)
        if dlg.exec():
            self.db.save_settings(self.settings.as_dict())
            self.assistant.reload_settings()
            self.tts.set_speed(float(self.settings.get("tts_speed") or 1.0))
            self.tts.set_voice(str(self.settings.get("tts_voice") or ""))
            self.tts.engine = str(self.settings.get("tts_engine") or "piper")
            self.tts.output_device = self.settings.get("speaker_device")
            if dlg.clear_chat_requested:
                self.assistant.clear_chat()
                self.chat_panel.clear()
            # monitor
            if self.settings.get("screen_monitoring"):
                self.monitor.set_interval(int(self.settings.get("screen_monitor_interval_sec") or 30))
                if not self.monitor.enabled:
                    self.monitor.start()
            else:
                self.monitor.stop()
            # wake word
            if self.settings.get("wake_word_enabled"):
                self._start_wake_word()
            elif self.wake:
                self.wake.stop()
            self.refresh_status()

    def _start_wake_word(self) -> None:
        if self.wake:
            self.wake.stop()
        try:
            self.stt.load()
        except Exception as exc:
            self.chat_panel.append_message("system", f"Wake word недоступний: {exc}")
            return
        self.wake = WakeWordListener(
            self.stt,
            phrase=str(self.settings.get("wake_word") or "джарвіс"),
            device=self.settings.get("mic_device"),
            on_detect=lambda: self.wake_detected.emit(),
        )
        self.wake.start()
        self.chat_panel.append_message(
            "system",
            f"Wake word увімкнено: «{self.settings.get('wake_word')}»",
        )

    def _on_monitor_status(self, on: bool) -> None:
        self.system_panel.set_monitor(on)
        if on:
            self.monitor_indicator.setText("● MONITOR ON")
            self.monitor_indicator.setStyleSheet(f"color: {THEME['warn']}; font-weight:800;")
        else:
            self.monitor_indicator.setText("● MONITOR OFF")
            self.monitor_indicator.setStyleSheet(f"color: {THEME['text_dim']}; font-weight:700;")

    def _on_monitor_result(self, summary: str) -> None:
        self.chat_panel.append_message("system", f"[Моніторинг] {summary}")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.settings.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            self.tray.notify("JARVIS", "Працюю у фоні (трей)")
            return
        self.clean_shutdown()
        event.accept()

    def clean_shutdown(self) -> None:
        try:
            self.settings.set("first_run_done", self.settings.get("first_run_done", True))
            self.db.save_settings(self.settings.as_dict())
        except Exception:
            pass
        if self.wake:
            self.wake.stop()
        self.monitor.stop()
        self.tts.stop()
        self.assistant.emergency_stop()
        QApplication.instance().quit()
