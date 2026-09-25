# PRAETOR AI — status and final report

_Last updated: 2026-09-25 · Phases 0–4 built · everything local, no AWS (D47) · work on branch `phase-3-4-local` (main = audit-verified Phase 2) · **three checks still to run: Windows Smart App Control blocks `sentence_transformers` (V45)**_

## Resume here (next session)
1. When `uv run python -c "import sentence_transformers"` works again (the block is Windows' decision, see "Needs you"), run in order, one GPU job at a time:
   - `uv run pytest -m integration` → expect 19 (16 + 3 new API tests in `tests/integration/test_api.py`)
   - `.\praetor serve`, then in a second window `uv run python scripts/demo.py --fresh --save-examples docs/api/examples` → all seven scenarios `OK`; commit the examples
   - if both pass: `git checkout main && git merge --ff-only phase-3-4-local`
2. You: build the frontend against `docs/api/openapi.json` and [the API note](topics/architecture/api.md); deploy it on Vercel with [the deployment note](topics/ops/deployment.md).
3. You: verify the gold set (`evaluation/verification_sheet.csv`).
Local-only file: `.env` (gitignored). Leftover AWS lines in it are ignored; add `API_KEY` before any tunnel.

## Final report

### 1. What was implemented
- **Corpus and index (Phases 1–2):** 12 central Acts (India Code) and 1,000 Supreme Court judgments (2016–2025) → 27,560 chunks with full provenance in SQLite + FTS5 and FAISS; statute registry with in-force/repealed status and the 2024 criminal-law transition.
- **Retrieval:** rules classifier; lay-term → statutory-wording expansion (`data/registry/legal_terms.yaml`); exact section and CPC-rule lookup; dense (bge-m3) + keyword (BM25) with statute quotas; Act-scoped search; case-name lookup; repeal-section pin; RRF; bge-reranker-v2-m3; evidence gate; context with statute slots.
- **Grounded answers:** local `gemma4:latest` through Ollama (greedy, seed 42), prompt `answer-v3`; deterministic validator (unknown IDs stripped; sections checked against the Act they are named with; case names, reporter citations and Acts with years checked; verbatim quotes, ellipsis-aware; unsupported claims → one stricter retry → verbatim fallback); jurisdiction line, repeal/transition notes, high-stakes safety block and harmful-request refusal from code, not the model.
- **API (Phase 3):** `praetor serve` — `POST /v1/ask`, `GET /v1/sources/{chunk_id}`, `GET /v1/healthz`, `GET /v1/stats`; API key, CORS, request ids, one question at a time, answer cache; contract `docs/api/openapi.json`.
- **Handoff (Phase 4):** README from zero to demo, `scripts/demo.py` (seven scripted scenarios with invariant checks), deployment note for a Vercel frontend, repo-size guard.
- **Audit (2026-09-24/25):** four reported failures traced to the stage where each authority was lost and repaired there (D35–D46); index integrity guard; evaluation hygiene (paraphrase groups, run metadata, verification sheet).

### 2. What works, and the command that proves it (2026-09-25)
| Capability | Command | Result |
|---|---|---|
| Unit tests | `uv run pytest -m "not integration"` | **105 passed** (incl. 13 API tests with a stubbed engine and the repo-size guard) |
| Integration tests (GPU, real index) | `uv run pytest -m integration` | 16 passed on 2026-09-24 (before the API); the 3 API tests are written, not yet run (V45) |
| Corpus profile gate | `.\praetor profile` | every required field 100% → PASS |
| Ask with per-stage ranks | `.\praetor ask "question" --explain` | ranks, scores, gate, rewrite, statute slots, validator result |
| Evaluation | `.\praetor eval --split all` | final report `evaluation/reports/20260924T174231Z.md` (below) |
| API contract | `.\praetor openapi` | `docs/api/openapi.json`, 4 paths |
| API server and demo | `.\praetor serve` · `uv run python scripts/demo.py` | **not yet run end to end** (V45) |
| Diagnostics | `scripts/trace_stages.py`, `scripts/repeat_answers.py`, `scripts/make_verification_sheet.py` | stage trace before/after, repeated-run variance, gold review sheet |

Evaluation (exploratory: 59 unverified draft questions, all seen during development, D38):
| Metric (`gemma4:latest`, full pipeline) | Before the audit | Final (`20260924T174231Z`) |
|---|---|---|
| Retrieval Recall@5 / Recall@10 / MRR (n=54) | 0.91 / 0.93 / 0.84 | **0.96 / 1.00 / 0.85** |
| Expected source among the 8 context blocks | — | **1.00** |
| Out-of-corpus abstained / false abstentions | 5 of 5 / 1 | 5 of 5 / **0** |
| **Invalid citations after validation** (per row) | 0 | **0** |
| Expected source cited | 92% (n=53) | **98%** (n=54) |
| Must-mention phrases | 95% (n=43) | 95% (n=44)¹ |
| Confidence high / medium / low | 3 / 0 / 56 | 26 / 6 / 27 |
| Authority removals | 1 | 6² |

¹ The two misses/fallbacks were Ollama timeouts during the run; both answered normally on re-run. ² 2 correct catches of the model mixing CrPC s. 438 into the BNSS, 2 the old rule also makes, 2 costs of the strict Act check (D46).

### 3. What remains
- Run the three API integration tests and the demo, save `docs/api/examples/`, merge to `main` (blocked by V45 today).
- Human verification of the gold set, then a fresh verified holdout for an honest accuracy figure.
- Hindi source texts (need OCR, Tesseract not installed); answers are in English.
- Optional: the remote demo through a tunnel for the Vercel frontend.

### 4. How to run it
See [README.md](../README.md): `uv sync` → `.env` → `ollama pull gemma4:latest` → `.\praetor gpu-check` → ingest → `.\praetor index` → `.\praetor serve` → `uv run python scripts/demo.py`.

### 5. Required environment variables
`.env.example` is authoritative. Essential: `OLLAMA_MODEL=gemma4:latest`, `MIN_EVIDENCE_SCORE=0.10`, `EMBED_DEVICE`/`RERANK_DEVICE=cuda`; for the API `API_KEY` (required for any non-localhost or tunnel access), `API_HOST`, `API_PORT`, `CORS_ORIGINS`; `CACHE_ENABLED`, `CACHE_TTL_HOURS`; `LLM_TEMPERATURE=0`, `LLM_SEED=42`; `LOG_QUERIES=hash`.

### 6. Deployment steps
Backend: the laptop (`.\praetor serve`, localhost). Frontend: Vercel; its server-side route calls the API through a tunnel with `X-API-Key` from a Vercel environment variable, never from browser code. Vercel cannot host the backend (V43). Details: [deployment note](topics/ops/deployment.md).

### 7. Resources per query (no cloud spend)
Measured in the final eval: mean 3,544 input and 514 output tokens per answer; latency p50 13.4 s, p95 19.5 s (retrieval ~0.6 s of that); GPU: bge-m3 ~1.1 GB + reranker ~1.1 GB + `gemma4:latest` 3.2 GB resident on the 8 GB card (D33). Cached answers return in milliseconds. Cost: $0 in cloud services (D47).

### 8. Demo commands
`.\praetor serve` in one window; `uv run python scripts/demo.py` in another: statute lookup (Registration Act s. 23), procedure (consumer complaint), case law (Indore Development Authority v. Manoharlal), criminal-code transition (s. 438 CrPC → BNSS), Hindi (अग्रिम जमानत), out-of-corpus (Schengen visa, must abstain), high stakes (eviction without notice). Interactive: `http://127.0.0.1:8000/docs`.

### 9. Known limitations
- **Gold set unverified**; all percentages exploratory; no human-verified holdout, so no validated accuracy.
- **s. 438 CrPC question:** the answer now leads with the repeal (cites BNSS s. 531) but `gemma4:latest` still does not cite BNSS s. 482 although it is in context (S2).
- **Strict Act check** removes a true sentence when a judgment says only "the Code" or "the 1908 Act" (D46, accepted trade-off).
- **Transition "closest provision"** is not pinned (D44); for s. 482 CrPC (inherent powers) BNSS s. 528 is not surfaced.
- **CrPC text not ingested** (D20, D42); **no state law** (rent control, RERA interest rules); **no Hindi source text**; answers in English.
- **Term expansions** chosen after seeing failures; Hindi entries unverified; four concepts only.
- **Not bit-for-bit deterministic** (first run after loading can differ, V40); **Ollama can time out** (fallback: verbatim sources).
- **One question at a time** on the GPU; no rate limiting beyond that; the refusal rule is a narrow regex, not a safety classifier.
- **Windows Smart App Control** intermittently blocks downloaded binaries (torch, scikit-learn, the `praetor.exe` launcher; V37, V45).
- Judgment locators: 36% by page; 8 chunks over 450 tokens. Not built: LLM classification / query rewriting; soft domain filter.

### 10. Recommended next step
Clear the Smart App Control block (your decision), run the three checks in "Resume here", merge `phase-3-4-local`, then verify the gold set and build a small human-verified holdout before quoting any accuracy number.

## Audit record (2026-09-24/25; DECISIONS D35–D49, V29–V45)
| Reported failure | First loss (traced) | Repair | Verified |
|---|---|---|---|
| Anticipatory bail omits BNSS s. 482 | reranker 0.025 → final 12 (EN); not retrieved (HI); wrong pinned provision (s. 438) | term expansion, statute slots, Act-aware section check, repeal-section pin only (D44), repeal-first retry (D45) | s. 482 in context for all three; EN/HI answers cite it; s. 438 answer leads with the repeal |
| RERA refund omits s. 18 | reranker drops s. 18 to final 12 | statute slots, allottee/promoter expansion, "How it may apply" | s. 18 cited every run; withdraw vs stay; no invented rate |
| Eviction question refused | evidence gate (0.025 < 0.10) | eviction/tenancy expansion, high-stakes abstention with facts that matter, state-law note, harmful-request refusal | answered from TPA ss. 106/111 with the safety block |
| Lease notice unstable | generation (sampling) + ellipsis quote check | greedy + seed; ellipsis-aware quotes | s. 106 and "fifteen days" in all 10 repeated runs |
| Jurisdiction line / "low" confidence | quoted phrase in prompt v2 removed by the quote check | line from metadata; `answer-v3` | 45 → 0 removals |

Other fixes: Act-title keyword phrases (0 → 260 hits), FAISS/SQLite vector drift guard, visible duplicate drops, page provenance, validator logs without model text. Sources compared, nothing new ingested: BNSS ss. 482/531 match the Gazette; TPA s. 106 current (stale `tpa.pdf` rejected); RERA s. 18 identical; no reachable official pre-repeal CrPC; Hindi TPA/BNSS need OCR.

## Environment
`C:\dev\praetor-ai` (git; no remote yet; tracked files ~3.6 MB); Python 3.12 venv; torch 2.14.0+cu130; FastAPI 0.141.1, uvicorn 0.54.0; RTX 5070 Laptop 8 GB; Ollama 0.34.3, `gemma4:latest` = `c6eb396dbd59`. One GPU job at a time (D34). Disk: data/raw 0.40 GB, data/processed 0.13 GB, data/indexes 0.11 GB.

## Deferred
- **Tesseract OCR** (D9): 2 CPC image pages; the official Hindi TPA / BNSS PDFs (V35).
- **Download contact address** in `HTTP_USER_AGENT`; **India Code terms of use** (V15).

## Needs you
1. **Smart App Control** blocks `sentence_transformers` (a scikit-learn DLL) and the `praetor.exe` launcher again (V45). `.\praetor` avoids the launcher; the library block needs your decision on the Windows setting (check Microsoft's documentation first — it may not be possible to turn it back on without reinstalling Windows). I change no system setting.
2. **Merge** `phase-3-4-local` into `main` after the checks in "Resume here" pass.
3. **Verify the gold set** (`evaluation/verification_sheet.csv`; Hindi rows need a Hindi speaker) and confirm the Hindi terms in `data/registry/legal_terms.yaml`.
4. **CrPC text:** an official consolidated CrPC as in force on 30 June 2024 could be ingested as repealed law; none was reachable.
5. Choose whether to add a third demo language (needs source text that extracts cleanly or OCR).
