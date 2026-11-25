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
