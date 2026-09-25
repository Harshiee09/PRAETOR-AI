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
from app.parsing.pdf import parse_pdf

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


def _pack(units: list[dict], label: str) -> list[dict]:
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
        text = "\n".join(t for t, _ in p["lines"])
        out.append({"n": i, "locator": loc, "page_start": ps, "page_end": pe, "text": text,
                    "tokens": estimate_tokens(text)})
    return out


def parse_upload(data: bytes, max_pages: int) -> ParsedUpload:
    if not data.startswith(b"%PDF-"):
        raise UploadError(415, "only PDF files are accepted (the file does not start with %PDF-)")
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
    unreadable = [p.number for p in parsed.unusable_pages]
    if not parsed.lines:
        raise UploadError(422, "no readable text layer: this looks like a scanned PDF, and OCR (Tesseract) is not "
                               "installed, so its text cannot be read. Upload a PDF with selectable text.")
    passages = _pack(_units(parsed.lines), document_label([ln.text for ln in parsed.lines]))
    warnings = []
    if unreadable:
        warnings.append(f"Pages {', '.join(map(str, unreadable))} have no readable text (scanned or unusual fonts) and "
                        "were left out; answers cannot draw on them.")
    return ParsedUpload(sha256=hashlib.sha256(data).hexdigest(), pages=n_pages, unreadable_pages=unreadable,
                        passages=passages, words=sum(len(p["text"].split()) for p in passages), script=script,
                        warnings=warnings)
