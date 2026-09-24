"""Context statute slots: primary text the fusion ranked highly is not crowded out by reranked judgment paraphrases."""

from app.rag.context import reserve_statute_slots


def _c(i, doc_type, fused):
    return {"chunk_id": f"c{i}", "doc_type": doc_type, "ranks": {"fused": fused, "final": i}}


def test_top_fused_statute_displaces_the_last_judgment():
    # the shape of "How do I apply for anticipatory bail?": 11 judgment passages rank above BNSS s. 482 after
    # reranking although the fusion put s. 482 first (DECISIONS D35)
    cands = [_c(i, "judgment", i + 1) for i in range(11)] + [_c(11, "statute", 1)]
    out = reserve_statute_slots(cands, max_chunks=8)
    head = [c["chunk_id"] for c in out[:8]]
    assert "c11" in head and "c7" not in head and len(out) == len(cands)
    assert out[7]["ranks"]["context_slot"] == "statute"


def test_statute_ranked_low_by_fusion_is_not_forced_in():
    cands = [_c(i, "judgment", i + 1) for i in range(11)] + [_c(11, "statute", 25)]
    assert reserve_statute_slots(cands, max_chunks=8) == cands


def test_order_is_unchanged_when_the_statutes_are_already_in_context():
    cands = [_c(0, "statute", 1), _c(1, "statute", 2)] + [_c(i, "judgment", i + 1) for i in range(2, 12)]
    assert reserve_statute_slots(cands, max_chunks=8) == cands
