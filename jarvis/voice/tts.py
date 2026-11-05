"""Offline TTS — Piper (preferred) with pyttsx3 / espeak fallback."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(
        self,
        engine: str = "piper",
        voice: str = "uk_UA-ukrainian_tts-medium",
        speed: float = 1.0,
        output_device: int | None = None,
    ) -> None:
        self.engine = engine
        self.voice = voice
        self.speed = speed
        self.output_device = output_device
        self._stop_event = threading.Event()
        self._muted = False
        self._playing = False
        self._lock = threading.Lock()

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        if muted:
            self.stop()

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.5, min(2.0, float(speed)))

    def set_voice(self, voice: str) -> None:
        self.voice = voice

    def stop(self) -> None:
        """Interrupt current speech."""
        self._stop_event.set()
        self._playing = False

    def speak(self, text: str, blocking: bool = False) -> None:
        if self._muted or not text.strip():
            return
        self._stop_event.clear()

        def _run() -> None:
            with self._lock:
                self._playing = True
                try:
                    if self.engine == "piper":
                        ok = self._speak_piper(text)
                        if not ok:
                            self._speak_fallback(text)
                    else:
                        self._speak_fallback(text)
                finally:
                    self._playing = False

        if blocking:
            _run()
        else:
            threading.Thread(target=_run, daemon=True).start()

    @property
    def is_playing(self) -> bool:
        return self._playing

    def _piper_binary(self) -> str | None:
        return shutil.which("piper") or shutil.which("piper.exe")

    def _voice_model_path(self) -> Path | None:
        voices_dir = DATA_DIR / "voices"
        candidates = [
            voices_dir / f"{self.voice}.onnx",
            voices_dir / self.voice / f"{self.voice}.onnx",
            Path(self.voice) if self.voice.endswith(".onnx") else None,
        ]
        for c in candidates:
            if c and c.exists():
                return c
        # any uk onnx
        if voices_dir.exists():
            found = list(voices_dir.rglob("*.onnx"))
            if found:
                return found[0]
        return None

    def _speak_piper(self, text: str) -> bool:
        piper = self._piper_binary()
        model = self._voice_model_path()
        if not piper or not model:
            logger.warning("Piper binary or voice model missing")
            return False
        wav_path = Path(tempfile.mktemp(suffix=".wav"))
        try:
            length_scale = 1.0 / self.speed
            cmd = [
                piper,
                "--model",
                str(model),
                "--output_file",
                str(wav_path),
                "--length_scale",
                str(length_scale),
            ]
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=120,
            )
            if proc.returncode != 0 or not wav_path.exists():
                logger.error("Piper failed: %s", proc.stderr.decode(errors="ignore"))
                return False
            self._play_wav(wav_path)
            return True
        except Exception as exc:
            logger.error("Piper speak error: %s", exc)
            return False
        finally:
            if wav_path.exists():
                try:
                    wav_path.unlink()
                except OSError:
                    pass

    def _play_wav(self, path: Path) -> None:
        try:
            import sounddevice as sd
            import soundfile as sf

            data, sr = sf.read(str(path), dtype="float32")
            if self._stop_event.is_set():
                return
            sd.play(data, sr, device=self.output_device)
            # wait in slices so we can interrupt
            while sd.get_stream().active and not self._stop_event.is_set():
                sd.sleep(50)
            if self._stop_event.is_set():
                sd.stop()
        except Exception:
            # fallback players
            if sys.platform == "win32":
                import winsound

                if not self._stop_event.is_set():
                    winsound.PlaySound(str(path), winsound.SND_FILENAME)
            else:
                for player in ("aplay", "ffplay", "paplay"):
                    if shutil.which(player):
                        args = [player, str(path)]
                        if player == "ffplay":
                            args = ["ffplay", "-nodisp", "-autoexit", str(path)]
                        subprocess.run(args, capture_output=True, timeout=120)
                        break

    def _speak_fallback(self, text: str) -> None:
        """espeak / espeak-ng / pyttsx3 / Windows SAPI."""
        if self._stop_event.is_set():
            return
        # espeak-ng with Ukrainian if available
        for bin_name in ("espeak-ng", "espeak"):
            if shutil.which(bin_name):
                speed = int(160 * self.speed)
                cmd = [bin_name, "-v", "uk", "-s", str(speed), text]
                try:
                    proc = subprocess.Popen(cmd)
                    while proc.poll() is None:
                        if self._stop_event.is_set():
                            proc.terminate()
                            break
                        proc.wait(timeout=0.05) if False else None
                        import time

                        time.sleep(0.05)
                    return
                except Exception:
                    pass
        if sys.platform == "win32":
            try:
                # PowerShell SAPI — may lack Ukrainian voice but works offline
                safe = text.replace("'", "''")
                rate = int((self.speed - 1.0) * 5)
                ps = (
                    f"Add-Type -AssemblyName System.Speech; "
                    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Rate = {rate}; "
                    f"$s.Speak('{safe}')"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True,
                    timeout=120,
                )
                return
            except Exception as exc:
                logger.error("SAPI fallback failed: %s", exc)
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", int(160 * self.speed))
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            logger.error("All TTS backends failed: %s", exc)

    def status(self) -> dict:
        return {
            "engine": self.engine,
            "voice": self.voice,
            "piper_available": bool(self._piper_binary()),
            "voice_model": str(self._voice_model_path() or ""),
            "muted": self._muted,
            "playing": self._playing,
        }
