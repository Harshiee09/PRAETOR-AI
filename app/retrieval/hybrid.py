"""Hybrid retrieval: classify -> exact statute lookup + dense (FAISS) + keyword (FTS5) -> RRF -> rerank ->
evidence gate (docs/topics/architecture/retrieval-pipeline.md).

Modes exist so `praetor eval` can run the ablation through the same code path:
  dense | keyword | hybrid (dense+keyword RRF) | hybrid_rerank | full (hybrid_rerank + exact lookup)
Every candidate records its rank at each stage, which `praetor ask --explain` prints.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field

from app.config import Settings
from app.rag.classify import Classification, classify
from app.reranking.reranker import Reranker
from app.retrieval.dense import DenseRetriever
from app.retrieval.exact import act_scoped, case_lookup, exact_lookup
from app.retrieval.fusion import rrf
from app.retrieval.keyword import KeywordRetriever
from app.retrieval.registry import Registry
from app.store.db import chunks_by_rowids

MODES = ("dense", "keyword", "hybrid", "hybrid_rerank", "full")
STATUTE_QUOTA = 10


@dataclass
class RetrievalResult:
    query: str
    mode: str
    classification: Classification
    candidates: list[dict]              # chunk dicts, best first, each with "ranks" and "scores"
    abstained: bool
    gate: dict                          # {"score": .., "threshold": .., "on": "rerank"|"dense"|"exact"|"none"}
    notes: list[str] = field(default_factory=list)
    timings_ms: dict = field(default_factory=dict)
    keyword_match: str | None = None
    rewrites: list[str] = field(default_factory=list)  # the expanded query used by dense/act-scoped/rerank, if any


class HybridRetriever:
    def __init__(self, settings: Settings, dense: DenseRetriever, reranker: Reranker | None, registry: Registry):
        self.s = settings
        self.dense = dense
        self.reranker = reranker
        self.registry = registry

    def retrieve(self, conn: sqlite3.Connection, query: str, mode: str = "full",
                 cls: Classification | None = None) -> RetrievalResult:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        s = self.s
        t: dict = {}
        t0 = time.perf_counter()
        cls = cls or classify(query, self.registry, s.registry_dir)
        t["classify_ms"] = round((time.perf_counter() - t0) * 1000)

        allowed_juris = {"IN", *cls.jurisdiction_hint}
        lists: dict[str, list[int]] = {}
        scores: dict[str, dict[int, float]] = {}
        notes: list[str] = []
        pinned: list[int] = []
        match = None

        if mode == "full":
            t0 = time.perf_counter()
            pinned, notes = exact_lookup(conn, cls, self.registry)
            t["exact_ms"] = round((time.perf_counter() - t0) * 1000)

        fused_modes = ("hybrid", "hybrid_rerank", "full")
        # Rewrite (retrieval-pipeline note, step 3): lay terms add the statutes' own wording (legal_terms.yaml), e.g.
        # "anticipatory bail" -> "bail to person apprehending arrest", the BNSS s. 482 heading, which the reranker
        # otherwise scored 0.025 for "How do I apply for anticipatory bail?" (DECISIONS D35). Fused modes only, so the
        # single-retriever ablation rows stay comparable with earlier runs.
        expand = bool(cls.expansions) and mode in fused_modes
        xq = f"{query} ({'; '.join(cls.expansions)})" if expand else query
        dense_queries = [("dense", query)] + ([("dense_expanded", xq)] if expand else [])
        if mode in ("dense", *fused_modes):
            dt_total = 0
            for name, dq in dense_queries:
                hits, dt = self.dense.search(dq, s.top_k_dense * 4)
                meta = {r["rowid"]: r for r in chunks_by_rowids(conn, [h[0] for h in hits])}
                hits = [h for h in hits if h[0] in meta and meta[h[0]]["jurisdiction"] in allowed_juris]
                lists[name] = [h[0] for h in hits[: s.top_k_dense]]
                scores.setdefault("dense", {}).update({r: v for r, v in hits[: s.top_k_dense] if r not in scores.get("dense", {})})
                if mode in fused_modes:
                    # Statute quota: judgments outnumber statute chunks ~8:1, so the best statute hits get their own
                    # list in the fusion and always reach the reranker (retrieval-pipeline note, step 4, doc_type).
                    st = [h for h in hits if meta[h[0]]["doc_type"] == "statute"][:STATUTE_QUOTA]
                    lists[f"{name}_statute"] = [h[0] for h in st]
                    scores["dense"].update({r: v for r, v in st if r not in scores["dense"]})
                dt_total += dt["embed_ms"] + dt["search_ms"]
            t["dense_ms"] = dt_total

        if mode in ("keyword", *fused_modes):
            phrases = [self.registry.short_title(a) for a in cls.search_acts] + (list(cls.expansions) if expand else [])
            placeholders = ",".join("?" for _ in allowed_juris)
            kw = KeywordRetriever(conn)
            hits, dt = kw.search(query, s.top_k_keyword, extra_phrases=phrases,
                                 where=f"c.jurisdiction IN ({placeholders})", params=tuple(sorted(allowed_juris)))
            lists["keyword"] = [h[0] for h in hits]
            scores["keyword"] = dict(hits)
            match = dt["match"]
            t["keyword_ms"] = dt["keyword_ms"]
            if mode in fused_modes:
                st, _ = kw.search(query, STATUTE_QUOTA, extra_phrases=phrases,
                                  where=f"c.doc_type = 'statute' AND c.jurisdiction IN ({placeholders})",
                                  params=tuple(sorted(allowed_juris)))
                lists["keyword_statute"] = [h[0] for h in st]
                scores["keyword"].update(dict(st))

        if mode in fused_modes and cls.search_acts:
            # Act-scoped statute search: a question naming an Act (or a repealed one whose successor is ingested)
            # ranks that Act's own sections by similarity, so "s. 438 CrPC" can reach BNSS s. 482.
            t0 = time.perf_counter()
            titles = [self.registry.short_title(a) for a in cls.search_acts]
            lists["act_scoped"] = act_scoped(conn, xq, titles, self.dense, STATUTE_QUOTA)
            t["act_scoped_ms"] = round((time.perf_counter() - t0) * 1000)

        if mode == "full":
            # Case-name lookup: "Indore Development Authority v. Manoharlal" pins that judgment's closest passages.
            case_rows = case_lookup(conn, query, self.dense)
            pinned += [r for r in case_rows if r not in pinned]
            # Transition pin: a question naming a repealed Act gets the successor's closest provision in context, so
            # the answer can state the law now in force (statute-status note). The reranker alone misses these:
            # "anticipatory bail" scored 0.002 against BNSS s. 482 "bail to person apprehending arrest".
            # The successor's own repeal section ("The Code of Criminal Procedure, 1973 ... is hereby repealed") is
            # pinned too: it is the citable source for the repeal itself.
            for a in cls.acts:
                act = self.registry.get(a)
                if act and act["status"] == "repealed" and act.get("successor"):
                    succ_title = self.registry.short_title(act["successor"])
                    old_name = act["short_title"].split(",")[0]
                    repeal = conn.execute(
                        "SELECT rowid FROM chunks WHERE act_title = ? AND jurisdiction = 'IN' AND section_heading LIKE 'Repeal%' "
                        "AND text LIKE ? ORDER BY rowid LIMIT 1", (succ_title, f"%{old_name}%")).fetchall()
                    succ = [r[0] for r in repeal] + act_scoped(conn, xq, [succ_title], self.dense, 1)
                    pinned += [r for r in succ if r not in pinned]

        if len(lists) == 1 and not pinned:
            name = next(iter(lists))
            fused = [(r, scores[name][r], {name: i}) for i, r in enumerate(lists[name], 1)]
        else:
            fused = rrf(lists, k=s.rrf_k, pinned=pinned)
        for i, (_, _, ranks) in enumerate(fused, 1):
            ranks["fused"] = i

        pool = fused[: max(s.rerank_top_n, len(pinned))] if mode in ("hybrid_rerank", "full") else fused[: s.rerank_top_n]
        rows = {r["rowid"]: r for r in chunks_by_rowids(conn, [f[0] for f in pool])}
        cands = []
        for rid, fscore, ranks in pool:
            if rid not in rows:
                continue
            c = dict(rows[rid])
            c["ranks"] = dict(ranks)
            c["scores"] = {k: round(v[rid], 4) for k, v in scores.items() if rid in v} | {"fused": round(fscore, 5)}
            cands.append(c)

        gate = {"on": "none", "score": None, "threshold": None}
        if mode in ("hybrid_rerank", "full") and self.reranker is not None and cands:
            t0 = time.perf_counter()
            rr = self.reranker.score(xq, [c["embed_text"] for c in cands])
            t["rerank_ms"] = round((time.perf_counter() - t0) * 1000)
            for c, sc in zip(cands, rr):
                c["scores"]["rerank"] = round(sc, 4)
            # Final order: RRF over (fused rank, rerank rank). The cross-encoder alone prefers judgment paragraphs that
            # paraphrase a rule over the statute text itself; as one voter among two it lifted Recall@5 on the dev
            # split from 0.89 (rerank only) to 0.93, with no extra parameter (DECISIONS D29). Pinned hits stay first.
            by_rr = sorted(cands, key=lambda c: -c["scores"]["rerank"])
            for i, c in enumerate(by_rr, 1):
                c["ranks"]["rerank"] = i
            pinned_set = set(pinned)
            cands.sort(key=lambda c: (c["rowid"] not in pinned_set,
                                      -(1 / (s.rrf_k + c["ranks"]["fused"]) + 1 / (s.rrf_k + c["ranks"]["rerank"]))))
            for i, c in enumerate(cands, 1):
                c["ranks"]["final"] = i
            top = max(c["scores"]["rerank"] for c in cands)
            gate = {"on": "rerank", "score": round(top, 4), "threshold": s.min_evidence_score}
            if pinned:
                gate["on"] = "exact"  # the query named a section that exists: that is evidence enough to answer
        elif mode in ("dense", "hybrid") and "dense" in scores and scores["dense"]:
            top = max(scores["dense"].values())
            gate = {"on": "dense", "score": round(top, 4), "threshold": s.min_dense_score}
        abstained = not cands or (gate["on"] in ("rerank", "dense") and gate["score"] < gate["threshold"])
        return RetrievalResult(query=query, mode=mode, classification=cls, candidates=cands, abstained=abstained,
                               gate=gate, notes=notes, timings_ms=t, keyword_match=match,
                               rewrites=[xq] if expand else [])
