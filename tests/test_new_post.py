import json
from pathlib import Path

import pytest

from conftest import make_png
from new_post import create_post, load_types, read_post, rebuild_site, slugify


def test_load_types_keeps_order(site_root):
    assert list(load_types(site_root)) == ["trend", "hunt-app", "keyword", "aso", "review", "youtube"]


@pytest.mark.parametrize("text,expected", [
    ("Speaker Cleaner — Keyword Ranks!", "speaker-cleaner-keyword-ranks"),
    ("  Café  apps  2026 ", "cafe-apps-2026"),
    ("a" * 70, "a" * 60),
    ("word " * 20, "word-word-word-word-word-word-word-word-word-word-word-word"),
])
def test_slugify(text, expected):
    assert slugify(text) == expected
    assert len(slugify(text)) <= 60


def _new(site_root, slug="speaker-cleaner-keyword-ranks", date="2026-11-23", type_="keyword", title=None):
    src = make_png(site_root / f"shot-{slug}-{date.replace('/', '-')}.png")
    return create_post(site_root, type_, date, slug, title or f"Title {slug}",
                       "speaker cleaner", "ShotMatic Keyword ranks, US App Store, measured 2026-11-23", src)


def test_create_post_writes_image_and_skeleton(site_root):
    r = _new(site_root)
    post = Path(r["post"])
    assert post == site_root / "docs/keyword/2026-11-23-speaker-cleaner-keyword-ranks.md"
    assert Path(r["image"]).name == "shotmatic.app-speaker-cleaner-keyword-ranks-2026-11-23.png"
    assert Path(r["image"]).parent == site_root / "docs/keyword/img"
    fm, body = read_post(post)
    assert list(fm) == ["title", "date", "type", "keyword", "short", "image", "source", "x_caption"]
    assert fm["date"] == "2026-11-23"
    assert fm["short"] == "Speaker cleaner keyword ranks"
    assert fm["image"] == "img/shotmatic.app-speaker-cleaner-keyword-ranks-2026-11-23.png"
    assert fm["x_caption"] == ""
    assert "## The short answer" in body and "## How this was measured" in body
    assert "WRITE:" in body
    assert "](img/shotmatic.app-speaker-cleaner-keyword-ranks-2026-11-23.png)" in body
    assert "https://shotmatic.app" in body


def test_slug_collision_gets_suffix(site_root):
    _new(site_root)
    r2 = _new(site_root)
    assert r2["slug"] == "speaker-cleaner-keyword-ranks-2"
    assert Path(r2["image"]).name == "shotmatic.app-speaker-cleaner-keyword-ranks-2-2026-11-23.png"


def test_unknown_type_rejected(site_root):
    with pytest.raises(ValueError, match="unknown type"):
        _new(site_root, type_="podcast")


def test_bad_date_rejected(site_root):
    with pytest.raises(ValueError, match="date"):
        _new(site_root, date="23/11/2026")


def test_rebuild_nav_groups_by_type_newest_first(site_root):
    _new(site_root, slug="old-one", date="2026-11-20")
    _new(site_root, slug="new-one", date="2026-11-23")
    _new(site_root, slug="a-trend", date="2026-11-22", type_="trend")
    yml = (site_root / "mkdocs.yml").read_text()
    block = yml.split("# BEGIN NAV")[1].split("# END NAV")[0]
    assert block.index("- Trend:") < block.index("- Keyword:")
    assert block.index("new-one") < block.index("old-one")
    assert '"Nov 23 · New one": keyword/2026-11-23-new-one.md' in block
    assert "- keyword/index.md" in block
    assert "Hunt App" not in block  # empty types are hidden
    assert yml.startswith("site_name: T\n") and yml.rstrip().endswith("# END NAV")


def test_rebuild_writes_home_and_type_index(site_root):
    _new(site_root, slug="old-one", date="2026-11-20", title="Old title")
    _new(site_root, slug="a-trend", date="2026-11-22", type_="trend", title="Trend title")
    home = (site_root / "docs/index.md").read_text()
    assert home.startswith("# Home")
    posts = home.split("<!-- BEGIN POSTS -->")[1].split("<!-- END POSTS -->")[0]
    assert posts.index("Nov 22, 2026") < posts.index("Nov 20, 2026")
    assert "- [Trend title](trend/2026-11-22-a-trend.md) · Trend" in posts
    assert "_No reports yet._" not in posts
    kw = (site_root / "docs/keyword/index.md").read_text()
    assert kw.startswith("# Keyword reports")
    assert "- Nov 20, 2026 · [Old title](2026-11-20-old-one.md)" in kw


def test_titles_with_quotes_survive_yaml(site_root):
    _new(site_root, slug="q", title='Top 10 "speaker cleaner" apps: ranks')
    fm, _ = read_post(site_root / "docs/keyword/2026-11-23-q.md")
    assert fm["title"] == 'Top 10 "speaker cleaner" apps: ranks'
