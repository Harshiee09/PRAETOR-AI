"""Answer pipeline: classify -> hybrid retrieval (exact + dense + keyword -> RRF -> rerank) -> evidence gate ->
[S#] context -> LLM router -> full citation validator -> response contract
(docs/topics/legal/grounding-and-citations.md, docs/topics/architecture/retrieval-pipeline.md).

Deterministic additions never come from the model: the high-stakes safety block, the criminal-code transition note
(dates from statutes.yaml), repeal notes for Acts the question names, and exact-lookup notes.
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
from app.embeddings.embedder import Embedder, count_tokens
from app.llm.base import LLMError, Message
from app.llm.extractive import ExtractiveClient
from app.llm.ollama import OllamaClient
from app.multilingual.script import dominant_script, nfc
from app.rag.context import build_context, render_context
from app.reranking.reranker import Reranker
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever, RetrievalResult
from app.retrieval.registry import Registry, load_registry
from app.store.db import connect

log = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parent / "prompts" / "answer_system.md"
DISCLAIMER = ("General information drawn from the cited sources, not legal advice. For your own situation, consult an "
              "advocate or your District Legal Services Authority.")
SAFETY = ("> **If anyone is in immediate danger, call 112.** If this involves arrest or detention, eviction, violence "
          "or a deadline that is close, contact a lawyer or your District Legal Services Authority now.\n\n")
STRICTER = ("\n\nYour previous answer had sentences without source IDs. Every sentence under 'What the sources say' "
            "MUST end with a source ID like [S1]. Leave out anything you cannot support from the sources.")
CLOUD_PROVIDERS = {"bedrock"}
CRIMINAL = ("crpc-1973", "bnss-2023", "ipc-1860", "bns-2023", "iea-1872", "bsa-2023")
UNSUPPORTED_LIMIT = 0.20


@dataclass
class Engine:
    """Loaded once and reused across questions (embedding model, reranker, index and registry stay in memory)."""
    settings: Settings
    retriever: HybridRetriever
    registry: Registry
    system_prompt: str
    prompt_version: str

    @classmethod
    def load(cls, settings: Settings, rerank: bool = True) -> "Engine":
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        m = re.search(r"version:\s*([\w.-]+)", prompt)
        embedder = Embedder(settings.embed_model, settings.embed_device, settings.embed_batch_size)
        reranker = Reranker(settings.rerank_model, settings.rerank_device) if rerank else None
        registry = load_registry(str(settings.registry_dir))
        return cls(settings=settings,
                   retriever=HybridRetriever(settings, DenseRetriever(settings, embedder), reranker, registry),
                   registry=registry, system_prompt=re.sub(r"<!--.*?-->\s*", "", prompt, flags=re.S),
                   prompt_version=m.group(1) if m else "?")


def _providers(settings: Settings) -> list[str]:
    chain = [settings.llm_answer] + [p.strip() for p in settings.llm_fallback.split(",") if p.strip()]
    if settings.privacy_mode == "strict":
        chain = [p for p in chain if p not in CLOUD_PROVIDERS]
    if "extractive" not in chain:
        chain.append("extractive")  # always ends in the honest no-model mode
    return list(dict.fromkeys(chain))


def _language(query: str) -> str:
    script, _ = dominant_script(query)
    if script == "Latn":
        return "en"
    return f"und-{script}" if script else "und"


def _corpus_summary(conn) -> str:
    n_acts = conn.execute("SELECT COUNT(*) FROM documents WHERE doc_type='statute'").fetchone()[0]
    n_j = conn.execute("SELECT COUNT(*) FROM documents WHERE doc_type='judgment'").fetchone()[0]
    return f"{n_acts} central Acts and {n_j} Supreme Court judgments"


def deterministic_notes(r: RetrievalResult, registry: Registry) -> list[str]:
    cls = r.classification
    notes = list(r.notes)
    for a in cls.acts:
        act = registry.get(a)
        if act and act["status"] == "repealed":
            succ = registry.short_title(act["successor"]) if act.get("successor") else "a successor law"
            notes.append(f"The {act['short_title']} was repealed from {act['repealed_from']} and replaced by the {succ}.")
    if cls.domain == "criminal_procedure" or any(a in CRIMINAL for a in cls.search_acts):
        start = registry.get("bnss-2023")["in_force_from"]
        years = sorted(d[:4] for d in cls.event_dates)
        if not years:
            notes.append(f"Criminal law changed on {start}: the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha "
                         "Sanhita and Bharatiya Sakshya Adhiniyam replaced the Indian Penal Code, the Code of Criminal "
                         "Procedure and the Indian Evidence Act. Which applies depends on when the events happened and "
                         "the stage of any proceedings; proceedings pending on that date continue under the old Code.")
        elif all(y < str(start)[:4] for y in years):
            notes.append(f"The events mentioned are from before {start}, when the Indian Penal Code, the Code of Criminal "
                         "Procedure and the Indian Evidence Act were in force; they may govern those events and "
                         "proceedings pending on that date.")
        else:
            notes.append(f"Events on or after {start} are governed by the Bharatiya Nyaya Sanhita, Bharatiya Nagarik "
                         "Suraksha Sanhita and Bharatiya Sakshya Adhiniyam.")
    if cls.jurisdiction_hint:
        notes.append(f"You mentioned {', '.join(cls.jurisdiction_hint)}: state amendments are included only where "
                     "India Code prints them, and state rules are not in the corpus.")
    return list(dict.fromkeys(notes))


def _generate(engine: Engine, provider: str, user: str, model: str | None, stricter: bool, blocks: list[dict]):
    s = engine.settings
    system = engine.system_prompt + (STRICTER if stricter else "")
    if provider == "ollama":
        client = OllamaClient(s.ollama_base_url, model or s.ollama_model, s.ollama_timeout_s)
        return client.generate([Message("user", user)], system=system, max_tokens=900, temperature=0.1)
    if provider == "extractive":
        return ExtractiveClient().answer_from_blocks(blocks)
    raise LLMError(f"provider {provider!r} is not available until Phase 3")


def answer(engine: Engine, query: str, *, explain: bool = False, mode: str = "full", model: str | None = None) -> dict:
    s = engine.settings
    trace_id = uuid.uuid4().hex[:16]
    t_start = time.perf_counter()
    q = re.sub(r"\s+", " ", nfc(query)).strip()
    conn = connect(s.sqlite_path)
    count = partial(count_tokens, model_name=s.embed_model)
    try:
        r = engine.retriever.retrieve(conn, q, mode=mode)
        cls = r.classification
        notes = deterministic_notes(r, engine.registry)
        base = {"language": _language(q), "trace_id": trace_id, "disclaimer": DISCLAIMER,
                "classification": {"domain": cls.domain, "intent": cls.intent, "high_stakes": cls.high_stakes},
                "jurisdiction_note": ("Central Acts as published on India Code (state amendments only where India Code "
                                      "prints them) and Supreme Court judgments; state rules and later changes may "
                                      "not be covered.")}
        explain_info = {"classification": cls.as_dict(), "gate": r.gate, "timings_ms": r.timings_ms,
                        "keyword_match": r.keyword_match,
                        "candidates": [{"chunk_id": c["chunk_id"], "title": c["title"], "locator": c["locator"],
                                        "ranks": c["ranks"], "scores": c["scores"]} for c in r.candidates[:15]]}
        safety = SAFETY if cls.high_stakes else ""

        if r.abstained:
            gate = r.gate
            why = (f"the best passage scored {gate['score']:.2f}, below the evidence threshold of {gate['threshold']:.2f}"
                   if gate.get("score") is not None else "nothing relevant was found")
            text = (safety + f"I could not find sources in the current corpus that answer this. I searched "
                    f"{_corpus_summary(conn)}; {why}, so no answer was generated. A reliable answer would need the Act, "
                    "rules or state regulations that govern this topic, which may not be in the corpus yet.")
            out = {**base, "answer_markdown": text, "confidence": "low", "abstained": True, "citations": [],
                   "warnings": ["insufficient_sources"] + notes, "provider": None}
            _log(s, q, trace_id, out, t_start)
            return {**out, "explain": explain_info} if explain else out

        blocks, id_map = build_context(r.candidates, engine.registry, count, s.context_max_chunks, s.context_max_tokens)
        user = f"Sources:\n\n{render_context(blocks)}\n\nQuestion: {q}"
        warnings: list[str] = []
        result = provider = v = None
        attempts = []
        for name in _providers(s):
            try:
                result = _generate(engine, name, user, model, False, blocks)
                provider = name
            except LLMError as exc:
                warnings.append(f"{name} unavailable: {exc}")
                log.warning("provider failed, falling back", extra={"provider": name, "error": str(exc), "trace_id": trace_id})
                continue
            v = validate(result.text, id_map, engine.registry.statutes, engine.registry)
            attempts.append({"provider": name, "unsupported_share": round(v.unsupported_share, 3), "used": len(v.used_ids),
                             "raw": result.text})
            if provider != "extractive" and (v.unsupported_share > UNSUPPORTED_LIMIT or not v.used_ids):
                result = _generate(engine, name, user, model, True, blocks)
                v = validate(result.text, id_map, engine.registry.statutes, engine.registry)
                attempts.append({"provider": name, "stricter": True, "unsupported_share": round(v.unsupported_share, 3),
                                 "used": len(v.used_ids), "raw": result.text})
                if v.unsupported_share > UNSUPPORTED_LIMIT or not v.used_ids:
                    warnings.append("The generated answer was not grounded well enough in the sources, so the "
                                    "verbatim passages are shown instead.")
                    result, provider = ExtractiveClient().answer_from_blocks(blocks), "extractive"
                    v = validate(result.text, id_map, engine.registry.statutes, engine.registry)
            break

        warnings += v.warnings + notes
        gate = r.gate
        comfortable = gate["on"] == "exact" or (gate.get("score") is not None and gate["score"] >= (gate["threshold"] or 0) + 0.4)
        if v.changed or provider == "extractive" or len(v.used_ids) < 2:
            confidence = "low"
        elif comfortable and not v.unsupported:
            confidence = "high"
        else:
            confidence = "medium"
        out = {**base, "answer_markdown": safety + v.text, "confidence": confidence, "abstained": False,
               "citations": [citation_card(sid, id_map[sid]) for sid in v.used_ids], "warnings": warnings,
               "provider": provider, "model": result.model}
        explain_info.update(context_ids={b["sid"]: b["chunk_id"] for b in blocks}, prompt_version=engine.prompt_version,
                            llm={"provider": provider, "model": result.model, "input_tokens": result.input_tokens,
                                 "output_tokens": result.output_tokens, "latency_ms": result.latency_ms},
                            attempts=attempts,
                            validator={"invalid_ids": v.invalid_ids, "unverified_quotes": v.unverified_quotes,
                                       "unverified_authority": v.unverified_authority, "unsupported": v.unsupported,
                                       "unsupported_share": round(v.unsupported_share, 3),
                                       "removed_sentences": v.removed_sentences})
        _log(s, q, trace_id, out, t_start)
        return {**out, "explain": explain_info} if explain else out
    finally:
        conn.close()


def _log(s: Settings, q: str, trace_id: str, out: dict, t_start: float) -> None:
    log.info("answered", extra={"trace_id": trace_id, **loggable_query(q, s.log_queries), "abstained": out["abstained"],
                                "provider": out.get("provider"), "citations": len(out["citations"]),
                                "latency_ms": round((time.perf_counter() - t_start) * 1000)})
