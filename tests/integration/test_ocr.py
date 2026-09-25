"""Scanned uploads through the real Windows OCR engine (DECISIONS D55; needs Windows with an English OCR language).

The scan is made here from a real statute PDF already on disk (India Code's Transfer of Property Act): its pages
are rendered to images and saved as an image-only PDF, which is exactly what a scanner produces."""

import io
from pathlib import Path

import pytest

from app.documents.parse import parse_upload
from app.ocr.windows_ocr import ocr_language

pytestmark = pytest.mark.integration
TPA = Path(__file__).parents[2] / "data" / "raw" / "indiacode" / "tpa-1882" / "a1882-04.pdf"


def _image_only(pdf_bytes: bytes, pages: range, dpi: int = 150) -> bytes:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_bytes)
    images = [doc[i].render(scale=dpi / 72, grayscale=True).to_pil() for i in pages]
    buffer = io.BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:], resolution=dpi)
    return buffer.getvalue()


def test_a_scanned_statute_page_is_read_with_ocr():
    if not TPA.exists():
        pytest.skip("run the India Code ingest first")
    if ocr_language("Latn") is None:
        pytest.skip("no English Windows OCR language installed")
    source = TPA.read_bytes()
    import pdfplumber
    with pdfplumber.open(io.BytesIO(source)) as pdf:
        page = next(i for i, p in enumerate(pdf.pages) if "fifteen days" in (p.extract_text() or ""))
    doc = parse_upload(_image_only(source, range(page, page + 1)), 10)
    text = " ".join(" ".join(p["text"] for p in doc.passages).split()).lower()
    assert doc.ocr_pages == [1] and doc.unreadable_pages == []
    assert "fifteen days" in text and "month to month" in text.replace("-", " ")
    assert all(p["locator"].endswith("· OCR") for p in doc.passages)


def test_a_photo_of_a_statute_page_is_read_with_ocr():
    """A JPEG like a phone photo (rendered from the real India Code page), read by the real Windows OCR engine."""
    if not TPA.exists():
        pytest.skip("run the India Code ingest first")
    if ocr_language("Latn") is None:
        pytest.skip("no English Windows OCR language installed")
    import pdfplumber
    import pypdfium2 as pdfium

    from app.documents.parse import parse_document

    source = TPA.read_bytes()
    with pdfplumber.open(io.BytesIO(source)) as pdf:
        index = next(i for i, p in enumerate(pdf.pages) if "fifteen days" in (p.extract_text() or ""))
    photo = io.BytesIO()
    pdfium.PdfDocument(source)[index].render(scale=220 / 72).to_pil().convert("RGB").save(photo, format="JPEG", quality=80)
    doc = parse_document(photo.getvalue(), 10)
    text = " ".join(" ".join(p["text"] for p in doc.passages).split()).lower()
    assert doc.ocr_pages == [1] and "fifteen days" in text
