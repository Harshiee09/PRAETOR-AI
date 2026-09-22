"""Paragraph splitter against real Supreme Court Reports excerpts (both layouts)."""

from app.chunking.judgment import PARA_NUM, find_body, para_label, split_judgment
from tests.conftest import load_fixture, parsed_from_fixture


def _numbers(jp):
    return sorted({p.number for p in jp.paras if p.number is not None})


def test_old_scr_layout_body_and_paragraphs():
    doc = parsed_from_fixture("sc_2021_11_scr_1181_old_layout")
    start, _ = find_body(doc.lines)
    assert "delivered by" in doc.lines[start - 1].text
    jp = split_judgment(doc)
    nums = _numbers(jp)
    assert nums[:5] == [1, 2, 3, 4, 5]
    first = next(p for p in jp.paras if p.number == 1)
    assert first.text.startswith("1. Feeling aggrieved and dissatisfied with the impugned order")
    # no counsel list or headnote text in the body
    assert not any("Advs. for the" in p.text for p in jp.paras)


def test_digital_scr_layout_stops_before_editorial_tail():
    doc = parsed_from_fixture("sc_2025_1_scr_62_digital_layout")
    jp = split_judgment(doc)
    assert jp.paras and _numbers(jp)[0] == 1
    assert next(p for p in jp.paras if p.number == 1).text.startswith("1. Leave granted.")
    body = " ".join(p.text for p in jp.paras)
    assert "Result of the case" not in body and "Headnotes prepared by" not in body


def test_fixture_metadata_is_the_dataset_record():
    fx = load_fixture("sc_2021_11_scr_1181_old_layout")
    assert fx["download_url"].startswith("s3://indian-supreme-court-judgments/")
    assert fx["metadata"]["neutral_citation"] == "2021 INSC 836"


def test_paragraph_number_pattern():
    assert PARA_NUM.match("12. The appellant").group("num") == "12"
    assert PARA_NUM.match("7.1 Pre-deposit of").group("sub") == "1"
    assert PARA_NUM.match("2.At the heart of this dispute").group("num") == "2"
    assert PARA_NUM.match("22.10.2010 forming part of") is None  # a date, not a paragraph


def test_para_labels():
    assert para_label([3, 4, 5]) == (3, 5, "paras 3-5")
    assert para_label([7]) == (7, 7, "para 7")
    assert para_label([None]) == (None, None, None)
    assert para_label([1002, 1003])[2] == "paras 2-3 (opinion 2)"
