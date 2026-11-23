from pathlib import Path

from check_post import check_post, short_answer, x_length
from conftest import make_png
from new_post import create_post, read_post

GOOD_SHORT = ("Speaker cleaner is a crowded App Store keyword: the top 10 is almost all "
              "look-alike blue water icons, and the same five apps hold the first spots across "
              "speaker cleaner, cleaner volume and cleaner volume booster. A new app needs a "
              "different icon and a narrower long-tail keyword to stand out here.")
TABLE = "| Keyword | Rank |\n|---|---|\n| speaker cleaner | #1 |"


def _create(site, slug="speaker-cleaner-app-keywords"):
    landing, appdemo = site
    src = make_png(landing.parent / "shot.png")
    return Path(create_post("keyword", "2026-11-23", slug, "Speaker cleaner apps", "speaker cleaner",
                            "ShotMatic Keyword ranks, US App Store, measured 2026-11-23", src, landing, appdemo)["post"])


def _filled(site) -> Path:
    post = _create(site)
    t = post.read_text()
    t = t.replace("x_caption: ''", "x_caption: Speaker cleaner apps look the same. https://example.com/x")
    t = t.replace(t.split("## The short answer\n\n")[1].split("\n")[0], GOOD_SHORT)
    t = t.replace(t.split("## The numbers in the screenshot\n\n")[1].split("\n\n")[0], TABLE)
    t = t.replace("- WRITE: 3–5 bullets about the keyword niche, each with a number and where it comes from.", "- 5 of 10 icons are blue.")
    t = t.replace("WRITE: 2–3 sentences of advice for an indie app maker.", "Pick a narrower keyword.")
    post.write_text(t)
    return post


def test_x_length_counts_urls_as_23():
    assert x_length("hi https://example.com/very/long/path/that/is/long") == 3 + 23


def test_short_answer_extracts_section():
    assert short_answer("# T\n\n## The short answer\n\nOne two three.\n\n## Next\n\nx").strip() == "One two three."


def test_filled_post_passes(site):
    assert check_post(_filled(site), *site) == []


def test_skeleton_fails_with_reasons(site):
    errors = check_post(_create(site, "s"), *site)
    assert any("WRITE:" in e for e in errors)
    assert any("x_caption" in e for e in errors)
    assert any("short answer" in e for e in errors)


def test_long_caption_fails(site):
    post = _filled(site)
    fm, _ = read_post(post)
    post.write_text(post.read_text().replace(fm["x_caption"], "x" * 281))
    assert any("280" in e for e in check_post(post, *site))


def test_image_missing_in_appdemo_fails(site):
    post = _filled(site)
    for p in (site[1] / "shotmatic/reports/keyword").glob("*.png"):
        p.unlink()
    assert any("image not found in app-demo" in e for e in check_post(post, *site))


def test_image_not_on_appdemo_url_fails(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("https://nvminhtu.github.io/app-demo/", "https://example.com/"))
    assert any("image name must be" in e for e in check_post(post, *site))


def test_numbers_section_needs_table(site):
    post = _filled(site)
    post.write_text(post.read_text().replace(TABLE, "Just words."))
    assert any("needs a Markdown table" in e for e in check_post(post, *site))


def test_missing_numbers_section_fails(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("## The numbers in the screenshot", "## Numbers"))
    assert any("The numbers in the screenshot" in e for e in check_post(post, *site))


def test_wrong_folder_and_date_fail(site):
    post = _filled(site)
    moved = site[0] / "content/reports/trend/2026-11-22-speaker-cleaner-app-keywords.md"
    moved.parent.mkdir(parents=True, exist_ok=True)
    moved.write_text(post.read_text())
    errors = check_post(moved, *site)
    assert any("folder" in e for e in errors)
    assert any("date" in e for e in errors)


def test_missing_measured_section_fails(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("## How this was measured", "## Notes"))
    assert any("How this was measured" in e for e in check_post(post, *site))
