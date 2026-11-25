#!/usr/bin/env python3
"""Create a report on shotmatic.app/reports: stamp the screenshot into app-demo, write the post skeleton into the landing.

Post:  <LANDING>/content/reports/<type>/<YYYY-MM-DD>-<slug>.md   → https://shotmatic.app/reports/<type>/<slug>
Image: <APPDEMO>/shotmatic/reports/<type>/shotmatic.app-<slug>-<date>.png
       → https://nvminhtu.github.io/app-demo/shotmatic/reports/<type>/<file>  (app-demo is pushed before the landing)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import yaml

from watermark import WatermarkError, watermark

LANDING = Path(os.environ.get("REPORTS_LANDING",
    "/Users/tucarmd/DATA/PROJECTS/OTHERS/CLAUDE_SKILL/Master-List-Dashboard/shotmatic-reports-section"))
APPDEMO = Path(os.environ.get("REPORTS_APPDEMO", "/Users/tucarmd/DATA/PROJECTS/OTHERS/app-demo"))
IMG_URL = "https://nvminhtu.github.io/app-demo/shotmatic/reports"
SITE_URL = "https://shotmatic.app/reports"
STORES = ("app-store", "google-play")
FM_KEYS = ["title", "description", "date", "type", "store", "country", "keyword", "seo_keyword", "target_keywords", "aso_keywords",
           "short", "image", "source", "x_caption"]

BODY = """# {title}

## The short answer

WRITE: 40–60 words about the long-tail keyword niche "{keyword}" (not about one app), with 1–2 numbers from the screenshot.

![WRITE: alt text, what the screenshot shows in words (≤ 125 chars, with the niche keyword)]({image})

## The numbers in the screenshot

| WRITE: column | Column |
|---|---|
| WRITE: one row for every number on the screenshot (keyword, rank, score…) | |

## Is anyone searching for this?

WRITE: 1–3 sentences on demand, each with a number + source: Google / store autocomplete position, Google Trends 12-month direction (google-trends MCP), ShotMatic demand score. Write "not measured" only for a signal you tried and could not get.

## What the data shows

- WRITE: 3–5 bullets about the keyword niche, each with a number and where it comes from.

## What this means if you build in this niche

WRITE: 2–3 sentences of advice for an indie app maker.

## ASO keywords for this niche

| Keyword | Where to use it | Why (number from the data) |
|---|---|---|
| WRITE: one row per aso_keyword (title, subtitle, keyword field or description) | | |

## Go deeper on shotmatic.app

{deeper}

## How this was measured

{source}.
"""


def reports_dir(landing: Path) -> Path:
    return landing / "content" / "reports"


def img_dir(appdemo: Path, type_: str) -> Path:
    return appdemo / "shotmatic" / "reports" / type_


def load_types(landing: Path = LANDING) -> dict[str, str]:
    return json.loads((reports_dir(landing) / "types.json").read_text())


def slugify(text: str, max_len: int = 60) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    if len(slug) > max_len:
        cut = slug[:max_len]
        slug = cut.rsplit("-", 1)[0] if "-" in cut and slug[max_len] != "-" else cut
    return slug.strip("-")


def read_post(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter")
    _, fm_text, body = text.split("---\n", 2)
    fm = yaml.safe_load(fm_text) or {}
    if "date" in fm:
        fm["date"] = str(fm["date"])
    return fm, body


def write_post(path: Path, fm: dict, body: str) -> None:
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000)
    path.write_text(f"---\n{fm_text}---\n\n{body.lstrip(chr(10))}")


def _taken(folder: Path) -> set[str]:
    """Slugs already used in a type folder (the URL has no date, so a slug is unique per type)."""
    return {p.name[11:-3] for p in folder.glob("*.md")} if folder.exists() else set()


def _unique_slug(folder: Path, slug: str) -> str:
    taken, candidate, n = _taken(folder), slug, 2
    while candidate in taken:
        candidate, n = f"{slug}-{n}", n + 1
    return candidate


def create_post(type_: str, date: str, slug: str, title: str, keyword: str, source: str,
                image_src: Path, landing: Path = LANDING, appdemo: Path = APPDEMO,
                seo_keyword: str = "", targets: list[str] | None = None, links: dict[str, str] | None = None,
                store: str = "", country: str = "") -> dict:
    """targets: 1–3 shotmatic.app keywords from keywords/bank.csv; links: keyword → page (defaults to the bank)."""
    if type_ not in load_types(landing):
        raise ValueError(f"unknown type {type_!r}; add it to content/reports/types.json in the landing")
    try:
        dt.date.fromisoformat(date)
    except ValueError as e:
        raise ValueError(f"date must be YYYY-MM-DD, got {date!r}") from e
    folder = reports_dir(landing) / type_
    slug = _unique_slug(folder, slugify(slug))
    image = watermark(Path(image_src), img_dir(appdemo, type_), slug, date)
    image_url = f"{IMG_URL}/{type_}/{image.name}"
    targets = targets or []
    if links is None:
        from seo_keywords import load_bank
        links = {r["keyword"]: r["link"] for r in load_bank()}
    unknown = [t for t in targets if t.lower() not in links]
    if unknown:
        raise ValueError(f"not in keywords/bank.csv: {', '.join(unknown)} (see scripts/seo_keywords.py suggest)")
    deeper = "\n".join(f"- [{t}]({links[t.lower()]}): WRITE: one line on why this helps someone in this niche" for t in targets) \
        or "- WRITE: one link per target keyword"
    fm = {
        "title": title,
        "description": "",
        "date": date,
        "type": type_,
        "store": store,
        "country": country.upper(),
        "keyword": keyword,
        "seo_keyword": seo_keyword,
        "target_keywords": targets,
        "aso_keywords": [],
        "short": slug.replace("-", " ").capitalize(),
        "image": image_url,
        "source": source,
        "x_caption": "",
    }
    folder.mkdir(parents=True, exist_ok=True)
    post = folder / f"{date}-{slug}.md"
    write_post(post, fm, BODY.format(title=title, keyword=keyword, image=image_url, source=source.rstrip("."), deeper=deeper))
    return {"slug": slug, "post": str(post), "image": str(image), "image_url": image_url,
            "url": f"{SITE_URL}/{type_}/{slug}"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--type", required=True)
    c.add_argument("--slug", required=True)
    c.add_argument("--title", required=True)
    c.add_argument("--keyword", required=True)
    c.add_argument("--source", required=True)
    c.add_argument("--store", required=True, choices=STORES, help="store the numbers come from (site filter)")
    c.add_argument("--country", required=True, help="2-letter country of the numbers, e.g. US (site filter)")
    c.add_argument("--image", type=Path, required=True)
    c.add_argument("--date", default=dt.date.today().isoformat())
    c.add_argument("--seo-keyword", default="", help="the search phrase this report should rank for")
    c.add_argument("--target", action="append", default=[], help="shotmatic.app keyword from keywords/bank.csv (1–3)")
    a = ap.parse_args(argv)
    try:
        r = create_post(a.type, a.date, a.slug, a.title, a.keyword, a.source, a.image,
                        seo_keyword=a.seo_keyword, targets=a.target, store=a.store, country=a.country)
        print(json.dumps(r, indent=2))
    except (ValueError, WatermarkError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
