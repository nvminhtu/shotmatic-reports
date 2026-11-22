from pathlib import Path

from check_post import check_post, short_answer, x_length
from conftest import make_png
from new_post import create_post, read_post

GOOD_SHORT = ("Speaker cleaner is a crowded App Store keyword: the top 10 is almost all "
              "look-alike blue water icons, and the same five apps hold the first spots across "
              "speaker cleaner, cleaner volume and cleaner volume booster. A new app needs a "
              "different icon and a narrower long-tail keyword to stand out here.")


def _filled(site_root) -> Path:
    src = make_png(site_root / "shot.png")
    r = create_post(site_root, "keyword", "2026-11-23", "speaker-cleaner-keyword-ranks",
                    "Top 10 speaker cleaner apps", "speaker cleaner",
                    "ShotMatic Keyword ranks, US App Store, measured 2026-11-23", src)
    post = Path(r["post"])
    text = post.read_text()
    text = text.replace("x_caption: ''", "x_caption: Top 10 speaker cleaner apps on the App Store look the same. https://example.com/x")
    text = text.replace(text.split("## The short answer\n\n")[1].split("\n")[0], GOOD_SHORT)
    text = text.replace("- WRITE: 3–5 bullets, each with a number and where it comes from.", "- 5 of 10 icons are blue.")
    text = text.replace("WRITE: 2–3 sentences of advice for an indie app maker.", "Pick a narrower keyword.")
    post.write_text(text)
    return post


def test_x_length_counts_urls_as_23():
    assert x_length("hi https://example.com/very/long/path/that/is/long") == 3 + 23


def test_short_answer_extracts_section():
    body = "# T\n\n## The short answer\n\nOne two three.\n\n## Next\n\nx"
    assert short_answer(body).strip() == "One two three."


def test_filled_post_passes(site_root):
    post = _filled(site_root)
    assert check_post(post, site_root) == []


def test_skeleton_fails_with_reasons(site_root):
    src = make_png(site_root / "shot.png")
    r = create_post(site_root, "keyword", "2026-11-23", "s", "T", "k", "src", src)
    errors = check_post(Path(r["post"]), site_root)
    assert any("WRITE:" in e for e in errors)
    assert any("x_caption" in e for e in errors)
    assert any("short answer" in e for e in errors)


def test_long_caption_fails(site_root):
    post = _filled(site_root)
    fm, _ = read_post(post)
    post.write_text(post.read_text().replace(fm["x_caption"], "x" * 281))
    assert any("280" in e for e in check_post(post, site_root))


def test_missing_image_fails(site_root):
    post = _filled(site_root)
    fm, _ = read_post(post)
    (post.parent / fm["image"]).unlink()
    assert any("image not found" in e for e in check_post(post, site_root))


def test_bad_image_name_fails(site_root):
    post = _filled(site_root)
    post.write_text(post.read_text().replace("image: img/shotmatic.app-", "image: img/shot-"))
    assert any("image name" in e for e in check_post(post, site_root))


def test_wrong_folder_and_date_fail(site_root):
    post = _filled(site_root)
    moved = site_root / "docs" / "trend" / "2026-11-22-speaker-cleaner-keyword-ranks.md"
    moved.parent.mkdir(parents=True, exist_ok=True)
    moved.write_text(post.read_text())
    errors = check_post(moved, site_root)
    assert any("folder" in e for e in errors)
    assert any("date" in e for e in errors)


def test_missing_measured_section_fails(site_root):
    post = _filled(site_root)
    post.write_text(post.read_text().replace("## How this was measured", "## Notes"))
    assert any("How this was measured" in e for e in check_post(post, site_root))
