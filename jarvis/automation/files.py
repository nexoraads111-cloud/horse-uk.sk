"""Open files and folders safely."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class FileController:
    def open_path(self, path: str) -> tuple[bool, str]:
        p = Path(path).expanduser()
        if not p.exists():
            return False, f"Шлях не існує: {p}"
        try:
            if sys.platform == "win32":
                os.startfile(str(p))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
            return True, f"Відкрито: {p}"
        except Exception as exc:
            return False, f"Не вдалося відкрити: {exc}"
