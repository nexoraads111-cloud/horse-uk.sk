#!/usr/bin/env python3
"""Generate a simple cyan JARVIS .ico for the Windows exe (no external assets)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "icons" / "jarvis.ico"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow required to generate icon")
        return 1

    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    font_candidates = (
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\seguiui.ttf",
    )
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = max(1, size // 16)
        draw.ellipse(
            [margin, margin, size - margin - 1, size - margin - 1],
            fill=(0, 229, 255, 255),
            outline=(5, 10, 20, 255),
        )
        font = ImageFont.load_default()
        for fp in font_candidates:
            try:
                font = ImageFont.truetype(fp, size=max(10, size // 2))
                break
            except OSError:
                continue
        text = "J"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((size - tw) / 2, (size - th) / 2 - size * 0.05),
            text,
            fill=(5, 10, 20, 255),
            font=font,
        )
        images.append(img)

    # Largest first + append_images so Windows gets multiple resolutions
    images[-1].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
