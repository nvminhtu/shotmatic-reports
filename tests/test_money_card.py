import json

import pytest

from card_data import CardError, load_card
from money_card import age, build, growth, money


def result(**over):
    a = {"name": "Verbi", "anonymous": False, "description": "Speak a language faster", "url": "https://trustmrr.com/startup/verbi",
         "ageMonths": 7, "verified": {"last30": 14699, "allTime": 277056, "growth30": -59.0, "syncedAt": "2026-11-25"}}
    a.update(over)
    return a


def test_formats():
    assert [money(14699), money(277056), money(1_250_000), money(950), money(0), money(None)] == ["$14.7K", "$277K", "$1.2M", "$950", None, None]
    assert [age(7), age(30), age(None)] == ["7 mo", "2 yr", None]
    assert [growth(122.3), growth(-59), growth(None)] == ["+122%", "-59%", None]


def test_build_drops_anonymous_and_loads_as_card(tmp_path):
    r = {"checkedAt": "2026-11-25", "apps": [result(), result(name="Stealth Company", anonymous=True), result(name="Pattrn"), result(name="Kori")]}
    card = build(r, "3 indie apps making real money", "Verified revenue · last 30 days")
    assert [a["name"] for a in card["apps"]] == ["Verbi", "Pattrn", "Kori"]
    assert card["apps"][0]["verified"] == "$14.7K"
    p = tmp_path / "m.card.json"
    p.write_text(json.dumps(card))
    loaded = load_card(p)
    assert loaded.verified_note is True and loaded.revenue_note is False
    assert loaded.columns == ["verified", "earned", "age"]


def test_verified_column_rejects_ranges(tmp_path):
    card = build({"checkedAt": "2026-11-25", "apps": [result(), result(), result()]}, "t", "s")
    card["apps"][0]["verified"] = "$10K–30K/mo"
    p = tmp_path / "m.card.json"
    p.write_text(json.dumps(card))
    with pytest.raises(CardError):
        load_card(p)


def test_money_errors():
    from check_post import money_errors
    good = ("Verbi made **$14.7K** ([TrustMRR](https://trustmrr.com/startup/verbi)). This is a sample.\n"
            "The founder [says it was vibe coded](https://x.com/a/status/1).")
    assert money_errors(good) == []
    errs = money_errors("Verbi makes an estimated $10K. A solo dev built it.")
    assert len(errs) == 4
