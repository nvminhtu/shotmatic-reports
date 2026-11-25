#!/usr/bin/env python3
"""Money apps card from niche-radar get_money_apps output:
money_card.py <get_money_apps.json> <out.card.json> --title "…" --subtitle "…" [--top 10]

Every amount is TrustMRR verified revenue (never an estimate). Anonymous startups are dropped (readers can't look them up).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def money(v: float | None) -> str | None:
    if v is None or v <= 0:
        return None
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M".replace(".0M", "M")
    if v >= 1_000:
        return f"${v / 1_000:.1f}K".replace(".0K", "K") if v < 100_000 else f"${round(v / 1_000)}K"
    return f"${round(v)}"


def age(months: int | None) -> str | None:
    if months is None:
        return None
    return f"{months} mo" if months < 24 else f"{months // 12} yr"


def growth(p: float | None) -> str | None:
    return None if p is None else f"{'+' if p > 0 else ''}{p:.0f}%"


def build(result: dict, title: str, subtitle: str, top: int = 10) -> dict:
    apps = [a for a in result.get("apps", []) if not a.get("anonymous")][:top]
    synced = sorted({a["verified"]["syncedAt"] for a in apps if a["verified"].get("syncedAt")})
    when = synced[-1] if synced else result.get("checkedAt")
    return {
        "title": title, "subtitle": subtitle,
        "source": f"TrustMRR verified revenue, read by ShotMatic {result.get('checkedAt')} (synced up to {when})",
        "columns": ["verified", "earned", "age"],
        "apps": [{
            "name": a["name"], "focus": (a.get("description") or "")[:60], "icon": a.get("icon"),
            "verified": money(a["verified"].get("last30")), "earned": money(a["verified"].get("allTime")),
            "age": age(a.get("ageMonths")), "growth": growth(a["verified"].get("growth30")),
            "url": a.get("url"),
        } for a in apps],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("result", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", required=True)
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args(argv)
    card = build(json.loads(a.result.read_text()), a.title, a.subtitle, a.top)
    a.out.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
