#!/usr/bin/env python3
"""Build keywords/bank.csv: the search phrases shotmatic.app targets, each with the live page that owns it.

Sources (niche-radar docs/marketing):
  - shotmatic-seo-longtail-keywords-2026-11-21.xlsx, sheet Keywords (351 Google Autocomplete long-tails → topic → page)
  - plan-blog-ai-search-30-keywords-2026-11-09.md, K1–K30 (AI-search / GEO keywords)
`link` is a page that exists in the landing today; a planned page ("NEW: …", a draft post) falls back to the cluster hub.
Re-run when those files change: .venv/bin/python scripts/build_keyword_bank.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import openpyxl

from new_post import LANDING

ROOT = Path(__file__).resolve().parent.parent
MKT = Path("/Users/tucarmd/DATA/PROJECTS/OTHERS/CLAUDE_SKILL/Niche-Research/niche-radar/docs/marketing")
XLSX = MKT / "shotmatic-seo-longtail-keywords-2026-11-21.xlsx"
GEO = MKT / "plan-blog-ai-search-30-keywords-2026-11-09.md"
OUT = ROOT / "keywords" / "bank.csv"
HUB = {  # cluster letter → hub page on shotmatic.app
    "A": "/app-idea-checker", "B": "/app-category-tier-list", "C": "/app-store-keyword-research",
    "D": "/app-competitor-analysis", "E": "/features/demand-and-money", "F": "/free-vs-pro", "G": "/features",
}
GEO_CLUSTER = {"A": "A · Validate app idea", "B": "B · Find app ideas / niche", "C": "C · ASO / store keywords",
               "D": "D · Competitors / downloads / revenue", "E": "E · Google Trends", "F": "F · Tools / alternatives",
               "G": "G · Launch / publish"}


def live(landing: Path, page: str) -> bool:
    page = page.split("#")[0].rstrip("/") or "/"
    if page.startswith("/blog/"):
        f = landing / "content" / "blog" / f"{page[6:]}.md"
        return f.exists() and not re.search(r"^draft:\s*true", f.read_text(), re.M)
    if page.startswith("/features/"):
        return f"slug: '{page[10:]}'" in (landing / "components" / "guide" / "features.js").read_text()
    return page == "/" or (landing / "pages" / f"{page.lstrip('/')}.jsx").exists() or (landing / "pages" / page.lstrip("/") / "index.jsx").exists()


def resolve(landing: Path, target: str | None, cluster: str) -> str:
    t = (target or "").strip()
    if t and not t.startswith("NEW") and live(landing, t):
        return t
    return HUB[cluster[0]]


def rows_from_xlsx(landing: Path) -> list[dict]:
    ws = openpyxl.load_workbook(XLSX, read_only=True)["Keywords"]
    out = []
    for kw, cluster, topic, fit, pos, _hits, _words, target, *_ in list(ws.iter_rows(values_only=True))[1:]:
        if kw:
            out.append({"keyword": kw.strip().lower(), "cluster": cluster, "topic": topic, "fit": fit,
                        "autocomplete_pos": pos, "link": resolve(landing, target, cluster), "source": "seo-longtail-2026-11-21"})
    return out


def rows_from_geo(landing: Path) -> list[dict]:
    out, cluster = [], "A"
    for line in GEO.read_text().splitlines():
        m = re.match(r"^### Cụm ([A-G])", line)
        if m:
            cluster = m.group(1)
        m = re.match(r"^\*\*(K\d+) · (.+?)\*\*", line)
        if m:
            out.append({"keyword": m.group(2).strip().lower(), "cluster": GEO_CLUSTER[cluster], "topic": f"GEO {m.group(1)}",
                        "fit": "Core", "autocomplete_pos": "", "link": HUB[cluster], "source": f"geo-30-{m.group(1)}"})
    return out


def build(landing: Path = LANDING) -> list[dict]:
    seen, bank = set(), []
    for r in rows_from_geo(landing) + rows_from_xlsx(landing):  # GEO first: it wins on duplicates
        if r["keyword"] not in seen:
            seen.add(r["keyword"])
            bank.append(r)
    return bank


def main() -> int:
    bank = build()
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bank[0]))
        w.writeheader()
        w.writerows(bank)
    print(f"{len(bank)} keywords → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
