"""Context builder: [S#] blocks whose headers are rendered from metadata (retrieval-pipeline note, step 8).

Order: statutes, then Supreme Court judgments; relevance order within each, with the parts of one section (or one
judgment's neighbouring paragraphs) kept together. Repealed material is labelled with its repeal date and successor
from statutes.yaml. The S# -> chunk map stays server-side and is the only thing a citation can resolve to.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from app.retrieval.registry import Registry

STATUS_LABEL = {"in_force": "in force", "partially_in_force": "partially in force", "unknown": "status unknown", "n/a": None}
TYPE_ORDER = {"statute": 0, "judgment": 1, "procedure": 2, "form": 3}
STATUTE_SLOTS = 2           # context places kept for the statute text the fusion ranked highest
STATUTE_SLOT_MAX_FUSED = 10  # ...if the fusion ranked it this high


def reserve_statute_slots(cands: list[dict], max_chunks: int, slots: int = STATUTE_SLOTS,
                          max_fused: int = STATUTE_SLOT_MAX_FUSED) -> list[dict]:
    """Final order, except that the `slots` statute chunks with the best fused rank (<= max_fused) are moved into the
    first `max_chunks` places, displacing the lowest-ranked non-statute passages.

    Why: the cross-encoder prefers judgment paragraphs that paraphrase a provision over the provision itself. RERA
    s. 18 was the top statute hit (fused 7) and BNSS s. 482 the top fused hit overall (fused 1), yet both ended 12th
    after reranking and missed the 8 context places (DECISIONS D35). The answer must be able to cite primary text."""
    head = list(cands[:max_chunks])
    best = sorted((c for c in cands if c["doc_type"] == "statute" and c.get("ranks", {}).get("fused", 10**9) <= max_fused),
                  key=lambda c: c["ranks"]["fused"])[:slots]
    moved = False
    for c in best:
        if any(c is h for h in head):
            continue
        for i in range(len(head) - 1, -1, -1):
            if head[i]["doc_type"] != "statute":
                del head[i]
                break
        else:
            break  # the head is all statute text already
        c.setdefault("ranks", {})["context_slot"] = "statute"
        head.append(c)
        moved = True
    if not moved:
        return list(cands)
    return head + [c for c in cands if not any(c is h for h in head)]


def block_label(c: dict) -> str:
    if c["doc_type"] == "statute":
        head = f"{c['act_title']} — {c['locator']}"
        if c.get("section_heading") and c.get("section") not in (None, "Preamble"):
            head += f" ({c['section_heading']})"
        return head
    if c["doc_type"] == "judgment":
        return f"{c['case_title']} — {c['locator']}"
    return f"{c['title']} — {c['locator']}"


def status_text(c: dict, registry: Registry | None) -> str | None:
    if c["status"] == "repealed":
        act = registry.by_short_title(c.get("act_title") or "") if registry else None
        succ = registry.short_title(act["successor"]) if act and act.get("successor") else (c.get("successor") or "a successor law")
        when = f" from {act['repealed_from']}" if act and act.get("repealed_from") else ""
        return f"REPEALED{when}, replaced by {succ}"
    return STATUS_LABEL.get(c["status"])


def block_header(sid: str, c: dict, registry: Registry | None) -> str:
    parts = [f"[{sid}] {block_label(c)}"]
    st = status_text(c, registry)
    if st:
        parts.append(st)
    if c["doc_type"] == "judgment":
        parts.append(f"{c['court']}, decided {c['decision_date']}")
        if c.get("citation"):
            parts.append(c["citation"])
    if c["jurisdiction"] != "IN":
        parts.append(f"state law: {c['jurisdiction']}")
    parts += [c["source_name"], f"retrieved {c['retrieved_at'][:10]}", c["source_url"]]
    return " | ".join(parts)


def _group_key(c: dict) -> tuple:
    if c["doc_type"] == "statute":
        return (c["doc_id"], c.get("section"), c["jurisdiction"])
    return (c["doc_id"],)


def _part_no(c: dict) -> int:
    m = re.search(r"part (\d+) of", c.get("locator") or "")
    return int(m.group(1)) if m else (c.get("para_start") or 0)


def build_context(chunks: list[dict], registry: Registry | None, count: Callable[[str], int],
                  max_chunks: int, max_tokens: int) -> tuple[list[dict], dict[str, dict]]:
    """chunks: relevance-ordered. Returns (blocks, S# -> chunk)."""
    chosen, used = [], 0
    for c in chunks:
        if len(chosen) >= max_chunks:
            break
        n = c.get("token_count") or count(c["text"])
        if used + n > max_tokens:
            continue
        chosen.append(c)
        used += n
    first_seen: dict[tuple, int] = {}
    for i, c in enumerate(chosen):
        first_seen.setdefault(_group_key(c), i)
    ordered = sorted(chosen, key=lambda c: (TYPE_ORDER.get(c["doc_type"], 9), first_seen[_group_key(c)], _part_no(c)))
    blocks, id_map = [], {}
    for i, c in enumerate(ordered, 1):
        sid = f"S{i}"
        id_map[sid] = c
        blocks.append({"sid": sid, "chunk_id": c["chunk_id"], "label": block_label(c),
                       "header": block_header(sid, c, registry), "text": c["text"]})
    return blocks, id_map


def render_context(blocks: list[dict]) -> str:
    return "\n\n".join(f"{b['header']}\n{b['text']}" for b in blocks)
