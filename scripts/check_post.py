#!/usr/bin/env python3
"""Lint reports (content/reports in the landing) before they are pushed."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from new_post import APPDEMO, FM_KEYS, IMG_URL, LANDING, img_dir, load_types, read_post, reports_dir

URL_RE = re.compile(r"https?://\S+")
POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9-]+\.md$")
IMAGE_NAME_RE = re.compile(r"^shotmatic\.app-[a-z0-9-]+-\d{4}-\d{2}-\d{2}\.png$")
SHORT_RE = re.compile(r"^## The short answer\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
NUMBERS_RE = re.compile(r"^## The numbers in the screenshot\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
TABLE_SEP_RE = re.compile(r"^\|\s*:?-{3,}", re.M)


def x_length(caption: str) -> int:
    return len(URL_RE.sub("x" * 23, caption))


def short_answer(body: str) -> str | None:
    """First paragraph of the short-answer section (the screenshot line after it is not counted)."""
    m = SHORT_RE.search(body)
    return m.group(1).strip().split("\n\n")[0] if m else None


def check_post(path: Path, landing: Path = LANDING, appdemo: Path = APPDEMO) -> list[str]:
    try:
        fm, body = read_post(path)
    except Exception as e:  # malformed YAML or no frontmatter
        return [f"cannot read frontmatter: {e}"]

    errors = [f"missing or empty frontmatter: {k}" for k in FM_KEYS if not str(fm.get(k, "")).strip()]

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

    if "WRITE:" in body:
        errors.append("unfilled WRITE: placeholder left in the post")

    sa = short_answer(body)
    if sa is None:
        errors.append("missing '## The short answer' section")
    else:
        n = len(sa.split())
        if not 40 <= n <= 80:
            errors.append(f"short answer is {n} words; keep it 40–80 (target 40–60)")

    nm = NUMBERS_RE.search(body)
    if nm is None:
        errors.append("missing '## The numbers in the screenshot' section")
    elif not TABLE_SEP_RE.search(nm.group(1)):
        errors.append("'## The numbers in the screenshot' needs a Markdown table")

    if "## How this was measured" not in body:
        errors.append("missing '## How this was measured' section")

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
