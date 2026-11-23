#!/usr/bin/env python3
"""SEO / ASO keyword step of a report.

  suggest --type keyword --text "speaker cleaner keyword ranks app store"
      → the shotmatic.app target keywords (keywords/bank.csv) that fit this report, best first, with the page to link.
  taken
      → search phrases already owned by a report (seo_keyword) or a blog post (keyword): never reuse one.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from new_post import LANDING, read_post, reports_dir

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "keywords" / "bank.csv"
TYPE_CLUSTER = {"keyword": "C", "aso": "C", "trend": "E", "hunt-app": "B", "review": "D", "youtube": None}
STOP = {"a", "an", "the", "for", "of", "to", "in", "on", "and", "or", "vs", "with", "my", "your", "is", "are", "do", "does",
        "how", "what", "which", "best", "free", "top"}


def tokens(text: str) -> set[str]:
    """Content words, lowercase, plural 's' dropped: 'Speaker cleaner apps' → {'speaker', 'cleaner', 'app'}."""
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        out.add(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
    return out


def covers(text: str, phrase: str) -> bool:
    return tokens(phrase) <= tokens(text)


def load_bank(path: Path = BANK) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def suggest(type_: str, text: str, bank: list[dict], n: int = 10) -> list[dict]:
    want, cl = tokens(text), TYPE_CLUSTER.get(type_)
    scored = []
    for r in bank:
        overlap = len(want & tokens(r["keyword"]))
        same = cl is not None and r["cluster"].startswith(cl)
        if not overlap and not same:
            continue
        pos = int(r["autocomplete_pos"]) if str(r["autocomplete_pos"]).isdigit() else 11
        score = 3 * overlap + (5 if same else 0) + (1 if r["fit"] == "Core" else 0) + (11 - pos) / 10
        scored.append((score, r))
    scored.sort(key=lambda s: -s[0])
    return [dict(r, score=round(s, 1)) for s, r in scored[:n]]


def taken(landing: Path = LANDING) -> dict[str, list[str]]:
    """search phrase (lowercase) → every file that targets it (reports' seo_keyword, blog posts' keyword)."""
    owners: dict[str, list[str]] = {}
    for p in sorted(reports_dir(landing).glob("*/*.md")):
        kw = str(read_post(p)[0].get("seo_keyword", "")).strip().lower()
        if kw:
            owners.setdefault(kw, []).append(str(p))
    for p in sorted((landing / "content" / "blog").glob("*.md")):
        try:
            kw = str(read_post(p)[0].get("keyword", "")).strip().lower()
        except ValueError:
            continue
        if kw:
            owners.setdefault(kw, []).append(str(p))
    return owners


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("suggest")
    s.add_argument("--type", required=True)
    s.add_argument("--text", required=True, help="niche + what the screenshot shows")
    s.add_argument("-n", type=int, default=10)
    sub.add_parser("taken")
    a = ap.parse_args(argv)
    if a.cmd == "suggest":
        for r in suggest(a.type, a.text, load_bank(), a.n):
            print(f"{r['score']:>5}  {r['keyword']:<45} {r['link']:<45} {r['cluster']}")
    else:
        for kw, files in sorted(taken().items()):
            print(f"{kw:<50} " + ", ".join(f"{Path(f).parent.name}/{Path(f).name}" for f in files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
