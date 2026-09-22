"""PDF text extraction with layout facts the legal splitters need (spec: chunk-schema note, "Parsing rules").

Per line we keep the page, position, dominant font size, the leading bold run (section headings are bold) and the
superscript footnote markers that were lifted out of the text. Noise removed at character level:
- the rotated "India Code" watermark stamped into downloaded Act PDFs (DECISIONS V16);
- superscript footnote markers (`1[State Government]` -> `[State Government]`, marker kept on the line);
- the A-H margin letters printed in Supreme Court Reports pages (judgments only);
- page numbers, and running headers that repeat across pages (judgments only: Act pages carry none, and a
  repeating "STATE AMENDMENT" line near the top of an Act page is content).

A page with almost no text layer but an image, or whose letters are mostly outside the expected script (legacy
non-Unicode fonts), needs OCR. Without Tesseract (DECISIONS D9) such pages are marked unusable, never indexed.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from app.multilingual.script import nfc, script_share
from app.ocr.tesseract import tesseract_available

log = logging.getLogger(__name__)
PARSER_VERSION = "pdf-1"
MIN_LAYER_CHARS = 50
MIN_SCRIPT_SHARE = 0.5
MARGIN_LETTERS = set("ABCDEFGH")


@dataclass
class Line:
    text: str
    page: int
    x0: float
    x1: float
    top: float
    size: float
    bold_prefix: str = ""
    markers: list[str] = field(default_factory=list)


@dataclass
class PageInfo:
    number: int
    text_source: str  # layer | ocr | none
    usable: bool
    reason: str | None = None
    ocr_confidence: float | None = None
    watermark_chars: int = 0
    margin_chars: int = 0


@dataclass
class ParsedPdf:
    path: Path
    pages: list[PageInfo]
    lines: list[Line]
    body_size: float
    page_height: float
    parser_version: str = PARSER_VERSION

    @property
    def unusable_pages(self) -> list[PageInfo]:
        return [p for p in self.pages if not p.usable]


def _is_watermark(obj: dict) -> bool:
    m = obj.get("matrix")
    return obj.get("object_type") == "char" and m is not None and (abs(m[1]) > 0.01 or abs(m[2]) > 0.01)


def _is_bold(ch: dict) -> bool:
    return "bold" in ch.get("fontname", "").lower()


def _dominant(values: list[float]) -> float:
    return Counter(round(v, 1) for v in values).most_common(1)[0][0] if values else 0.0


def _margin_letter_keys(lines: list[dict]) -> set[tuple]:
    """Single A-H letters separated from any neighbour on their line by a wide gap (the SCR margin letters)."""
    keys = set()
    for ln in lines:
        chars = [c for c in ln["chars"] if c["text"].strip()]
        for i, c in enumerate(chars):
            if c["text"] not in MARGIN_LETTERS:
                continue
            left_gap = c["x0"] - chars[i - 1]["x1"] if i > 0 else None
            right_gap = chars[i + 1]["x0"] - c["x1"] if i + 1 < len(chars) else None
            wide = lambda g: g is None or g > 7.0  # noqa: E731
            if wide(left_gap) and wide(right_gap):
                keys.add((round(c["x0"], 1), round(c["top"], 1)))
    return keys


def _line_from(ln: dict, page_no: int, markers: list[str]) -> Line:
    chars = ln["chars"]
    text = nfc(ln["text"].strip())
    # Leading "[" / "*" / quotes (inserted-section brackets, omission marks) are often set in the regular face even
    # when the heading after them is bold, so they don't end the bold run.
    n_bold, n_real = 0, 0
    for ch in chars:
        if not ch["text"].strip():
            continue
        if _is_bold(ch):
            n_real += 1
        elif not (n_real == 0 and ch["text"] in "[*“\"‘"):
            break
        n_bold += 1
    if n_real == 0:
        n_bold = 0
    bold_prefix = ""
    if n_bold:
        seen = 0
        for i, ch in enumerate(text):
            if not ch.isspace():
                seen += 1
            if seen == n_bold:
                bold_prefix = text[: i + 1]
                break
    return Line(text=text, page=page_no, x0=ln["x0"], x1=ln["x1"], top=ln["top"],
                size=_dominant([c["size"] for c in chars]), bold_prefix=bold_prefix, markers=markers)


def _group_markers(marker_chars: list[dict]) -> list[tuple[str, float, float]]:
    """Adjacent small characters form one marker: (text, x0, top)."""
    out: list[list] = []
    for c in sorted(marker_chars, key=lambda c: (round(c["top"]), c["x0"])):
        if out and abs(c["top"] - out[-1][2]) < 2 and c["x0"] - out[-1][3] < 1.5:
            out[-1][0] += c["text"]
            out[-1][3] = c["x1"]
        else:
            out.append([c["text"], c["x0"], c["top"], c["x1"]])
    return [(t.strip(), x0, top) for t, x0, top, _ in out if t.strip()]


def parse_pdf(path: Path, expected_script: str = "Latn", *, drop_margin_letters: bool = False,
              strip_running_headers: bool = False, drop_small_text: bool = False) -> ParsedPdf:
    """drop_small_text: remove text well below body size entirely (judgment footnotes, editor lines) instead of
    treating it as footnote markers."""
    pdf = pdfplumber.open(path)
    try:
        sizes: Counter = Counter()
        for p in pdf.pages:
            for ch in p.chars:
                if not _is_watermark(ch) and ch["text"].strip():
                    sizes[round(ch["size"], 1)] += 1
        body_size = sizes.most_common(1)[0][0] if sizes else 0.0
        marker_max = body_size - 2.4  # 11pt body -> markers <= 8.6pt; 9pt footnote text is kept

        pages: list[PageInfo] = []
        lines: list[Line] = []
        page_height = pdf.pages[0].height if pdf.pages else 0.0
        for page_no, page in enumerate(pdf.pages, 1):
            n_wm = sum(1 for c in page.chars if _is_watermark(c))
            small = [c for c in page.chars if not _is_watermark(c) and c["size"] <= marker_max and c["text"].strip()]
            small_ids = {(round(c["x0"], 1), round(c["top"], 1)) for c in small}
            keep = lambda o, drop=frozenset(): not (  # noqa: E731
                _is_watermark(o)
                or (o.get("object_type") == "char" and (round(o["x0"], 1), round(o["top"], 1)) in small_ids)
                or (o.get("object_type") == "char" and (round(o["x0"], 1), round(o["top"], 1)) in drop)
            )
            raw = page.filter(keep).extract_text_lines(return_chars=True)
            margin: set = set()
            if drop_margin_letters:
                margin = _margin_letter_keys(raw)
                if margin:
                    raw = page.filter(lambda o, d=frozenset(margin): keep(o, d)).extract_text_lines(return_chars=True)

            text = "".join(ln["text"] for ln in raw)
            nonspace = len(re.sub(r"\s", "", text))
            info = PageInfo(number=page_no, text_source="layer", usable=True, watermark_chars=n_wm, margin_chars=len(margin))
            if nonspace < MIN_LAYER_CHARS and page.images:
                info.reason = f"only {nonspace} text-layer characters on an image page"
            elif nonspace >= MIN_LAYER_CHARS and script_share(text, expected_script) < MIN_SCRIPT_SHARE:
                info.reason = f"text layer is not {expected_script} (legacy font or wrong language)"
            if info.reason:
                info.text_source, info.usable = "none", False
                if not tesseract_available():
                    info.reason += "; OCR needed but Tesseract is not installed"
                log.warning("page unusable", extra={"file": str(path), "page": page_no, "reason": info.reason})
                pages.append(info)
                continue
            pages.append(info)

            markers = [] if drop_small_text else _group_markers(small)
            page_lines = []
            for ln in raw:
                if not ln["text"].strip():
                    continue
                own = [m for m, x0, top in markers if ln["top"] - 6 <= top <= ln["bottom"] and ln["x0"] - 12 <= x0 <= ln["x1"] + 4]
                page_lines.append(_line_from(ln, page_no, own))
            lines.extend(page_lines)

        lines = _strip_page_furniture(lines, len(pdf.pages), page_height, strip_running_headers)
        return ParsedPdf(path=path, pages=pages, lines=lines, body_size=body_size, page_height=page_height)
    finally:
        pdf.close()


def _furniture_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", text)).strip().lower()


def _strip_page_furniture(lines: list[Line], n_pages: int, height: float, running_headers: bool) -> list[Line]:
    top_band, bottom_band = 0.16 * height, 0.86 * height
    in_band = lambda ln: ln.top < top_band or ln.top > bottom_band  # noqa: E731
    repeated: set[str] = set()
    if running_headers and n_pages >= 3:
        pages_by_key: dict[str, set[int]] = {}
        for ln in lines:
            if in_band(ln):
                pages_by_key.setdefault(_furniture_key(ln.text), set()).add(ln.page)
        threshold = max(2, int(0.25 * n_pages))
        repeated = {k for k, pages in pages_by_key.items() if len(pages) >= threshold and k.strip("# ")}
    kept = []
    for ln in lines:
        if in_band(ln) and re.fullmatch(r"\d{1,4}", ln.text.strip()):
            continue  # page number
        if in_band(ln) and _furniture_key(ln.text) in repeated:
            continue
        kept.append(ln)
    return kept
