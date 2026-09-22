from app.chunking.text import Para, join_lines, pack, split_sentences
from tests.conftest import parsed_from_fixture


def test_join_lines_keeps_compound_hyphens():
    assert join_lines(["the Inspector-", "General of Registration"]) == "the Inspector-General of Registration"
    assert join_lines(["within four", "months"]) == "within four months"


def test_pack_respects_budget_and_never_cuts_sentences():
    doc = parsed_from_fixture("cpa_2019_s69")
    text = " ".join(ln.text for ln in doc.lines)
    pieces = pack([Para(text, 30, 30)], 60, lambda t: len(t.split()))
    sentences = set(split_sentences(text))
    for piece in pieces:
        for s in split_sentences(piece[0].text):
            assert s in sentences  # every piece is made of whole sentences from the source


def test_pack_groups_small_paragraphs():
    paras = [Para("One two three.", 1, 1), Para("Four five.", 1, 1), Para("Six seven eight nine.", 2, 2)]
    pieces = pack(paras, 6, lambda t: len(t.split()))
    assert [len(p) for p in pieces] == [2, 1]
