#!/usr/bin/env python3
"""Draw a Top N apps card PNG from a *.card.json file: card_render.py <card.json> <out.png>"""
from __future__ import annotations

import hashlib
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

from card_data import COLUMN_LABELS, Card, load_card
from watermark import _font

WIDTH, ROW_H, HEAD_H, FOOT_H, PAD = 1600, 96, 230, 90, 64
WHITE, NAVY, MUTED, ORANGE, LINE = (255, 255, 255), (31, 42, 68), (110, 118, 135), (249, 115, 22), (234, 236, 240)
ICON = 64
COL_W = 210  # each number column, right-aligned from the right edge
REV_W = 300  # the revenue column is wider ("$12K/mo verified")


def _col_w(c: str) -> int:
    return REV_W if c in ("revenue", "verified", "earned") else COL_W


def _download(url: str) -> bytes:
    """Python.org builds on macOS ship without CA certs: use certifi, else curl."""
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "shotmatic-report"})
        return urllib.request.urlopen(req, timeout=10, context=ctx).read()
    except Exception:
        return subprocess.run(["curl", "-sfL", "--max-time", "10", "-A", "shotmatic-report", url],
                              capture_output=True, check=True).stdout


def fetch_icon(src: str | None, icon_dir: Path) -> Image.Image | None:
    if not src:
        return None
    try:
        if src.startswith("http"):
            icon_dir.mkdir(parents=True, exist_ok=True)
            cached = icon_dir / (hashlib.sha1(src.encode()).hexdigest()[:16] + ".img")
            if not cached.exists():
                cached.write_bytes(_download(src))
            src = str(cached)
        return Image.open(src).convert("RGBA").resize((ICON, ICON), Image.LANCZOS)
    except Exception:
        return None


def _letter_tile(name: str) -> Image.Image:
    tile = Image.new("RGBA", (ICON, ICON), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, ICON - 1, ICON - 1), radius=16, fill=(255, 237, 213))
    f = _font(34)
    d.text((ICON / 2, ICON / 2), name[:1].upper(), font=f, fill=ORANGE, anchor="mm")
    return tile


def _round(icon: Image.Image) -> Image.Image:
    mask = Image.new("L", icon.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ICON - 1, ICON - 1), radius=16, fill=255)
    out = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    out.paste(icon, (0, 0), mask)
    return out


def _fit(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def render_card(card: Card, out: Path, icon_dir: Path) -> Path:
    h = HEAD_H + len(card.apps) * ROW_H + FOOT_H
    img = Image.new("RGB", (WIDTH, h), WHITE)
    d = ImageDraw.Draw(img)
    f_title, f_sub, f_head = _font(64), _font(34), _font(22)
    f_name, f_focus, f_num = _font(32), _font(24), _font(32)

    d.text((PAD, 50), card.title, font=f_title, fill=NAVY)
    d.text((PAD, 132), card.subtitle, font=f_sub, fill=ORANGE)
    col_x, right = {}, WIDTH - PAD
    for c in reversed(card.columns):
        col_x[c] = right
        right -= _col_w(c)
    col_x = {c: col_x[c] for c in card.columns}
    for c, x in col_x.items():
        d.text((x, HEAD_H - 24), COLUMN_LABELS[c].upper(), font=f_head, fill=MUTED, anchor="rs")
    d.line((PAD, HEAD_H - 8, WIDTH - PAD, HEAD_H - 8), fill=LINE, width=2)

    text_x = PAD + 48 + ICON + 20
    text_w = right + 40 - text_x
    for i, app in enumerate(card.apps):
        y = HEAD_H + i * ROW_H
        mid = y + ROW_H // 2
        d.text((PAD, mid), f"{i + 1:02d}", font=f_head, fill=MUTED, anchor="lm")
        icon = fetch_icon(app.icon, icon_dir)
        tile = _round(icon) if icon else _letter_tile(app.name)
        img.paste(tile, (PAD + 48, mid - ICON // 2), tile)
        d.text((text_x, mid - 4), _fit(d, app.name, f_name, text_w), font=f_name, fill=NAVY, anchor="ls")
        if app.focus:
            d.text((text_x, mid + 6), _fit(d, app.focus, f_focus, text_w), font=f_focus, fill=MUTED, anchor="lt")
        for c, x in col_x.items():
            v = app.values.get(c)
            color = ORANGE if c in ("revenue", "verified") and v else (NAVY if v else MUTED)
            d.text((x, mid), v or "—", font=f_num, fill=color, anchor="rm")
        d.line((PAD, y + ROW_H - 1, WIDTH - PAD, y + ROW_H - 1), fill=LINE, width=1)

    note = card.source + (" · Revenue = ShotMatic estimate range, not real numbers" if card.revenue_note else "")
    if card.verified_note:
        note = card.source
    d.text((PAD, h - FOOT_H / 2), _fit(d, note, f_head, WIDTH - 2 * PAD), font=f_head, fill=MUTED, anchor="lm")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent.parent
    print(render_card(load_card(Path(args[0])), Path(args[1]), root / "inbox" / ".icons"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
