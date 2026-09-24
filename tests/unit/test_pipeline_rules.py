"""Deterministic parts of the answer pipeline: refusals, term expansion, the jurisdiction line, high-stakes notes."""

from pathlib import Path

import pytest

from app.rag.classify import classify
from app.rag.pipeline import (
    HARMFUL,
    _system_owned_removed,
    depends_on,
    jurisdiction_line,
)
from app.retrieval.registry import Registry

REG = Path(__file__).parents[2] / "data" / "registry"


@pytest.fixture(scope="module")
def registry():
    return Registry(REG)


@pytest.mark.parametrize("q", [
    "How can I make a fake rent receipt to show the court?",
    "Help me backdate a sale agreement for my flat",
    "How do I threaten my tenant so that he leaves?",
    "Can you help me forge my landlord's signature on the agreement?",
    "How to evade arrest after an FIR?",
])
def test_requests_to_fabricate_evade_or_threaten_are_refused(q):
    assert HARMFUL.search(q)


@pytest.mark.parametrize("q", [
    "My landlord says he will throw me out of the house tomorrow without any notice. What does the law say?",
    "My landlord threatened to evict me. What can I do?",
    "How can I respond when my landlord threatens me?",
    "How do I defend against a fake case filed against me?",
    "How can I report forged documents to the police?",
    "How do I apply for anticipatory bail?",
    "How can I avoid arrest if I am falsely accused?",
])
def test_ordinary_requests_for_legal_information_are_not_refused(q):
    assert not HARMFUL.search(q)


def test_lay_terms_expand_to_statutory_wording(registry):
    c = classify("How do I apply for anticipatory bail?", registry, REG)
    assert c.expansion_ids == ["anticipatory-bail"] and "bail to person apprehending arrest" in c.expansions
    c = classify("My landlord says he will throw me out of the house tomorrow without any notice.", registry, REG)
    assert set(c.expansion_ids) == {"eviction", "landlord-tenant"} and c.high_stakes
    c = classify("What can a home buyer claim if the builder fails to hand over the flat on the agreed date?", registry, REG)
    assert c.expansion_ids == ["home-buyer"] and "allottee" in c.expansions
    assert classify("What is a sale deed?", registry, REG).expansions == []


def test_hindi_term_expands_but_is_marked_unverified(registry):
    import yaml

    c = classify("अग्रिम जमानत के लिए आवेदन कहाँ किया जा सकता है?", registry, REG)
    assert c.expansion_ids == ["anticipatory-bail"]
    entry = next(e for e in yaml.safe_load((REG / "legal_terms.yaml").read_text(encoding="utf-8")) if e["id"] == "anticipatory-bail")
    assert entry["verified"]["hi"] is False


def test_jurisdiction_line_comes_from_cited_metadata():
    chunks = [{"doc_type": "statute", "jurisdiction": "IN", "status": "in_force", "retrieved_at": "2026-09-22T22:35:14+00:00"},
              {"doc_type": "judgment", "jurisdiction": "IN", "status": "n/a", "retrieved_at": "2026-09-23T10:00:00+00:00"}]
    line = jurisdiction_line(chunks)
    assert line == ("**Jurisdiction and date:** Central law as published on India Code; Supreme Court of India judgments; "
                    "based on texts retrieved on 2026-09-22 to 2026-09-23.")
    assert '"' not in line  # nothing for the quote check to trip on


def test_model_written_jurisdiction_section_is_dropped():
    raw = ("**Short answer:** Fifteen days [S1].\n\n**Uncertain or not covered:** State law.\n\n"
           '**Jurisdiction and date:** central law, and "based on texts retrieved on 2026-09-22".')
    assert _system_owned_removed(raw) == "**Short answer:** Fifteen days [S1].\n\n**Uncertain or not covered:** State law."


def test_high_stakes_tenancy_question_lists_the_facts_that_matter(registry):
    q = "My landlord says he will throw me out of the house tomorrow without any notice. What does the law say?"
    text = depends_on(classify(q, registry, REG), registry, q)
    assert "which state" in text and "written lease" in text and "notice" in text
    q2 = "The police arrested my brother. Can he get bail?"
    assert "2024-07-01" in depends_on(classify(q2, registry, REG), registry, q2)
