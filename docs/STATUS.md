# PRAETOR AI — status

_Last updated: 2026-09-24 · Phases 0–1 done · **Phase 2 built; two wrap-up runs pending (see "Resume here")** · next: Phase 3 (AWS, needs your go-ahead)_

## Resume here (next session)
Phase 2 code, registries, corpus, index and KB are committed. Two runs remain before the Phase 2 report:
1. `uv run pytest -m integration` with Ollama idle (Phase 1 + Phase 2 sets; expect 11). Fix anything red.
2. `uv run praetor eval --split all` (uses `gemma4:latest` from `.env`, ~15 min) → paste the answer block into "Answer metrics" below and confirm "invalid citations after validation" is 0 on all 59.
3. Commit as `phase-2: wrap-up — integration tests and final eval`, then give the Phase 2 report with the eval table.
Uncommitted local-only file: `.env` (gitignored; `OLLAMA_MODEL=gemma4:latest`, `MIN_EVIDENCE_SCORE=0.10`).

## What works (with the command that proves it)
All commands run from `C:\dev\praetor-ai` as `uv run <command>`.

| Capability | Command | Result (2026-09-24) |
|---|---|---|
| Unit tests | `pytest -m "not integration"` | 56 passed |
| Integration tests (real corpus, GPU) | `pytest -m integration` | Phase 1 set: 5 passed (2026-09-23). Phase 2 set (`tests/integration/test_phase2.py`, 6 tests) **not yet run** — run with Ollama idle |
| Corpus | `praetor ingest --source indiacode --phase 2` · `praetor ingest --source sc-judgments --years 2016-2025 --limit 1000 --via tar` | 12 central Acts + 1,000 SC judgments (English year tars, 3.3 GB downloaded one at a time and deleted after extraction) |
| Index | `praetor index` | 1,012 documents → 27,560 chunks (3,725 statute, 23,835 judgment), 0 failed, FAISS 27,560 vectors; re-run adds 0 |
| Corpus profile gate | `praetor profile` | every required field 100% → **PASS** |
| Ask with per-stage ranks | `praetor ask "question" --explain` | shows exact / dense / keyword / fused / rerank ranks and scores, gate, timings, validator result |
| Evaluation | `praetor eval [--no-llm] [--calibrate] [--split dev|test] [--model NAME]` | ablation, abstention, gate sweep, answer metrics → `evaluation/reports/` |

### Phase 2 gates (evaluation note), on 59 **draft** gold questions
| Gate | Target | Result |
|---|---|---|
| Hybrid + rerank beats dense-only on Recall@5 | > dense | 0.89 vs 0.83 (n=54); dev 0.89 vs 0.85, test 0.89 vs 0.81 — **pass** |
| Statute-lookup Recall@5 | ≥ 0.8 | 0.91 (n=22) full config; dev 1.00, test 0.80 — **pass** |
| Invalid citations after validation | 0 | 0 for each of 3 models on the dev split (n=26 answered each) — **pass on dev**; all-split run pending |
| Out-of-corpus questions abstained | ≥ 4 of 5 | 5 of 5 (1 false abstention of 54 answerable) — **pass**, threshold chosen after seeing all scores (D27) |

### Retrieval ablation (all 59 questions, 54 answerable; report `evaluation/reports/20260923T232023Z.md`)
| Configuration | Recall@5 | Recall@10 | MRR | Statute R@5 (n=22) |
|---|---|---|---|---|
| dense | 0.83 | 0.87 | 0.67 | 0.91 |
| keyword (FTS5 bm25) | 0.44 | 0.54 | 0.36 | 0.41 |
| hybrid (RRF + statute quota + Act scoping) | 0.85 | 0.96 | 0.72 | 0.86 |
| hybrid + rerank | 0.89 | 0.91 | 0.83 | 0.91 |
| full (+ exact / case-name / transition lookups) | **0.91** | 0.93 | **0.84** | 0.91 |

Per language (full): English R@5 0.92 (n=49), Hindi R@5 0.80 (n=5, Hindi questions retrieve English text cross-lingually).
With n=54, differences of a few points between neighbouring rows are not meaningful.

### Local model benchmark (dev split, same questions for each model)
| Model (Ollama) | Resident | Extractive fallbacks | Authority removals | Unsupported flags | Must-mention (n=21) | Expected source cited (n=26) | p50 / p95 |
|---|---|---|---|---|---|---|---|
| qwen3.5:4b | 3.3 GB | 3 | 3 | 0 | 90% | 92% | 10.2 / 20.9 s |
| gemma4:e2b-it-qat (clean re-run, D34) | 1.8 GB | 1 | 6 | 3 | 95% | 88% | 6.6 / 9.6 s |
| **gemma4:latest** (chosen, D32) | 3.2 GB | 0 | 0 | 5 | 95% | 92% | 10.6 / 17.4 s |

All three: 0 invalid citations after validation, 100% of answers cited. Reports: `evaluation/reports/20260923T233233Z` (qwen), `20260923T234816Z` (e2b), `20260923T234336Z` (gemma4:latest). With n=26 the differences are small.

### Answer metrics (full pipeline, chosen model, all 59 questions)
**Pending.** The all-split run with `gemma4:latest` was stopped when the session ended; re-run `praetor eval --split all` (about 15 minutes) and paste its answer block here.

## What changed in Phase 2
- **Registries:** `statutes.yaml` (18 entries, every one with source URL, date and evidence; commencement dates and the BNS s. 106(2) exception from the Acts' own footnotes), `aliases.yaml` (an alias names one Act; search expands to successors), `jurisdictions.yaml`.
- **Retrieval:** rules classifier; FTS5 keyword search with sanitised queries and an Indic-safe tokenizer; exact lookup for sections and CPC rules; statute quota, Act-scoped search, case-name lookup, transition pin; RRF; bge-reranker-v2-m3; final order RRF(fused, rerank); rerank evidence gate (0.10).
- **Grounding:** full validator (authority scan for sections, Acts with years, case names and reporter citations; verbatim quotes; unsupported-sentence check with one stricter regeneration then the extractive fallback); deterministic high-stakes block, criminal-transition note, repeal notes; confidence levels.
- **Parsing:** CPC Orders and rules (`O. XXXIX r. 1`), appendices, Statement of Objects and Reasons dropped, table of contents read from "Arrangement of Sections"; OCR-garbled judgment markers; "In re" titles; memory-safe parsing of 300-page PDFs; parallel parsing.

## Known limitations
- **Gold set is unverified** (59 drafts). All Phase 2 numbers are provisional until a person checks them; the gate threshold was set after seeing every score.
- **CrPC text not ingested** (India Code only has a 1974 scan, V23). CrPC questions get the BNSS repeal section and closest BNSS provision; the small local model still sometimes misses that BNSS s. 482 is the anticipatory-bail provision.
- **Keyword search is weak** on its own (R@5 0.44): English-only terms, generic words; it helps only inside the fusion.
- **Hindi:** retrieval is cross-lingual and works for most Hindi questions, but the reranker scores Hindi–English pairs lower (one Hindi question sits near the gate), no Hindi text is ingested yet, and answers are in English.
- **Judgment locators:** 36% of judgment chunks are located by page (paragraph numbering lost, mostly older OCR-layer scans); 8 chunks exceed the 450-token budget (single long sentences).
- **Eviction question** (high-stakes) abstains: the reranker scores the Transfer of Property Act s. 106 notice rule low for "thrown out tomorrow"; state rent-control law, which would really answer it, is not ingested. The safety block is still shown.
- Not built (cut list #2): LLM classification / query rewriting; soft domain filter.

## Environment
- `C:\dev\praetor-ai` (git, `main`); Python 3.12 venv; torch 2.14.0+cu130; RTX 5070 Laptop 8 GB. Models: bge-m3 (1.1 GB VRAM), bge-reranker-v2-m3 (1.1 GB), Ollama `gemma4:latest` (3.2 GB resident; `OLLAMA_MODEL` in `.env`) — all on GPU together. Run only one GPU job at a time: two Ollama models plus two copies of the encoders crash the Ollama runner (D34).
- Disk: data/raw 0.40 GB (12 Act PDFs, 1,000 judgment PDFs, metadata), data/processed 0.13 GB (SQLite), data/indexes 0.11 GB (FAISS); the tars were deleted after extraction.

## Deferred
- **Tesseract OCR** (D9): 2 CPC image pages (334–335, appendix forms) are unusable without it.
- **Download contact address** in `HTTP_USER_AGENT`; **India Code terms of use** (V15).
- **Hindi Act texts and regional-language judgments** for the multilingual demo (Phase 4).

## Needs you
1. **Verify the 59 draft gold questions** in `evaluation/gold.jsonl` (set `verified_by` / `verified_on`); the 5 Hindi phrasings need a Hindi speaker. Then re-run `praetor eval --calibrate` to re-check the gate on verified data.
2. **Phase 3 go-ahead:** AWS work needs the `praetor` profile, a look at your credit balance and eligible services, and your explicit "go" before anything is created.
3. Choose the third demo language (Phase 4).

## Next step
Phase 3 (`KICKOFF_PROMPT.md`, Session 3): read-only AWS checks, a costed resource list for your approval, then the stack, `s3-sync`, the Bedrock client behind the cost meter, and a local-versus-Bedrock comparison.
