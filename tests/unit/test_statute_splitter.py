"""Section splitter against real India Code excerpts (fixtures carry their source URL)."""

from app.chunking.statute import SECTION_START, split_statute
from app.chunking.text import join_lines, paragraphs
from tests.conftest import load_fixture, parsed_from_fixture


def _sections(sp):
    return {s.num: s for s in sp.sections if s.kind == "section"}


def test_fixture_provenance_is_recorded():
    fx = load_fixture("registration_1908_ss1-8")
    assert fx["source_url"] == "https://indiacode.gov.in/handle/123456789/496068"
    assert len(fx["raw_sha256"]) == 64 and fx["pages"] == [1, 4, 5, 6, 7]


def test_registration_sections_follow_arrangement(known_states):
    sp = split_statute(parsed_from_fixture("registration_1908_ss1-8"), known_states)
    secs = _sections(sp)
    assert list(secs)[:8] == ["1", "2", "3", "4", "5", "6", "7", "8"]
    assert secs["1"].heading == "Short title, extent and commencement"
    assert secs["3"].heading == "Inspector-General of Registration"
    assert secs["3"].part.startswith("Part II")


def test_state_amendments_are_separated_from_central_text(known_states):
    secs = _sections(split_statute(parsed_from_fixture("registration_1908_ss1-8"), known_states))
    s3 = secs["3"]
    assert [b.state for b in s3.state_blocks] == ["Uttarakhand", "Uttar Pradesh"]
    central = join_lines([ln.text for ln in s3.lines])
    assert "Uttarakhand" not in central and "Vide" not in central
    assert "shall appoint an officer to be the Inspector-General of Registration" in central
    assert "Uttarakhand Act 24 of 2014" in join_lines([ln.text for ln in s3.state_blocks[0].lines])


def test_footnote_markers_are_lifted_and_linked(known_states):
    sp = split_statute(parsed_from_fixture("registration_1908_ss1-8"), known_states)
    s3 = _sections(sp)["3"]
    assert "The [State Government] shall appoint" in join_lines([ln.text for ln in s3.lines])
    notes = {m: sp.footnotes[pg][m] for pg, ms in s3.markers_by_page.items() for m in ms if m in sp.footnotes.get(pg, {})}
    assert notes["1"].startswith("Subs. by the A.O. 1950")


def test_nested_footnotes_do_not_leak_into_sections(known_states):
    """TPA p. 7 has a footnote with indented sub-lists; it once leaked into s. 1 and derailed ss. 2-4."""
    sp = split_statute(parsed_from_fixture("tpa_1882_ss1-3_nested_footnotes"), known_states)
    secs = _sections(sp)
    assert {"1", "2", "3"} <= set(secs)
    s1 = join_lines([ln.text for ln in secs["1"].lines])
    assert "This Act may be called the Transfer of Property Act, 1882" in s1
    assert "Presidency of Bombay" not in s1
    assert "Presidency of Bombay" in sp.footnotes[7]["5"]


def test_inserted_section_and_marginal_headings(known_states):
    """p. 20: `1 [53A. Part performance.—` (inserted), s. 54 with bold marginal headings, an Assam amendment."""
    doc = parsed_from_fixture("tpa_1882_s53A-55_state_amendment")
    starts = [SECTION_START.match(ln.text).group("num") for ln in doc.lines
              if ln.bold_prefix and SECTION_START.match(ln.text)]
    assert starts == ["53A", "54", "55"]
    s54 = [ln for ln in doc.lines if ln.text.startswith("54. ")][0]
    assert s54.text.startswith("54. “Sale” defined.—“Sale” is a transfer of ownership in exchange for a price")


def test_section_23_paragraphs():
    doc = parsed_from_fixture("registration_1908_s23")
    i = next(i for i, ln in enumerate(doc.lines) if ln.text.startswith("23. Time for presenting documents"))
    j = next(k for k, ln in enumerate(doc.lines) if k > i and ln.bold_prefix and SECTION_START.match(ln.text))
    assert SECTION_START.match(doc.lines[j].text).group("num") == "23A"  # printed as "[23A." (inserted section)
    paras = paragraphs(doc.lines[i:j])
    assert len(paras) == 2
    assert "within four months from the date of its execution" in paras[0].text
    assert paras[1].text.startswith("Provided that")


def test_section_start_pattern():
    for text, num in [("23. Time for presenting documents.—Subject", "23"), ("[53A. Part performance.—Where", "53A"),
                      ("16A. Keeping of books in computer floppies", "16A")]:
        assert SECTION_START.match(text).group("num") == num
    assert SECTION_START.match("“22A. Documents registration of which is opposed") is None
