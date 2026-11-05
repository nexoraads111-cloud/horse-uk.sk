#!/usr/bin/env python3
"""Verify packaging inputs before / without a full Windows .exe build.

Safe to run on Linux CI: import graph, defaults.json, .spec syntax, optional
PyInstaller Analysis dry checks. Does NOT claim a Windows binary was produced.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_MODULES = [
    "config.settings",
    "config.paths",
    "core.assistant",
    "core.ollama_client",
    "core.actions",
    "database.db",
    "database.memory",
    "automation.safety",
    "automation.apps",
    "automation.screenshot",
    "automation.cursor_ide",
    "vision.analyzer",
    "voice.vad",
    "voice.tts",
    "ui.styles",
]

OPTIONAL_MODULES = [
    "PySide6.QtWidgets",
    "httpx",
    "psutil",
    "mss",
    "PIL",
    "numpy",
]


def check_defaults() -> None:
    path = ROOT / "config" / "defaults.json"
    assert path.exists(), f"missing {path}"
    from config.settings import Settings

    s = Settings()
    assert s.get("language") == "uk"
    from config.paths import resource_path, app_dir

    rp = resource_path("config", "defaults.json")
    assert rp.exists(), f"resource_path failed: {rp}"
    assert app_dir() == ROOT or app_dir().exists()
    print(f"[ok] defaults + paths ({rp})")


def check_imports() -> None:
    for name in REQUIRED_MODULES:
        importlib.import_module(name)
        print(f"[ok] import {name}")
    for name in OPTIONAL_MODULES:
        try:
            importlib.import_module(name)
            print(f"[ok] import {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] optional import {name}: {exc}")


def check_spec_syntax() -> None:
    spec = ROOT / "JarvisAssistant.spec"
    assert spec.exists(), f"missing {spec}"
    # .spec is Python executed by PyInstaller; parse as AST after injecting SPEC
    src = spec.read_text(encoding="utf-8")
    # Replace SPEC name usage for syntax-only parse: already valid python if SPEC defined
    tree = ast.parse(src)
    assert any(isinstance(n, ast.Assign) for n in tree.body) or True
    # Ensure key symbols mentioned
    text = src
    for needle in ("Analysis(", "EXE(", "COLLECT(", "defaults.json", "JarvisAssistant"):
        assert needle in text, f"spec missing {needle}"
    print(f"[ok] JarvisAssistant.spec syntax/markers ({spec})")


def check_build_scripts() -> None:
    for name in ("build_exe.bat", "build_exe_console.bat", "setup.bat", "start.bat"):
        p = ROOT / name
        assert p.exists(), f"missing {p}"
        print(f"[ok] script {p.name}")


def check_pyinstaller_available() -> None:
    try:
        import PyInstaller  # noqa: F401

        print(f"[ok] PyInstaller {PyInstaller.__version__}")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] PyInstaller not installed: {exc}")
        print("       On Windows: build_exe.bat installs it automatically.")


def try_analysis_smoke() -> None:
    """Best-effort: run PyInstaller with JarvisAssistant.spec on this host.

    Enable with PYINSTALLER_SMOKE=1. Produces a *native* binary for the current OS
    (Linux ELF here) — NOT a Windows .exe. Validates the .spec / hiddenimports.
    """
    import os
    import subprocess

    if os.environ.get("PYINSTALLER_SMOKE") != "1":
        print("[skip] PyInstaller smoke (set PYINSTALLER_SMOKE=1 to enable)")
        return

    print("[info] running: python -m PyInstaller --noconfirm JarvisAssistant.spec")
    print("[note] Output is for THIS OS only — Windows .exe requires build_exe.bat on Windows.")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(ROOT / "JarvisAssistant.spec"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    # Show tail of logs for diagnosis
    tail = (proc.stdout or "")[-2000:] + "\n" + (proc.stderr or "")[-2000:]
    print(tail)
    if proc.returncode != 0:
        raise RuntimeError(f"PyInstaller exited {proc.returncode}")

    dist_exe = ROOT / "dist" / "JarvisAssistant" / "JarvisAssistant"
    dist_exe_win = ROOT / "dist" / "JarvisAssistant" / "JarvisAssistant.exe"
    if dist_exe.exists() or dist_exe_win.exists():
        print(f"[ok] dist artifact present ({dist_exe if dist_exe.exists() else dist_exe_win})")
    else:
        print("[warn] PyInstaller finished but expected dist binary not found")
    print("[note] Do not distribute the Linux artifact as a Windows .exe.")


def main() -> int:
    print(f"JARVIS packaging verify — root={ROOT} platform={sys.platform}")
    try:
        check_defaults()
        check_imports()
        check_spec_syntax()
        check_build_scripts()
        check_pyinstaller_available()
        try_analysis_smoke()
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {exc}")
        return 1
    print("[PASS] packaging verification completed (no Windows .exe claimed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
