"""Turn parsed statutes and judgments into Chunk records. Headers inside `embed_text` come from metadata, never
from a model: e.g. `Registration Act, 1908 > Part IV — Of the Time of Presentation > s. 23 — Time for presenting
documents`."""

from __future__ import annotations

import re
from collections.abc import Callable

from app.chunking.judgment import JudgmentParse, header_text, para_label
from app.chunking.schema import Chunk, Document, make_chunk_id
from app.chunking.statute import SectionDraft, StatuteParse
from app.chunking.text import Para, join_lines, pack, paragraphs

SMALL_WORDS = {"of", "the", "and", "in", "to", "for", "by", "on", "or", "a", "an", "under", "with", "from", "as", "at"}
MAX_PARA_PARTS = 3


def nice_title(s: str) -> str:
    """'OF THE TIME OF PRESENTATION' -> 'Of the Time of Presentation'."""
    words = s.lower().split()
    return " ".join(w if (i and w in SMALL_WORDS) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def _tidy_label(label: str | None) -> str | None:
    if not label:
        return None
    head, _, title = label.partition(" — ")
    return f"{head} — {nice_title(title)}" if title else head


def _base(doc: Document, **kw) -> dict:
    return dict(doc_id=doc.doc_id, doc_type=doc.doc_type, title=doc.title, source_name=doc.source_name,
                source_url=doc.source_url, licence=doc.licence, retrieved_at=doc.retrieved_at, authority=doc.authority,
                jurisdiction=doc.jurisdiction, language=doc.language, script=doc.script, **kw)


def _pieces_text(piece: list[Para]) -> str:
    return "\n".join(p.text for p in piece)


def statute_chunks(doc: Document, sp: StatuteParse, act: dict, jurisdictions: dict, domain_tags: list[str],
                   count: Callable[[str], int], max_tokens: int) -> list[Chunk]:
    """act: the statutes.yaml entry (status, short_title, act_year, act_number, successor)."""
    act_title = act["short_title"]
    out: list[Chunk] = []
    # provisions not yet in force, e.g. BNS "106(2)": the whole section is marked partially in force
    partial_sections = {re.match(r"\w+", p).group(0) for p in act.get("not_in_force") or []}

    def status_for(sec: SectionDraft) -> str:
        return "partially_in_force" if sec.kind == "section" and sec.num in partial_sections else act["status"]

    def notes_for(sec: SectionDraft) -> list[dict] | None:
        notes = [{"page": pg, "marker": m, "text": sp.footnotes[pg][m]}
                 for pg, markers in sorted(sec.markers_by_page.items()) for m in sorted(markers)
                 if m in sp.footnotes.get(pg, {})]
        return notes or None

    def emit(sec: SectionDraft, lines, locator_base: str, jurisdiction: str, header_tail: str, notes):
        paras = paragraphs(lines)
        pieces = pack(paras, max_tokens, count)
        path = " > ".join(x for x in [act_title, _tidy_label(sec.part), _tidy_label(sec.chapter), header_tail] if x)
        for i, piece in enumerate(pieces, 1):
            text = _pieces_text(piece)
            locator = locator_base if len(pieces) == 1 else f"{locator_base} (part {i} of {len(pieces)})"
            header = path if len(pieces) == 1 else f"{path} (part {i} of {len(pieces)})"
            embed_text = f"{header}\n{text}"
            base = _base(doc)
            base["jurisdiction"] = jurisdiction
            out.append(Chunk(
                chunk_id=make_chunk_id(doc.doc_id, locator, text), **base,
                locator=locator, page_start=piece[0].page_start, page_end=piece[-1].page_end,
                text=text, embed_text=embed_text, token_count=count(text), status=status_for(sec),
                domain_tags=domain_tags, text_source="layer",
                act_title=act_title, act_year=act["act_year"], act_number=str(act.get("act_number") or "") or None,
                part=_tidy_label(sec.part), chapter=_tidy_label(sec.chapter),
                section=sec.num,
                section_heading=sec.heading, amendment_notes=notes, successor=act.get("successor"),
            ))

    for sec in sp.sections:
        if sec.kind == "section":
            loc, tail = f"s. {sec.num}", f"s. {sec.num} — {sec.heading}"
        elif sec.kind == "rule":  # e.g. CPC First Schedule, "O. XXXIX r. 1"
            rule_no = sec.num.split(" r. ")[-1]
            loc, tail = sec.num, f"r. {rule_no} — {sec.heading}"
        elif sec.kind == "schedule":
            loc, tail = sec.num, sec.num
        else:
            loc, tail = "Preamble", "Long title and preamble"
        if sec.lines:
            emit(sec, sec.lines, loc, doc.jurisdiction, tail, notes_for(sec))
        for block in sec.state_blocks:
            state = jurisdictions["aliases"].get(block.state, block.state)
            code = jurisdictions["codes"].get(state, "")  # unmapped -> empty -> rejected by validation
            emit(sec, block.lines, f"{loc}, State amendment ({state or 'unnamed'})", code,
                 f"{tail} > State amendment: {state or 'unnamed'}", None)
    return out


def judgment_chunks(doc: Document, jp: JudgmentParse, meta: dict, domain_tags: list[str],
                    count: Callable[[str], int], max_tokens: int) -> list[Chunk]:
    common = dict(status="n/a", domain_tags=domain_tags, case_title=meta["case_title"], court=meta["court"],
                  decision_date=meta["decision_date"], judges=meta.get("judges") or None,
                  citation="; ".join(x for x in [meta.get("citation"), meta.get("neutral_citation")] if x) or None,
                  disposal_nature=meta.get("disposal_nature"), cnr=meta.get("cnr"))
    short = re.sub(r"\s+versus\s+", " v. ", meta["case_title"], flags=re.I)
    path = f"{short} ({meta['court']}, {meta['decision_date']})"

    head = header_text(meta)
    out = [Chunk(chunk_id=make_chunk_id(doc.doc_id, "header", head), **_base(doc), locator="header",
                 page_start=None, page_end=None, text=head, embed_text=f"{path} > case header\n{head}",
                 token_count=count(head), text_source="metadata", **common)]

    pieces = pack(jp.paras, max_tokens, count)

    def only_number(piece: list[Para]) -> int | None:
        nums = {p.number for p in piece}
        return next(iter(nums)) if len(nums) == 1 else None

    # a paragraph spread over several pieces gets "(part i of n)"
    split_counts: dict[int, int] = {}
    for piece in pieces:
        n = only_number(piece)
        if n is not None:
            split_counts[n] = split_counts.get(n, 0) + 1
    seen: dict[int, int] = {}
    for piece in pieces:
        a, b, loc = para_label([p.number for p in piece])
        n = only_number(piece)
        # A "paragraph" spread over many pieces usually means the numbering was lost partway through a judgment;
        # a label like "para 11 (part 47 of 73)" would mislead, so such pieces are located by page instead.
        if loc is not None and n is not None and split_counts.get(n, 0) > MAX_PARA_PARTS:
            a = b = loc = None
        if loc is None:
            loc = f"p. {piece[0].page_start}" if piece[0].page_start == piece[-1].page_end else \
                f"pp. {piece[0].page_start}-{piece[-1].page_end}"
        elif n is not None and split_counts.get(n, 0) > 1:
            seen[n] = seen.get(n, 0) + 1
            loc += f" (part {seen[n]} of {split_counts[n]})"
        text = _pieces_text(piece)
        out.append(Chunk(chunk_id=make_chunk_id(doc.doc_id, loc, text), **_base(doc), locator=loc,
                         page_start=piece[0].page_start, page_end=piece[-1].page_end, text=text,
                         embed_text=f"{path} > {loc}\n{text}", token_count=count(text), text_source="layer",
                         para_start=a, para_end=b, **common))
    return out


__all__ = ["statute_chunks", "judgment_chunks", "nice_title", "join_lines"]
