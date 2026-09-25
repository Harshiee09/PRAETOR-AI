"""Uploaded Word documents and images (DECISIONS D56): detection by content, not by name.

- Word (.docx): the text comes straight from `word/document.xml` (paragraphs in order, tables row by row, Word
  headings kept as headings). Page numbers follow the page breaks Word recorded the last time it laid the document
  out, so they can differ slightly from a printout. List numbers that Word generates are not part of the text and
  are not invented here.
- Images (JPG, PNG, WebP, TIFF, BMP): turned upright from the camera's EXIF orientation, converted to grayscale,
  scaled to at most MAX_SIDE pixels, and read with the Windows OCR engine like scanned PDF pages.
"""

from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree as ET

from app.parsing.pdf import Line

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_SIDE = 4000
IMAGE_DPI = 150  # nominal, only to express OCR positions in points
UNSUPPORTED = ("Upload a PDF, a Word document (.docx) or a photo or scan (JPG, PNG, WebP or TIFF).")


def detect_kind(data: bytes) -> str | None:
    """"pdf", "docx", "image", "doc" (old Word), "heic" or None, from the first bytes."""
    head = data[:16]
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                return "docx" if "word/document.xml" in z.namelist() else None
        except zipfile.BadZipFile:
            return None
    if head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "doc"
    if data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftyphevc", b"ftypheim"):
        return "heic"
    if (head.startswith(b"\x89PNG\r\n\x1a\n") or head.startswith(b"\xff\xd8\xff") or head.startswith(b"BM")
            or head[:4] in (b"II*\x00", b"MM\x00*") or (head[:4] == b"RIFF" and data[8:12] == b"WEBP")):
        return "image"
    return None


def _paragraph(p: ET.Element) -> tuple[str, int]:
    """Text of one paragraph and the number of page breaks inside it."""
    parts, breaks = [], 0
    for el in p.iter():
        tag = el.tag
        if tag == W + "t":
            parts.append(el.text or "")
        elif tag in (W + "tab", W + "cr"):
            parts.append(" ")
        elif tag == W + "br":
            if el.get(W + "type") == "page":
                breaks += 1
            else:
                parts.append(" ")
        elif tag == W + "lastRenderedPageBreak":
            breaks += 1
    return " ".join("".join(parts).split()), breaks


def _is_heading(p: ET.Element) -> bool:
    style = p.find(f"{W}pPr/{W}pStyle")
    value = (style.get(W + "val") if style is not None else "") or ""
    return value.lower().startswith(("heading", "title"))


def word_page_count(data: bytes) -> int | None:
    """The page count Word stored when it last saved the file (docProps/app.xml), if any."""
    import re

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if "docProps/app.xml" not in z.namelist():
            return None
        m = re.search(rb"<Pages>(\d+)</Pages>", z.read("docProps/app.xml"))
    return int(m.group(1)) if m else None


def docx_lines(data: bytes) -> tuple[list[Line], int]:
    """Lines of a .docx in reading order, with Word's last-rendered page numbers; returns (lines, pages)."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    lines: list[Line] = []
    page, order = 1, 0

    def add(text: str, heading: bool = False) -> None:
        nonlocal order
        if text:
            order += 1
            lines.append(Line(text=text, page=page, x0=0.0, x1=0.0, top=float(order), size=11.0,
                              bold_prefix=text if heading else ""))

    for block in list(body) if body is not None else []:
        if block.tag == W + "p":
            text, breaks = _paragraph(block)
            if breaks and not text:
                page += breaks
                continue
            add(text, _is_heading(block))
            page += breaks
        elif block.tag == W + "tbl":
            for row in block.iter(W + "tr"):
                cells = []
                for cell in row.iter(W + "tc"):
                    texts = []
                    for p in cell.iter(W + "p"):
                        text, breaks = _paragraph(p)
                        page += breaks
                        if text:
                            texts.append(text)
                    cells.append(" ".join(texts))
                add(" | ".join(c for c in cells if c))
    return lines, page


def image_pages(data: bytes, max_pages: int) -> dict[int, bytes]:
    """PNG bytes per image frame (1-based), upright, grayscale, longest side <= MAX_SIDE."""
    from PIL import Image, ImageOps

    out: dict[int, bytes] = {}
    with Image.open(io.BytesIO(data)) as img:
        frames = getattr(img, "n_frames", 1)
        for index in range(min(frames, max_pages)):
            img.seek(index)
            frame = ImageOps.exif_transpose(img.copy()).convert("L")
            if max(frame.size) > MAX_SIDE:
                frame.thumbnail((MAX_SIDE, MAX_SIDE))
            buffer = io.BytesIO()
            frame.save(buffer, format="PNG")
            out[index + 1] = buffer.getvalue()
    return out
