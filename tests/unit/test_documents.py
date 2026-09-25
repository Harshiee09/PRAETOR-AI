"""Uploaded documents (DECISIONS D50): upload limits, passages, delete, and the grounded analysis contract.

The PDFs are built here from real fixture text (Transfer of Property Act s. 106 as printed on India Code; source URL in
the fixture), so the upload path runs the real parser. The answer model is a stub that returns a fixed text: these
tests check what the system does with model output (validation, [D#]/[S#] relabelling, cards), not the model.
"""

import shutil
from functools import partial
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import Settings
from app.documents.analyze import analyze, select_passages
from app.documents.parse import _numbers, _pack, _units, parse_upload
from app.documents.store import DocumentStore
from app.llm.base import LLMResult
from app.store.db import chunk_by_id, connect, replace_document
from tests.conftest import load_fixture, parsed_from_fixture
from tests.unit.helpers import statute_fixture_chunks
from tests.unit.test_store_idempotency import _doc

REG = Path(__file__).parents[2] / "data" / "registry"


def _pdf(lines: list[str]) -> bytes:
    """A one-page PDF with a Helvetica text layer carrying `lines`."""
    def esc(t: str) -> str:
        t = t.encode("latin-1", "replace").decode("latin-1")
        return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = ("BT /F1 10 Tf 50 800 Td 12 TL " + " ".join(f"({esc(t)}) '" for t in lines) + " ET").encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def _s106_lines() -> list[str]:
    lines = [ln["text"] for ln in load_fixture("tpa_1882_s106")["lines"]]
    start = next(i for i, t in enumerate(lines) if t.lstrip("[").startswith("106."))
    return lines[start:start + 14]


class StubLLM:
    name = "ollama"

    def __init__(self, text: str):
        self.text, self.prompts = text, []

    def generate(self, messages, *, system, max_tokens, temperature=0.1, json_schema=None, seed=None):
        self.prompts.append(messages[0].content)
        return LLMResult(text=self.text, model="stub", input_tokens=1, output_tokens=1, latency_ms=1)


def _settings(tmp_path, **kw) -> Settings:
    data = tmp_path / "data"
    if not (data / "registry").exists():
        shutil.copytree(REG, data / "registry")
    return Settings(_env_file=None, data_dir=data, llm_answer="ollama", ollama_model="stub", **kw)


def _client(tmp_path, llm_text="**Short answer:** Notice is needed [S1].", **kw):
    settings = _settings(tmp_path, **kw)
    app = create_app(settings, engine=None, load_engine=False, analyze_fn=partial(analyze, llm=StubLLM(llm_text)))
    return TestClient(app, client=("127.0.0.1", 50000))


def test_upload_reads_a_text_pdf_into_located_passages(tmp_path):
    with _client(tmp_path) as c:
        r = c.post("/v1/documents", files={"file": ("my lease.pdf", _pdf(_s106_lines()), "application/pdf")})
        assert r.status_code == 201, r.text
        info = r.json()
        detail = c.get(f"/v1/documents/{info['document_id']}").json()
    assert info["filename"] == "my lease.pdf" and info["pages"] == 1 and info["passage_count"] >= 1
    assert info["unreadable_pages"] == [] and info["expires_at"] > info["uploaded_at"]
    p = detail["passages"][0]
    assert "106" in p["locator"] and "p. 1" in p["locator"] and "fifteen days" in " ".join(p["text"].split())


def test_upload_rejects_other_files_oversize_and_scanned_pdfs(tmp_path):
    with _client(tmp_path) as c:
        not_pdf = c.post("/v1/documents", files={"file": ("a.docx", b"PK\x03\x04 not a pdf", "application/octet-stream")})
        scanned = c.post("/v1/documents", files={"file": ("scan.pdf", _pdf([]), "application/pdf")})
    with _client(tmp_path, doc_max_mb=0.0001) as c:
        big = c.post("/v1/documents", files={"file": ("big.pdf", _pdf(_s106_lines()), "application/pdf")})
    assert not_pdf.status_code == 415 and not_pdf.json()["error"]["code"] == "unsupported_media_type"
    assert scanned.status_code == 422 and "scanned" in scanned.json()["error"]["message"]
    assert big.status_code == 413 and big.json()["error"]["code"] == "too_large"


def test_delete_forgets_the_document(tmp_path):
    with _client(tmp_path) as c:
        doc_id = c.post("/v1/documents", files={"file": ("x.pdf", _pdf(_s106_lines()), "application/pdf")}).json()["document_id"]
        assert c.delete(f"/v1/documents/{doc_id}").status_code == 204
        gone = c.get(f"/v1/documents/{doc_id}")
        again = c.post("/v1/documents/analyze", json={"document_ids": [doc_id], "task": "summary"})
    assert gone.status_code == 404 and again.status_code == 404


def test_analysis_request_shape_is_checked(tmp_path):
    with _client(tmp_path) as c:
        no_question = c.post("/v1/documents/analyze", json={"document_ids": ["x"], "task": "ask"})
        one_for_compare = c.post("/v1/documents/analyze", json={"document_ids": ["x"], "task": "compare"})
        two_for_summary = c.post("/v1/documents/analyze", json={"document_ids": ["x", "y"], "task": "summary"})
    assert {no_question.status_code, one_for_compare.status_code, two_for_summary.status_code} == {422}


def test_analysis_without_the_engine_uses_the_document_alone_and_says_so(tmp_path):
    with _client(tmp_path, llm_text="**In short:** A lease term on notice [S1].\n\n**Key terms:**\n- Notice of "
                                    "fifteen days applies to a month-to-month lease [S1].") as c:
        doc_id = c.post("/v1/documents", files={"file": ("x.pdf", _pdf(_s106_lines()), "application/pdf")}).json()["document_id"]
        r = c.post("/v1/documents/analyze", json={"document_ids": [doc_id], "task": "summary"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["task"] == "summary" and body["law_checked"] is False
    assert any(w.startswith("Law cross-check skipped") for w in body["warnings"])
    assert "[D1]" in body["answer_markdown"] and "[S1]" not in body["answer_markdown"]
    assert body["citations"][0]["kind"] == "document" and body["citations"][0]["document_id"] == doc_id
    assert body["documents"][0]["complete"] is True and body["documents"][0]["pages_read"] == "1"


def test_analysis_validates_citations_and_relabels_document_and_law(tmp_path):
    settings = _settings(tmp_path)
    chunks = statute_fixture_chunks("tpa_1882_s106", "tpa-1882")
    conn = connect(settings.sqlite_path)
    with conn:
        replace_document(conn, _doc(chunks[0]), chunks, "2026-09-25")
    s106 = chunk_by_id(conn, next(ch for ch in chunks if ch.locator == "s. 106").chunk_id)
    conn.close()
    store = DocumentStore(60, 5)
    doc = store.put("lease.pdf", parse_upload(_pdf(_s106_lines()), 10))
    law = f"S{len(doc.parsed.passages) + 1}"  # law passages follow the document's passages in the context
    llm = StubLLM("**Short answer:** The lease ends on notice [S1][S9].\n\n"
                  "**What your document says:**\n- The document ties notice to the kind of lease [S1].\n\n"
                  "**What the law says:**\n- Section 106 of the Transfer of Property Act, 1882 sets fifteen days' notice "
                  f"for a month-to-month lease [{law}].\n- Section 999 of the Transfer of Property Act, 1882 adds a "
                  f"penalty [{law}].")
    out = analyze(settings, [doc], "ask", "How much notice ends my lease?", llm=llm,
                  law_fn=lambda q: ([s106], [], {"on": "rerank"}), explain=True)
    md = out["answer_markdown"]
    assert "[D1]" in md and "[S1]" in md and f"[{law}]" not in md and "[S9]" not in md and "999" not in md
    assert [c["id"] for c in out["citations"]] == ["D1", "S1"] and [c["kind"] for c in out["citations"]] == ["document", "law"]
    assert out["citations"][1]["locator"] == "s. 106" and "Jurisdiction and date" in md
    assert any("Removed 1 citation" in w for w in out["warnings"]) and out["confidence"] == "low"
    assert "LAW: Transfer of Property Act" in llm.prompts[0] and 'YOUR DOCUMENT "lease.pdf"' in llm.prompts[0]
    assert out["law_checked"] is True and out["explain"]["relabel"][law] == "S1" and out["explain"]["relabel"]["S1"] == "D1"


def test_long_documents_keep_the_opening_and_the_best_matching_passages():
    passages = _pack(_units(parsed_from_fixture("tpa_1882_ss1-3_nested_footnotes").lines), "section")
    assert len(passages) >= 3
    budget = passages[0]["tokens"] + max(p["tokens"] for p in passages[1:])
    chosen, complete = select_passages(passages, budget, "immoveable property definition")
    assert not complete and chosen[0] is passages[0] and len(chosen) < len(passages)
    assert any("immoveable property" in p["text"].lower() for p in chosen[1:])
    assert chosen == sorted(chosen, key=lambda p: p["n"])


def test_locators_follow_the_documents_own_numbers():
    assert _numbers("clause", ["7"]) == "clause 7"
    assert _numbers("clause", ["3.1", "3.2", "3.10"]) == "clauses 3.1-3.10"
    assert _numbers("section", ["6", "1"]) == "sections 6, 1"


def test_long_runs_of_markers_are_cut_to_the_first_three():
    from app.documents.analyze import trim_marker_runs

    text, n = trim_marker_runs("It is an agreement [S1][S2][S3][S4][S5][S6][S7]. Parties [S1-S9]. Price [S2][S4].")
    assert n == 2 and text == "It is an agreement [S1][S2][S3]. Parties [S1][S2][S3]. Price [S2][S4]."


def test_ocr_pieces_on_one_printed_row_are_joined_in_reading_order():
    from app.documents.parse import merge_rows, page_runs
    from app.ocr.windows_ocr import OcrLine

    pieces = [OcrLine("Cancellation by Allottee.", 90, 300, 100.4, 10), OcrLine("7.5", 40, 60, 100, 10),
              OcrLine("The Allottee shall have the right", 40, 330, 114, 10)]
    rows = merge_rows(pieces)
    assert [r.text for r in rows] == ["7.5 Cancellation by Allottee.", "The Allottee shall have the right"]
    assert page_runs([7, 1, 2, 3, 9, 10]) == "1-3, 7, 9-10"


def test_scanned_pages_are_read_with_ocr_and_marked(monkeypatch):
    """A page without a text layer goes to OCR; its passages say so and the upload warns to check figures.
    The OCR engine is stubbed here with the real s. 106 wording (the real engine: tests/integration)."""
    import app.documents.parse as parse
    from app.ocr.windows_ocr import OcrLine

    lines = _s106_lines()
    monkeypatch.setattr(parse, "ocr_language", lambda script: "en-GB")
    monkeypatch.setattr(parse, "ocr_pages", lambda data, pages, lang: {1: [OcrLine(t, 40, 500, 100 + 14 * i, 10)
                                                                           for i, t in enumerate(lines)]})
    monkeypatch.setattr(parse, "parse_pdf", lambda stream, script, **kw: _no_text_layer())
    doc = parse.parse_upload(_pdf([]), 10)
    assert doc.ocr_pages == [1] and doc.unreadable_pages == []
    assert all(p["locator"].endswith("· OCR") for p in doc.passages)
    assert "fifteen days" in " ".join(" ".join(p["text"] for p in doc.passages).split())
    assert any("read with OCR" in w for w in doc.warnings)


def test_an_unreadable_scan_is_refused_with_a_clear_reason(monkeypatch):
    import app.documents.parse as parse
    from app.documents.parse import UploadError

    monkeypatch.setattr(parse, "ocr_language", lambda script: "en-GB")
    monkeypatch.setattr(parse, "ocr_pages", lambda data, pages, lang: {1: []})
    monkeypatch.setattr(parse, "parse_pdf", lambda stream, script, **kw: _no_text_layer())
    try:
        parse.parse_upload(_pdf([]), 10)
        raise AssertionError("expected a 422")
    except UploadError as exc:
        assert exc.status == 422 and "OCR could not recognise" in exc.message


def _no_text_layer():
    from pathlib import Path as _P

    from app.parsing.pdf import PageInfo, ParsedPdf
    return ParsedPdf(path=_P("scan.pdf"), pages=[PageInfo(number=1, text_source="none", usable=False,
                                                          reason="only 0 text-layer characters on an image page")],
                     lines=[], body_size=0.0, page_height=842.0)


def _docx(paragraphs: list[str], heading: str | None = None) -> bytes:
    """A minimal Word .docx (the parts Word needs) whose paragraphs are the given real text."""
    import io
    import zipfile
    from xml.sax.saxutils import escape

    body = ""
    if heading:
        body += f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>{escape(heading)}</w:t></w:r></w:p>'
    body += "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(t)}</w:t></w:r></w:p>" for t in paragraphs)
    body += '<w:p><w:r><w:br w:type="page"/></w:r></w:p><w:p><w:r><w:t>End of document.</w:t></w:r></w:p>'
    parts = {
        "[Content_Types].xml": '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                               '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/document.xml": '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                             f"<w:body>{body}</w:body></w:document>",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, xml in parts.items():
            z.writestr(name, xml)
    return buffer.getvalue()


def test_file_kinds_are_detected_by_content_not_name():
    from app.documents.formats import detect_kind

    assert detect_kind(_pdf(_s106_lines())) == "pdf"
    assert detect_kind(_docx(["x"])) == "docx"
    assert detect_kind(b"\x89PNG\r\n\x1a\n" + b"\0" * 20) == "image" and detect_kind(b"\xff\xd8\xff\xe0" + b"\0" * 20) == "image"
    assert detect_kind(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 20) == "doc"
    assert detect_kind(b"\0\0\0\x18ftypheic" + b"\0" * 20) == "heic"
    assert detect_kind(b"PK\x03\x04 not a docx") is None and detect_kind(b"plain text") is None


def test_word_documents_are_read_in_order_with_headings_and_page_breaks():
    from app.documents.parse import parse_document

    lines = _s106_lines()
    doc = parse_document(_docx(lines, heading="LEASE TERMS"), 10)
    text = " ".join(" ".join(p["text"] for p in doc.passages).split())
    assert "fifteen days" in text and text.index("LEASE TERMS") < text.index("fifteen days")
    assert doc.pages == 2 and doc.ocr_pages == [] and doc.passages[-1]["page_end"] == 2
    assert any(w.startswith("Word document") for w in doc.warnings)


def test_images_are_read_with_ocr(monkeypatch):
    import io

    from PIL import Image

    import app.documents.parse as parse
    from app.ocr.windows_ocr import OcrLine

    lines = _s106_lines()
    monkeypatch.setattr(parse, "ocr_language", lambda script: "en-GB")
    monkeypatch.setattr(parse, "ocr_images", lambda images, lang, dpi=150: {1: [OcrLine(t, 40, 500, 100 + 14 * i, 10)
                                                                                for i, t in enumerate(lines)]})
    buffer = io.BytesIO()
    Image.new("RGB", (800, 1100), "white").save(buffer, format="JPEG")
    doc = parse.parse_document(buffer.getvalue(), 10)
    assert doc.ocr_pages == [1] and all(p["locator"].endswith("· OCR") for p in doc.passages)
    assert any(w.startswith("The image was read with OCR") for w in doc.warnings)


def test_unsupported_files_get_a_clear_reason():
    from app.documents.parse import UploadError, parse_document

    for data, fragment in [(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 64, "old Word .doc"),
                           (b"\0\0\0\x18ftypheic" + b"\0" * 32, "HEIC"), (b"hello", "Word document (.docx)")]:
        try:
            parse_document(data, 10)
            raise AssertionError("expected a refusal")
        except UploadError as exc:
            assert exc.status == 415 and fragment in exc.message
