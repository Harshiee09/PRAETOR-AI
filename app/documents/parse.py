"""An uploaded PDF -> numbered passages with page and clause locators (DECISIONS D50).

Reuses the corpus PDF parser (text layer only; pages that would need OCR are reported, never guessed). Passages
follow the document's own numbering where it has one ("3.", "3.2", "Clause 7", "Article 4", judgment "12."), so a
citation card can say "clause 7 · p. 2"; unnumbered text is packed by page. Nothing here is written to disk.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from io import BytesIO

import pdfplumber

from app.multilingual.script import dominant_script, nfc
from app.documents.formats import IMAGE_DPI, UNSUPPORTED, detect_kind, docx_lines, image_pages, word_page_count
from app.ocr.engine import MIN_PAGE_CHARS, OcrLine, OcrUnavailable, ocr_images, ocr_language, ocr_pages
from app.parsing.pdf import Line, parse_pdf

PASSAGE_WORDS = 200
PREFIXED = re.compile(r"^\s*(?:clause|article|para(?:graph)?)\s+(?P<num>\d{1,3}(?:\.\d{1,2}){0,3})\b", re.I)
NUMBERED = re.compile(r"^\s*\[?(?P<num>\d{1,2}(?:\.\d{1,2}){1,3}\.?|\d{1,3}[.)])\s+\S")
ACT_TITLE = re.compile(r"\b(?:Act|Code|Sanhita|Adhiniyam),?\s+\d{4}\b", re.I)
AGREEMENT = re.compile(r"\b(?:agreement|lease|licen[cs]e|contract|deed|policy|terms and conditions|undertaking)\b", re.I)


class UploadError(ValueError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass
class ParsedUpload:
    sha256: str
    pages: int
    unreadable_pages: list[int]
    passages: list[dict]
    words: int
    script: str
    warnings: list[str] = field(default_factory=list)
    ocr_pages: list[int] = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    """Upper-side estimate for the answer model's window (no tokenizer load: the bge-m3 tokenizer is not the
    model's, and loading models is what this path avoids)."""
    wide = sum(1 for ch in text if ord(ch) > 0x2FF)  # Indic scripts take far more tokens per character
    return int(max(len(text.split()) * 1.5, (len(text) - wide) / 3.2 + wide / 1.5)) + 1


def _clause_number(line: str) -> str | None:
    m = PREFIXED.match(line) or NUMBERED.match(line)
    return m.group("num").rstrip(".)") if m else None


def _is_heading(line) -> bool:
    t = line.text.strip()
    n = len(t.split())
    if not t or n > 12 or t.endswith((",", ";")):
        return False
    return (line.bold_prefix.strip() == t) or (t.isupper() and n <= 10 and sum(c.isalpha() for c in t) >= 4)


def _units(lines) -> list[dict]:
    """Consecutive lines grouped under a clause number or heading."""
    units: list[dict] = []
    cur: dict | None = None
    for ln in lines:
        text = nfc(ln.text).strip()
        if not text:
            continue
        num = _clause_number(text)
        if cur is None or num or _is_heading(ln):
            cur = {"num": num, "lines": []}
            units.append(cur)
        cur["lines"].append((text, ln.page))
    return units


def _key(num: str) -> tuple[int, ...]:
    return tuple(int(x) for x in num.split("."))


def _numbers(label: str, nums: list[str]) -> str:
    """"clause 7", "clauses 3-5", or "clauses 6, 1" when the numbers do not run in order (footnotes, schedules)."""
    if len(nums) == 1:
        return f"{label} {nums[0]}"
    if all(_key(a) < _key(b) for a, b in zip(nums, nums[1:])):
        return f"{label}s {nums[0]}-{nums[-1]}"
    return f"{label}s " + ", ".join(nums[:3]) + (" …" if len(nums) > 3 else "")


def document_label(lines: list[str]) -> str:
    """What the document's numbers are called: "section" in an Act, "clause" in an agreement, else "para"."""
    head, title = " ".join(lines[:40]), " ".join(lines[:6])
    if "ARRANGEMENT OF SECTIONS" in head.upper() or (ACT_TITLE.search(title) and not AGREEMENT.search(title)):
        return "section"
    return "clause" if AGREEMENT.search(head) else "para"


def page_runs(pages: list[int]) -> str:
    """[1, 2, 3, 7] -> "1-3, 7"."""
    runs, start = [], None
    pages = sorted(set(pages))
    for i, pg in enumerate(pages):
        start = pg if start is None else start
        if i + 1 == len(pages) or pages[i + 1] != pg + 1:
            runs.append(str(start) if start == pg else f"{start}-{pg}")
            start = None
    return ", ".join(runs)


def merge_rows(lines: list[OcrLine]) -> list[OcrLine]:
    """OCR splits one printed line into pieces when there is a wide gap ("7.5" and its text): join pieces whose
    vertical extents overlap by more than half the smaller height, left to right, top to bottom."""
    rows: list[list[OcrLine]] = []
    for line in sorted(lines, key=lambda ln: (ln.top, ln.x0)):
        for row in rows:
            ref = row[0]
            overlap = min(ref.top + ref.size, line.top + line.size) - max(ref.top, line.top)
            if overlap > 0.5 * min(ref.size, line.size):
                row.append(line)
                break
        else:
            rows.append([line])
    merged = []
    for row in rows:
        row.sort(key=lambda ln: ln.x0)
        merged.append(OcrLine(text=" ".join(ln.text.strip() for ln in row), x0=row[0].x0, x1=max(ln.x1 for ln in row),
                              top=min(ln.top for ln in row), size=max(ln.size for ln in row)))
    return sorted(merged, key=lambda ln: ln.top)


def _pack(units: list[dict], label: str, ocr: frozenset[int] = frozenset()) -> list[dict]:
    """Units -> passages of about PASSAGE_WORDS words; a long unit is split at line boundaries."""
    pieces: list[dict] = []
    for u in units:
        part, words = [], 0
        for text, page in u["lines"]:
            n = len(text.split())
            if part and words + n > PASSAGE_WORDS:
                pieces.append({"nums": [u["num"]] if u["num"] else [], "lines": part})
                part, words = [], 0
            part.append((text, page))
            words += n
        if part:
            pieces.append({"nums": [u["num"]] if u["num"] else [], "lines": part})
    passages: list[dict] = []
    cur = None
    for p in pieces:
        n = sum(len(t.split()) for t, _ in p["lines"])
        if cur is not None and cur["words"] + n <= PASSAGE_WORDS:
            cur["nums"] += [x for x in p["nums"] if x not in cur["nums"]]
            cur["lines"] += p["lines"]
            cur["words"] += n
        else:
            cur = {"nums": list(p["nums"]), "lines": list(p["lines"]), "words": n}
            passages.append(cur)
    out = []
    for i, p in enumerate(passages, 1):
        pages = [pg for _, pg in p["lines"]]
        ps, pe = min(pages), max(pages)
        where = f"p. {ps}" if ps == pe else f"pp. {ps}-{pe}"
        nums = p["nums"]
        loc = f"{_numbers(label, nums)} · {where}" if nums else where
        if ocr & set(range(ps, pe + 1)):
            loc += " · OCR"  # read from a scanned page: the card says so
        text = "\n".join(t for t, _ in p["lines"])
        out.append({"n": i, "locator": loc, "page_start": ps, "page_end": pe, "text": text,
                    "tokens": estimate_tokens(text)})
    return out


OCR_WARNING = ("{what} read with OCR. OCR can misread words and figures: check amounts, dates and "
               "names against the original.")


def parse_document(data: bytes, max_pages: int, ocr_max_pages: int = 40) -> ParsedUpload:
    """Any supported upload: PDF (text layer, or OCR for scanned pages), Word .docx, or a photo/scan image."""
    kind = detect_kind(data)
    if kind == "pdf":
        return parse_upload(data, max_pages, ocr_max_pages)
    if kind == "docx":
        return _parse_docx(data, max_pages)
    if kind == "image":
        return _parse_image(data, ocr_max_pages)
    if kind == "doc":
        raise UploadError(415, "this is an old Word .doc file: open it in Word and save it as .docx or PDF, then "
                               "upload that")
    if kind == "heic":
        raise UploadError(415, "iPhone HEIC photos cannot be read here: export the photo as JPG (or set the camera to "
                               "Most Compatible) and upload that")
    raise UploadError(415, UNSUPPORTED)


def _finish(data: bytes, lines: list, pages: int, script: str, warnings: list[str], ocr: list[int],
            unreadable: list[int] | None = None) -> ParsedUpload:
    passages = _pack(_units(lines), document_label([ln.text for ln in lines]), frozenset(ocr))
    return ParsedUpload(sha256=hashlib.sha256(data).hexdigest(), pages=pages, unreadable_pages=unreadable or [],
                        passages=passages, words=sum(len(p["text"].split()) for p in passages), script=script,
                        warnings=warnings, ocr_pages=ocr)


def _parse_docx(data: bytes, max_pages: int) -> ParsedUpload:
    try:
        lines, pages = docx_lines(data)
    except Exception as exc:  # noqa: BLE001 — damaged or password-protected files raise many zip/XML errors
        raise UploadError(422, f"the Word document could not be read ({type(exc).__name__}); if it is "
                               "password-protected, remove the password and upload it again") from exc
    if pages > max_pages:
        raise UploadError(413, f"the document has about {pages} pages; the limit is {max_pages} (DOC_MAX_PAGES)")
    if not lines:
        raise UploadError(422, "the Word document has no text (it may contain only pictures): save it as PDF and "
                               "upload that, so its pages can be read with OCR")
    lines = [Line(text=nfc(ln.text), page=ln.page, x0=ln.x0, x1=ln.x1, top=ln.top, size=ln.size,
                  bold_prefix=nfc(ln.bold_prefix)) for ln in lines]
    script = dominant_script(" ".join(ln.text for ln in lines[:200]))[0] or "Latn"
    recorded = word_page_count(data)
    if recorded and recorded != pages:
        warnings = [f"Word document: Word recorded {recorded} pages but only {pages} page breaks are marked in the "
                    "file, so page numbers here are approximate; use the clause or paragraph text to find a passage."]
    else:
        warnings = ["Word document: page numbers follow Word's own layout of this file and can differ slightly from "
                    "a printout."]
    return _finish(data, lines, pages, script, warnings, [])


def _parse_image(data: bytes, ocr_max_pages: int) -> ParsedUpload:
    try:
        images = image_pages(data, max(1, ocr_max_pages))
    except Exception as exc:  # noqa: BLE001 — truncated or unusual image files
        raise UploadError(422, f"the image could not be opened ({type(exc).__name__}); upload it again as JPG or "
                               "PNG") from exc
    language = ocr_language("Latn")
    if not language:
        raise UploadError(422, "images are read with OCR, and no OCR engine with English is available on this "
                               "server")
    try:
        recognised = ocr_images(images, language, dpi=IMAGE_DPI)
    except OcrUnavailable as exc:
        raise UploadError(422, f"the image could not be read: {exc}") from exc
    lines, done = [], []
    for number in sorted(images):
        rows = merge_rows(recognised.get(number, []))
        if sum(len(row.text.strip()) for row in rows) >= MIN_PAGE_CHARS:
            lines += [Line(text=nfc(row.text), page=number, x0=row.x0, x1=row.x1, top=row.top, size=row.size)
                      for row in rows]
            done.append(number)
    if not lines:
        raise UploadError(422, "no readable text in the image: photograph the page straight on, in good light, with "
                               "the whole page in view, or upload a PDF")
    what = "The image was" if len(images) == 1 else f"Images {page_runs(done)} were"
    unreadable = [n for n in images if n not in done]
    warnings = [OCR_WARNING.format(what=what)]
    if unreadable:
        warnings.append(f"Images {page_runs(unreadable)} have no readable text and were left out.")
    return _finish(data, lines, len(images), "Latn", warnings, done, unreadable)


def parse_upload(data: bytes, max_pages: int, ocr_max_pages: int = 40) -> ParsedUpload:
    if not data.startswith(b"%PDF-"):
        raise UploadError(415, UNSUPPORTED)
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            n_pages = len(pdf.pages)
            if n_pages > max_pages:
                raise UploadError(413, f"the PDF has {n_pages} pages; the limit is {max_pages} (DOC_MAX_PAGES)")
            sample = " ".join((p.extract_text() or "") for p in pdf.pages[:3])
        script = dominant_script(sample)[0] or "Latn"
        parsed = parse_pdf(BytesIO(data), script, strip_running_headers=True)
    except UploadError:
        raise
    except Exception as exc:  # noqa: BLE001 — encrypted or damaged files; the parser's own error types vary
        raise UploadError(422, f"the PDF could not be read ({type(exc).__name__}); if it is password-protected, "
                               "remove the password and upload it again") from exc
    unusable = [p.number for p in parsed.unusable_pages]
    lines = list(parsed.lines)
    warnings: list[str] = []
    done: list[int] = []
    language = ocr_language(script) if unusable else None
    todo = unusable[:max(0, ocr_max_pages)] if language else []
    if todo:
        try:
            recognised = ocr_pages(data, todo, language)
        except OcrUnavailable as exc:
            recognised = {}
            warnings.append(f"OCR could not run ({exc}), so the scanned pages were left out.")
        for number in todo:
            rows = merge_rows(recognised.get(number, []))
            if sum(len(row.text.strip()) for row in rows) >= MIN_PAGE_CHARS:
                lines += [Line(text=nfc(row.text), page=number, x0=row.x0, x1=row.x1, top=row.top, size=row.size)
                          for row in rows]
                done.append(number)
        lines.sort(key=lambda ln: ln.page)  # stable: reading order within each page is kept
    unreadable = [n for n in unusable if n not in done]
    if not lines:
        if unusable and not language:
            raise UploadError(422, "no readable text: the pages look scanned, and no OCR language for this script is "
                                   "installed here. Upload a PDF with selectable text.")
        raise UploadError(422, "no readable text: the pages look scanned and OCR could not recognise text on them. "
                               "Rescan clearly (300 dpi, straight, good contrast) or upload a PDF with selectable text.")
    passages = _pack(_units(lines), document_label([ln.text for ln in lines]), frozenset(done))
    if done:
        warnings.append(f"Page{'s' if len(done) > 1 else ''} {page_runs(done)} had no text layer (scanned) and "
                        f"{'were' if len(done) > 1 else 'was'} read with OCR. OCR can misread words "
                        "and figures: check amounts, dates and names against the original.")
    if unreadable:
        why = (f" (only the first {ocr_max_pages} scanned pages are read)" if len(unusable) > len(todo) and language
               else "")
        warnings.append(f"Pages {page_runs(unreadable)} have no readable text{why} and were left out; answers cannot "
                        "draw on them.")
    return ParsedUpload(sha256=hashlib.sha256(data).hexdigest(), pages=n_pages, unreadable_pages=unreadable,
                        passages=passages, words=sum(len(p["text"].split()) for p in passages), script=script,
                        warnings=warnings, ocr_pages=done)
