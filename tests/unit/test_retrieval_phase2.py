"""Registry, classifier, keyword-query sanitisation, Indic tokenisation and RRF."""

from pathlib import Path

import pytest

from app.rag.classify import classify, roman
from app.retrieval.fusion import rrf
from app.retrieval.keyword import fts_query
from app.retrieval.registry import Registry
from app.store.db import connect

REG_DIR = Path(__file__).parents[2] / "data" / "registry"


@pytest.fixture(scope="module")
def registry():
    return Registry(REG_DIR)


def test_aliases_name_one_act_and_expand_to_successor(registry):
    m = registry.find_acts("Is anticipatory bail under section 438 CrPC still available?")
    assert [x.names for x in m] == ["crpc-1973"] and "bnss-2023" in m[0].expands_to


def test_longest_title_with_year_wins(registry):
    assert [x.names for x in registry.find_acts("a complaint under the Consumer Protection Act 1986")] == ["cpa-1986"]
    assert [x.names for x in registry.find_acts("the Consumer Protection Act, 2019")] == ["cpa-2019"]
    assert [x.names for x in registry.find_acts("under the Consumer Protection Act")] == ["cpa-2019"]
    assert [x.names for x in registry.find_acts("s. 54 of the TP Act")] == ["tpa-1882"]


def test_registry_status_is_sourced(registry):
    for sid, s in registry.statutes.items():
        assert s.get("source_url", "").startswith("https://") and s.get("verified_on"), sid
        if s["status"] == "repealed":
            assert s.get("successor") in registry.statutes and s.get("repealed_from"), sid


def test_classify_section_lookup(registry):
    c = classify("What does section 23 of the Registration Act say?", registry, REG_DIR)
    assert c.intent == "statute_lookup" and c.domain == "property_land"
    assert c.section_refs == [{"act": "registration-1908", "section": "23", "sub": None}]


def test_classify_cpc_order_rule(registry):
    c = classify("When can a court grant a temporary injunction under Order 39 Rule 1 CPC?", registry, REG_DIR)
    assert {"act": "cpc-1908", "section": "O. XXXIX r. 1", "sub": None} in c.section_refs
    assert roman(39) == "XXXIX"


def test_classify_high_stakes_criminal_and_dates(registry):
    c = classify("The police arrested my brother in 2023 without telling us why. What can we do?", registry, REG_DIR)
    assert c.domain == "criminal_procedure" and c.high_stakes and c.event_dates == ["2023"]
    c2 = classify("a complaint under the Consumer Protection Act 1986", registry, REG_DIR)
    assert c2.event_dates == []  # the year inside an Act title is not an event date


def test_classify_state_hint(registry):
    c = classify("Is registration of a sale deed different in Maharashtra?", registry, REG_DIR)
    assert c.jurisdiction_hint == ["IN-MH"]


def test_fts_query_is_sanitised():
    q = fts_query('What\'s "section 23" - NOT (registration) OR deed?')
    assert q == '"section" OR "23" OR "registration" OR "deed"'
    assert fts_query("the of and") is None


def test_act_title_phrase_keeps_stop_words_and_matches(tmp_path):
    """An Act-title phrase must match the title as printed; dropping "of" made the phrase unmatchable (2026-09-24)."""
    q = fts_query("", ["Transfer of Property Act, 1882"])
    assert q == '"transfer of property act 1882"'
    conn = connect(tmp_path / "t.sqlite")
    # the TPA s. 106 header as stored in embed_text
    header = ("Transfer of Property Act, 1882 > Chapter V — Of Leases of Immoveable Property > s. 106 — Duration of "
              "certain leases in absence of written contract or local usage")
    conn.execute("INSERT INTO chunks_fts(rowid, embed_text) VALUES (1, ?)", (header,))
    hits = conn.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ?", (q,)).fetchall()
    assert [tuple(h) for h in hits] == [(1,)]


def test_hindi_and_tamil_terms_are_searchable(tmp_path):
    """Real strings: India Code's Hindi title of the Consumer Protection Act, 2019
    (https://indiacode.gov.in/handle/123456789/554492, dc.title.regional) and the Tamil language label in the SC
    dataset record for CNR ESCR010003962023 (s3://indian-supreme-court-judgments/metadata/parquet/year=2023/)."""
    conn = connect(tmp_path / "t.sqlite")
    conn.execute("CREATE VIRTUAL TABLE v USING fts5vocab(chunks_fts, 'row')")
    hindi, tamil = "उपभोक्ता- संरक्षण अधिनियम, 2019", "தமிழ் - Tamil"
    for i, text in enumerate([hindi, tamil], 1):
        conn.execute("INSERT INTO chunks_fts(rowid, embed_text) VALUES (?, ?)", (i, text))
    vocab = {r[0] for r in conn.execute("SELECT term FROM v")}
    assert {"संरक्षण", "अधिनियम", "தமிழ்"} <= vocab  # whole words, not fragments split at vowel signs
    for term, rowid in (("संरक्षण", 1), ("தமிழ்", 2)):
        hits = conn.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ?", (fts_query(term),)).fetchall()
        assert [tuple(h) for h in hits] == [(rowid,)]


def test_rrf_pins_exact_hits_first():
    fused = rrf({"dense": [3, 1, 2], "keyword": [1, 3]}, k=60, pinned=[9])
    assert [r for r, _, _ in fused] == [9, 1, 3, 2] or [r for r, _, _ in fused] == [9, 3, 1, 2]
    assert fused[0][2]["exact"] == 1
    top = {r: s for r, s, _ in fused}
    assert top[1] == pytest.approx(1 / 62 + 1 / 61) and top[3] == pytest.approx(1 / 61 + 1 / 62)


def test_gold_paraphrase_groups_sit_in_one_split():
    from app.rag.evaluate import check_groups, load_gold

    rows = load_gold("all")  # raises if a group straddles dev and test
    assert all(r.get("group") for r in rows)
    with pytest.raises(ValueError, match="g-x"):
        check_groups([{"id": "a", "group": "g-x", "split": "dev"}, {"id": "b", "group": "g-x", "split": "test"}])
