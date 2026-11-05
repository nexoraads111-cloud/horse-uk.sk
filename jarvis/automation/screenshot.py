"""Screenshot capture via mss."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from config.settings import DATA_DIR


class ScreenshotService:
    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = Path(output_dir or (DATA_DIR / "screenshots"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, filename: str | None = None) -> Path:
        import mss
        from PIL import Image

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / (filename or f"screen_{stamp}.png")
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            img.save(path)
        return path
