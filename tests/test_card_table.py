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
