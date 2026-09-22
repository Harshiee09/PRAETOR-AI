"""Ingestion gate: reject, don't warn (chunk-schema note)."""

import dataclasses
from datetime import date

from app.chunking.schema import make_chunk_id, validate_chunk
from tests.unit.helpers import judgment_fixture_chunks, statute_fixture_chunks


def test_real_statute_and_judgment_chunks_pass():
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    chunks += judgment_fixture_chunks("sc_2021_11_scr_1181_old_layout")
    assert chunks
    for c in chunks:
        assert validate_chunk(c) == [], (c.locator, validate_chunk(c))


def test_state_amendment_chunks_carry_state_jurisdiction():
    chunks = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")
    s3_states = [c for c in chunks if c.locator.startswith("s. 3, State amendment")]
    assert {c.jurisdiction for c in s3_states} == {"IN-UK", "IN-UP"}
    assert all(c.jurisdiction == "IN" for c in chunks if "State amendment" not in c.locator)


def test_missing_required_field_rejects():
    c = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")[1]
    assert "missing section_heading" in validate_chunk(dataclasses.replace(c, section_heading=""))
    assert "missing source_url" in " ".join(validate_chunk(dataclasses.replace(c, source_url=None)))


def test_placeholders_and_impossible_values_reject():
    j = judgment_fixture_chunks("sc_2021_11_scr_1181_old_layout")[0]
    assert any("placeholder party" in p for p in validate_chunk(dataclasses.replace(j, case_title="... versus STATE")))
    assert any("future" in p for p in validate_chunk(dataclasses.replace(j, decision_date="2099-01-01")))
    assert any("before 1950-01-28" in p for p in validate_chunk(dataclasses.replace(j, decision_date="1949-12-01")))
    assert any("TBD" in p for p in validate_chunk(dataclasses.replace(j, court="TBD")))
    assert any("https://" in p for p in validate_chunk(dataclasses.replace(j, source_url="http://example.org/x.pdf")))


def test_unmapped_state_is_rejected_not_guessed():
    c = statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")[1]
    assert "missing jurisdiction" in validate_chunk(dataclasses.replace(c, jurisdiction=""))


def test_chunk_id_is_stable_and_text_sensitive():
    a = make_chunk_id("a" * 64, "s. 23", "text one")
    assert a == make_chunk_id("a" * 64, "s. 23", "text one")
    assert a != make_chunk_id("a" * 64, "s. 23", "text two")
    assert a.startswith("aaaaaaaaaaaa:s-23:")


def test_validation_uses_today():
    j = judgment_fixture_chunks("sc_2021_11_scr_1181_old_layout")[0]
    assert validate_chunk(j, today=date(2021, 12, 6))  # decided 2021-12-07: "future" relative to that day
