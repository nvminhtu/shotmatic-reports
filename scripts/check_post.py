#!/usr/bin/env python3
"""Lint reports (content/reports in the landing) before they are pushed."""
from __future__ import annotations

import re

import yaml
import sys
from pathlib import Path

from new_post import APPDEMO, FM_KEYS, STORES, IMG_URL, LANDING, img_dir, load_types, read_post, reports_dir
from seo_check import seo_errors

URL_RE = re.compile(r"https?://\S+")
POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9-]+\.md$")
IMAGE_NAME_RE = re.compile(r"^shotmatic\.app-[a-z0-9-]+-\d{4}-\d{2}-\d{2}\.png$")
SHORT_RE = re.compile(r"^## The short answer\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
NUMBERS_RE = re.compile(r"^## The numbers in the screenshot\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
TABLE_SEP_RE = re.compile(r"^\|\s*:?-{3,}", re.M)
DEMAND_RE = re.compile(r"^## Is anyone searching for this\?\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$", re.M)
# Rules added 2026-11-24 (demand section, no junk store keywords, real image alt). Older posts are not re-checked.
STRICT_FROM = "2026-11-24"
IMG_ALT_RE = re.compile(r"!\[([^\]]*)\]\(https?://[^)]*\.png\)")
# ShotMatic's internal run ids ("[ASO #45 · 2026-11-21]", "Audit #45", "trending #48") mean nothing to readers:
# write the feature + store + country + date instead. Ranks such as "#5" or "| #11 |" are fine.
INTERNAL_ID_RE = re.compile(r"\[[^\]\n]*#\d+[^\]\n]*\]|\b(?:ASO|Audit|Research|research|Trending|trending|Explore|explore|Hunt|hunt|Review|review|Compare|compare)\s+#\d+")


def x_length(caption: str) -> int:
    return len(URL_RE.sub("x" * 23, caption))


def short_answer(body: str) -> str | None:
    """First paragraph of the short-answer section (the screenshot line after it is not counted)."""
    m = SHORT_RE.search(body)
    return m.group(1).strip().split("\n\n")[0] if m else None


def junk_keywords(body: str) -> list[str]:
    """Store-matched noise in table first cells, e.g. 'r money', 'm money x': a 1-letter word that is not 'a'."""
    bad = []
    for m in TABLE_ROW_RE.finditer(body):
        cell = m.group(1).split("|")[0].strip().strip("`*\"'")
        if not cell or set(cell) <= set("-: "):
            continue
        words = cell.lower().split()
        if any(len(w) == 1 and w.isalpha() and w not in ("a", "i") for w in words):
            bad.append(cell)
    return sorted(set(bad))



CHART_RE = re.compile(r"^```chart\n(.*?)^```$", re.S | re.M)
CHART_TYPES = ("stats", "bars", "change", "line")


def chart_errors(body: str) -> list[str]:
    """```chart blocks (rendered by the landing's lib/report-charts.mjs): YAML must parse and have the fields of its type."""
    errors = []
    for n, m in enumerate(CHART_RE.finditer(body), 1):
        try:
            spec = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            errors.append(f"chart {n}: YAML does not parse ({str(e).splitlines()[0]})")
            continue
        t = spec.get("type")
        if t not in CHART_TYPES:
            errors.append(f"chart {n}: type must be one of {', '.join(CHART_TYPES)} (got {t!r})")
        elif t == "line":
            x, series = spec.get("x"), spec.get("series")
            if not isinstance(x, list) or not isinstance(series, list) or not series:
                errors.append(f"chart {n}: line needs x: [...] and series: [{{name, values}}]")
            else:
                errors += [f"chart {n}: series {s.get('name')!r} needs {len(x)} values" for s in series
                           if not isinstance(s.get("values"), list) or len(s["values"]) != len(x)]
        else:
            items = spec.get("items")
            need = {"stats": ("value", "label"), "bars": ("label", "value"), "change": ("label", "from", "to")}[t]
            if not isinstance(items, list) or not items:
                errors.append(f"chart {n}: {t} needs items: [...]")
            else:
                errors += [f"chart {n}: item {k} needs {', '.join(need)}" for k, i in enumerate(items, 1)
                           if not isinstance(i, dict) or any(f not in i for f in need)]
        if not spec.get("source"):
            errors.append(f"chart {n}: add source: (where the numbers come from)")
    return errors

def check_post(path: Path, landing: Path = LANDING, appdemo: Path = APPDEMO, bank: list[dict] | None = None) -> list[str]:
    try:
        fm, body = read_post(path)
    except Exception as e:  # malformed YAML or no frontmatter
        return [f"cannot read frontmatter: {e}"]

    errors = [f"missing or empty frontmatter: {k}" for k in FM_KEYS
              if k not in ("target_keywords", "aso_keywords", "highlight") and not str(fm.get(k, "")).strip()]

    type_ = fm.get("type")
    if type_ not in load_types(landing):
        errors.append(f"type {type_!r} is not in content/reports/types.json")
    elif path.parent.resolve() != (reports_dir(landing) / type_).resolve():
        errors.append(f"post must live in folder content/reports/{type_}/")

    m = POST_NAME_RE.match(path.name)
    if not m:
        errors.append("file name must be YYYY-MM-DD-<slug>.md")
    elif m.group(1) != fm.get("date"):
        errors.append(f"file name date {m.group(1)} != frontmatter date {fm.get('date')}")

    image = str(fm.get("image", ""))
    if image:
        prefix = f"{IMG_URL}/{type_}/"
        name = image[len(prefix):] if image.startswith(prefix) else ""
        if not IMAGE_NAME_RE.match(name):
            errors.append(f"image name must be {prefix}shotmatic.app-<slug>-<YYYY-MM-DD>.png")
        elif not (img_dir(appdemo, type_) / name).exists():
            errors.append(f"image not found in app-demo: shotmatic/reports/{type_}/{name}")

    if fm.get("store") and fm.get("store") not in STORES:
        errors.append(f"store must be one of {', '.join(STORES)}")
    if fm.get("country") and not re.fullmatch(r"[A-Z]{2}", str(fm.get("country"))):
        errors.append("country must be a 2-letter code like US")
    ids = sorted({m.group(0) for m in INTERNAL_ID_RE.finditer(f"{fm.get('source', '')}\n{body}")})
    if ids:
        errors.append(f"internal ShotMatic ids mean nothing to readers, write feature + store + country + date instead: {', '.join(ids)}")

    updated = fm.get("updated")
    if updated not in (None, ""):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(updated)):
            errors.append("updated must be YYYY-MM-DD")
        elif str(updated) < str(fm.get("date", "")):
            errors.append("updated must be on or after date")

    if "WRITE:" in body:
        errors.append("unfilled WRITE: placeholder left in the post")
    errors += chart_errors(body)
    # the first ```chart must be type: stats (headline numbers): the page turns it into Key facts for AI tools
    first = CHART_RE.search(body)
    if not first or (yaml.safe_load(first.group(1)) or {}).get("type") != "stats":
        errors.append("add a ```chart type: stats block (2–4 headline numbers) right after the main screenshot; it becomes the Key facts")

    # Opportunity highlight (shown on /reports): stat = one short number from the data, text = what it means for a founder
    hl = fm.get("highlight") if isinstance(fm.get("highlight"), dict) else {}
    stat, hl_text = str(hl.get("stat") or "").strip(), str(hl.get("text") or "").strip()
    if not stat or not hl_text:
        errors.append("highlight: set stat (one number from the data, e.g. '+3,200%', '#7', '2 of 11') and text (one sentence)")
    else:
        if len(stat) > 12 or not re.search(r"\d", stat):
            errors.append(f"highlight.stat must be a short number from the data (≤ 12 chars, with a digit), got {stat!r}")
        if not 60 <= len(hl_text) <= 220:
            errors.append(f"highlight.text is {len(hl_text)} chars; keep 60–220")

    sa = short_answer(body)
    if sa is None:
        errors.append("missing '## The short answer' section")
    else:
        # readability + GEO: the 1–4 numbers that answer the question are **bold**, so a skimmer and an AI see them first
        bold = re.findall(r"\*\*(.+?)\*\*", sa)
        if not bold:
            errors.append("short answer: make the 1–4 key numbers or phrases **bold**")
        elif len(bold) > 5:
            errors.append(f"short answer has {len(bold)} bold parts; keep 1–5 so they still stand out")
        n = len(sa.split())
        if not 40 <= n <= 80:
            errors.append(f"short answer is {n} words; keep it 40–80 (target 40–60)")

    nm = NUMBERS_RE.search(body)
    if nm is None:
        errors.append("missing '## The numbers in the screenshot' section")
    elif not TABLE_SEP_RE.search(nm.group(1)):
        errors.append("'## The numbers in the screenshot' needs a Markdown table")

    if str(fm.get("date", "")) >= STRICT_FROM:
        dm = DEMAND_RE.search(body)
        if dm is None or not dm.group(1).strip():
            errors.append("missing '## Is anyone searching for this?' section (autocomplete / Trends / demand score, or 'not measured')")
        alts = IMG_ALT_RE.findall(body)
        if not alts or any(len(a) < 40 or a.endswith("ShotMatic report") for a in alts):
            errors.append("screenshot alt text must say what the image shows in words (40–125 chars, not '<keyword> — ShotMatic report')")
        junk = junk_keywords(body)
        if junk:
            errors.append(f"junk store keywords (1-letter fragments) — drop them and say so in 'How this was measured': {', '.join(junk)}")

    if "## How this was measured" not in body:
        errors.append("missing '## How this was measured' section")

    errors += seo_errors(path, fm, body, landing, bank)

    caption = str(fm.get("x_caption", ""))
    if caption and x_length(caption) > 280:
        errors.append(f"x_caption is {x_length(caption)} chars; X allows 280")
    return errors


def all_posts(landing: Path = LANDING) -> list[Path]:
    posts = []
    for type_ in load_types(landing):
        posts += sorted((reports_dir(landing) / type_).glob("*.md"))
    return posts


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    posts = [Path(a) for a in args] or all_posts()
    if not posts:
        print("no posts")
        return 0
    failed = False
    for p in posts:
        errors = check_post(p)
        if errors:
            failed = True
            print(f"FAIL {p}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK {p}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
