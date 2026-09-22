"""Deterministic citation validator, v1 (spec: docs/topics/legal/grounding-and-citations.md).

v1 covers what Phase 1 requires:
- `[S#]` markers resolve only through this request's S# -> chunk map; unknown IDs are stripped and logged as
  `invalid_citation`. Variants like `[S1, S3]`, `[S1-S3]`, `[s2]` are normalised first.
- A quotation in the answer (text in double quotes, 15+ characters) must be a verbatim substring (whitespace and
  quote-style normalised) of a chunk cited in the same sentence, or of any context chunk if the sentence cites none.
  Otherwise the sentence is removed and a warning added (`unverified_quote`).
- Citation cards are built from chunk metadata only; each card's `quote` is cut from the chunk text in code.
- A cited chunk whose status is `repealed` adds a deterministic warning naming the successor.
The authority-string scan (sections, case names, reporter citations) and the unsupported-sentence check come in
Phase 2 (full validator).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.llm.extractive import excerpt

log = logging.getLogger(__name__)

MARKER = re.compile(r"\[\s*[Ss]\s*(\d{1,3})\s*\]")
GROUP = re.compile(r"\[\s*[Ss]\s*\d{1,3}(?:\s*(?:,|;|-|–|and)\s*[Ss]?\s*\d{1,3})+\s*\]")
QUOTE = re.compile(r"[“\"]([^”\"]{15,})[”\"]")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"(\[*-])|\n+")
QUOTE_CHARS = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


@dataclass
class ValidationResult:
    text: str
    used_ids: list[str]
    invalid_ids: list[str] = field(default_factory=list)
    unverified_quotes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.invalid_ids or self.unverified_quotes)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.translate(QUOTE_CHARS)).strip().lower()


def _expand_group(m: re.Match) -> str:
    inner = m.group(0)[1:-1]
    parts = re.split(r"\s*(?:,|;|and)\s*", inner)
    out = []
    for p in parts:
        rng = re.match(r"[Ss]?\s*(\d+)\s*[-–]\s*[Ss]?\s*(\d+)$", p.strip())
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            out += [f"[S{i}]" for i in range(a, b + 1)] if 0 < b - a < 10 else [f"[S{a}]", f"[S{b}]"]
        else:
            n = re.sub(r"\D", "", p)
            if n:
                out.append(f"[S{n}]")
    return "".join(out)


def validate(answer: str, id_map: dict[str, dict], statutes: dict[str, dict] | None = None) -> ValidationResult:
    """id_map: "S1" -> chunk dict (the only thing a citation can resolve to)."""
    text = GROUP.sub(_expand_group, answer)
    invalid: list[str] = []

    def keep_or_strip(m: re.Match) -> str:
        sid = f"S{int(m.group(1))}"
        if sid in id_map:
            return f"[{sid}]"
        invalid.append(sid)
        return ""

    text = MARKER.sub(keep_or_strip, text)
    for sid in invalid:
        log.warning("invalid_citation", extra={"sid": sid})

    # quotes: check per sentence against the chunks that sentence cites
    unverified: list[str] = []
    kept_parts: list[str] = []
    pos = 0
    pieces = []
    for m in SENTENCE.finditer(text):
        pieces.append((text[pos:m.start()], text[m.start():m.end()]))
        pos = m.end()
    pieces.append((text[pos:], ""))
    for sentence, sep in pieces:
        cited = [f"S{int(n)}" for n in MARKER.findall(sentence)]
        pool = [id_map[s]["text"] for s in cited if s in id_map] or [c["text"] for c in id_map.values()]
        bad = [q for q in QUOTE.findall(sentence) if not any(_norm(q) in _norm(t) for t in pool)]
        if bad:
            unverified.extend(bad)
            log.warning("unverified_quote", extra={"quote": bad[0][:80]})
            continue
        kept_parts.append(sentence + sep)
    text = "".join(kept_parts)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    used = list(dict.fromkeys(f"S{int(n)}" for n in MARKER.findall(text)))
    warnings = []
    if invalid:
        warnings.append(f"Removed {len(invalid)} citation(s) to sources that were not provided: {', '.join(sorted(set(invalid)))}.")
    if unverified:
        warnings.append(f"Removed {len(unverified)} sentence(s) whose quotation did not match the cited source word for word.")
    for sid in used:
        c = id_map[sid]
        if c.get("status") == "repealed":
            succ = (statutes or {}).get(c.get("successor") or "", {}).get("short_title") or c.get("successor") or "a successor law"
            warnings.append(f"[{sid}] {c.get('act_title') or c.get('title')} is repealed; it was replaced by {succ}. "
                            "It may still govern events or proceedings from before the repeal.")
    return ValidationResult(text=text, used_ids=used, invalid_ids=invalid, unverified_quotes=unverified, warnings=warnings)


def citation_card(sid: str, c: dict) -> dict:
    """Rendered from metadata only. `quote` is cut from the stored text in code, so it is verbatim by construction."""
    quote = excerpt(c["text"], 300).rstrip(" …")
    if quote not in re.sub(r"\s+", " ", c["text"]):
        raise ValueError(f"citation quote for {c['chunk_id']} is not a verbatim substring of its chunk")
    card = {"id": sid, "chunk_id": c["chunk_id"], "title": c["title"], "locator": c["locator"],
            "authority": c["authority"], "jurisdiction": c["jurisdiction"], "status": c["status"],
            "source_url": c["source_url"], "retrieved_at": (c["retrieved_at"] or "")[:10], "quote": quote}
    if c["doc_type"] == "judgment":
        card.update(court=c.get("court"), decision_date=c.get("decision_date"), citation=c.get("citation"))
    if c["doc_type"] == "statute":
        card.update(section_heading=c.get("section_heading"))
    return card
