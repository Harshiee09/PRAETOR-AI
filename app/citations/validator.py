"""Deterministic citation validator (spec: docs/topics/legal/grounding-and-citations.md).

1. `[S#]` markers resolve only through this request's S# -> chunk map; unknown IDs are stripped (`invalid_citation`).
   Variants like `[S1, S3]`, `[S1-S3]`, `[s2]` are normalised first.
2. Authority scan: section references (`Section 23`, `s. 23`, `ss. 24 to 26`, `धारा 23`, `Order XXXIX`), Act titles with
   years, case names (`X v. Y`), and reporter citations (`(2020) 8 SCC 129`, `AIR 1956 SC 35`, `[2021] 11 S.C.R. 1181`,
   `2021 INSC 836`) must appear in the text or metadata of the chunks the sentence cites (all context chunks when it
   cites none). Otherwise the sentence is removed (`unverified_authority`).
3. Quotations (15+ characters in double quotes) must be verbatim in a cited chunk; otherwise the sentence is removed.
4. Sentences under "What the sources say" without a marker are flagged (`unsupported`); the pipeline regenerates once
   when more than 20% are flagged, then falls back to the extractive answer.
5. A cited chunk that is repealed adds a deterministic warning naming the successor.
6. Citation cards are built from metadata only; each card's `quote` is cut from the chunk text in code.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import regex

from app.llm.extractive import excerpt

log = logging.getLogger(__name__)

MARKER = re.compile(r"\[\s*[Ss]\s*(\d{1,3})\s*\]")
GROUP = re.compile(r"\[\s*[Ss]\s*\d{1,3}(?:\s*(?:,|;|-|–|and)\s*[Ss]?\s*\d{1,3})+\s*\]")
QUOTE = re.compile(r"[“\"]([^”\"]{15,})[”\"]")
# Sentence boundary, but never right after legal abbreviations ("X v. State", "s. 23", "No. 5", "Ltd.", initials),
# or a case name would be cut in two and escape the authority scan.
SENTENCE = regex.compile(
    r"(?<!\b(?:v|vs|s|ss|No|Nos|Ltd|Pvt|Co|Corpn|Mr|Mrs|Ms|Dr|Smt|Shri|Art|Arts|cl|r|rr|O|Or|Sec|Secs|para|paras|"
    r"p|pp|viz|etc|ors|anr|Ors|Anr|i\.e|e\.g|[A-Z])\.)(?<=[.!?])\s+(?=[A-Z“\"(\[*-])|\n+")
QUOTE_CHARS = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
HEADING = re.compile(r"^\s*(\*\*[^*\n]{2,60}\*\*:?)")

SECTION_MENTION = regex.compile(
    r"(?:\b(?:sections?|secs?\.|ss?\.|u/s\.?)\s*|धारा\s*)"
    r"(?P<nums>\d{1,3}[A-Z]{0,2}(?:\s*\(\w{1,4}\))*(?:\s*(?:,|and|to|&|-|–|or)\s*\d{1,3}[A-Z]{0,2}(?:\s*\(\w{1,4}\))*)*)",
    regex.I)
ORDER_MENTION = regex.compile(r"\bOrder\s+(?P<order>[IVXLC]+)\b")
CASE_NAME = regex.compile(
    r"\b(?P<a>[A-Z][\w.&'’-]*(?:\s+(?:of|and|&|the|[A-Z][\w.&'’-]*)){0,6})\s+(?:v\.|vs\.?|versus)\s+"
    r"(?P<b>[A-Z][\w.&'’-]*(?:\s+(?:of|and|&|the|[A-Z][\w.&'’-]*)){0,6})")
REPORTER = [regex.compile(p, regex.I) for p in (
    r"\(\d{4}\)\s*\d+\s*SCC\s*\d+", r"\bAIR\s*\d{4}\s*SC\s*\d+", r"\[\d{4}\]\s*\d+\s*S\.?\s?C\.?\s?R\.?\s*\d+",
    r"\b\d{4}\s*INSC\s*\d+", r"\b\d{4}\s*SCC\s*OnLine\s*\w+\s*\d+")]
ACT_WITH_YEAR = regex.compile(r"\b(?P<name>(?:[A-Z][\w()]*\s+){1,9}(?:Act|Code|Sanhita|Adhiniyam)),?\s*(?P<year>1[89]\d\d|20[0-4]\d)\b")
STOP_PARTY = {"the", "state", "union", "of", "and", "ors", "anr", "others", "another", "india", "m/s", "mr", "smt", "shri"}


@dataclass
class ValidationResult:
    text: str
    used_ids: list[str]
    invalid_ids: list[str] = field(default_factory=list)
    unverified_quotes: list[str] = field(default_factory=list)
    unverified_authority: list[str] = field(default_factory=list)
    unsupported: int = 0
    unsupported_share: float = 0.0
    warnings: list[str] = field(default_factory=list)
    removed_sentences: list[str] = field(default_factory=list)  # for --explain / eval only, never shown in the answer

    @property
    def changed(self) -> bool:
        return bool(self.invalid_ids or self.unverified_quotes or self.unverified_authority)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.translate(QUOTE_CHARS)).strip().lower()


def _alnum(s: str) -> str:
    return re.sub(r"[^0-9a-z]", "", s.lower())


def _expand_group(m: re.Match) -> str:
    inner = m.group(0)[1:-1]
    out = []
    for p in re.split(r"\s*(?:,|;|and)\s*", inner):
        rng = re.match(r"[Ss]?\s*(\d+)\s*[-–]\s*[Ss]?\s*(\d+)$", p.strip())
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            out += [f"[S{i}]" for i in range(a, b + 1)] if 0 < b - a < 10 else [f"[S{a}]", f"[S{b}]"]
        else:
            n = re.sub(r"\D", "", p)
            if n:
                out.append(f"[S{n}]")
    return "".join(out)


def _evidence(chunks: list[dict]) -> tuple[str, set[str]]:
    """Lower-cased text + metadata of the given chunks, and every section number they are about or mention
    ("section 49", "sections 24, 25 and 26", "s. 49", "u/s 49", "धारा 49")."""
    parts, sections = [], set()
    for c in chunks:
        parts += [c.get("text") or "", c.get("title") or "", c.get("act_title") or "", c.get("section_heading") or "",
                  c.get("case_title") or "", c.get("citation") or "", c.get("locator") or ""]
        if c.get("section"):
            sections.add(str(c["section"]).upper())
        for m in SECTION_MENTION.finditer(c.get("text") or ""):
            sections.update(n.upper() for n in re.findall(r"\d{1,3}[A-Z]{0,2}", m.group("nums")))
    return _norm(" ".join(parts)), sections


def _section_ok(num: str, ev: str, sections: set[str]) -> bool:
    return re.match(r"\d{1,3}[A-Z]{0,2}", num.upper()).group(0) in sections


def _authority_problems(sentence: str, ev: str, sections: set[str], registry) -> list[str]:
    problems = []
    for m in SECTION_MENTION.finditer(sentence):
        for num in re.findall(r"\d{1,3}[A-Z]{0,2}", m.group("nums")):
            if not _section_ok(num, ev, sections):
                problems.append(f"section {num}")
    for m in ORDER_MENTION.finditer(sentence):
        if f"order {m.group('order').lower()}" not in ev and f"o. {m.group('order').lower()}" not in ev:
            problems.append(f"Order {m.group('order')}")
    for m in REPORTER:
        for cite in m.findall(sentence):
            if _alnum(cite) not in _alnum(ev):
                problems.append(cite)
    for m in CASE_NAME.finditer(sentence):
        for party in (m.group("a"), m.group("b")):
            words = [w for w in re.findall(r"[a-z]{3,}", party.lower()) if w not in STOP_PARTY]
            if words and words[0] not in ev:
                problems.append(f"{m.group('a')} v. {m.group('b')}")
                break
    for m in ACT_WITH_YEAR.finditer(sentence):
        name, year = m.group("name").strip(), m.group("year")
        if year not in ev:
            problems.append(f"{name}, {year}")
            continue
        if registry is not None:
            mentions = registry.find_acts(m.group(0))
            titles = {_norm(registry.short_title(i)) for x in mentions for i in x.expands_to}
            if mentions and not any(t in ev for t in titles) and _norm(name) not in ev:
                problems.append(f"{name}, {year}")
        elif _norm(name).removeprefix("the ") not in ev:
            problems.append(f"{name}, {year}")
    return problems


def _split(text: str) -> list[tuple[str, str]]:
    pieces, pos = [], 0
    for m in SENTENCE.finditer(text):
        pieces.append((text[pos:m.start()], text[m.start():m.end()]))
        pos = m.end()
    pieces.append((text[pos:], ""))
    return pieces


def _unsupported(text: str) -> tuple[int, int]:
    """(flagged, total) sentences under the "What the sources say" heading that carry no [S#] marker."""
    block = re.search(r"What the sources say[^\n]*\n(.*?)(?=\n\s*\*\*|\Z)", text, re.S | re.I)
    if not block:
        return 0, 0
    sentences = [s for s, _ in _split(block.group(1)) if len(re.findall(r"\w+", s)) >= 5]
    flagged = [s for s in sentences if not MARKER.search(s)]
    return len(flagged), len(sentences)


def validate(answer: str, id_map: dict[str, dict], statutes: dict[str, dict] | None = None, registry=None) -> ValidationResult:
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

    all_chunks = list(id_map.values())
    unverified_q, unverified_a, kept, removed = [], [], [], []
    for sentence, sep in _split(text):
        cited = [id_map[f"S{int(n)}"] for n in MARKER.findall(sentence) if f"S{int(n)}" in id_map]
        pool = cited or all_chunks
        ev, sections = _evidence(pool)
        heading = HEADING.match(sentence)  # "**Short answer:** ..." keeps its heading if the sentence goes
        bad_q = [q for q in QUOTE.findall(sentence) if _norm(q) not in _norm(" ".join(c["text"] for c in pool))]
        if bad_q:
            unverified_q += bad_q
            removed.append(sentence.strip())
            log.warning("unverified_quote", extra={"quote": bad_q[0][:80]})
            if heading:
                kept.append(heading.group(1) + sep)
            continue
        bad_a = _authority_problems(sentence, ev, sections, registry)
        if bad_a:
            unverified_a += bad_a
            removed.append(sentence.strip())
            log.warning("unverified_authority", extra={"items": bad_a[:3]})
            if heading:
                kept.append(heading.group(1) + sep)
            continue
        kept.append(sentence + sep)
    text = "".join(kept)
    text = re.sub(r"[ \t]+([.,;:])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    flagged, total = _unsupported(text)
    used = list(dict.fromkeys(f"S{int(n)}" for n in MARKER.findall(text)))
    warnings = []
    if invalid:
        warnings.append(f"Removed {len(invalid)} citation(s) to sources that were not provided: {', '.join(sorted(set(invalid)))}.")
    if unverified_q:
        warnings.append(f"Removed {len(unverified_q)} sentence(s) whose quotation did not match the cited source word for word.")
    if unverified_a:
        warnings.append(f"Removed sentence(s) naming authorities not found in the cited sources: {', '.join(dict.fromkeys(unverified_a))}.")
    for sid in used:
        c = id_map[sid]
        if c.get("status") == "repealed":
            succ = (statutes or {}).get(c.get("successor") or "", {}).get("short_title") or c.get("successor") or "a successor law"
            warnings.append(f"[{sid}] {c.get('act_title') or c.get('title')} is repealed; it was replaced by {succ}. "
                            "It may still govern events or proceedings from before the repeal.")
    return ValidationResult(text=text, used_ids=used, invalid_ids=invalid, unverified_quotes=unverified_q,
                            unverified_authority=unverified_a, unsupported=flagged,
                            unsupported_share=(flagged / total) if total else 0.0, warnings=warnings,
                            removed_sentences=removed)


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
