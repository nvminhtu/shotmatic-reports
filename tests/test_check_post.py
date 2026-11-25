from pathlib import Path

from check_post import check_post, short_answer, x_length
from conftest import make_png
from new_post import create_post, read_post

GOOD_SHORT = ("Speaker cleaner is a crowded App Store keyword: the top 10 is almost all "
              "look-alike blue water icons, and the same five apps hold the first spots across "
              "speaker cleaner, cleaner volume and cleaner volume booster. A new app needs a "
              "different icon and a narrower long-tail keyword to stand out here.")
TABLE = "| Keyword | Rank |\n|---|---|\n| speaker cleaner | #1 |"
BANK = [{"keyword": "aso keyword ranking", "link": "/app-store-keyword-research", "cluster": "C · ASO / store keywords",
         "fit": "Core", "autocomplete_pos": "1", "topic": "t", "source": "s"}]
DESC = ("Speaker cleaner app keywords on the US App Store: 4 of 8 long-tail searches are winnable, 3 belong to other "
        "niches. Ranks and what they mean.")
ASO_TABLE = ("| Keyword | Where to use it | Why |\n|---|---|---|\n| speaker cleaner | title | #1 |\n"
             "| cleaner volume | subtitle | #2 |\n| water eject | keyword field | not measured |")


def check(post, landing, appdemo):
    return check_post(post, landing, appdemo, BANK)


def _create(site, slug="speaker-cleaner-app-keywords"):
    landing, appdemo = site
    src = make_png(landing.parent / "shot.png")
    return Path(create_post("keyword", "2026-11-23", slug, "Speaker cleaner app keywords ranked for 2026", "speaker cleaner",
                            "ShotMatic Keyword ranks, US App Store, measured 2026-11-23", src, landing, appdemo,
                            seo_keyword="speaker cleaner app keywords", targets=["aso keyword ranking"],
                            links={r["keyword"]: r["link"] for r in BANK}, store="app-store", country="us")["post"])


def _filled(site) -> Path:
    post = _create(site)
    t = post.read_text()
    t = t.replace("x_caption: ''", "x_caption: Speaker cleaner apps look the same. https://example.com/x")
    t = t.replace(t.split("## The short answer\n\n")[1].split("\n")[0], GOOD_SHORT)
    t = t.replace(t.split("## The numbers in the screenshot\n\n")[1].split("\n\n")[0], TABLE)
    t = t.replace("WRITE: alt text, what the screenshot shows in words (≤ 125 chars, with the niche keyword)",
                  "ShotMatic keyword ranks for speaker cleaner apps on the US App Store")
    t = t.replace(t.split("## Is anyone searching for this?\n\n")[1].split("\n\n")[0],
                  "\"speaker cleaner\" is the #1 App Store autocomplete suggestion for \"speaker\".")
    t = t.replace("- WRITE: 3–5 bullets about the keyword niche, each with a number and where it comes from.", "- 5 of 10 icons are blue.")
    t = t.replace("WRITE: 2–3 sentences of advice for an indie app maker.",
                  "Pick a narrower keyword; an aso keyword ranking check shows where you stand.")
    t = t.replace("description: ''", f"description: '{DESC}'")
    t = t.replace("aso_keywords: []", "aso_keywords:\n- speaker cleaner\n- cleaner volume\n- water eject")
    t = t.replace("  stat: ''\n  text: ''", "  stat: '#1'\n  text: 'A speaker cleaner app holds #1 for \"speaker cleaner\" but misses the top 50 for \"volume\".'")
    t = t.replace(t.split("## ASO keywords for this niche\n\n")[1].split("\n\n## ")[0], ASO_TABLE)
    t = t.replace("WRITE: one line on why this helps someone in this niche", "see every keyword rank in one place")
    post.write_text(t)
    return post


def test_x_length_counts_urls_as_23():
    assert x_length("hi https://example.com/very/long/path/that/is/long") == 3 + 23


def test_short_answer_extracts_section():
    assert short_answer("# T\n\n## The short answer\n\nOne two three.\n\n## Next\n\nx").strip() == "One two three."


def test_filled_post_passes(site):
    assert check(_filled(site), *site) == []


def test_skeleton_fails_with_reasons(site):
    errors = check(_create(site, "s"), *site)
    assert any("WRITE:" in e for e in errors)
    assert any("x_caption" in e for e in errors)
    assert any("short answer" in e for e in errors)


def test_long_caption_fails(site):
    post = _filled(site)
    fm, _ = read_post(post)
    post.write_text(post.read_text().replace(fm["x_caption"], "x" * 281))
    assert any("280" in e for e in check(post, *site))


def test_image_missing_in_appdemo_fails(site):
    post = _filled(site)
    for p in (site[1] / "shotmatic/reports/keyword").glob("*.png"):
        p.unlink()
    assert any("image not found in app-demo" in e for e in check(post, *site))


def test_image_not_on_appdemo_url_fails(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("https://nvminhtu.github.io/app-demo/", "https://example.com/"))
    assert any("image name must be" in e for e in check(post, *site))


def test_numbers_section_needs_table(site):
    post = _filled(site)
    post.write_text(post.read_text().replace(TABLE, "Just words."))
    assert any("needs a Markdown table" in e for e in check(post, *site))


def test_missing_numbers_section_fails(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("## The numbers in the screenshot", "## Numbers"))
    assert any("The numbers in the screenshot" in e for e in check(post, *site))


def test_wrong_folder_and_date_fail(site):
    post = _filled(site)
    moved = site[0] / "content/reports/trend/2026-11-22-speaker-cleaner-app-keywords.md"
    moved.parent.mkdir(parents=True, exist_ok=True)
    moved.write_text(post.read_text())
    errors = check(moved, *site)
    assert any("folder" in e for e in errors)
    assert any("date" in e for e in errors)


def test_missing_measured_section_fails(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("## How this was measured", "## Notes"))
    assert any("How this was measured" in e for e in check(post, *site))


def _edit(post, old, new):
    post.write_text(post.read_text().replace(old, new))


def test_title_without_seo_keyword_fails(site):
    post = _filled(site)
    _edit(post, "title: Speaker cleaner app keywords ranked for 2026", "title: Some other title")
    assert any("title must contain" in e for e in check(post, *site))


def test_short_description_fails(site):
    post = _filled(site)
    _edit(post, DESC, "Speaker cleaner app keywords.")
    assert any("description is" in e for e in check(post, *site))


def test_target_link_required(site):
    post = _filled(site)
    _edit(post, "](/app-store-keyword-research)", "](/somewhere)")
    assert any("needs a link to /app-store-keyword-research" in e for e in check(post, *site))


def test_aso_keyword_missing_from_section_fails(site):
    post = _filled(site)
    _edit(post, "| water eject | keyword field | not measured |", "")
    assert any("missing: water eject" in e for e in check(post, *site))


def test_seo_keyword_owned_by_blog_post_fails(site):
    post = _filled(site)
    blog = site[0] / "content" / "blog"
    blog.mkdir(parents=True)
    (blog / "x.md").write_text("---\nkeyword: speaker cleaner app keywords\n---\nbody")
    assert any("already owned by x.md" in e for e in check(post, *site))


def test_internal_ids_fail_but_ranks_pass(site):
    post = _filled(site)
    t = post.read_text()
    assert check(post, *site) == []  # the filled post has ranks like #1, which are fine
    post.write_text(t.replace("## How this was measured", "Source: [ASO #45 · 2026-11-21].\n\n## How this was measured"))
    assert any("[ASO #45 · 2026-11-21]" in e for e in check(post, *site))
    post.write_text(t.replace("## How this was measured", "From trending #48.\n\n## How this was measured"))
    assert any("trending #48" in e for e in check(post, *site))


def test_store_and_country_required(site):
    post = _filled(site)
    fm, _ = read_post(post)
    assert fm["store"] == "app-store" and fm["country"] == "US"
    post.write_text(post.read_text().replace("store: app-store", "store: play"))
    assert any("store must be" in e for e in check(post, *site))


def _strict(post: Path) -> Path:
    """Move a filled post to a date where the 2026-11-24 rules apply."""
    new = post.with_name(post.name.replace("2026-11-23", "2026-11-25"))
    new.write_text(post.read_text().replace("date: '2026-11-23'", "date: '2026-11-25'"))
    post.unlink()
    return new


def test_strict_post_needs_demand_section(site):
    post = _strict(_filled(site))
    t = post.read_text()
    start = t.index("## Is anyone searching for this?")
    post.write_text(t[:start] + t[t.index("## What the data shows"):])
    assert any("Is anyone searching" in e for e in check(post, *site))


def test_strict_post_rejects_junk_keywords(site):
    post = _strict(_filled(site))
    t = post.read_text()
    assert check(post, *site) == []
    post.write_text(t.replace("| speaker cleaner | #1 |", "| speaker cleaner | #1 |\n| r money | #8 |"))
    assert any("junk store keywords" in e and "r money" in e for e in check(post, *site))


def test_junk_keywords_keeps_real_phrases():
    from check_post import junk_keywords
    body = "| Keyword | Rank |\n|---|---|\n| budget tracker | #7 |\n| m money x lao | #12 |\n| a budget app | #3 |"
    assert junk_keywords(body) == ["m money x lao"]


def test_strict_post_needs_real_alt(site):
    post = _strict(_filled(site))
    t = post.read_text()
    post.write_text(t.replace("ShotMatic keyword ranks for speaker cleaner apps on the US App Store", "speaker cleaner — ShotMatic report"))
    assert any("alt text" in e for e in check(post, *site))


def test_updated_must_follow_date(site):
    post = _filled(site)
    t = post.read_text()
    post.write_text(t.replace("date: '2026-11-23'", "date: '2026-11-23'\nupdated: '2026-11-30'"))
    assert check(post, *site) == []
    post.write_text(t.replace("date: '2026-11-23'", "date: '2026-11-23'\nupdated: '2026-11-01'"))
    assert any("updated must be on or after" in e for e in check(post, *site))


def test_highlight_required(site):
    post = _filled(site)
    assert check_post(post, *site, bank=BANK) == []
    post.write_text(post.read_text().replace("  stat: '#1'", "  stat: ''"))
    assert any("highlight" in e for e in check_post(post, *site, bank=BANK))


def test_highlight_stat_needs_a_number(site):
    post = _filled(site)
    post.write_text(post.read_text().replace("  stat: '#1'", "  stat: 'big'"))
    assert any("highlight.stat" in e for e in check_post(post, *site, bank=BANK))


def test_chart_blocks_checked(site):
    from check_post import chart_errors
    ok = "```chart\ntype: change\nitems:\n  - { label: g, from: 1, to: 2 }\nsource: Trends\n```"
    assert chart_errors(ok) == []
    assert any("type must be" in e for e in chart_errors("```chart\ntype: pie\nsource: x\n```"))
    assert any("needs label, from, to" in e for e in chart_errors("```chart\ntype: change\nitems:\n  - { label: g }\nsource: x\n```"))
    assert any("needs 2 values" in e for e in chart_errors("```chart\ntype: line\nx: [a, b]\nseries:\n  - { name: s, values: [1] }\nsource: x\n```"))
    assert any("source" in e for e in chart_errors("```chart\ntype: stats\nitems:\n  - { value: 1, label: a }\n```"))
