"""Context builder: [S#] blocks whose headers are rendered from metadata (retrieval-pipeline note, step 8).

Order: statutes, then Supreme Court judgments; relevance order within each. The S# -> chunk map stays
server-side and is the only thing a citation can resolve to.
"""

from __future__ import annotations

from collections.abc import Callable

STATUS_LABEL = {"in_force": "in force", "repealed": "REPEALED", "partially_in_force": "partially in force",
                "unknown": "status unknown", "n/a": None}
TYPE_ORDER = {"statute": 0, "judgment": 1, "procedure": 2, "form": 3}


def block_label(c: dict) -> str:
    if c["doc_type"] == "statute":
        head = f"{c['act_title']} — {c['locator']}"
        if c.get("section_heading") and c.get("section") not in (None, "Preamble"):
            head += f" ({c['section_heading']})"
        return head
    if c["doc_type"] == "judgment":
        return f"{c['case_title']} — {c['locator']}"
    return f"{c['title']} — {c['locator']}"


def block_header(sid: str, c: dict, statutes: dict[str, dict]) -> str:
    parts = [f"[{sid}] {block_label(c)}"]
    status = STATUS_LABEL.get(c["status"])
    if c["status"] == "repealed":
        succ = statutes.get(c.get("successor") or "", {}).get("short_title") or c.get("successor") or "a successor law"
        status = f"REPEALED, replaced by {succ}"
    if status:
        parts.append(status)
    if c["doc_type"] == "judgment":
        parts.append(f"{c['court']}, decided {c['decision_date']}")
        if c.get("citation"):
            parts.append(c["citation"])
    if c["jurisdiction"] != "IN":
        parts.append(f"state law: {c['jurisdiction']}")
    parts += [c["source_name"], f"retrieved {c['retrieved_at'][:10]}", c["source_url"]]
    return " | ".join(parts)


def build_context(chunks: list[dict], statutes: dict[str, dict], count: Callable[[str], int],
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
    ordered = sorted(enumerate(chosen), key=lambda ic: (TYPE_ORDER.get(ic[1]["doc_type"], 9), ic[0]))
    blocks, id_map = [], {}
    for i, (_, c) in enumerate(ordered, 1):
        sid = f"S{i}"
        id_map[sid] = c
        blocks.append({"sid": sid, "chunk_id": c["chunk_id"], "label": block_label(c),
                       "header": block_header(sid, c, statutes), "text": c["text"]})
    return blocks, id_map


def render_context(blocks: list[dict]) -> str:
    return "\n\n".join(f"{b['header']}\n{b['text']}" for b in blocks)
