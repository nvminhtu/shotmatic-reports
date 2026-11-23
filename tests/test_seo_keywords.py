from seo_keywords import covers, suggest, tokens

BANK = [
    {"keyword": "aso keyword ranking", "cluster": "C · ASO / store keywords", "fit": "Core", "autocomplete_pos": "2", "link": "/a"},
    {"keyword": "google trends for apps", "cluster": "E · Google Trends", "fit": "Core", "autocomplete_pos": "", "link": "/b"},
    {"keyword": "how to publish an app", "cluster": "G · Launch / publish", "fit": "Core", "autocomplete_pos": "1", "link": "/c"},
]


def test_tokens_drop_stopwords_and_plural():
    assert tokens("The best Speaker Cleaner apps for iPhone") == {"speaker", "cleaner", "app", "iphone"}


def test_covers_is_word_based():
    assert covers("Speaker cleaner apps: 8 keywords ranked", "speaker cleaner app keywords")
    assert not covers("Speaker apps ranked", "speaker cleaner app")


def test_suggest_prefers_type_cluster_and_overlap():
    out = suggest("keyword", "speaker cleaner keyword ranking app store", BANK)
    assert out[0]["keyword"] == "aso keyword ranking"
    assert "how to publish an app" in [r["keyword"] for r in out]  # 'app' overlap
    assert suggest("trend", "nothing shared", BANK)[0]["keyword"] == "google trends for apps"
