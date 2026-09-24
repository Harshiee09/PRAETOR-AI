"""Rank of a required statute chunk at every retrieval stage, to find where it is lost (one-off diagnostic utility).

For each query: classification, rewrite, gate, the target's dense rank over the whole index, keyword rank, fused /
rerank / final ranks, its reranker score, and whether it reaches the [S#] context (after the statute slots).
Queries labelled "diag:" are close paraphrases written for the 2026-09-24 audit (DECISIONS D35), not gold questions.

    uv run python scripts/trace_stages.py evaluation/reports/diagnostics/<name>.json
"""
import json
import sys

from app.config import get_settings
from app.embeddings.embedder import count_tokens
from app.rag.context import build_context, reserve_statute_slots
from app.rag.pipeline import Engine
from app.retrieval.keyword import KeywordRetriever
from app.store.db import connect

T = {"bnss482": ("Bharatiya Nagarik Suraksha Sanhita, 2023", "482"),
     "bnss531": ("Bharatiya Nagarik Suraksha Sanhita, 2023", "531"),
     "rera18": ("Real Estate (Regulation and Development) Act, 2016", "18"),
     "tpa106": ("Transfer of Property Act, 1882", "106")}

QUERIES = [
    ("gold:proc-bnss-482-anticipatory", "How do I apply for anticipatory bail?", ["bnss482"]),
    ("gold:hi-bnss-482-anticipatory", "अग्रिम जमानत के लिए आवेदन कहाँ किया जा सकता है?", ["bnss482"]),
    ("gold:tr-438-anticipatory", "Is anticipatory bail under section 438 CrPC still available?", ["bnss482", "bnss531"]),
    ("diag:bail-paraphrase", "Where can a person who fears arrest for a non-bailable offence apply for bail before being arrested?", ["bnss482"]),
    ("diag:bnss-482-explicit", "What does section 482 of the Bharatiya Nagarik Suraksha Sanhita provide?", ["bnss482"]),
    ("diag:pending-438", "My anticipatory bail application under section 438 CrPC was filed in 2023 and is still pending. Which law applies to it?", ["bnss531", "bnss482"]),
    ("diag:crpc-482-quash", "Can the High Court quash an FIR under section 482 CrPC?", []),
    ("gold:rera-018-refund", "What can a home buyer claim if the builder fails to hand over the flat on the agreed date?", ["rera18"]),
    ("diag:rera-withdraw", "The builder has not given possession on time and I want to withdraw from the project. Can I get my money back with interest?", ["rera18"]),
    ("diag:rera-stay", "If I do not want to withdraw from a delayed housing project, what does the law give me for the delay?", ["rera18"]),
    ("gold:hs-eviction-tomorrow", "My landlord says he will throw me out of the house tomorrow without any notice. What does the law say?", ["tpa106"]),
    ("diag:eviction-notice", "Can a landlord evict a tenant without giving notice?", ["tpa106"]),
    ("gold:tpa-106-lease-notice", "How much notice is needed to end a monthly residential lease when there is no written contract?", ["tpa106"]),
]


def main(out_path):
    s = get_settings()
    eng = Engine.load(s)
    conn = connect(s.sqlite_path)
    tid = {k: conn.execute("SELECT rowid FROM chunks WHERE act_title=? AND section=? AND jurisdiction='IN'", v).fetchone()[0]
           for k, v in T.items()}
    ntotal = eng.retriever.dense.index.ntotal
    count = lambda t: count_tokens(t, model_name=s.embed_model)
    out = []
    for label, q, targets in QUERIES:
        r = eng.retriever.retrieve(conn, q, mode="full")
        cls = r.classification
        hits, _ = eng.retriever.dense.search(q, ntotal)
        dense_rank = {rid: i for i, (rid, _) in enumerate(hits, 1)}
        dense_score = dict(hits)
        kw, _ = KeywordRetriever(conn).search(q, 30000)
        kw_rank = {rid: i for i, (rid, _) in enumerate(kw, 1)}
        _, id_map = build_context(reserve_statute_slots(r.candidates, s.context_max_chunks), eng.registry, count,
                                  s.context_max_chunks, s.context_max_tokens)
        ctx = {c["rowid"]: sid for sid, c in id_map.items()}
        # reranker score of each target against the query even when it never reached the pool
        rr_direct = {}
        for t in targets:
            txt = conn.execute("SELECT embed_text FROM chunks WHERE rowid=?", (tid[t],)).fetchone()[0]
            rr_direct[t] = round(eng.retriever.reranker.score(q, [txt])[0], 4)
        row = {"label": label, "query": q, "classification": {k: getattr(cls, k) for k in
               ("domain", "intent", "high_stakes", "acts", "search_acts", "section_refs", "event_dates", "jurisdiction_hint")},
               "gate": r.gate, "abstained": r.abstained, "notes": r.notes, "rewrites": r.rewrites,
               "top5": [(c["ranks"].get("final"), c["title"][:60], c["locator"], c["scores"].get("rerank")) for c in r.candidates[:5]],
               "context": [f"{sid} {c['title'][:50]} {c['locator']}" for sid, c in id_map.items()],
               "targets": {}}
        for t in targets:
            rid = tid[t]
            cand = next((c for c in r.candidates if c["rowid"] == rid), None)
            row["targets"][t] = {
                "dense_rank": dense_rank.get(rid), "dense_score": round(dense_score.get(rid, 0), 4),
                "keyword_rank": kw_rank.get(rid),
                "in_pool": cand is not None,
                "stage_ranks": cand["ranks"] if cand else None,
                "rerank_score": cand["scores"].get("rerank") if cand else None,
                "rerank_direct": rr_direct[t],
                "in_context": ctx.get(rid)}
        out.append(row)
        print(json.dumps({k: row[k] for k in ("label", "gate", "abstained", "targets")}, ensure_ascii=False))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
