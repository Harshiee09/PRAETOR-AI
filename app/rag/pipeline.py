"""Phase 1 answer pipeline: normalise -> dense retrieval -> evidence gate -> [S#] context -> LLM router ->
citation validator v1 -> response contract (docs/topics/legal/grounding-and-citations.md).

Phase 2 adds classification, keyword search, exact statute lookup, fusion, reranking and the full validator.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from app.citations.validator import citation_card, validate
from app.config import Settings
from app.config.logs import loggable_query
from app.embeddings.embedder import count_tokens
from app.ingestion.sources import load_statutes
from app.llm.base import LLMError, Message
from app.llm.extractive import ExtractiveClient
from app.llm.ollama import OllamaClient
from app.multilingual.script import dominant_script, nfc
from app.rag.context import build_context, render_context
from app.retrieval.dense import DenseRetriever
from app.store.db import chunks_by_rowids, connect

log = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parent / "prompts" / "answer_system.md"
DISCLAIMER = ("General information drawn from the cited sources, not legal advice. For your own situation, consult an "
              "advocate or your District Legal Services Authority.")
CLOUD_PROVIDERS = {"bedrock"}


@dataclass
class Engine:
    """Loaded once and reused across questions (the embedding model and index stay in memory)."""
    settings: Settings
    retriever: DenseRetriever
    statutes: dict[str, dict]
    system_prompt: str
    prompt_version: str

    @classmethod
    def load(cls, settings: Settings) -> "Engine":
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        m = re.search(r"version:\s*([\w.-]+)", prompt)
        return cls(settings=settings, retriever=DenseRetriever(settings),
                   statutes={s["id"]: s for s in load_statutes(settings.registry_dir)},
                   system_prompt=re.sub(r"<!--.*?-->\s*", "", prompt, flags=re.S), prompt_version=m.group(1) if m else "?")


def _providers(settings: Settings) -> list[str]:
    chain = [settings.llm_answer] + [p.strip() for p in settings.llm_fallback.split(",") if p.strip()]
    if settings.privacy_mode == "strict":
        chain = [p for p in chain if p not in CLOUD_PROVIDERS]
    if "extractive" not in chain:
        chain.append("extractive")  # always ends in the honest no-model mode
    return list(dict.fromkeys(chain))


def _language(query: str) -> str:
    script, share = dominant_script(query)
    if script == "Latn":
        return "en"
    return f"und-{script}" if script else "und"


def _corpus_summary(conn) -> str:
    acts = [r[0] for r in conn.execute("SELECT title FROM documents WHERE doc_type='statute' ORDER BY title")]
    n_j = conn.execute("SELECT COUNT(*) FROM documents WHERE doc_type='judgment'").fetchone()[0]
    return f"{', '.join(acts)} and {n_j} Supreme Court judgments"


def answer(engine: Engine, query: str, *, explain: bool = False) -> dict:
    s = engine.settings
    trace_id = uuid.uuid4().hex[:16]
    t_start = time.perf_counter()
    q = re.sub(r"\s+", " ", nfc(query)).strip()
    lang = _language(q)
    conn = connect(s.sqlite_path)
    count = partial(count_tokens, model_name=s.embed_model)
    try:
        hits, timings = engine.retriever.search(q, s.top_k_dense)
        rows = chunks_by_rowids(conn, [rid for rid, _ in hits])
        score_of = dict(hits)
        for r in rows:
            r["dense_score"] = score_of[r["rowid"]]
        top = hits[0][1] if hits else 0.0
        base = {"language": lang, "trace_id": trace_id, "disclaimer": DISCLAIMER,
                "jurisdiction_note": ("Central Acts as published on India Code, with state amendments only where India "
                                      "Code prints them, and Supreme Court judgments; state rules and later changes may "
                                      "not be covered.")}
        explain_info = {"top_dense_score": round(top, 4), "min_dense_score": s.min_dense_score, "timings_ms": timings,
                        "candidates": [{"rank": i + 1, "chunk_id": r["chunk_id"], "title": r["title"], "locator": r["locator"],
                                        "dense": round(r["dense_score"], 4)} for i, r in enumerate(rows[:15])]}

        if top < s.min_dense_score:
            text = (f"I could not find sources in the current corpus that answer this. I searched {_corpus_summary(conn)}; "
                    f"the closest passage scored {top:.2f}, below the evidence threshold of {s.min_dense_score:.2f}, so no "
                    "answer was generated. A reliable answer would need the Act, rules or state regulations that govern "
                    "this topic, which are not in the corpus yet.")
            out = {**base, "answer_markdown": text, "confidence": "low", "abstained": True, "citations": [],
                   "warnings": ["insufficient_sources"], "provider": None}
            _log(s, q, trace_id, out, t_start)
            return {**out, "explain": explain_info} if explain else out

        blocks, id_map = build_context(rows, engine.statutes, count, s.context_max_chunks, s.context_max_tokens)
        context = render_context(blocks)
        user = f"Sources:\n\n{context}\n\nQuestion: {q}"
        warnings: list[str] = []
        result, provider = None, None
        for name in _providers(s):
            try:
                if name == "ollama":
                    client = OllamaClient(s.ollama_base_url, s.ollama_model, s.ollama_timeout_s)
                    result = client.generate([Message("user", user)], system=engine.system_prompt, max_tokens=900, temperature=0.1)
                elif name == "extractive":
                    result = ExtractiveClient().answer_from_blocks(blocks)
                else:
                    raise LLMError(f"provider {name!r} is not available until Phase 3")
                provider = name
                break
            except LLMError as exc:
                warnings.append(f"{name} unavailable: {exc}")
                log.warning("provider failed, falling back", extra={"provider": name, "error": str(exc), "trace_id": trace_id})

        v = validate(result.text, id_map, engine.statutes)
        if not v.used_ids and provider != "extractive":
            warnings.append("The generated answer cited no valid source, so the verbatim passages are shown instead.")
            result, provider = ExtractiveClient().answer_from_blocks(blocks), "extractive"
            v = validate(result.text, id_map, engine.statutes)
        warnings += v.warnings
        confidence = "low" if (v.changed or provider == "extractive" or len(v.used_ids) < 2) else "medium"
        out = {**base, "answer_markdown": v.text, "confidence": confidence, "abstained": False,
               "citations": [citation_card(sid, id_map[sid]) for sid in v.used_ids], "warnings": warnings,
               "provider": provider, "model": result.model}
        explain_info.update(context_ids={b["sid"]: b["chunk_id"] for b in blocks}, prompt_version=engine.prompt_version,
                            llm={"provider": provider, "model": result.model, "input_tokens": result.input_tokens,
                                 "output_tokens": result.output_tokens, "latency_ms": result.latency_ms},
                            validator={"invalid_ids": v.invalid_ids, "unverified_quotes": v.unverified_quotes})
        _log(s, q, trace_id, out, t_start)
        return {**out, "explain": explain_info} if explain else out
    finally:
        conn.close()


def _log(s: Settings, q: str, trace_id: str, out: dict, t_start: float) -> None:
    log.info("answered", extra={"trace_id": trace_id, **loggable_query(q, s.log_queries), "abstained": out["abstained"],
                                "provider": out.get("provider"), "citations": len(out["citations"]),
                                "latency_ms": round((time.perf_counter() - t_start) * 1000)})
