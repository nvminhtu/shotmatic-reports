#!/usr/bin/env python3
"""Stamp the ShotMatic badge on a screenshot and save it under its report name."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "docs" / "images" / "shotmatic-wordmark-light.png"
MAX_WIDTH = 2400
BADGE_TEXT = "shotmatic.app"
BADGE_BG = (31, 42, 68, 224)  # navy #1F2A44 at ~88%
FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


class WatermarkError(Exception):
    pass


def image_name(slug: str, date: str) -> str:
    return f"shotmatic.app-{slug}-{date}.png"


def badge_height(img_h: int) -> int:
    return max(28, min(64, round(img_h * 0.04)))


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def make_badge(height: int, logo_path: Path = LOGO) -> Image.Image:
    logo = Image.open(logo_path).convert("RGBA")
    lh = round(height * 0.62)
    lw = round(logo.width * lh / logo.height)
    logo = logo.resize((lw, lh), Image.LANCZOS)

    font = _font(round(height * 0.42))
    left, top, right, bottom = font.getbbox(BADGE_TEXT)
    tw, th = right - left, bottom - top
    pad, gap = round(height * 0.3), round(height * 0.28)
    width = pad + lw + gap + tw + pad

    badge = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=height // 3, fill=BADGE_BG)
    badge.alpha_composite(logo, (pad, (height - lh) // 2))
    draw.text((pad + lw + gap - left, (height - th) // 2 - top), BADGE_TEXT,
              font=font, fill=(255, 255, 255, 255))
    return badge


def watermark(src: Path, out_dir: Path, slug: str, date: str, logo_path: Path = LOGO) -> Path:
    try:
        img = Image.open(src)
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise WatermarkError(f"cannot open image {src}: {e}") from e

    img = img.convert("RGBA")
    if img.width > MAX_WIDTH:
        img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)

    badge = make_badge(badge_height(img.height), logo_path)
    margin = max(8, round(min(img.size) * 0.02))
    x = img.width - badge.width - margin
    if x < margin:
        raise WatermarkError(f"image too small for the badge: {img.width}x{img.height}")
    # Add a strip under the screenshot (same colour as its bottom-left pixel) so the
    # badge never covers data, then put the badge bottom-right inside that strip.
    strip_h = badge.height + 2 * margin
    canvas = Image.new("RGBA", (img.width, img.height + strip_h), img.getpixel((0, img.height - 1)))
    canvas.alpha_composite(img, (0, 0))
    canvas.alpha_composite(badge, (x, img.height + margin))
    img = canvas

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / image_name(slug, date)
    img.convert("RGB").save(out, "PNG", optimize=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--date", required=True)
    a = ap.parse_args(argv)
    try:
        print(watermark(a.src, a.out_dir, a.slug, a.date))
    except WatermarkError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
