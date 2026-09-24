"""Citation validator. Model outputs are hand-written (as the grounding note prescribes); the sources are real
chunks built from fixtures (Registration Act, 1908, ss. 1 and 2; BNSS s. 482; TPA s. 106) or a verbatim judgment
excerpt with its source URL."""

from pathlib import Path

import pytest

from app.citations.validator import citation_card, validate
from app.retrieval.registry import Registry
from tests.unit.helpers import as_row, statute_fixture_chunks

REG = Path(__file__).parents[2] / "data" / "registry"

# Dhanraj Aswani v. Amar S. Mulchandani, [2024] 9 S.C.R. 257; 2024 INSC 669, para 7 (verbatim excerpt)
DHANRAJ = {
    "chunk_id": "fad3381b8be4:para-7-part-2-of-3:92e7f45b", "doc_type": "judgment", "status": "n/a",
    "title": "DHANRAJ ASWANI versus AMAR S. MULCHANDANI & ANR.", "case_title": "DHANRAJ ASWANI versus AMAR S. MULCHANDANI & ANR.",
    "locator": "para 7 (part 2 of 3)", "citation": "[2024] 9 S.C.R. 257; 2024 INSC 669",
    "source_url": "https://indian-supreme-court-judgments.s3.ap-south-1.amazonaws.com/data/pdf/year=2024/english/2024_9_257_312_EN.pdf",
    "text": ("The restrictions on the exercise of power to grant pre-arrest bail under Section 438 of the CrPC are "
             "prescribed under Section 438(4) of the CrPC which provides that the provisions of Section 438 shall not "
             "apply to cases involving arrest under Sections 376(3), 376AB, 376DA or 376DB respectively of the IPC."),
}


@pytest.fixture(scope="module")
def registry():
    return Registry(REG)


def _bnss_482():
    return as_row(next(c for c in statute_fixture_chunks("bnss_2023_s482", "bnss-2023") if c.locator == "s. 482"))


def _tpa_106():
    return as_row(next(c for c in statute_fixture_chunks("tpa_1882_s106", "tpa-1882") if c.locator == "s. 106"))


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


def test_section_number_of_one_act_does_not_vouch_for_another(registry):
    """s. 482 BNSS (anticipatory bail) is not s. 482 CrPC (inherent powers): a number match is not enough."""
    id_map = {"S1": _bnss_482()}
    wrong = "Section 482 of the CrPC lets a person apply for anticipatory bail [S1]."
    right = "Section 482 of the BNSS lets a person who fears arrest apply to the High Court or the Court of Session [S1]."
    v = validate(wrong + " " + right, id_map, registry=registry)
    assert "CrPC" not in v.text and right in v.text
    assert v.unverified_authority == ["section 482 of the Code of Criminal Procedure, 1973"]


def test_old_code_section_is_accepted_when_a_cited_passage_names_it(registry):
    id_map = {"S1": _bnss_482(), "S2": DHANRAJ}
    ans = ("Under the old law, Section 438 of the CrPC did not apply to arrests under Section 376AB of the IPC [S2]. "
           "Section 438 CrPC is the provision in [S1].")
    v = validate(ans, id_map, registry=registry)
    assert "did not apply to arrests" in v.text  # S2 names s. 438 of the CrPC
    assert "is the provision in" not in v.text   # S1 is BNSS text and does not name s. 438 CrPC
    assert v.unverified_authority == ["section 438 of the Code of Criminal Procedure, 1973"]


def test_section_without_an_act_keeps_the_number_check(registry):
    v = validate("Sub-section (4) of section 482 excludes certain offences [S1].", {"S1": _bnss_482()}, registry=registry)
    assert not v.changed


def test_quote_with_ellipsis_matches_piece_by_piece():
    id_map = {"S1": _tpa_106()}
    ok = ('A lease for other purposes "shall be deemed to be a lease from month to month ... by fifteen days\' notice" [S1].')
    v = validate(ok, id_map)
    assert not v.unverified_quotes and "by fifteen days' notice\" [S1]" in v.text
    reordered = ('The Act says "by fifteen days\' notice ... shall be deemed to be a lease from month to month" [S1].')
    assert validate(reordered, id_map).unverified_quotes


def test_short_answer_and_how_it_may_apply_need_markers():
    ans = ("**Short answer:** A monthly lease can be ended by fifteen days' notice from either side.\n\n"
           "**What the sources say:**\n- The notice period runs from the date the notice is received [S1].\n\n"
           "**How it may apply:**\n- A contract or local law saying otherwise changes the period [S1].\n\n"
           "**Uncertain or not covered:** The sources do not say what state rent-control laws require.")
    v = validate(ans, {"S1": _tpa_106()})
    assert (v.unsupported, round(v.unsupported_share, 2)) == (1, 0.33)


def test_saying_the_sources_are_silent_is_not_an_unsupported_claim():
    ans = "**Short answer:** The sources do not say how to file the application.\n\n**What the sources say:**\n- x [S1]."
    assert validate(ans, {"S1": _tpa_106()}).unsupported == 0
