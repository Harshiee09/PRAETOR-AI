"""Reciprocal rank fusion: score = sum over lists of 1 / (k + rank), k = RRF_K (retrieval-pipeline note, step 6)."""

from __future__ import annotations


def rrf(ranked_lists: dict[str, list[int]], k: int = 60, pinned: list[int] | None = None) -> list[tuple[int, float, dict]]:
    """ranked_lists: name -> rowids best first. `pinned` (exact lookup hits) are placed first, in order.
    Returns [(rowid, fused score, {list name: rank})] best first; ranks are 1-based."""
    scores: dict[int, float] = {}
    ranks: dict[int, dict] = {}
    for name, ids in ranked_lists.items():
        for rank, rid in enumerate(ids, 1):
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank)
            ranks.setdefault(rid, {})[name] = rank
    order = sorted(scores, key=lambda r: -scores[r])
    if pinned:
        pinned_set = set(pinned)
        order = list(pinned) + [r for r in order if r not in pinned_set]
        for r in pinned:
            ranks.setdefault(r, {})["exact"] = pinned.index(r) + 1
            scores.setdefault(r, 0.0)
    return [(r, scores[r], ranks.get(r, {})) for r in order]
