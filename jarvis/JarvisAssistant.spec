# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for JARVIS AI Assistant (Windows onedir build).

Build on Windows:
  build_exe.bat

Ollama, Piper binary, and Whisper model weights are NOT bundled — install separately.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_all, collect_data_files

SPECDIR = Path(SPEC).resolve().parent  # type: ignore[name-defined]  # noqa: F821
BLOCK_CIPHER = None

datas = [
    (str(SPECDIR / "config" / "defaults.json"), "config"),
]

binaries: list = []
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtSvg",
    "httpx",
    "httpcore",
    "anyio",
    "sniffio",
    "certifi",
    "psutil",
    "mss",
    "PIL",
    "PIL.Image",
    "numpy",
    "sounddevice",
    "soundfile",
    "cffi",
    "pyperclip",
    "faster_whisper",
    "ctranslate2",
    "tokenizers",
    "huggingface_hub",
    "av",
    "config",
    "config.settings",
    "config.paths",
    "config.defaults",
    "core",
    "core.assistant",
    "core.ollama_client",
    "core.actions",
    "database",
    "database.db",
    "database.memory",
    "voice",
    "voice.stt",
    "voice.tts",
    "voice.vad",
    "voice.wake_word",
    "voice.audio_devices",
    "automation",
    "automation.apps",
    "automation.files",
    "automation.safety",
    "automation.screenshot",
    "automation.cursor_ide",
    "vision",
    "vision.analyzer",
    "vision.screen_monitor",
    "ui",
    "ui.main_window",
    "ui.chat_panel",
    "ui.system_panel",
    "ui.visualizer",
    "ui.settings_dialog",
    "ui.first_run",
    "ui.tray",
    "ui.styles",
]

# Heavy / platform packages — collect when importable
for pkg in ("PySide6", "faster_whisper", "ctranslate2"):
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception as exc:  # noqa: BLE001
        print(f"[spec] collect_all({pkg}) skipped: {exc}")

try:
    datas += collect_data_files("certifi")
except Exception:
    pass

if sys.platform == "win32":
    hiddenimports += [
        "win32api",
        "win32con",
        "win32gui",
        "win32process",
        "pywintypes",
        "pythoncom",
        "pyautogui",
        "mouseinfo",
        "pygetwindow",
        "pymsgbox",
        "pyrect",
        "pyscreeze",
        "pytweening",
    ]

# Exclude unused Qt / test bulk to keep size down
excludes = [
    "tkinter",
    "matplotlib",
    "scipy",
    "IPython",
    "notebook",
    "pytest",
    "pytest_qt",
]

a = Analysis(
    [str(SPECDIR / "main.py")],
    pathex=[str(SPECDIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=BLOCK_CIPHER,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=BLOCK_CIPHER)

# Prefer console=False on Windows GUI; build_exe.bat can override via --console flag in alternate target.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JarvisAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(SPECDIR / "assets" / "icons" / "jarvis.ico")
    if (SPECDIR / "assets" / "icons" / "jarvis.ico").exists()
    else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="JarvisAssistant",
)
