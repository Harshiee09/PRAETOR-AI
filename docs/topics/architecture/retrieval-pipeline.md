---
id: 20260922-retrieval-pipeline
title: Retrieval pipeline
tags: [retrieval, architecture, multilingual]
created: 2026-09-22
updated: 2026-09-24
related: [20260922-chunk-schema, 20260922-llm-layer, 20260922-grounding-and-citations, 20260922-statute-status, 20260922-multilingual, 20260922-evaluation]
summary: Query side from classification through hybrid search, fusion, reranking, the evidence gate and context building.
---

# Retrieval pipeline

> Summary: Query side from classification through hybrid search, fusion, reranking, the evidence gate and context building.

## Context
This covers query classification, rewriting, metadata filtering, dense and keyword retrieval, fusion, reranking, context construction and citation tracking. Grounded generation itself lives in the grounding note. Every stage returns its candidates, scores and timings, so `praetor ask --explain` and the eval harness can show where a relevant chunk was won or lost.

## Details

### 1. Normalise and detect
Apply Unicode NFC and collapse whitespace. Strip zero-width characters in search keys only, since they carry meaning in some Indic scripts and display text must keep them. Detect script and language. Produce a redacted copy of the query for cloud calls and logs, masking Aadhaar-like 12-digit numbers, PAN-format identifiers (`[A-Z]{5}[0-9]{4}[A-Z]`), Indian mobile numbers and email addresses.

### 2. Classify
Rules first — keyword lists, Act aliases, section regexes — and the local LLM only when the rules are unsure (`LLM_CLASSIFY=ollama`, JSON output validated with pydantic, falling back to `other` when parsing fails). Output:
- `domain`: `property_land`, `contract_civil`, `consumer`, `criminal_procedure`, `constitutional` or `other`
- `intent`: `statute_lookup`, `explain`, `procedure`, `case_law`, `drafting` or `out_of_scope`
- `high_stakes`: true for arrest or detention, violence or threats, eviction, an imminent limitation deadline, or child safety
- `jurisdiction_hint`: states named in the query
- `event_dates`: dates or years mentioned, which drive old-versus-new criminal code handling

### 3. Rewrite
1. Expand aliases from `data/registry/aliases.yaml`. `CrPC` expands to the Code of Criminal Procedure, 1973 and to its successor, the BNSS, 2023; `TP Act` to the Transfer of Property Act, 1882; likewise `NI Act`, `CPA` and `RERA`.
2. When the query is not in English, produce an English rewrite for keyword search. Dense search uses both the original and the rewrite, since bge-m3 is cross-lingual.
3. Optionally (`LLM_REWRITE=ollama`), generate up to three search queries in one cached local-model call.

The answer always addresses the user's original query.

### 4. Filters
Applied in SQL for keyword search, and as a post-filter over fetched dense results (fetch four times `TOP_K_DENSE` when filters are active):
- `domain_tags` contains the classified domain. This filter is soft: if fewer than 10 candidates survive, drop it.
- `jurisdiction` is `IN` or a state named in the query.
- `status` prefers `in_force`. Include `repealed` when the query names an old code, or when `event_dates` fall before the successor's commencement.
- `doc_type` preference follows intent: `statute_lookup` boosts statutes without excluding judgments.

### 5. Candidates
- **Exact statute lookup.** A regex for `section`, `sec.`, `s.` or `धारा` plus a number, next to an Act alias, fetches `(act_title, section)` directly and places it at rank 1. This is what makes "section 23 of the Registration Act" reliable.
- **Dense.** Embed the query with bge-m3, normalised, then take the FAISS top `TOP_K_DENSE`.
- **Keyword.** FTS5 `MATCH` ranked by `bm25()`, top `TOP_K_KEYWORD`. Sanitise first: split into terms, quote each one, and join with `OR`, because raw text containing quotes, hyphens or `NOT` breaks FTS5 syntax. Start from `tokenize = "unicode61 remove_diacritics 0"` and keep a unit test proving that Hindi and Tamil terms are searchable.

### 6. Fusion
Reciprocal rank fusion, `score = sum(1 / (RRF_K + rank))` with `RRF_K = 60`. Deduplicate by `chunk_id`, and merge adjacent chunks from the same section or run of paragraphs.

### 7. Rerank and the evidence gate
Score the top `RERANK_TOP_N` (query, `embed_text`) pairs with bge-reranker-v2-m3 in one GPU batch, using scores in the 0 to 1 range — a sigmoid over the logit, though recent `CrossEncoder` versions may already apply one, so check rather than double-applying. Keep the best `CONTEXT_MAX_CHUNKS` that fit the token budget.

Evidence gate: when the top score is below `MIN_EVIDENCE_SCORE`, or nothing from an allowed authority survives, abstain without calling the LLM. Calibrate the threshold on the eval dev split, maximising correct abstentions without losing answerable questions, and record the value in DECISIONS.md.

### 8. Context construction
Order blocks as statute text, then Supreme Court judgments, then High Court judgments, then procedures. Render each block's header from metadata:
```text
[S1] Registration Act, 1908 — s. 23 (Time for presenting documents) | in force | India Code | https://...
<chunk text>
```
Repealed material gets `| REPEALED from <date>, replaced by <successor>`, taken from the statute registry. Trim long chunks at sentence boundaries to stay inside `CONTEXT_MAX_TOKENS`. The `S# -> chunk_id` map stays server-side and is the only thing a citation can resolve to.

### As built in Phase 2 (DECISIONS D25–D29)
- Classification is rules only (`app/rag/classify.py`); `LLM_CLASSIFY=ollama` and LLM query rewriting are not built (cut list #2). The soft domain filter is not applied.
- Candidate pool: dense top 50 + keyword top 50, plus a **statute quota** (top 10 statute chunks from dense and from keyword, each fused as its own list), **Act-scoped** statute search when the query names an Act, a **case-name lookup** (`X v. Y` against stored case titles, pinning the named judgment's closest passages), and a **transition pin** (for a named repealed Act: the successor's repeal section and closest provision).
- Exact lookup covers sections (`s. 23`, `धारा 23`) and CPC rules (`Order 39 Rule 1` → `O. XXXIX r. 1`), only in the Act the query names.
- Final order: pinned hits, then RRF over (fused rank, rerank rank). Rerank-only ordering lost statute text to judgment paraphrases.
- Evidence gate: top rerank score < `MIN_EVIDENCE_SCORE` (0.10) abstains; exact/case lookups bypass it.
- FTS5 uses `categories 'L* N* Co M*'` so Indic words are not split at vowel signs.

### Output
`RetrievalResult {query, rewrites, classification, candidates[{chunk_id, ranks: {exact, dense, keyword, fused, rerank}, scores}], context_blocks, abstained, timings_ms}`, logged under the request's `trace_id`.

## Related
- [Chunk schema and provenance](chunk-schema.md) — prerequisite: the fields used by filters and headers.
- [LLM layer](llm-layer.md) — next stage: consumes the context blocks.
- [Grounding and citations](../legal/grounding-and-citations.md) — next stage: validates citations against the S# map.
- [Statute status and repeal](../legal/statute-status.md) — supplies aliases and status for rewriting and filters.
- [Multilingual strategy](../data/multilingual.md) — detection and cross-lingual retrieval detail.
- [Evaluation](../ops/evaluation.md) — measures each stage through the ablation table.
