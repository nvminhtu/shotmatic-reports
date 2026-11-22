#!/usr/bin/env python3
"""Lint report posts before they are pushed."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from new_post import FM_KEYS, load_types, read_post

ROOT = Path(__file__).resolve().parent.parent
URL_RE = re.compile(r"https?://\S+")
POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9-]+\.md$")
IMAGE_RE = re.compile(r"^img/shotmatic\.app-[a-z0-9-]+-\d{4}-\d{2}-\d{2}\.png$")
SHORT_RE = re.compile(r"^## The short answer\s*\n(.*?)(?=^## |\Z)", re.M | re.S)


def x_length(caption: str) -> int:
    return len(URL_RE.sub("x" * 23, caption))


def short_answer(body: str) -> str | None:
    m = SHORT_RE.search(body)
    return m.group(1) if m else None


def check_post(path: Path, root: Path = ROOT) -> list[str]:
    try:
        fm, body = read_post(path)
    except Exception as e:  # malformed YAML or no frontmatter
        return [f"cannot read frontmatter: {e}"]

    errors = [f"missing or empty frontmatter: {k}" for k in FM_KEYS if not str(fm.get(k, "")).strip()]

    type_ = fm.get("type")
    if type_ not in load_types(root):
        errors.append(f"type {type_!r} is not in scripts/types.json")
    elif path.parent.resolve() != (root / "docs" / type_).resolve():
        errors.append(f"post must live in folder docs/{type_}/")

    m = POST_NAME_RE.match(path.name)
    if not m:
        errors.append("file name must be YYYY-MM-DD-<slug>.md")
    elif m.group(1) != fm.get("date"):
        errors.append(f"file name date {m.group(1)} != frontmatter date {fm.get('date')}")

    image = str(fm.get("image", ""))
    if image:
        if not IMAGE_RE.match(image):
            errors.append("image name must be img/shotmatic.app-<slug>-<YYYY-MM-DD>.png")
        if not (path.parent / image).exists():
            errors.append(f"image not found: {image}")

    if "WRITE:" in body:
        errors.append("unfilled WRITE: placeholder left in the post")

    sa = short_answer(body)
    if sa is None:
        errors.append("missing '## The short answer' section")
    else:
        n = len(sa.split())
        if not 40 <= n <= 80:
            errors.append(f"short answer is {n} words; keep it 40–80 (target 40–60)")

    if "## How this was measured" not in body:
        errors.append("missing '## How this was measured' section")

    caption = str(fm.get("x_caption", ""))
    if caption and x_length(caption) > 280:
        errors.append(f"x_caption is {x_length(caption)} chars; X allows 280")
    return errors


def all_posts(root: Path = ROOT) -> list[Path]:
    posts = []
    for type_ in load_types(root):
        posts += [p for p in sorted((root / "docs" / type_).glob("*.md")) if p.name != "index.md"]
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
