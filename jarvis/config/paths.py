"""Resolve app / resource paths for source runs and PyInstaller frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Directory that contains the executable (onedir) or project root (dev)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def meipass_dir() -> Path | None:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return None


def resource_path(*parts: str) -> Path:
    """
    Locate bundled data files.
    PyInstaller puts --add-data under _MEIPASS (onefile) or next to the exe (onedir).
    """
    candidates: list[Path] = []
    mp = meipass_dir()
    if mp is not None:
        candidates.append(mp.joinpath(*parts))
    candidates.append(app_dir().joinpath(*parts))
    candidates.append(Path(__file__).resolve().parents[1].joinpath(*parts))
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]
