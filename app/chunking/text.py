"""Shared helpers: join PDF lines into paragraphs, and pack paragraphs into pieces under a token budget without
cutting a sentence (docs/topics/architecture/chunk-schema.md, "Legal-aware chunking")."""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from app.parsing.pdf import Line

log = logging.getLogger(__name__)

_PARA_START = re.compile(r"^(\(\w{1,6}\)|\[\(\w{1,6}\)|Provided|Explanation|Illustrations?\b|“|\[“)")
_ENDS_CLAUSE = re.compile(r"[.:;—–\-\]]\s*$|[.:;]”\s*$")


@dataclass
class Para:
    text: str
    page_start: int
    page_end: int
    number: int | None = None  # judgment paragraph number, when known


def join_lines(texts: list[str]) -> str:
    out = ""
    for t in texts:
        t = t.strip()
        if not t:
            continue
        if not out:
            out = t
        elif out.endswith("-") and len(out) > 1 and out[-2].isalpha() and t[:1].isalpha():
            out += t  # "Inspector-" + "General" -> "Inspector-General"
        else:
            out += " " + t
    return re.sub(r"[ \t]+", " ", out)


def paragraphs(lines: list[Line], indent_step: float = 8.0) -> list[Para]:
    """A new paragraph starts where a line is indented relative to the one before it (India Code's first-line
    indent), or, after a line that closed a clause, where the next line starts a sub-section / proviso /
    Explanation / quoted definition, starts with a bold marginal heading, or sits right of the base margin
    (a first-line indent that crosses a page break)."""
    if not lines:
        return []
    base_x = Counter(round(ln.x0) for ln in lines).most_common(1)[0][0]
    paras: list[Para] = []
    buf: list[Line] = []

    def flush():
        if buf:
            paras.append(Para(join_lines([b.text for b in buf]), buf[0].page, buf[-1].page))
            buf.clear()

    for ln in lines:
        if buf:
            prev = buf[-1]
            indented = ln.x0 > prev.x0 + indent_step and ln.page == prev.page
            closed = bool(_ENDS_CLAUSE.search(prev.text))
            opens = (bool(_PARA_START.match(ln.text)) or bool(ln.bold_prefix)
                     or (ln.x0 >= base_x + 10 and ln.x0 > prev.x0 - 1))
            if indented or (closed and opens):
                flush()
        buf.append(ln)
    flush()
    return paras


_SENTENCE_END = re.compile(r"(?<=[.;:?!])[”\"']?\s+(?=[“\"(A-Z0-9\[])")


def split_sentences(text: str) -> list[str]:
    parts, start = [], 0
    for m in _SENTENCE_END.finditer(text):
        parts.append(text[start:m.start()].rstrip() + text[m.start():m.end()].strip())
        start = m.end()
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


def pack(paras: list[Para], max_tokens: int, count: Callable[[str], int], sep: str = "\n") -> list[list[Para]]:
    """Group consecutive paragraphs into pieces of at most max_tokens. A paragraph that alone exceeds the budget
    is split at sentence boundaries; a single sentence over budget stays whole (never cut mid-sentence) and is
    logged, since bge-m3 still embeds it up to its sequence limit."""
    pieces: list[list[Para]] = []
    cur: list[Para] = []
    cur_tokens = 0
    for p in paras:
        n = count(p.text)
        if n > max_tokens:
            if cur:
                pieces.append(cur)
                cur, cur_tokens = [], 0
            sub, sub_tokens = [], 0
            for s in split_sentences(p.text):
                sn = count(s)
                if sub and sub_tokens + sn > max_tokens:
                    pieces.append([Para(" ".join(sub), p.page_start, p.page_end, p.number)])
                    sub, sub_tokens = [], 0
                if sn > max_tokens:
                    log.warning("single sentence exceeds MAX_CHUNK_TOKENS; kept whole", extra={"tokens": sn})
                sub.append(s)
                sub_tokens += sn
            if sub:
                pieces.append([Para(" ".join(sub), p.page_start, p.page_end, p.number)])
            continue
        if cur and cur_tokens + n > max_tokens:
            pieces.append(cur)
            cur, cur_tokens = [], 0
        cur.append(p)
        cur_tokens += n
    if cur:
        pieces.append(cur)
    return pieces
