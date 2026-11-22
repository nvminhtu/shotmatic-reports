from pathlib import Path

import pytest
from PIL import Image

from conftest import make_png
from watermark import WatermarkError, badge_height, image_name, watermark


def test_image_name():
    assert image_name("speaker-cleaner-keyword-ranks", "2026-11-23") == \
        "shotmatic.app-speaker-cleaner-keyword-ranks-2026-11-23.png"


@pytest.mark.parametrize("h,expected", [(300, 28), (1000, 40), (2000, 64), (800, 32)])
def test_badge_height_clamped(h, expected):
    assert badge_height(h) == expected


def strip(h: int) -> int:
    """Height of the strip added under an image of height h."""
    return badge_height(h) + 2 * max(8, round(h * 0.02))


def test_watermark_names_file_and_adds_strip(tmp_path: Path):
    src = make_png(tmp_path / "in.png", (1200, 800))
    out = watermark(src, tmp_path / "out", "speaker-cleaner", "2026-11-23")
    assert out == tmp_path / "out" / "shotmatic.app-speaker-cleaner-2026-11-23.png"
    img = Image.open(out)
    assert img.size == (1200, 800 + strip(800))  # 800 + 32 + 2*16
    assert img.format == "PNG"


def test_badge_in_strip_never_covers_screenshot(tmp_path: Path):
    src = make_png(tmp_path / "in.png", (1200, 800), color=(250, 250, 250))
    img = Image.open(watermark(src, tmp_path, "s", "2026-11-23")).convert("RGB")
    margin, h = 16, badge_height(800)  # 2% of 800, 32
    # the original screenshot area is untouched, even its bottom-right corner
    assert img.getpixel((1199, 799)) == (250, 250, 250)
    assert img.getpixel((5, 5)) == (250, 250, 250)
    # middle of the badge, inside the strip: dark navy
    r, g, b = img.getpixel((1200 - margin - 6, 800 + margin + h // 2))
    assert r < 120 and g < 120 and b < 140
    # strip takes the screenshot's bottom colour
    assert img.getpixel((5, 800 + 4)) == (250, 250, 250)


def test_wide_image_scaled_to_2400(tmp_path: Path):
    src = make_png(tmp_path / "in.png", (4800, 1000))
    img = Image.open(watermark(src, tmp_path, "s", "2026-11-23"))
    assert img.size == (2400, 500 + strip(500))


def test_small_image_not_upscaled(tmp_path: Path):
    src = make_png(tmp_path / "in.png", (900, 600))
    assert Image.open(watermark(src, tmp_path, "s", "2026-11-23")).size == (900, 600 + strip(600))


def test_webp_input(tmp_path: Path):
    src = tmp_path / "in.webp"
    Image.new("RGB", (1000, 700), (240, 240, 240)).save(src, "WEBP")
    out = watermark(src, tmp_path, "s", "2026-11-23")
    assert out.suffix == ".png"


def test_not_an_image_raises(tmp_path: Path):
    bad = tmp_path / "bad.png"
    bad.write_text("hello")
    with pytest.raises(WatermarkError, match="cannot open image"):
        watermark(bad, tmp_path, "s", "2026-11-23")


def test_too_small_raises(tmp_path: Path):
    src = make_png(tmp_path / "in.png", (120, 60))
    with pytest.raises(WatermarkError, match="too small"):
        watermark(src, tmp_path, "s", "2026-11-23")
