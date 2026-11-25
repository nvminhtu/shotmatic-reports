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
