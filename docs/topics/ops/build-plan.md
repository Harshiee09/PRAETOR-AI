---
id: 20260922-build-plan
title: 3-day build plan
tags: [plan, evaluation]
created: 2026-09-22
updated: 2026-09-25
related: [20260922-minimum-viable-architecture, 20260922-chunk-schema, 20260922-data-sources, 20260922-evaluation, 20260925-deployment]
summary: Phases with acceptance criteria, the session protocol, the cut list and the final report format.
---

# 3-day build plan

> Summary: Phases with acceptance criteria, the session protocol, the cut list and the final report format.

## Context
The order is fixed: a working local RAG first, legal intelligence second, the local API third, demo and handoff last (AWS was dropped on 2026-09-25, D47). Each phase ends with a check that proves it works. Nothing counts as done because the code exists.

## Details

### Phase 0 — environment and inspection (about 2 hours)
- Inspect the repository and environment read-only, then write `docs/STATUS.md`: what exists, what works when run, gaps against the minimum viable architecture, and risks.
- Set up the Python environment, a `pyproject.toml` with a `praetor` console script, `.env.example` from the env contract, a `.gitignore` covering data, models and `.env`, pytest configuration with the `integration` marker, and structured logging.
- Prove the GPU: `nvidia-smi`, torch from a CUDA 12.8+ index, and `praetor gpu-check` running a matmul, embedding ten sentences with bge-m3, and reporting device, VRAM and timing.
- Install Ollama and pull two or three candidate models — ask before large downloads.

**Accept:** `pytest -m "not integration"` is green, and `praetor gpu-check` shows CUDA in use.

### Phase 1 — working local RAG (Day 1)
- Ingest three Acts from India Code (Registration Act 1908, Transfer of Property Act 1882, Consumer Protection Act 2019) and about 50 Supreme Court judgments chosen through the metadata parquet.
- Parse, OCR the pages that need it, clean, chunk legally, attach metadata, validate, write to SQLite, embed with bge-m3, index in FAISS.
- `praetor ask` with dense retrieval, context blocks, Ollama, `[S#]` markers, and citations rendered from metadata. Validator v1: unknown IDs stripped, quotes checked as verbatim substrings.
- `praetor profile` report, and the first 10 gold questions.

**Accept:**
- Three known-item questions return the right section, each verified against the ingested text first: the time limit for presenting a document for registration (Registration Act 1908, s. 23), what counts as a sale of immovable property (Transfer of Property Act 1882, s. 54), and the limitation period for a consumer complaint (Consumer Protection Act 2019, s. 69).
- Re-running ingest and index over unchanged sources adds zero rows.
- Unit tests pass for the section splitter and paragraph splitter against real fixtures, for schema validation, and for citation stripping.
- The corpus profile shows every required field green.

### Phase 2 — legal intelligence (Day 2)
Classifier, alias rewriting and optional LLM rewriting, filters, FTS5 keyword search, exact statute lookup, RRF fusion, reranker, evidence gate, and a context builder with status headers. Full validator with the authority-string scan, repeal warnings and confidence. `statutes.yaml` and `aliases.yaml`. Corpus expanded to the seed list plus 300–1,000 judgments. Gold set to 40–60 questions, `praetor eval` with the ablation table, and a local-model benchmark.

**Accept:** the Phase 2 gates in the evaluation note, and `praetor ask --explain` showing per-stage ranks.

### Phase 3 — the local API (redefined 2026-09-25, DECISIONS D47–D48; was "AWS")
AWS is dropped; everything runs on the laptop. FastAPI server `praetor serve`: `POST /v1/ask`, `GET /v1/sources/{chunk_id}`, `GET /v1/healthz`, `GET /v1/stats`; an API key for anything that is not a direct localhost call; CORS allowlist; request IDs; one question at a time on the GPU; error handling with actionable messages; the answer cache. Export the contract (`praetor openapi` → `docs/api/openapi.json`) plus real example responses first, so the separately built frontend can start at once.

**Accept:** HTTP-layer unit tests; `tests/integration/test_api.py` green on the real index; `praetor serve` answers a known-item question with resolvable citations; the OpenAPI contract and examples committed.

### Phase 4 — demo and handoff (local; the frontend is deployed on Vercel separately)
- The README from zero to demo, and `scripts/demo.py` with 6–8 scripted queries through the API: statute lookup, procedure, case law, criminal-code transition, a Hindi query, an out-of-corpus abstention, and a high-stakes query.
- The multilingual demo (a Hindi question retrieves and cites the English statute text).
- Remote demo, optional: the Vercel frontend calls the local API from server-side code through a tunnel with the API key ([deployment note](deployment.md)).
- Keep the GitHub repository under 10 MB (a unit test guards tracked size).

**Accept:** a fresh clone, the README steps, and the demo runs. The final report is written.

### Session protocol
- Start: read `docs/STATUS.md`, this note's current phase, and only the notes that phase needs.
- Work in milestones: implement, run tests, run the acceptance check, update STATUS.md, commit as `phase-N: ...`.
- Blocked for more than about 30 minutes on something non-essential: log it under "Deferred", take the simpler path, continue.
- End: STATUS.md lists what works with the command that proves it, what's next, and any open questions.
- Between phases the user clears the conversation and pastes the next phase prompt; these notes carry the context.

### Cut list if you're behind, cut from the top
1. The remote (tunnel) demo. 2. LLM query rewriting, keeping alias expansion. 3. High Court judgments. 4. The third demo language. 5. OCR beyond basic Tesseract. 6. Rhetorical-role and NER enrichment.

Never cut: provenance validation, the citation validator, the evidence gate, the statute registry, a gold set even if small, and the cost meter.

### Final report format (end of Phase 4, also saved to STATUS.md)
1. What was implemented. 2. What is working, with the command that proves it. 3. What remains. 4. How to run it. 5. Required environment variables. 6. Deployment steps (local server; Vercel frontend through a tunnel). 7. Resources per query: measured tokens, latency and VRAM; no cloud spend. 8. Demo commands. 9. Known limitations. 10. Recommended next step.

## Related
- [Minimum viable architecture](../architecture/minimum-viable-architecture.md) — what is being built.
- [Chunk schema and provenance](../architecture/chunk-schema.md) — Phase 1 ingestion detail.
- [Data sources](../data/data-sources.md) — the seed corpus for Phases 1 and 2.
- [Evaluation](evaluation.md) — the gates each phase must pass.
- [Deployment](deployment.md) — Phase 4 remote demo detail.
- [API](../architecture/api.md) — Phase 3 contract.
