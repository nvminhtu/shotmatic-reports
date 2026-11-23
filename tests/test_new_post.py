from pathlib import Path

import pytest

from conftest import make_png
from new_post import create_post, load_types, read_post, slugify

URL = "https://nvminhtu.github.io/app-demo/shotmatic/reports"


def test_load_types_keeps_order(site):
    assert list(load_types(site[0])) == ["trend", "hunt-app", "keyword", "aso", "review", "youtube"]


@pytest.mark.parametrize("text,expected", [
    ("Speaker Cleaner — Keyword Ranks!", "speaker-cleaner-keyword-ranks"),
    ("  Café  apps  2026 ", "cafe-apps-2026"),
    ("a" * 70, "a" * 60),
    ("word " * 20, "word-word-word-word-word-word-word-word-word-word-word-word"),
])
def test_slugify(text, expected):
    assert slugify(text) == expected
    assert len(slugify(text)) <= 60


def _new(site, slug="speaker-cleaner-app-keywords", date="2026-11-23", type_="keyword", title="T"):
    landing, appdemo = site
    src = make_png(landing.parent / f"shot-{slug}-{date.replace('/', '-')}.png")
    return create_post(type_, date, slug, title, "speaker cleaner",
                       "ShotMatic Keyword ranks, US App Store, measured 2026-11-23", src, landing, appdemo)


def test_create_post_writes_post_to_landing_and_image_to_appdemo(site):
    landing, appdemo = site
    r = _new(site)
    post = Path(r["post"])
    assert post == landing / "content/reports/keyword/2026-11-23-speaker-cleaner-app-keywords.md"
    name = "shotmatic.app-speaker-cleaner-app-keywords-2026-11-23.png"
    assert Path(r["image"]) == appdemo / "shotmatic/reports/keyword" / name
    assert r["image_url"] == f"{URL}/keyword/{name}"
    assert r["url"] == "https://shotmatic.app/reports/keyword/speaker-cleaner-app-keywords"
    fm, body = read_post(post)
    assert list(fm) == ["title", "date", "type", "keyword", "short", "image", "source", "x_caption"]
    assert fm["date"] == "2026-11-23" and fm["image"] == r["image_url"] and fm["x_caption"] == ""
    assert fm["short"] == "Speaker cleaner app keywords"
    for h in ["## The short answer", "## The numbers in the screenshot", "## What the data shows",
              "## What this means if you build in this niche", "## How this was measured"]:
        assert h in body
    assert f"]({r['image_url']})" in body and "WRITE:" in body


def test_slug_unique_per_type_across_dates(site):
    _new(site, date="2026-11-20")
    r2 = _new(site, date="2026-11-23")
    assert r2["slug"] == "speaker-cleaner-app-keywords-2"
    assert Path(r2["post"]).name == "2026-11-23-speaker-cleaner-app-keywords-2.md"


def test_same_slug_ok_in_other_type(site):
    _new(site)
    assert _new(site, type_="trend")["slug"] == "speaker-cleaner-app-keywords"


def test_unknown_type_rejected(site):
    with pytest.raises(ValueError, match="unknown type"):
        _new(site, type_="podcast")


def test_bad_date_rejected(site):
    with pytest.raises(ValueError, match="date"):
        _new(site, date="23/11/2026")


def test_titles_with_quotes_survive_yaml(site):
    r = _new(site, slug="q", title='Top 10 "speaker cleaner" apps: ranks')
    assert read_post(Path(r["post"]))[0]["title"] == 'Top 10 "speaker cleaner" apps: ranks'
