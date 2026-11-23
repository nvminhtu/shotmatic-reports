"""SEO / ASO rules of a report (called by check_post.py)."""
from __future__ import annotations

import re
from pathlib import Path

from seo_keywords import covers, load_bank, taken

ASO_RE = re.compile(r"^## ASO keywords for this niche\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
DEEPER_RE = re.compile(r"^## Go deeper on shotmatic\.app\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
SHORT_RE = re.compile(r"^## The short answer\s*\n(.*?)(?=^## |\Z)", re.M | re.S)


def _list(v) -> list[str]:
    return [str(x).strip() for x in v] if isinstance(v, list) else []


def seo_errors(path: Path, fm: dict, body: str, landing: Path, bank: list[dict] | None = None) -> list[str]:
    errors: list[str] = []
    bank = load_bank() if bank is None else bank
    links = {r["keyword"]: r["link"] for r in bank}
    seo = str(fm.get("seo_keyword", "")).strip().lower()
    if not seo:
        return ["missing seo_keyword (the search phrase this report should rank for)"]

    title, desc = str(fm.get("title", "")), str(fm.get("description", ""))
    if len(title) > 65:
        errors.append(f"title is {len(title)} chars; keep ≤ 65 for Google")
    if not covers(title, seo):
        errors.append(f"title must contain the seo_keyword words: {seo!r}")
    if not 110 <= len(desc) <= 160:
        errors.append(f"description is {len(desc)} chars; keep 110–160")
    if not covers(desc, seo):
        errors.append(f"description must contain the seo_keyword words: {seo!r}")
    if not covers(path.name.replace("-", " "), seo):
        errors.append(f"slug must contain the seo_keyword words: {seo!r}")
    sa = SHORT_RE.search(body)
    if sa and not covers(sa.group(1).split("\n\n")[0], seo):
        errors.append(f"short answer must contain the seo_keyword words: {seo!r}")

    others = [f for f in taken(landing).get(seo, []) if Path(f).resolve() != path.resolve()]
    if others:
        errors.append(f"seo_keyword {seo!r} is already owned by {Path(others[0]).name}; pick another phrase")

    targets = _list(fm.get("target_keywords"))
    if not 1 <= len(targets) <= 3:
        errors.append("target_keywords: pick 1–3 from keywords/bank.csv (scripts/seo_keywords.py suggest)")
    deeper = DEEPER_RE.search(body)
    if deeper is None:
        errors.append("missing '## Go deeper on shotmatic.app' section")
    for t in targets:
        k = t.lower()
        if k not in links:
            errors.append(f"target keyword {t!r} is not in keywords/bank.csv")
        elif deeper and f"]({links[k]})" not in deeper.group(1):
            errors.append(f"'Go deeper' needs a link to {links[k]} for target keyword {t!r}")
        if k not in body.lower():
            errors.append(f"target keyword {t!r} must appear in the text")

    aso = _list(fm.get("aso_keywords"))
    if not 3 <= len(aso) <= 12:
        errors.append(f"aso_keywords: list 3–12 store keywords for this niche (now {len(aso)})")
    sec = ASO_RE.search(body)
    if sec is None:
        errors.append("missing '## ASO keywords for this niche' section")
    else:
        missing = [k for k in aso if k.lower() not in sec.group(1).lower()]
        if missing:
            errors.append(f"ASO section must list every aso_keyword; missing: {', '.join(missing)}")
    return errors
