# scripts/card_data.py
"""Load and check a Top N apps card file (inbox/<slug>.card.json) written by Claude from the niche-radar MCP."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

COLUMN_LABELS = {"installs": "Installs", "rating": "Rating", "revenue": "Est. revenue",
                 # Money apps (TrustMRR, verified from the payment provider — never estimates)
                 "verified": "Last 30 days", "earned": "Total earned", "age": "App age", "growth": "30-day change"}
VERIFIED_COLS = ("verified", "earned")
MONEY = re.compile(r"^\$[\d.,]+[KM]?$")  # "$14.7K", "$277K", "$1.2M"
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
    verified_note: bool = False


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
        for c in VERIFIED_COLS:
            v = values.get(c)
            if v and not MONEY.match(v):
                raise CardError(f"{c} must be one verified amount like $14.7K, got {v!r} for {a['name']}")
        apps.append(CardApp(a["name"].strip(), (a.get("focus") or "").strip(), a.get("icon"), values))
    if "revenue" in columns and sum(1 for a in apps if a.values["revenue"]) < MIN_REVENUE:
        columns.remove("revenue")
        for a in apps:
            a.values.pop("revenue", None)
    return Card(data.get("title", "").strip(), data.get("subtitle", "").strip(), source, columns, apps,
                revenue_note="revenue" in columns, verified_note=any(c in columns for c in VERIFIED_COLS))
