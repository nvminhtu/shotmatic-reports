from pathlib import Path

from PIL import Image

from card_data import Card, CardApp
from card_render import HEAD_H, FOOT_H, ROW_H, WIDTH, render_card
from conftest import make_png


def card(n: int, icon: str | None) -> Card:
    apps = [CardApp(f"App {i}", "Period & symptom tracking", icon,
                    {"installs": "1M+", "rating": "4.6" if i else None}) for i in range(n)]
    return Card("5 period tracker apps", "Top apps · US App Store", "ShotMatic Research, US App Store, measured 2026-11-25",
                ["installs", "rating"], apps, revenue_note=False)


def test_size_grows_with_rows(tmp_path):
    out = render_card(card(5, None), tmp_path / "c.png", tmp_path / "icons")
    img = Image.open(out)
    assert img.width == WIDTH
    assert img.height == HEAD_H + 5 * ROW_H + FOOT_H


def test_uses_local_icon_and_white_background(tmp_path):
    icon = make_png(tmp_path / "icon.png", (100, 100), (255, 0, 0))
    out = render_card(card(3, str(icon)), tmp_path / "c.png", tmp_path / "icons")
    img = Image.open(out).convert("RGB")
    assert img.getpixel((5, 5)) == (255, 255, 255)
    reds = sum(1 for x in range(0, 300) for y in range(HEAD_H, HEAD_H + ROW_H) if img.getpixel((x, y)) == (255, 0, 0))
    assert reds > 1000  # the icon is drawn in row 1


def test_missing_icon_does_not_crash(tmp_path):
    out = render_card(card(3, str(tmp_path / "nope.png")), tmp_path / "c.png", tmp_path / "icons")
    assert Path(out).exists()
