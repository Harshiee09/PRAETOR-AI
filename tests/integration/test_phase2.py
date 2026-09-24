"""Phase 2 checks against the real corpus and index (needs `praetor ingest` + `praetor index`, GPU or CPU models)."""

import pytest

from app.config import get_settings

pytestmark = pytest.mark.integration
REAL = get_settings()


@pytest.fixture(scope="module")
def engine():
    if not REAL.faiss_path.exists():
        pytest.skip("index missing: run `praetor index`")
    from app.rag.pipeline import Engine

    return Engine.load(REAL)


@pytest.fixture()
def conn():
    from app.store.db import connect

    c = connect(REAL.sqlite_path)
    yield c
    c.close()


def test_cpc_orders_are_split_into_rules(conn):
    n = conn.execute("SELECT COUNT(*) FROM chunks WHERE act_title = 'Code of Civil Procedure, 1908' AND section LIKE 'O. %'").fetchone()[0]
    row = conn.execute("SELECT section_heading, chapter FROM chunks WHERE act_title = 'Code of Civil Procedure, 1908' "
                       "AND section = 'O. XXXIX r. 1'").fetchone()
    assert n > 600
    assert row["section_heading"] == "Cases in which temporary injunction may be granted" and "Order XXXIX" in row["chapter"]


def test_bns_106_is_partially_in_force(conn):
    statuses = {r[0] for r in conn.execute("SELECT status FROM chunks WHERE act_title = 'Bharatiya Nyaya Sanhita, 2023' AND section = '106'")}
    others = {r[0] for r in conn.execute("SELECT DISTINCT status FROM chunks WHERE act_title = 'Bharatiya Nyaya Sanhita, 2023' AND section = '105'")}
    assert statuses == {"partially_in_force"} and others == {"in_force"}


def test_exact_lookup_pins_order_rule(engine, conn):
    r = engine.retriever.retrieve(conn, "When can a court grant a temporary injunction under Order 39 Rule 1 CPC?", mode="full")
    assert r.candidates[0]["section"] == "O. XXXIX r. 1" and r.gate["on"] == "exact"


def test_repealed_act_pins_successor_repeal_section(engine, conn):
    r = engine.retriever.retrieve(conn, "Is anticipatory bail under section 438 CrPC still available?", mode="full")
    top = [(c["act_title"], c["section"]) for c in r.candidates[:3]]
    assert ("Bharatiya Nagarik Suraksha Sanhita, 2023", "531") in top
    assert any("not in the corpus" in n for n in r.notes)


def test_named_case_is_pinned(engine, conn):
    r = engine.retriever.retrieve(conn, "What did the Supreme Court decide in Indore Development Authority v. Manoharlal?", mode="full")
    assert any("2020 INSC 294" in (c.get("citation") or "") for c in r.candidates[:4])


def test_out_of_corpus_question_abstains(engine, conn):
    r = engine.retriever.retrieve(conn, "What documents do I need to apply for a Schengen visa?", mode="full")
    assert r.abstained


def test_guessed_successor_provision_is_not_pinned(engine, conn):
    """Only the successor's repeal section is pinned. The "closest provision" is a similarity guess and must earn its
    place through the reranker: pinned, it put BNSS s. 442 (revision) first for a question about s. 482 CrPC, whose
    BNSS counterpart is the inherent power in s. 528 (DECISIONS D44)."""
    r = engine.retriever.retrieve(conn, "Can the High Court quash an FIR under section 482 CrPC?", mode="full")
    pinned = [(c["act_title"], c["section"]) for c in r.candidates if "exact" in c["ranks"]]
    assert pinned == [("Bharatiya Nagarik Suraksha Sanhita, 2023", "531")]


@pytest.mark.parametrize("question, act, section", [
    ("How do I apply for anticipatory bail?", "Bharatiya Nagarik Suraksha Sanhita, 2023", "482"),
    ("Is anticipatory bail under section 438 CrPC still available?", "Bharatiya Nagarik Suraksha Sanhita, 2023", "482"),
    ("What can a home buyer claim if the builder fails to hand over the flat on the agreed date?",
     "Real Estate (Regulation and Development) Act, 2016", "18"),
    ("My landlord says he will throw me out of the house tomorrow without any notice. What does the law say?",
     "Transfer of Property Act, 1882", "106"),
])
def test_reported_failures_reach_the_context(engine, conn, question, act, section):
    """The four failures of the 2026-09-24 audit (DECISIONS D35): the provision must be among the 8 context blocks and
    the question must not abstain. Regression checks on questions that were used to design the fix."""
    from app.rag.context import reserve_statute_slots

    r = engine.retriever.retrieve(conn, question, mode="full")
    ctx = reserve_statute_slots(r.candidates, engine.settings.context_max_chunks)[: engine.settings.context_max_chunks]
    assert not r.abstained
    assert (act, section) in [(c["act_title"], c["section"]) for c in ctx]
