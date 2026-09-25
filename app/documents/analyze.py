"""Analyses of uploaded documents: ask, summary, risks, checklist, lawyer questions, compare (DECISIONS D50).

Same guarantees as corpus answers (grounding note): the model sees numbered passages only; the deterministic
validator strips unknown IDs and removes sentences with authorities or quotations the cited passages do not contain;
ungrounded output gets one stricter retry, then the verbatim passages. Citation cards come from stored passage
metadata. In the answer, the user's own passages are cited as [D#] and law passages as [S#].

Law cross-check: when the retrieval engine is loaded, up to DOC_LAW_PASSAGES corpus passages that pass the usual
evidence gate are added, so a clause can be compared with the Act it touches. Without the engine the analysis runs
on the document alone and says so.
"""

from __future__ import annotations

import logging
import math
import re
import threading
import time
import uuid
from collections import Counter, OrderedDict
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from app.citations.validator import GROUP, _expand_group, citation_card, validate
from app.config import Settings
from app.documents.store import StoredDocument
from app.llm.base import LLMError, Message
from app.llm.bedrock import BedrockClient
from app.llm.extractive import ExtractiveClient, excerpt
from app.llm.ollama import OllamaClient
from app.rag.classify import classify
from app.rag.context import block_header
from app.rag.pipeline import DISCLAIMER, HARMFUL, REFUSAL, SAFETY, UNSUPPORTED_LIMIT, _language, _providers, \
    _system_owned_removed, jurisdiction_line
from app.retrieval.registry import Registry, load_registry

log = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parents[1] / "rag" / "prompts" / "document_system.md"
MAX_OUTPUT = 1200
DOC_DISCLAIMER = DISCLAIMER + " PRAETOR does not decide whether a document is valid or enforceable."
STRICTER = ("\n\nYour previous answer had sentences without passage IDs. Every sentence under the headings MUST end "
            "with a passage ID like [S1]. Leave out anything you cannot support from the passages.")
SID = re.compile(r"\[S(\d{1,3})\]")
TASK_NAMES = {"ask": "answer", "summary": "summary", "risks": "review", "checklist": "checklist",
              "lawyer_questions": "list of questions for a lawyer", "compare": "comparison"}
MARKER_RUN = re.compile(r"(?:\[S\d{1,3}\]){6,}")
RUN_KEEP = 3
STOP = set("the a an and or of to in on for by with is are be as at this that from any all such shall will may "
           "which who whom its it his her their they them than then there these those not no".split())
RISK_TERMS = ("terminate termination notice penalty interest late fee forfeit forfeiture deposit refund liable liability "
              "indemnify indemnity breach default damages arbitration jurisdiction dispute lock renewal increase "
              "escalation waive waiver discretion evict vacate")
CHECK_TERMS = ("within days date deadline due pay payment rent notice renew renewal expiry register registration stamp "
               "sign signature copy receipt deposit")

TASKS: dict[str, dict] = {
    "ask": {"query": None, "claims": ("short answer", "what your document says", "what the law says"), "format": """\
Answer in this format:
**Short answer:** one or two sentences, each ending with its [S#].

**What your document says:**
- one point per bullet, naming the clause or page, each ending with its [S#]

**What the law says:** only if a LAW passage covers the question, each bullet ending with its [S#]; otherwise leave this heading out.

**What to check:** facts or parts of the document the answer depends on, or that the document does not settle."""},
    "summary": {"query": None, "claims": ("in short", "key points", "not shown or left blank"), "format": """\
Summarise the document briefly, in points, in this format:
**In short:** one or two sentences: what kind of document this is (for example a certificate, an agreement, a notice, an order or a receipt), who issued it or who the parties are, and what it is for, each ending with its [S#].

**Key points:**
- at most eight short points: names, ID or reference numbers, dates (issue, validity, expiry, deadlines), amounts, places, conditions and obligations, each exactly as the document states it and each ending with its [S#]

**Not shown or left blank:**
- things the document itself mentions or has a place for but that are missing or blank in it (signatures, seals or stamps, dates, annexures or attachments, filled-in details), each ending with its [S#]; if nothing is missing, say so

**Worth confirming with a lawyer:**
- two or three specific questions about this document, each tied to a point above and ending with its [S#]"""},
    "risks": {"query": RISK_TERMS, "claims": ("important clauses", "obligations", "risks", "inconsistencies and gaps",
                                              "compared with the law"), "format": """\
Review the document in this format:
**Important clauses:**
- the clauses that matter most, in plain language, each ending with its [S#]

**Obligations:**
- who must do what, by when, and what happens if they do not, each ending with its [S#]

**Risks:**
- terms that could cost the user money, rights or time (penalties, forfeiture, one-sided termination, waivers, wide indemnities, lock-ins, automatic renewal, dispute terms), each ending with its [S#]

**Inconsistencies and gaps:**
- clauses that contradict each other, blanks, missing dates, amounts or signatures, and vague terms, each ending with its [S#]; if there are none, say so

**Compared with the law:** only if a LAW passage covers the same point as a clause: where the clause may differ from it, citing both; otherwise leave this heading out."""},
    "checklist": {"query": CHECK_TERMS, "claims": ("checklist", "key dates and amounts", "documents to keep"), "format": """\
Turn the document into a checklist in this format:
**Checklist:**
- [ ] one concrete action (pay, give notice, keep a receipt, renew, register, sign, check), with its date or deadline if the document gives one, each ending with its [S#]

**Key dates and amounts:**
- each date, deadline and amount the document sets, exactly as written, each ending with its [S#]

**Documents to keep:** copies, receipts or notices the document mentions, each ending with its [S#]."""},
    "lawyer_questions": {"query": RISK_TERMS, "claims": ("what this document is", "facts to gather"), "format": """\
Help the user prepare for a meeting with a lawyer, in this format:
**What this document is:** one or two sentences, each ending with its [S#].

**Facts to gather:**
- facts, dates and papers the lawyer will need that the document refers to or leaves open, each ending with the [S#] of that clause

**Questions to ask a lawyer:**
- specific questions about the clauses that carry the most risk or are unclear, each naming the clause and ending with its [S#]"""},
    "compare": {"query": None, "claims": ("in short", "differences", "only in document a", "only in document b",
                                          "which terms favour whom"), "format": """\
Compare DOCUMENT A and DOCUMENT B{focus} in this format:
**In short:** the most important differences in two or three sentences, each ending with its [S#].

**Differences:**
- one topic per bullet (parties, duration, money, notice, termination, liability, disputes): what A says and what B says, citing a passage from each

**Only in Document A:** terms with no counterpart in B, each ending with its [S#].

**Only in Document B:** terms with no counterpart in A, each ending with its [S#].

**Which terms favour whom:** where a difference makes one document stricter or more generous for a party, each ending with its [S#]."""},
}


@lru_cache(maxsize=1)
def _prompt() -> tuple[str, str]:
    raw = PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"version:\s*([\w.-]+)", raw)
    return re.sub(r"<!--.*?-->\s*", "", raw, flags=re.S), (m.group(1) if m else "?")


@lru_cache(maxsize=2)
def _registry(path: str) -> Registry:
    return load_registry(path)


def _terms(text: str) -> list[str]:
    return [w for w in re.findall(r"\w+", text.lower()) if len(w) > 2 and w not in STOP]


def bm25_order(passages: list[dict], query: str, k1: float = 1.2, b: float = 0.75) -> list[int]:
    """Passage indexes by BM25 score for `query` (best first); ties keep document order."""
    docs = [Counter(_terms(p["text"])) for p in passages]
    avg = sum(sum(d.values()) for d in docs) / max(1, len(docs))
    q = set(_terms(query))
    df = {t: sum(1 for d in docs if t in d) for t in q}
    n = len(docs)

    def score(d: Counter) -> float:
        size = sum(d.values()) or 1
        return sum(math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * d[t] * (k1 + 1) / (d[t] + k1 * (1 - b + b * size / avg))
                   for t in q if d.get(t))
    return sorted(range(n), key=lambda i: (-score(docs[i]), i))


def select_passages(passages: list[dict], budget: int, query: str | None) -> tuple[list[dict], bool]:
    """All passages if they fit; otherwise the opening passage plus the best BM25 matches for `query` (or the first
    passages in order when there is no query), returned in document order. The bool says whether all were kept."""
    if sum(p["tokens"] for p in passages) <= budget:
        return list(passages), True
    order = ([0] + [i for i in bm25_order(passages, query) if i != 0]) if query else list(range(len(passages)))
    chosen, used = [], 0
    for i in order:
        if used + passages[i]["tokens"] <= budget:
            chosen.append(i)
            used += passages[i]["tokens"]
    return [passages[i] for i in sorted(chosen)], False


def _pages(passages: list[dict]) -> str:
    pages = sorted({pg for p in passages for pg in range(p["page_start"], p["page_end"] + 1)})
    runs, start = [], None
    for i, pg in enumerate(pages):
        if start is None:
            start = pg
        if i + 1 == len(pages) or pages[i + 1] != pg + 1:
            runs.append(str(start) if start == pg else f"{start}-{pg}")
            start = None
    return ", ".join(runs)


def _doc_header(sid: str, c: dict) -> str:
    return f"[{sid}] {c['role']} \"{c['title']}\" — {c['locator']}"


def _doc_card(did: str, c: dict) -> dict:
    quote = excerpt(c["text"], 300).rstrip(" …")
    return {"id": did, "kind": "document", "chunk_id": c["chunk_id"], "document_id": c["document_id"],
            "title": c["title"], "locator": c["locator"], "authority": "Uploaded by you", "jurisdiction": "n/a",
            "status": "n/a", "source_url": "", "retrieved_at": c["uploaded_at"], "quote": quote,
            "page_start": c["page_start"], "page_end": c["page_end"]}


def _relabel(text: str, doc_sids: set[str], law_order: list[str]) -> tuple[str, dict[str, str]]:
    """[S#] of the user's passages -> [D#] (same number as in the context); law passages -> [S1], [S2] ... in order."""
    mapping = {sid: f"D{sid[1:]}" for sid in doc_sids}
    mapping.update({sid: f"S{i}" for i, sid in enumerate(law_order, 1)})
    return SID.sub(lambda m: f"[{mapping.get('S' + m.group(1), 'S' + m.group(1))}]", text), mapping


def trim_marker_runs(text: str) -> tuple[str, int]:
    """A run of 6+ markers on one sentence ("[S1][S2]...[S44]") cites everything and helps no one: keep the first
    RUN_KEEP. Every kept marker is still a passage from this request; returns (text, runs trimmed)."""
    text = GROUP.sub(_expand_group, text)  # "[S1-S44]" -> "[S1][S2]..." first, as the validator would
    return MARKER_RUN.subn(lambda m: "".join(f"[S{x}]" for x in SID.findall(m.group(0))[:RUN_KEEP]), text)


def analyze(settings: Settings, docs: list[StoredDocument], task: str, question: str | None = None, *,
            law_fn: Callable[[str], tuple[list[dict], list[str], dict]] | None = None, llm=None,
            explain: bool = False, trace_id: str | None = None) -> dict:
    """law_fn(query) -> (law chunks, deterministic notes, gate info), or None when the engine is not loaded.
    llm: an LLM client for the "ollama" slot of the provider chain (tests inject one)."""
    s = settings
    t0 = time.perf_counter()
    trace_id = trace_id or uuid.uuid4().hex[:16]
    spec = TASKS[task]
    registry = _registry(str(s.registry_dir))
    system_base, prompt_version = _prompt()
    q = re.sub(r"\s+", " ", question or "").strip()
    head = " ".join(docs[0].parsed.passages[0]["text"].split()[:60]) if docs[0].parsed.passages else ""
    cls = classify(q or head, registry, s.registry_dir)
    base = {"language": _language(q) if q else "en", "trace_id": trace_id, "disclaimer": DOC_DISCLAIMER, "task": task,
            "classification": {"domain": cls.domain, "intent": f"document_{task}", "high_stakes": cls.high_stakes}}
    if q and HARMFUL.search(q):
        return {**base, "answer_markdown": REFUSAL, "confidence": "low", "abstained": True, "citations": [],
                "warnings": ["refused: the request asks for help with fabrication, evasion of process or threats"],
                "provider": None, "model": None, "jurisdiction_note": "", "documents": [], "law_checked": False,
                "explain": {"refused": True} if explain else None}

    warnings: list[str] = []
    law, notes, gate = [], [], None
    if s.doc_law_passages > 0 and task != "compare":
        if law_fn is None:
            warnings.append("Law cross-check skipped: the retrieval engine is not loaded, so this analysis uses the "
                            "document alone.")
        else:
            law, notes, gate = law_fn(q if task == "ask" and q else f"{head} {q}".strip())
            law = law[: s.doc_law_passages]
    law_tokens = sum(len(c["text"]) // 3 + 60 for c in law)
    budget = max(800, s.doc_context_tokens - law_tokens)
    per_doc = budget // len(docs)
    query = q if task in ("ask", "compare") and q else spec["query"]

    blocks, id_map, coverage = [], {}, []
    roles = ["DOCUMENT A", "DOCUMENT B"] if len(docs) == 2 else ["YOUR DOCUMENT"]
    for d, role in zip(docs, roles):
        chosen, complete = select_passages(d.parsed.passages, per_doc, query)
        coverage.append({"document_id": d.document_id, "filename": d.filename, "pages_read": _pages(chosen),
                         "complete": complete and not d.parsed.unreadable_pages})
        if not complete:
            pick = "the opening and the passages that best match" + (" the question" if q and query == q else " the task")
            warnings.append(f"\"{d.filename}\" is longer than one analysis can read: this {TASK_NAMES[task]} used "
                            f"{len(chosen)} of its {len(d.parsed.passages)} passages ("
                            + (pick if query else "from the start") + f"; pages {_pages(chosen)} of {d.parsed.pages}).")
        for p in chosen:
            sid = f"S{len(blocks) + 1}"
            c = d.chunk(p, role)
            id_map[sid] = c
            blocks.append({"sid": sid, "chunk_id": c["chunk_id"], "label": f"{role} — {c['locator']}",
                           "header": _doc_header(sid, c), "text": c["text"]})
    doc_sids = set(id_map)
    for c in law:
        sid = f"S{len(blocks) + 1}"
        id_map[sid] = c
        blocks.append({"sid": sid, "chunk_id": c["chunk_id"], "label": f"LAW — {c.get('act_title') or c['title']}",
                       "header": block_header(sid, c, registry).replace(f"[{sid}] ", f"[{sid}] LAW: ", 1), "text": c["text"]})

    fmt = spec["format"].replace("{focus}", f", focusing on: {q}" if q and task == "compare" else "")
    ask_line = f"Question: {q}" if task == "ask" else (f"The user adds: {q}" if q and task != "compare" else "")
    user = "Passages:\n\n" + "\n\n".join(f"{b['header']}\n{b['text']}" for b in blocks) + "\n\n" + \
           (ask_line + "\n\n" if ask_line else "") + fmt

    attempts, result, provider, v = [], None, None, None
    for name in _providers(s):
        try:
            if name == "extractive":
                result, provider = ExtractiveClient().answer_from_blocks(blocks, max_blocks=6), name
            elif name == "ollama":
                client = llm or OllamaClient(s.ollama_base_url, s.ollama_model, s.ollama_timeout_s, num_ctx=s.doc_num_ctx)
                result = client.generate([Message("user", user)], system=system_base, max_tokens=MAX_OUTPUT,
                                         temperature=s.llm_temperature, seed=s.llm_seed)
                provider = name
            elif name == "bedrock":
                client = llm or BedrockClient(s.bedrock_model_id, s.aws_region, s.ollama_timeout_s)
                result = client.generate([Message("user", user)], system=system_base, max_tokens=MAX_OUTPUT,
                                         temperature=s.llm_temperature)
                provider = name
            else:
                raise LLMError(f"unknown provider {name!r}")
        except LLMError as exc:
            warnings.append(f"{name} unavailable: {exc}")
            continue
        v = validate(trim_marker_runs(_system_owned_removed(result.text))[0], id_map, registry.statutes, registry,
                         spec["claims"])
        attempts.append({"provider": name, "unsupported_share": round(v.unsupported_share, 3), "used": len(v.used_ids)})
        if provider != "extractive" and (v.unsupported_share > UNSUPPORTED_LIMIT or not v.used_ids):
            result = client.generate([Message("user", user)], system=system_base + STRICTER, max_tokens=MAX_OUTPUT,
                                     temperature=s.llm_temperature, seed=s.llm_seed)
            v = validate(trim_marker_runs(_system_owned_removed(result.text))[0], id_map, registry.statutes, registry,
                         spec["claims"])
            attempts.append({"provider": name, "stricter": True, "unsupported_share": round(v.unsupported_share, 3),
                             "used": len(v.used_ids)})
            if v.unsupported_share > UNSUPPORTED_LIMIT or not v.used_ids:
                warnings.append("The generated analysis was not grounded well enough in the passages, so the passages "
                                "themselves are shown instead.")
                result, provider = ExtractiveClient().answer_from_blocks(blocks, max_blocks=6), "extractive"
                v = validate(result.text, id_map, registry.statutes, registry, spec["claims"])
        break

    law_used = [sid for sid in v.used_ids if sid not in doc_sids]
    text, mapping = _relabel(v.text, doc_sids, law_used)
    cards = [_doc_card(mapping[sid], id_map[sid]) if sid in doc_sids else {**citation_card(mapping[sid], id_map[sid]), "kind": "law"}
             for sid in v.used_ids]
    cited_law = [id_map[sid] for sid in law_used]
    if cited_law:
        text += "\n\n" + jurisdiction_line(cited_law)
    all_complete = all(c["complete"] for c in coverage)
    if v.changed or provider == "extractive" or len(v.used_ids) < 2:
        confidence = "low"
    elif not v.unsupported and all_complete:
        confidence = "high"
    else:
        confidence = "medium"
    doc_note = "Based on the document you uploaded" if len(docs) == 1 else "Based on the two documents you uploaded"
    out = {**base, "answer_markdown": (SAFETY if cls.high_stakes else "") + text, "confidence": confidence,
           "abstained": False, "citations": cards,
           "warnings": [_relabel(w, doc_sids, law_used)[0] for w in warnings + v.warnings] + notes,
           "jurisdiction_note": doc_note + ("; law passages are central Acts as published on India Code and Supreme "
                                            "Court judgments, and state law is not covered." if cited_law else "."),
           "provider": provider, "model": result.model if result else None, "documents": coverage,
           "law_checked": bool(law_fn) and task != "compare"}
    log.info("document analysed", extra={"trace_id": trace_id, "task": task, "provider": provider,
                                         "citations": len(cards), "latency_ms": round((time.perf_counter() - t0) * 1000)})
    if explain:
        out["explain"] = {"prompt_version": prompt_version, "context_ids": {b["sid"]: b["chunk_id"] for b in blocks},
                          "relabel": mapping, "law_gate": gate, "attempts": attempts,
                          "llm": {"provider": provider, "model": result.model, "input_tokens": result.input_tokens,
                                  "output_tokens": result.output_tokens, "latency_ms": result.latency_ms},
                          "validator": {"invalid_ids": v.invalid_ids, "unverified_quotes": v.unverified_quotes,
                                        "unverified_authority": v.unverified_authority, "unsupported": v.unsupported,
                                        "unsupported_share": round(v.unsupported_share, 3)}}
    else:
        out["explain"] = None
    return out


_LAW_CACHE: OrderedDict = OrderedDict()
_LAW_CACHE_LOCK = threading.Lock()
LAW_CACHE_SIZE = 128


def law_lookup(engine, settings: Settings) -> Callable[[str], tuple[list[dict], list[str], dict]]:
    """Corpus passages for a document's topic through the normal retrieval and evidence gate (nothing below the gate).

    Results are kept in a small in-process LRU keyed by the query: every task on one document asks the same law
    question, and on the CPU server the reranker makes each lookup ~20 s (V52). The index cannot change while the
    process runs, so a cached result is identical to a fresh one; only the query text is the key, never stored."""
    from app.rag.context import reserve_statute_slots
    from app.rag.pipeline import deterministic_notes
    from app.store.db import connect

    def find(query: str):
        key = (query, settings.doc_law_passages, id(engine))
        with _LAW_CACHE_LOCK:
            if key in _LAW_CACHE:
                _LAW_CACHE.move_to_end(key)
                law, notes, gate = _LAW_CACHE[key]
                return list(law), list(notes), dict(gate or {})
        result = _find(query)
        with _LAW_CACHE_LOCK:
            _LAW_CACHE[key] = result
            while len(_LAW_CACHE) > LAW_CACHE_SIZE:
                _LAW_CACHE.popitem(last=False)
        law, notes, gate = result
        return list(law), list(notes), dict(gate or {})

    def _find(query: str):
        conn = connect(settings.sqlite_path)
        try:
            cls = classify(query, engine.registry, settings.registry_dir)
            r = engine.retriever.retrieve(conn, query, mode="full", cls=cls)
        finally:
            conn.close()
        if r.abstained:
            return [], [], r.gate
        slots = reserve_statute_slots(r.candidates, settings.doc_law_passages)[: settings.doc_law_passages]
        return slots, deterministic_notes(r, engine.registry), r.gate
    return find
