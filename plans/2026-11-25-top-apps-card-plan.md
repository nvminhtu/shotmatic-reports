# Top N Apps Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Top N apps card" mode to `/shotmatic-report`: Claude pulls the top apps of one niche from the niche-radar MCP, writes them to a JSON file, a script draws a share-ready ranking card PNG (title, icons, focus, installs, rating, revenue range), and the existing pipeline stamps it, writes the post and prints the X caption.

**Architecture:** The MCP is a Claude tool, so scripts never call it. Claude writes `inbox/<slug>.card.json`. `card_data.py` loads and checks that file. `card_render.py` draws the card with Pillow (already a dependency, no browser needed). `card_table.py` turns the same JSON into the Markdown table for `## The numbers in the screenshot`. `new_post.py create --card` uses the rendered PNG as the image (the badge is stamped as usual) and fills the table. A new report type `top-apps` makes the cards their own chip on /reports.

**Tech Stack:** Python 3 + Pillow + pytest (in `$TOOL/.venv`), niche-radar MCP, Next.js landing (only `types.json` changes).

## Global Constraints

- Every number on the card comes from the niche-radar MCP. Missing → `null` in JSON → `—` on the card and `not measured` in the table. Never invent installs, ratings or revenue.
- Revenue is only ever a **range** from ShotMatic (`list_history kind=inspect` → `money.estimateRange`) or real TrustMRR (`money.trustLast30`, marked "verified"). The card footer always says: `Revenue = ShotMatic estimate range, not real numbers` when any range is shown.
- One `source` line per card (feature + store + country + measured date), printed in the card footer. No internal ids (`Research #12`, `inspect #19`) on the card or in the post.
- English only on the card and the post.
- Card is 1 column of rows (one app per row); only short numbers sit side by side.
- Card colors: white background, ShotMatic orange `#F97316` accent, navy `#1F2A44` text (same navy as the badge).
- Card width 1600 px; height grows with the number of rows; 3–25 apps.
- Tests run with `cd $TOOL && .venv/bin/python -m pytest -q`. They never touch the network: icons in tests are local files.
- Landing commits authored `Nguyen Vu Minh Tu <3124729+nvminhtu@users.noreply.github.com>`; tool commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

`$TOOL` = `/Users/tucarmd/DATA/PROJECTS/OTHERS/CLAUDE_SKILL/Niche-Research/shotmatic-reports`
`$LANDING` = `/Users/tucarmd/DATA/PROJECTS/OTHERS/CLAUDE_SKILL/Master-List-Dashboard/shotmatic-reports-section`

## Where the data comes from (checked 2026-11-25)

| Card column | MCP call | Field |
|---|---|---|
| name, icon, store link, installs, rating | `get_research(runId, limit=25)` | `competitors[]` |
| focus (short "what it does") | `get_research` competitor subtitle/genre; else Claude writes ≤ 6 words from the store page title | — |
| revenue | `list_history(kind="inspect")` rows whose title matches the app | `money.estimateRange` / `money.trustLast30` |
| runId | `search_niches(query="<niche>")` | `id` |

Today most competitors have **no** inspect row, so revenue is mostly `—`. Step 4 of the new SKILL mode tells Claude to inspect the top 5 apps in ShotMatic first (Soi app) when Tu wants a revenue card. If fewer than 3 apps have revenue, the card drops the revenue column instead of showing a column of dashes.

## File Structure

| File | Job |
|---|---|
| `scripts/card_data.py` (create) | Load + check `*.card.json`; the `Card` / `CardApp` types |
| `scripts/card_render.py` (create) | Draw the PNG with Pillow; fetch + cache icons |
| `scripts/card_table.py` (create) | Markdown table from a `Card` |
| `scripts/new_post.py` (modify) | `--card` flag: render → image, table → body |
| `scripts/types.json` + `$LANDING/content/reports/types.json` (modify) | add `top-apps` |
| `tests/test_card_data.py`, `tests/test_card_render.py`, `tests/test_card_table.py` (create) | tests |
| `tests/test_new_post.py` (modify) | `--card` test |
| `~/.claude/skills/shotmatic-report/SKILL.md` (modify) | the new mode |

### JSON file format (`inbox/<slug>.card.json`)

```json
{
  "title": "12 period tracker apps",
  "subtitle": "Top apps for \"period tracker\" · US App Store",
  "source": "ShotMatic Research, US App Store, measured 2026-11-25",
  "columns": ["installs", "rating", "revenue"],
  "apps": [
    {"name": "Flo", "focus": "Periods, fertility & pregnancy", "icon": "https://is1-ssl.mzstatic.com/.../100x100bb.jpg",
     "installs": "100M+", "rating": "4.8", "revenue": "$1M–3M/mo"},
    {"name": "Clue", "focus": "Period & symptom tracking", "icon": null,
     "installs": "10M+", "rating": "4.7", "revenue": null}
  ]
}
```

---

### Task 1: Card data (load + check)

**Files:**
- Create: `scripts/card_data.py`
- Test: `tests/test_card_data.py`

**Interfaces:**
- Produces: `CardApp(name: str, focus: str, icon: str | None, values: dict[str, str | None])`, `Card(title, subtitle, source, columns: list[str], apps: list[CardApp], revenue_note: bool)`, `load_card(path: Path) -> Card`, `CardError(Exception)`, `COLUMN_LABELS: dict[str, str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_card_data.py
import json
from pathlib import Path

import pytest

from card_data import CardError, load_card


def write(tmp_path: Path, **over) -> Path:
    data = {
        "title": "3 period tracker apps",
        "subtitle": "Top apps for \"period tracker\" · US App Store",
        "source": "ShotMatic Research, US App Store, measured 2026-11-25",
        "columns": ["installs", "rating", "revenue"],
        "apps": [
            {"name": "Flo", "focus": "Periods", "icon": None, "installs": "100M+", "rating": "4.8", "revenue": "$1M–3M/mo"},
            {"name": "Clue", "focus": "Symptoms", "icon": None, "installs": "10M+", "rating": "4.7", "revenue": "$300K–1M/mo"},
            {"name": "Stardust", "focus": "Hormones", "icon": None, "installs": "1M+", "rating": None, "revenue": "$100K–300K/mo"},
        ],
    }
    data.update(over)
    p = tmp_path / "x.card.json"
    p.write_text(json.dumps(data))
    return p


def test_loads_apps_and_keeps_missing_as_none(tmp_path):
    card = load_card(write(tmp_path))
    assert [a.name for a in card.apps] == ["Flo", "Clue", "Stardust"]
    assert card.apps[2].values["rating"] is None
    assert card.revenue_note is True


def test_drops_revenue_column_when_fewer_than_3_apps_have_it(tmp_path):
    apps = [{"name": n, "focus": "f", "icon": None, "installs": "1M+", "rating": "4.5", "revenue": None} for n in "ABC"]
    apps[0]["revenue"] = "$10K–30K/mo"
    card = load_card(write(tmp_path, apps=apps))
    assert card.columns == ["installs", "rating"]
    assert card.revenue_note is False


@pytest.mark.parametrize("bad", [
    {"apps": []},                                   # fewer than 3
    {"source": ""},                                 # source required
    {"source": "Research #12, US, 2026-11-25"},     # internal id
    {"columns": ["installs", "downloads"]},         # unknown column
])
def test_rejects_bad_cards(tmp_path, bad):
    with pytest.raises(CardError):
        load_card(write(tmp_path, **bad))


def test_rejects_revenue_that_is_not_a_range(tmp_path):
    apps = [{"name": n, "focus": "f", "icon": None, "installs": "1M+", "rating": "4.5", "revenue": "$7.8M"} for n in "ABC"]
    with pytest.raises(CardError, match="range"):
        load_card(write(tmp_path, apps=apps))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $TOOL && .venv/bin/python -m pytest tests/test_card_data.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'card_data'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/card_data.py
"""Load and check a Top N apps card file (inbox/<slug>.card.json) written by Claude from the niche-radar MCP."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

COLUMN_LABELS = {"installs": "Installs", "rating": "Rating", "revenue": "Est. revenue"}
INTERNAL_ID = re.compile(r"\b(research|inspect|hunt|audit|aso|trending)\s*#\d+", re.I)
RANGE = re.compile(r"[–-]|verified", re.I)  # "$1M–3M/mo" or "$12K/mo verified"
MIN_APPS, MAX_APPS, MIN_REVENUE = 3, 25, 3


class CardError(Exception):
    pass


@dataclass
class CardApp:
    name: str
    focus: str
    icon: str | None
    values: dict[str, str | None]


@dataclass
class Card:
    title: str
    subtitle: str
    source: str
    columns: list[str]
    apps: list[CardApp]
    revenue_note: bool


def load_card(path: Path) -> Card:
    data = json.loads(Path(path).read_text())
    source = (data.get("source") or "").strip()
    if not source:
        raise CardError("source is required: feature + store + country + measured date")
    if INTERNAL_ID.search(source):
        raise CardError(f"no internal ids in source: {source!r}")
    columns = list(data.get("columns") or ["installs", "rating"])
    unknown = [c for c in columns if c not in COLUMN_LABELS]
    if unknown:
        raise CardError(f"unknown columns {unknown}; allowed: {list(COLUMN_LABELS)}")
    raw = data.get("apps") or []
    if not MIN_APPS <= len(raw) <= MAX_APPS:
        raise CardError(f"need {MIN_APPS}–{MAX_APPS} apps, got {len(raw)}")
    apps = []
    for a in raw:
        if not (a.get("name") or "").strip():
            raise CardError("every app needs a name")
        values = {c: (str(a[c]).strip() if a.get(c) not in (None, "") else None) for c in columns}
        rev = values.get("revenue")
        if rev and not RANGE.search(rev):
            raise CardError(f"revenue must be a range or 'verified', got {rev!r} for {a['name']}")
        apps.append(CardApp(a["name"].strip(), (a.get("focus") or "").strip(), a.get("icon"), values))
    if "revenue" in columns and sum(1 for a in apps if a.values["revenue"]) < MIN_REVENUE:
        columns.remove("revenue")
        for a in apps:
            a.values.pop("revenue", None)
    return Card(data.get("title", "").strip(), data.get("subtitle", "").strip(), source, columns, apps,
                revenue_note="revenue" in columns)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd $TOOL && .venv/bin/python -m pytest tests/test_card_data.py -q`
Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
cd $TOOL && git add scripts/card_data.py tests/test_card_data.py && git commit -m "feat(card): load + check Top N apps card JSON

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Draw the card PNG

**Files:**
- Create: `scripts/card_render.py`
- Test: `tests/test_card_render.py`

**Interfaces:**
- Consumes: `Card`, `CardApp`, `COLUMN_LABELS` from `card_data`; `_font` from `watermark`.
- Produces: `render_card(card: Card, out: Path, icon_dir: Path) -> Path`, `fetch_icon(src: str | None, icon_dir: Path) -> Image.Image | None`, `WIDTH = 1600`, `ROW_H = 96`, CLI `card_render.py <card.json> <out.png>`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_card_render.py
from pathlib import Path

from PIL import Image

from card_data import Card, CardApp
from card_render import HEAD_H, FOOT_H, ROW_H, WIDTH, render_card
from conftest import make_png


def card(n: int, icon: str | None) -> Card:
    apps = [CardApp(f"App {i}", "Period & symptom tracking", icon,
                    {"installs": "1M+", "rating": "4.6" if i else None}) for i in range(n)]
    return Card("5 period tracker apps", "Top apps · US App Store", "ShotMatic Research, US App Store, measured 2026-11-25",
                ["installs", "rating"], apps, revenue_note=False)


def test_size_grows_with_rows(tmp_path):
    out = render_card(card(5, None), tmp_path / "c.png", tmp_path / "icons")
    img = Image.open(out)
    assert img.width == WIDTH
    assert img.height == HEAD_H + 5 * ROW_H + FOOT_H


def test_uses_local_icon_and_white_background(tmp_path):
    icon = make_png(tmp_path / "icon.png", (100, 100), (255, 0, 0))
    out = render_card(card(3, str(icon)), tmp_path / "c.png", tmp_path / "icons")
    img = Image.open(out).convert("RGB")
    assert img.getpixel((5, 5)) == (255, 255, 255)
    reds = sum(1 for x in range(0, 300) for y in range(HEAD_H, HEAD_H + ROW_H) if img.getpixel((x, y)) == (255, 0, 0))
    assert reds > 1000  # the icon is drawn in row 1


def test_missing_icon_does_not_crash(tmp_path):
    out = render_card(card(3, str(tmp_path / "nope.png")), tmp_path / "c.png", tmp_path / "icons")
    assert Path(out).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $TOOL && .venv/bin/python -m pytest tests/test_card_render.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'card_render'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/card_render.py
#!/usr/bin/env python3
"""Draw a Top N apps card PNG from a *.card.json file: card_render.py <card.json> <out.png>"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

from card_data import COLUMN_LABELS, Card, load_card
from watermark import _font

WIDTH, ROW_H, HEAD_H, FOOT_H, PAD = 1600, 96, 230, 90, 64
WHITE, NAVY, MUTED, ORANGE, LINE = (255, 255, 255), (31, 42, 68), (110, 118, 135), (249, 115, 22), (234, 236, 240)
ICON = 64
COL_W = 210  # each number column, right-aligned from the right edge


def fetch_icon(src: str | None, icon_dir: Path) -> Image.Image | None:
    if not src:
        return None
    try:
        if src.startswith("http"):
            icon_dir.mkdir(parents=True, exist_ok=True)
            cached = icon_dir / (hashlib.sha1(src.encode()).hexdigest()[:16] + ".img")
            if not cached.exists():
                req = urllib.request.Request(src, headers={"User-Agent": "shotmatic-report"})
                cached.write_bytes(urllib.request.urlopen(req, timeout=10).read())
            src = str(cached)
        return Image.open(src).convert("RGBA").resize((ICON, ICON), Image.LANCZOS)
    except Exception:
        return None


def _letter_tile(name: str) -> Image.Image:
    tile = Image.new("RGBA", (ICON, ICON), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, ICON - 1, ICON - 1), radius=16, fill=(255, 237, 213))
    f = _font(34)
    d.text((ICON / 2, ICON / 2), name[:1].upper(), font=f, fill=ORANGE, anchor="mm")
    return tile


def _round(icon: Image.Image) -> Image.Image:
    mask = Image.new("L", icon.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ICON - 1, ICON - 1), radius=16, fill=255)
    out = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    out.paste(icon, (0, 0), mask)
    return out


def _fit(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def render_card(card: Card, out: Path, icon_dir: Path) -> Path:
    h = HEAD_H + len(card.apps) * ROW_H + FOOT_H
    img = Image.new("RGB", (WIDTH, h), WHITE)
    d = ImageDraw.Draw(img)
    f_title, f_sub, f_head = _font(64), _font(34), _font(22)
    f_name, f_focus, f_num = _font(32), _font(24), _font(32)

    d.text((PAD, 50), card.title, font=f_title, fill=NAVY)
    d.text((PAD, 132), card.subtitle, font=f_sub, fill=ORANGE)
    col_x = {c: WIDTH - PAD - (len(card.columns) - i - 1) * COL_W for i, c in enumerate(card.columns)}
    for c, x in col_x.items():
        d.text((x, HEAD_H - 24), COLUMN_LABELS[c].upper(), font=f_head, fill=MUTED, anchor="rs")
    d.line((PAD, HEAD_H - 8, WIDTH - PAD, HEAD_H - 8), fill=LINE, width=2)

    text_x = PAD + 48 + ICON + 20
    text_w = min(col_x.values()) - COL_W + 40 - text_x
    for i, app in enumerate(card.apps):
        y = HEAD_H + i * ROW_H
        mid = y + ROW_H // 2
        d.text((PAD, mid), f"{i + 1:02d}", font=f_head, fill=MUTED, anchor="lm")
        icon = fetch_icon(app.icon, icon_dir)
        img.paste(_round(icon) if icon else _letter_tile(app.name), (PAD + 48, mid - ICON // 2),
                  _round(icon) if icon else _letter_tile(app.name))
        d.text((text_x, mid - 4), _fit(d, app.name, f_name, text_w), font=f_name, fill=NAVY, anchor="ls")
        if app.focus:
            d.text((text_x, mid + 6), _fit(d, app.focus, f_focus, text_w), font=f_focus, fill=MUTED, anchor="lt")
        for c, x in col_x.items():
            v = app.values.get(c)
            color = ORANGE if c == "revenue" and v else (NAVY if v else MUTED)
            d.text((x, mid), v or "—", font=f_num, fill=color, anchor="rm")
        d.line((PAD, y + ROW_H - 1, WIDTH - PAD, y + ROW_H - 1), fill=LINE, width=1)

    note = card.source + (" · Revenue = ShotMatic estimate range, not real numbers" if card.revenue_note else "")
    d.text((PAD, h - FOOT_H / 2), _fit(d, note, f_head, WIDTH - 2 * PAD), font=f_head, fill=MUTED, anchor="lm")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent.parent
    print(render_card(load_card(Path(args[0])), Path(args[1]), root / "inbox" / ".icons"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd $TOOL && .venv/bin/python -m pytest tests/test_card_render.py -q`
Expected: `3 passed`

- [ ] **Step 5: Look at it**

Run: `cd $TOOL && .venv/bin/python -c "from tests.test_card_render import card; from card_render import render_card; from pathlib import Path; render_card(card(12, None), Path('inbox/sample-card.png'), Path('inbox/.icons'))"` (with `PYTHONPATH=scripts`), then Read `inbox/sample-card.png`. Check: title big and dark, subtitle orange, numbers right-aligned in columns, long focus text ends with "…", footer source line readable. Fix sizes in the constants if something overlaps.

- [ ] **Step 6: Commit**

```bash
cd $TOOL && git add scripts/card_render.py tests/test_card_render.py && git commit -m "feat(card): draw Top N apps card PNG with Pillow

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Markdown table from the card + `new_post.py --card`

**Files:**
- Create: `scripts/card_table.py`
- Modify: `scripts/new_post.py` (`create_post` signature + `main` args)
- Test: `tests/test_card_table.py`, `tests/test_new_post.py`

**Interfaces:**
- Consumes: `load_card`, `COLUMN_LABELS` (Task 1), `render_card` (Task 2).
- Produces: `card_table(card: Card) -> str`; `create_post(..., card: Path | None = None)` — when `card` is set, `image_src` may be `None`; the rendered PNG is the image and the table replaces the first `WRITE:` table placeholder under `## The numbers in the screenshot`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_card_table.py
from card_data import Card, CardApp
from card_table import card_table


def test_table_has_every_number_and_not_measured():
    c = Card("t", "s", "src", ["installs", "revenue"], [
        CardApp("Flo", "Periods", None, {"installs": "100M+", "revenue": "$1M–3M/mo"}),
        CardApp("Clue", "Symptoms", None, {"installs": None, "revenue": "$300K–1M/mo"}),
    ], revenue_note=True)
    t = card_table(c)
    assert t.splitlines()[0] == "| # | App | Focus | Installs | Est. revenue |"
    assert "| 1 | Flo | Periods | 100M+ | $1M–3M/mo |" in t
    assert "| 2 | Clue | Symptoms | not measured | $300K–1M/mo |" in t
```

Add to `tests/test_new_post.py`:

```python
def test_create_from_card(site, tmp_path):
    import json
    from new_post import create_post, read_post
    landing, appdemo = site
    cj = tmp_path / "x.card.json"
    cj.write_text(json.dumps({
        "title": "3 period tracker apps", "subtitle": "US App Store",
        "source": "ShotMatic Research, US App Store, measured 2026-11-25", "columns": ["installs"],
        "apps": [{"name": n, "focus": "f", "icon": None, "installs": "1M+"} for n in ("Flo", "Clue", "Stardust")]}))
    r = create_post("top-apps", "2026-11-25", "period-tracker-top-apps-2026", "Top period tracker apps in 2026",
                    "period tracker", "ShotMatic Research, US App Store, measured 2026-11-25", None,
                    landing=landing, appdemo=appdemo, links={}, store="app-store", country="US", card=cj)
    _, body = read_post(Path(r["post"]))
    assert "| 1 | Flo | f | 1M+ |" in body
    assert Path(r["image"]).exists()
```

(`site` fixture copies `scripts/types.json`, so Task 4's `top-apps` entry must exist first — do Step 1 of Task 4 now: add `"top-apps": "Top Apps"` to `scripts/types.json`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd $TOOL && .venv/bin/python -m pytest tests/test_card_table.py tests/test_new_post.py -q`
Expected: FAIL (`No module named 'card_table'`, `unexpected keyword argument 'card'`)

- [ ] **Step 3: Write `card_table.py`**

```python
# scripts/card_table.py
"""Markdown table for '## The numbers in the screenshot' from a Top N apps card."""
from __future__ import annotations

from card_data import COLUMN_LABELS, Card


def card_table(card: Card) -> str:
    head = ["#", "App", "Focus"] + [COLUMN_LABELS[c] for c in card.columns]
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for i, a in enumerate(card.apps, 1):
        cells = [str(i), a.name, a.focus or "not measured"] + [a.values.get(c) or "not measured" for c in card.columns]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)
```

- [ ] **Step 4: Change `create_post` in `scripts/new_post.py`**

Add parameter `card: Path | None = None` at the end of the signature. Right after the date check, before `folder = ...`:

```python
    table = ""
    if card is not None:
        from card_data import load_card
        from card_render import render_card
        from card_table import card_table
        c = load_card(Path(card))
        image_src = render_card(c, Path(card).with_suffix(".png"), Path(card).parent / ".icons")
        table = card_table(c)
    if image_src is None:
        raise ValueError("--image or --card is required")
```

After `write_post(post, fm, BODY.format(...))`, when `table` is set, put it under the numbers heading:

```python
    if table:
        fm2, body = read_post(post)
        head = "## The numbers in the screenshot"
        body = body.replace(head, f"{head}\n\n{table}\n", 1)
        write_post(post, fm2, body)
```

In `main`: make `--image` `required=False, default=None`, add `c.add_argument("--card", type=Path, default=None, help="inbox/<slug>.card.json: draws the card and fills the numbers table")`, and pass `card=args.card` to `create_post`. Error if neither is given (handled by the `ValueError` above).

- [ ] **Step 5: Run all tests**

Run: `cd $TOOL && .venv/bin/python -m pytest -q`
Expected: all pass (old tests unchanged).

- [ ] **Step 6: Commit**

```bash
cd $TOOL && git add scripts/card_table.py scripts/new_post.py scripts/types.json tests/test_card_table.py tests/test_new_post.py && git commit -m "feat(card): new_post --card renders the card and fills the numbers table; type top-apps

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `top-apps` type on the landing

**Files:**
- Modify: `$LANDING/content/reports/types.json`

- [ ] **Step 1:** (tool side done in Task 3) Sync and edit the landing: `cd $LANDING && git fetch -q origin && git rebase -q origin/main`, then add `"top-apps": "Top Apps"` to `content/reports/types.json`.
- [ ] **Step 2:** `cd $LANDING && npm run build` → build passes, /reports chips list "Top Apps" (shows once a post exists).
- [ ] **Step 3:** Commit only (push happens with the first real report in Task 6):

```bash
cd $LANDING && git add content/reports/types.json && git commit -m "feat(reports): type top-apps for Top N apps cards"
```

---

### Task 5: The new mode in the skill

**Files:**
- Modify: `~/.claude/skills/shotmatic-report/SKILL.md` (add after `## Steps`)

- [ ] **Step 1: Add this section**

```markdown
## Mode: Top N apps card (no screenshot)

Use when Tu says "card top app", "list app kiểu 20 apps for women", "làm card top N app cho niche X".

1. Niche + store + country from Tu (ask in one line if missing). `type` = `top-apps`.
2. `search_niches(query="<niche>")` → newest run id. None → ask Tu to run Research on that niche in ShotMatic first (or `start_research` if "Let AI add data" is on), then wait.
3. `get_research(runId, limit=25)` → competitors: name, icon, installs, rating, store link. Drop apps that are not in the niche (Quality rule 2 for apps).
4. Revenue: `list_history(kind="inspect", limit=100)` → match by title. Use `money.estimateRange` as "$A–B/mo" or `money.trustLast30` as "$X/mo verified". Fewer than 3 matches → tell Tu "only N apps have revenue; inspect the top 5 in Soi app for a revenue card?" and go on without the column if Tu says no.
5. Focus: ≤ 6 words per app from its store subtitle; never a claim about the app that the store page doesn't make.
6. Write `$TOOL/inbox/<slug>.card.json` (format in `plans/2026-11-25-top-apps-card-plan.md`). Title = "<N> <niche> apps" or "<N> apps built for <audience>"; subtitle = what the list is + store + country.
7. `.venv/bin/python scripts/card_render.py inbox/<slug>.card.json inbox/<slug>.card.png` → Read the PNG, check it before going on.
8. Steps 4b–10 as usual, with `new_post.py create --type top-apps --card inbox/<slug>.card.json` instead of `--image`. The numbers table is filled; still write short answer, demand, top-spots, what it means. The post is about the niche ("is the period tracker market worth entering?"), the card is the hook.
9. X caption: hook in the card's style ("<N> <niche> apps, the top one makes <range>/mo 👇") + link.
```

- [ ] **Step 2:** Also add `"card top app"`, `"list app kiểu 20 apps"` to the skill `description` trigger phrases.

---

### Task 6: One real card end to end (needs Tu's go-ahead to publish)

- [ ] **Step 1:** Ask Tu for the first niche (suggestion: one already researched in ShotMatic, checked with `search_niches`). Run the mode, stop after step 7 and show Tu the PNG.
- [ ] **Step 2:** On Tu's OK, run steps 8–10 (check_post → build → look at 1340 and mobile → push app-demo, then landing incl. Task 4 commit) and hand back link + image path + caption.

---

## Not in this plan (later, if cards do well)

- Totals line on the card ("$4M+/mo across 12 apps") — needs enough revenue ranges to be honest.
- Cards from Trending (new/climbing apps) or Săn app results instead of one Research run.
- Auto-inspecting the top 5 for revenue through the MCP.
