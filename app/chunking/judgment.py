"""Split Supreme Court Reports (SCR) judgment PDFs into a case-header chunk plus groups of numbered paragraphs.

Built against the SCR PDFs in the AWS Open Data bucket (fixtures in tests/fixtures/). Two layouts occur:
- older SCR (to ~2023): headnotes, counsel, then "The Judgment of the Court was delivered by"; paragraphs
  `1. ...` with a first-line indent; A-H margin letters (removed by the parser);
- Digital SCR (2024+): headnotes, "Judgment / Order of the Supreme Court", the judge's name, then paragraphs with
  hanging numbers; ends with "Result of the case" and "Headnotes prepared by".
Headnotes, case-law lists and counsel are editorial or not the court's reasoning, so indexing starts at the
judgment itself. The header chunk is rendered from the dataset record (text_source = metadata), never from text.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.chunking.text import Para, join_lines
from app.parsing.pdf import Line, ParsedPdf

log = logging.getLogger(__name__)

BODY_MARKERS = [
    re.compile(r"Judgment\s*/\s*Order\s+of\s+the\s+Supreme\s+Court", re.I),
    re.compile(r"\b(Judgments?|Orders?)\s+of\s+the\s+Court\s+(was|were)\s+(delivered|passed|pronounced)", re.I),
    re.compile(r"\bfollowing\s+(Judgments?|Orders?)\s+(of\s+the\s+Court\s+)?(was|were)\s+(delivered|passed|pronounced)", re.I),
]
JUDGE_THEN_PARA = re.compile(r"^(?P<judge>[A-Z][\w.\s'’-]{2,60},\s*(?:C\.\s*)?J\.)\s+(?P<rest>1\.\s+\S.*)$")
SENTENCE_END = re.compile(r"[.:;”\"?)\]]\s*$")
END_MARKER = re.compile(r"^(Result\s+of\s+the\s+case|†?\s*Headnotes?\s+prepared\s+by)", re.I)
# "12. The ...", "7.1 The ...", and "2.At the heart ..." (no space after the number, common in some judgments)
PARA_NUM = re.compile(r"^(?P<num>\d{1,3})\.(?:(?P<sub>\d{1,2})\.?)?(?:\s+\S|(?=[A-Z“\"‘(\[]))")
JUDGE_LINE = re.compile(r"^\(?[A-Z][\w.\s'’-]{2,60},\s*(?:C\.\s*)?J\.?\)?:?$|^\(?[A-Z. ]{4,60},\s*(?:C\.\s*)?JJ?\.\)?:?$")


@dataclass
class JudgmentParse:
    paras: list[Para]
    opinions: int
    body_start_page: int | None


def find_body(lines: list[Line]) -> tuple[int, int]:
    """(start, end) indices of the judgment proper."""
    start = None
    for i, ln in enumerate(lines):
        window = ln.text if i + 1 >= len(lines) else ln.text + " " + lines[i + 1].text
        if any(p.search(ln.text) or p.search(window) for p in BODY_MARKERS):
            start = i + 1
            if not any(p.search(ln.text) for p in BODY_MARKERS):
                start = i + 2  # marker wrapped over two lines
            break
    if start is None:
        # Fallback: the first "1." paragraph preceded by a judge line ("X, J.") after page 1.
        for i, ln in enumerate(lines):
            if ln.page > 1 and PARA_NUM.match(ln.text) and PARA_NUM.match(ln.text).group("num") == "1" and i > 0 \
                    and any(JUDGE_LINE.match(lines[j].text.strip()) for j in range(max(0, i - 3), i)):
                start = i
                break
    if start is None:
        raise ValueError("could not find where the judgment text begins (no 'delivered by' / 'Judgment / Order' marker)")
    end = next((j for j in range(start, len(lines)) if END_MARKER.match(lines[j].text.strip())), len(lines))
    return start, end


def split_judgment(doc: ParsedPdf) -> JudgmentParse:
    """Numbered paragraphs are found by sequence, not position: page margins differ between odd and even pages,
    indented quotations share the paragraph indent, and some older PDFs carry an OCR text layer with irregular
    positions. A line starts paragraph n when n is the next number (one skipped number is tolerated so a single
    miss can't derail the rest) or a sub-number n.k of the current one, and the previous line ended a sentence or
    the page changed. Quoted material rarely carries exactly the next number, and never passes as a sub-number."""
    start, end = find_body(doc.lines)
    body = doc.lines[start:end]
    if not body:
        raise ValueError("judgment body is empty")

    paras: list[Para] = []
    buf: list[Line] = []
    cur_num: int | None = None
    last_top = 0
    opinions = 1

    def flush():
        if buf:
            paras.append(Para(join_lines([b.text for b in buf]), buf[0].page, buf[-1].page, cur_num))
            buf.clear()

    for i, ln in enumerate(body):
        text = ln.text.strip()
        jm = JUDGE_THEN_PARA.match(text) if last_top == 0 else None
        if jm:  # "A. M. KHANWILKAR, J. 1. This appeal ..." on one line
            buf.append(Line(jm.group("judge"), ln.page, ln.x0, ln.x1, ln.top, ln.size))
            text = jm.group("rest")
            ln = Line(text, ln.page, ln.x0, ln.x1, ln.top, ln.size, ln.bold_prefix, ln.markers)
        m = PARA_NUM.match(text)
        prev = body[i - 1] if i > 0 else None
        boundary = jm is not None or prev is None or prev.page != ln.page or bool(SENTENCE_END.search(prev.text)) \
            or bool(JUDGE_LINE.match(prev.text.strip()))
        if m and boundary:
            n = int(m.group("num"))
            sub = m.group("sub")
            is_next = not sub and last_top < n <= last_top + 2
            is_sub = sub is not None and n == last_top
            first = last_top == 0 and n in (1, 2)  # para 1 is sometimes unnumbered ("Leave granted.")
            new_opinion = n == 1 and last_top > 1 and any(JUDGE_LINE.match(body[j].text.strip()) for j in range(max(0, i - 3), i))
            if (is_next and last_top > 0) or is_sub or first or new_opinion:
                flush()
                if new_opinion:
                    opinions += 1
                last_top = n
                cur_num = n + (opinions - 1) * 1000  # keep numbers unique across opinions
                buf.append(ln)
                continue
        # Sub-paragraphs (indented first line after a sentence end, or a page turn after a sentence end) stay under
        # the current number but become their own unit, so packed pieces carry accurate page ranges.
        if buf and SENTENCE_END.search(buf[-1].text) and (
                ln.page != buf[-1].page or ln.x0 > buf[-1].x0 + 8):
            flush()
        buf.append(ln)
    flush()
    return JudgmentParse(paras=paras, opinions=opinions, body_start_page=body[0].page)


def para_label(nums: list[int]) -> tuple[int | None, int | None, str | None]:
    """(para_start, para_end, locator) for a group of paragraph numbers (opinion offset of 1000 per opinion)."""
    real = sorted({n for n in nums if n is not None})
    if not real:
        return None, None, None
    lo, hi = real[0], real[-1]
    opinion = lo // 1000 + 1
    a, b = lo % 1000, hi % 1000
    loc = f"para {a}" if a == b else f"paras {a}-{b}"
    if opinion > 1 or hi // 1000 != lo // 1000:
        loc += f" (opinion {opinion})"
    return a, b, loc


def header_text(meta: dict) -> str:
    judges = ", ".join(meta.get("judges") or [])
    lines = [meta["case_title"], f"{meta['court']} — decided {meta['decision_date']}"]
    if judges:
        lines.append(f"Bench: {judges}" + (f" (author: {meta['author_judge']})" if meta.get("author_judge") else ""))
    cites = "; ".join(x for x in [meta.get("citation"), meta.get("neutral_citation")] if x)
    if cites:
        lines.append(f"Citation: {cites}")
    if meta.get("disposal_nature"):
        lines.append(f"Disposal: {meta['disposal_nature']}")
    if meta.get("cnr"):
        lines.append(f"CNR: {meta['cnr']}")
    return "\n".join(lines)
