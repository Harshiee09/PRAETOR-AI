"""Citation validator v1. Model outputs are hand-written (as the grounding note prescribes); the sources are real
chunks built from fixtures (Registration Act, 1908, ss. 1 and 2)."""

from app.citations.validator import citation_card, validate
from tests.unit.helpers import as_row, statute_fixture_chunks


def _id_map():
    chunks = [as_row(c) for c in statute_fixture_chunks("registration_1908_ss1-8", "registration-1908")]
    return {"S1": next(c for c in chunks if c["locator"] == "s. 1"),
            "S2": next(c for c in chunks if c["locator"] == "s. 2")}


def test_clean_answer_passes_unchanged():
    ans = "The Act came into force on the first day of January, 1909 [S1]."
    v = validate(ans, _id_map())
    assert v.text == ans and v.used_ids == ["S1"] and not v.changed and not v.warnings


def test_unknown_id_is_stripped():
    v = validate("The Act extends to the whole of India [S1][S9].", _id_map())
    assert v.text == "The Act extends to the whole of India [S1]."
    assert v.invalid_ids == ["S9"] and v.used_ids == ["S1"]
    assert any("S9" in w for w in v.warnings)


def test_grouped_markers_are_normalised():
    v = validate("Sections 1 and 2 open the Act [S1, S2].", _id_map())
    assert "[S1][S2]" in v.text and v.used_ids == ["S1", "S2"]


def test_verbatim_quote_is_kept():
    ans = 'Section 1 says "It shall come into force on the first day of January, 1909" [S1].'
    v = validate(ans, _id_map())
    assert v.text == ans and not v.unverified_quotes


def test_non_verbatim_quote_removes_the_sentence():
    ans = ('The Act has a commencement clause [S1]. It says "It shall come into force on the first day of April, 1909" [S1]. '
           'Section 2 defines terms [S2].')
    v = validate(ans, _id_map())
    assert "April" not in v.text
    assert "The Act has a commencement clause [S1]." in v.text and "Section 2 defines terms [S2]." in v.text
    assert v.unverified_quotes and v.changed


def test_repealed_source_adds_a_warning():
    id_map = _id_map()
    id_map["S1"] = {**id_map["S1"], "status": "repealed", "successor": "cpa-2019"}
    statutes = {"cpa-2019": {"short_title": "Consumer Protection Act, 2019"}}
    v = validate("Old rule [S1].", id_map, statutes)
    assert any("repealed" in w and "Consumer Protection Act, 2019" in w for w in v.warnings)


def test_unverified_section_is_removed():
    ans = "The Act commenced on the first day of January, 1909 [S1]. Section 88 exempts government officers [S1]."
    v = validate(ans, _id_map())
    assert "Section 88" not in v.text and "first day of January, 1909 [S1]" in v.text
    assert v.unverified_authority == ["section 88"]


def test_section_of_the_cited_chunk_is_accepted():
    ans = "Section 1 says the Act may be called the Registration Act, 1908 [S1]."
    v = validate(ans, _id_map())
    assert v.text == ans and not v.changed


def test_case_name_and_reporter_citation_not_in_context_are_removed():
    ans = ("Registration is governed by the Act [S1]. As held in Kesavananda Bharati v. State of Kerala, this is settled [S1]. "
           "See (2020) 8 SCC 129 [S2]. Definitions are in section 2 [S2].")
    v = validate(ans, _id_map())
    assert "Kesavananda" not in v.text and "SCC" not in v.text
    assert "Registration is governed by the Act [S1]." in v.text and "Definitions are in section 2 [S2]." in v.text
    assert len(v.unverified_authority) == 2


def test_act_with_year_not_in_context_is_removed():
    v = validate("Stamp duty is payable under the Indian Stamp Act, 1899 [S1].", _id_map())
    assert v.text == "" and v.unverified_authority


def test_unsupported_sentences_are_counted():
    ans = ("**What the sources say:**\n- The Act extends to the whole of India [S1].\n"
           "- Registration offices are established in every district of the country.\n\n**Uncertain:** none.")
    v = validate(ans, _id_map())
    assert v.unsupported == 1 and v.unsupported_share == 0.5


def test_citation_card_is_metadata_and_verbatim_quote():
    s1 = _id_map()["S1"]
    card = citation_card("S1", s1)
    assert card["title"] == "Registration Act, 1908" and card["locator"] == "s. 1"
    assert card["source_url"] == "https://indiacode.gov.in/handle/123456789/496068"
    assert card["quote"] in " ".join(s1["text"].split())
    assert len(card["quote"]) <= 300
