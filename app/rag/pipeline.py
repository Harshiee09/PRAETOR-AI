"""Answer pipeline: classify -> hybrid retrieval (exact + dense + keyword -> RRF -> rerank) -> evidence gate ->
[S#] context -> LLM router -> full citation validator -> response contract
(docs/topics/legal/grounding-and-citations.md, docs/topics/architecture/retrieval-pipeline.md).

Deterministic additions never come from the model: the high-stakes safety block, the criminal-code transition note
(dates from statutes.yaml), repeal notes for Acts the question names, exact-lookup notes, the jurisdiction-and-date
line (rendered from the cited chunks' metadata), refusals of clearly harmful requests, and the high-stakes abstention
that lists the facts that matter.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import regex

from app.citations.validator import citation_card, validate
from app.config import Settings
from app.config.logs import loggable_query
from app.embeddings.embedder import Embedder, count_tokens
from app.llm.base import LLMError, Message
from app.llm.bedrock import BedrockClient
from app.llm.extractive import ExtractiveClient, excerpt
from app.llm.ollama import OllamaClient
from app.multilingual.script import dominant_script, nfc
from app.rag.classify import classify
from app.rag.context import build_context, render_context, reserve_statute_slots
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
STRICTER = ("\n\nYour previous answer had sentences without source IDs. Every sentence under 'Short answer', 'What the "
            "sources say' and 'How it may apply' MUST end with a source ID like [S1]. Leave out anything you cannot "
            "support from the sources.")
REPEAL_FIRST = ("\n\nThe sources include {sids}, the provision that repealed the {old}. The question names the {old}, so "
                "start the short answer by saying that it was repealed and replaced by the {new}, citing {sids}; then "
                "answer from the {new} provisions in the sources that deal with the question, and describe judgments "
                "under the {old} as the earlier law.")
CRIMINAL = ("crpc-1973", "bnss-2023", "ipc-1860", "bns-2023", "iea-1872", "bsa-2023")
UNSUPPORTED_LIMIT = 0.20
TENANCY = {"eviction", "landlord-tenant"}
MODEL_JURISDICTION = re.compile(r"\n*[ \t]*\*\*Jurisdiction and date:?\*\*:?.*?(?=\n\s*\*\*|\Z)", re.S | re.I)

# Grounding note, "High-stakes handling and refusals": decline to help fabricate documents or evidence, evade lawful
# process or threaten someone, and offer the lawful alternative. Rules need a first-person request cue next to the act,
# so "my landlord threatened to evict me" or "how do I apply for anticipatory bail" are never refused.
HARMFUL = regex.compile(
    r"\b(?:how (?:can|do|should|would) (?:i|we)|how to|help (?:me|us)|can you|could you|i want to|i need to|we want to"
    r"|teach me|ways? to|tips to)\b(?:\s+[\w'’]+){0,4}?\s+"
    r"(?:(?:make|create|prepare|produce|get|draft|print|generate|write|arrange) (?:a |an |some |the )?"
    r"(?:fake|forged|false|backdated|fabricated|bogus)\b"
    r"|forge (?:[\w'’]+ ){0,2}(?:signature|document|deed|receipt|will|stamp|agreement|certificate)s?\b"
    r"|fabricate\b|backdate\b|destroy (?:the |all )?evidence\b|tamper with (?:the )?(?:evidence|witness(?:es)?)\b"
    r"|bribe\b|threaten\b|intimidate\b|blackmail\b|abscond\b|evade (?:the )?(?:police|arrest|summons|warrant|court)\b"
    r"|hide from (?:the )?police\b)", regex.I)
REFUSAL = ("I can't help with creating false documents or evidence, evading lawful process, or threatening anyone. "
           "I can explain what the law in the sources says about your situation, how to respond to a notice or case "
           "lawfully, or where to get help: a lawyer, or your District Legal Services Authority for free legal aid.")
DEPENDS_ON = {
    "tenancy": "which state the property is in (state tenancy and rent-control laws are not in this corpus); whether "
               "there is a written lease or rent agreement and what it says about notice; whether rent is paid monthly "
               "or yearly; and when any notice was given or received.",
    "criminal": "when the events happened (the criminal codes changed on {bnss_from}); the offence alleged and whether it "
                "is bailable; whether an FIR has been registered; and whether the person is already in custody.",
    "deadline": "the exact dates involved, the kind of case or application, and which court or authority it is before.",
    "other": "the state, the dates involved, and any documents or notices you have.",
}


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


# Part of the answer-cache key: bump when deterministic notes or validator rules change, so answers cached
# under the old rules are not served again (they simply miss; nothing is deleted).
RULES_VERSION = "2026-09-26"
CONSTITUTION = regex.compile(r"\b(?:article|art\.)\s*\d{1,3}[A-Z]{0,2}\b|\bconstitution\b|अनुच्छेद|संविधान", regex.I)
CONSTITUTION_NOTE = ("The text of the Constitution of India is not in this library, so anything said here about its "
                     "articles comes only from the Supreme Court judgments cited.")


def constitution_note(query: str, registry: Registry) -> list[str]:
    """Library questions that name an Article or the Constitution: say plainly that its text is not indexed."""
    if CONSTITUTION.search(query) and not registry.get("constitution-1950"):
        return [CONSTITUTION_NOTE]
    return []


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
    elif TENANCY & set(cls.expansion_ids):
        notes.append("Tenancy and eviction can also depend on state law, such as a state's rent-control Act; no state "
                     "tenancy law is in this corpus, so the answer covers only the central Acts it cites.")
    return list(dict.fromkeys(notes))


def jurisdiction_line(chunks: list[dict]) -> str:
    """The "Jurisdiction and date" line, rendered from the cited chunks' metadata (answer-v2 asked the model for it in
    quotation marks, and the quote check then removed it from 45 of 53 answers: DECISIONS D35)."""
    statutes = [c for c in chunks if c["doc_type"] == "statute"]
    parts = []
    if any(c["jurisdiction"] == "IN" for c in statutes):
        parts.append("central law as published on India Code")
    states = sorted({c["jurisdiction"] for c in statutes if c["jurisdiction"] != "IN"})
    if states:
        parts.append("state amendments printed by India Code (" + ", ".join(states) + ")")
    if any(c["doc_type"] == "judgment" for c in chunks):
        parts.append("Supreme Court of India judgments")
    if any(c.get("status") == "repealed" for c in chunks):
        parts.append("including repealed law (see the notes)")
    dates = sorted({(c.get("retrieved_at") or "")[:10] for c in chunks if c.get("retrieved_at")})
    when = (dates[0] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}") if dates else "an unrecorded date"
    what = "; ".join(parts) or "the cited sources"
    return f"**Jurisdiction and date:** {what[0].upper() + what[1:]}; based on texts retrieved on {when}."


def depends_on(cls, registry: Registry, query: str) -> str:
    """The facts a high-stakes answer turns on, phrased as what to find out (not as legal conclusions)."""
    if TENANCY & set(cls.expansion_ids):
        key = "tenancy"
    elif cls.domain == "criminal_procedure":
        key = "criminal"
    elif regex.search(r"deadline|last date|limitation|time.?barred", query, regex.I):
        key = "deadline"
    else:
        key = "other"
    return DEPENDS_ON[key].format(bnss_from=registry.get("bnss-2023")["in_force_from"])


def repeal_sources(candidates: list[dict], id_map: dict[str, dict], cls, registry: Registry) -> tuple[list[str], str]:
    """S# of the pinned repeal sections in the context (the successor's "... is hereby repealed" for an Act the
    question names), plus the stricter instruction to use when the answer leaves them uncited (DECISIONS D45)."""
    pinned = {c["chunk_id"] for c in candidates if "exact" in c.get("ranks", {})
              and (c.get("section_heading") or "").startswith("Repeal")}
    sids = [sid for sid, c in id_map.items() if c["chunk_id"] in pinned]
    old = [registry.get(a) for a in cls.acts]
    old = [a for a in old if a and a["status"] == "repealed" and a.get("successor")]
    if not sids or not old:
        return [], ""
    return sids, REPEAL_FIRST.format(sids="".join(f"[{s}]" for s in sids), old=old[0]["short_title"],
                                     new=registry.short_title(old[0]["successor"]))


def _system_owned_removed(text: str) -> str:
    """Drop a "Jurisdiction and date" section the model wrote anyway: the system renders that line from metadata."""
    return MODEL_JURISDICTION.sub("", text).rstrip()


def _generate(engine: Engine, provider: str, user: str, model: str | None, stricter: bool, blocks: list[dict],
              extra: str = ""):
    s = engine.settings
    system = engine.system_prompt + (STRICTER if stricter else "") + extra
    if provider == "ollama":
        client = OllamaClient(s.ollama_base_url, model or s.ollama_model, s.ollama_timeout_s)
        return client.generate([Message("user", user)], system=system, max_tokens=900, temperature=s.llm_temperature,
                               seed=s.llm_seed)
    if provider == "bedrock":
        client = BedrockClient(model or s.bedrock_model_id, s.aws_region, s.ollama_timeout_s)
        return client.generate([Message("user", user)], system=system, max_tokens=900, temperature=s.llm_temperature)
    if provider == "extractive":
        return ExtractiveClient().answer_from_blocks(blocks)
    raise LLMError(f"unknown provider {provider!r}")


def answer(engine: Engine, query: str, *, explain: bool = False, mode: str = "full", model: str | None = None,
           trace_id: str | None = None) -> dict:
    s = engine.settings
    trace_id = trace_id or uuid.uuid4().hex[:16]
    t_start = time.perf_counter()
    q = re.sub(r"\s+", " ", nfc(query)).strip()
    conn = connect(s.sqlite_path)
    count = partial(count_tokens, model_name=s.embed_model)
    try:
        cls = classify(q, engine.registry, s.registry_dir)
        base = {"language": _language(q), "trace_id": trace_id, "disclaimer": DISCLAIMER,
                "classification": {"domain": cls.domain, "intent": cls.intent, "high_stakes": cls.high_stakes},
                "jurisdiction_note": ("Central Acts as published on India Code (state amendments only where India Code "
                                      "prints them) and Supreme Court judgments; state rules and later changes may "
                                      "not be covered.")}
        decoding = {"temperature": s.llm_temperature, "seed": s.llm_seed, "max_tokens": 900}
        if HARMFUL.search(q):
            out = {**base, "answer_markdown": REFUSAL, "confidence": "low", "abstained": True, "citations": [],
                   "warnings": ["refused: the request asks for help with fabrication, evasion of process or threats"],
                   "provider": None}
            _log(s, q, trace_id, out, t_start)
            return {**out, "explain": {"classification": cls.as_dict(), "refused": True}} if explain else out

        r = engine.retriever.retrieve(conn, q, mode=mode, cls=cls)
        notes = deterministic_notes(r, engine.registry) + constitution_note(q, engine.registry)
        explain_info = {"classification": cls.as_dict(), "gate": r.gate, "timings_ms": r.timings_ms,
                        "keyword_match": r.keyword_match, "rewrites": r.rewrites,
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
            citations, shown = [], {}
            if cls.high_stakes:
                # High stakes: still no model and no answer, but say what the answer turns on and show the closest
                # statute text verbatim, labelled as unconfirmed (grounding note: abstention + referral, not a bare
                # refusal). Only statute text the final order put in the top 5 is shown.
                text += f"\n\n**What an answer would depend on:** {depends_on(cls, engine.registry, q)}"
                near = [c for c in r.candidates[:5] if c["doc_type"] == "statute"][:2]
                if near:
                    shown = {f"S{i}": c for i, c in enumerate(near, 1)}
                    text += ("\n\n**Closest provisions found** — the system could not confirm that they answer your "
                             "question; they are shown verbatim, without any interpretation:\n" +
                             "\n".join(f"- {c['act_title']} — {c['locator']}: “{excerpt(c['text'])}” [{sid}]"
                                       for sid, c in shown.items()))
                    citations = [citation_card(sid, c) for sid, c in shown.items()]
                    text += "\n\n" + jurisdiction_line(list(shown.values()))
            explain_info["context_ids"] = {sid: c["chunk_id"] for sid, c in shown.items()}
            out = {**base, "answer_markdown": text, "confidence": "low", "abstained": True, "citations": citations,
                   "warnings": ["insufficient_sources"] + notes, "provider": None}
            _log(s, q, trace_id, out, t_start)
            return {**out, "explain": explain_info} if explain else out

        ordered = reserve_statute_slots(r.candidates, s.context_max_chunks)
        blocks, id_map = build_context(ordered, engine.registry, count, s.context_max_chunks, s.context_max_tokens)
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
            v = validate(_system_owned_removed(result.text), id_map, engine.registry.statutes, engine.registry)
            attempts.append({"provider": name, "unsupported_share": round(v.unsupported_share, 3), "used": len(v.used_ids),
                             "raw": result.text})
            grounded = not (v.unsupported_share > UNSUPPORTED_LIMIT or not v.used_ids)
            # A question naming a repealed Act, with the successor's repeal section in context but uncited: the answer
            # describes old law without saying so (D45). One stricter retry, the same one ungrounded answers get.
            repeal_sids, repeal_note = repeal_sources(r.candidates, id_map, cls, engine.registry)
            repeal_missed = bool(repeal_sids) and not set(repeal_sids) & set(v.used_ids)
            if provider != "extractive" and (not grounded or repeal_missed):
                first = (result, v)
                result = _generate(engine, name, user, model, True, blocks, repeal_note if repeal_missed else "")
                v = validate(_system_owned_removed(result.text), id_map, engine.registry.statutes, engine.registry)
                attempts.append({"provider": name, "stricter": True, "repeal_note": repeal_missed,
                                 "unsupported_share": round(v.unsupported_share, 3), "used": len(v.used_ids),
                                 "raw": result.text})
                if v.unsupported_share > UNSUPPORTED_LIMIT or not v.used_ids:
                    if grounded:
                        result, v = first  # the retry was only for the repeal and came back worse: keep the first
                    else:
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
        cited = [id_map[sid] for sid in v.used_ids]
        text = safety + v.text + (("\n\n" + jurisdiction_line(cited)) if cited else "")
        out = {**base, "answer_markdown": text, "confidence": confidence, "abstained": False,
               "citations": [citation_card(sid, id_map[sid]) for sid in v.used_ids], "warnings": warnings,
               "provider": provider, "model": result.model}
        explain_info.update(context_ids={b["sid"]: b["chunk_id"] for b in blocks}, prompt_version=engine.prompt_version,
                            statute_slots=[c["chunk_id"] for c in ordered[: s.context_max_chunks]
                                           if c.get("ranks", {}).get("context_slot") == "statute"],
                            llm={"provider": provider, "model": result.model, "input_tokens": result.input_tokens,
                                 "output_tokens": result.output_tokens, "latency_ms": result.latency_ms,
                                 "decoding": decoding if provider == "ollama" else None},
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
