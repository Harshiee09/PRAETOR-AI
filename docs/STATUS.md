# PRAETOR AI — status

_Last updated: 2026-09-23 · Phase 0 done · **Phase 1 done** · next: Phase 2 (legal intelligence)_

## What works (with the command that proves it)
All commands run from `C:\dev\praetor-ai` as `uv run <command>`.

| Capability | Command | Result (2026-09-23) |
|---|---|---|
| Unit tests | `pytest -m "not integration"` | 37 passed |
| Integration tests (real corpus, GPU) | `pytest -m integration` | 5 passed: parser noise removal, index idempotency, 3 known items at rank 1 |
| GPU + embeddings | `praetor gpu-check` | RTX 5070 Laptop sm_120, ~27 TFLOPS fp16, bge-m3 on CUDA, 1024-d normalised, peak 1.09 GiB |
| Download Acts | `praetor ingest --source indiacode` | Registration Act 1908, Transfer of Property Act 1882, Consumer Protection Act 2019 (English PDFs via the India Code REST API); re-run skips all |
| Download judgments | `praetor ingest --source sc-judgments --years 2016-2025 --limit 50` | metadata profile of 7,997 rows → `docs/reports/sc_metadata_profile.md`; 50 judgments selected by rule → `docs/reports/sc_selection.md` |
| Parse, chunk, validate, store, embed | `praetor index` | 53 documents → 1,887 chunks (566 statute, 1,321 judgment), 0 rejected, 0 failed; FAISS 1,887 vectors; re-run: 0 changed, 0 added |
| Corpus profile gate | `praetor profile` | every required field 100% → **PASS** (`docs/reports/corpus_profile.md`) |
| Ask with citations | `praetor ask "question" --explain` | dense retrieval → [S#] context → `qwen3.5:4b` → validator v1 → citation cards from metadata |
| Phase 1 acceptance | `python scripts/phase1_acceptance.py` | 4/4 PASS → `evaluation/reports/phase1_acceptance_*.json` |

### Phase 1 acceptance, in detail
| Check | Result |
|---|---|
| Registration Act s. 23 — time limit for presentation | ingested text verified ("within four months from the date of its execution"); retrieved at rank 1 (cos 0.707); answer cites s. 23 |
| Transfer of Property Act s. 54 — sale | text verified ("a transfer of ownership in exchange for a price paid or promised"); rank 1 (0.705); cited |
| Consumer Protection Act s. 69 — limitation | text verified ("within two years from the date on which the cause of action has arisen"); rank 1 (0.700); cited |
| Out-of-corpus question ("How do I apply for a passport?") | abstained without calling the LLM (top score 0.53 < 0.60) |
| Re-running ingest and index over unchanged sources | 0 manifest rows, 0 chunks, 0 vectors added (corpus hash unchanged) |
| Splitter, schema-validation and citation-stripping tests on real fixtures | pass (`tests/unit/`, fixtures in `tests/fixtures/` with source URL and sha256) |
| Corpus profile: every required field green | PASS |
| First gold questions | 11 drafted in `evaluation/gold.jsonl`, **all unverified** (see "Needs you") |

Parser quality on the real corpus: the Acts match their Arrangement of Sections exactly (96/96, 147/147, 107/107 sections); 145 state-amendment blocks separated into 157 state-jurisdiction chunks (12 states); 225 footnotes captured into `amendment_notes`; all 50 judgments parse, most with complete paragraph numbering.

## Environment
- `C:\dev\praetor-ai`, own git repo on `main`. Python 3.12.13 (uv) in `.venv`; torch 2.14.0+cu130, sentence-transformers 6.1, faiss-cpu 1.15.1, SQLite 3.50.4 + FTS5.
- RTX 5070 Laptop, **8 GB** (DECISIONS D8). Ollama 0.34.2 with `qwen3.5:4b` (Phase 1 answer model, 100% GPU, warm answers 7–14 s) and `gemma4:e2b-it-qat` (benchmark candidate).
- Local `.env` (gitignored) copied from `.env.example`; sets `OLLAMA_MODEL=qwen3.5:4b`.
- The old copy at `C:\Users\DELL\OneDrive\Desktop\Praetor AI` is no longer used and can be deleted.

## Known limitations
- Retrieval is dense-only; no keyword search, exact statute lookup, fusion or reranker yet (Phase 2).
- The evidence gate uses the top dense cosine with a provisional threshold of 0.60 set from 7 queries (D11); calibrate in Phase 2.
- Validator v1 strips unknown IDs and non-verbatim quotes, but doesn't yet scan for unverified section numbers or case names. Example checked by hand: an answer's "Section 8 of the Transfer of Property Act" came from cited judgment text (grounded), but nothing enforces that automatically yet.
- Some judgment PDFs have run-together words in their text layer (`inunambiguousterms`, `oftransfer`), and a few older ones carry an OCR text layer with recognition errors (`pres(;Jnt`). These are indexed as-is.
- Paragraph numbering is lost partway through some judgments, and those chunks are located by page instead (D15): 361 of 1,321 judgment chunks across 18 judgments, most in 4 long ones (Neena Aneja 99, Veena Singh 61, Manik Majumder 39, Texco Marketing 28).
- The source PDFs themselves contain typos that are kept verbatim (e.g. "a copy a of a decree" in Registration Act s. 23, "Duites" in a Part heading).
- One TPA chapter heading ("Chapter IV") lost its title line; cosmetic.
- `retrieved_at` is UTC, so files fetched at 04:xx IST show the previous date (2026-09-22).
- Hindi queries retrieve the right English sections (cross-lingual bge-m3), but answers are English and query language is reported as `und-Deva` until a language-ID model is chosen.

## Risks
- 8 GB VRAM caps local answer models at the 2–4B class; the Day 3 Bedrock comparison matters.
- India Code moved domains in 2026 (V11), watermarks downloads (V16), and its terms page isn't located (V15).
- The home-directory git repo at `C:\Users\DELL` (origin `Harshiee09/GenentAi`) still has private files untracked inside it. Not touched.

## Deferred
- **Tesseract OCR** (D9): needs an admin install. Pages needing OCR are rejected and logged; none in the current corpus.
- **Download contact address:** `HTTP_USER_AGENT` has no contact; add one in `.env` if you want sites to be able to reach you.
- **India Code terms of use** (V15).

## Needs you
1. **Verify the 11 draft gold questions** in `evaluation/gold.jsonl`: check each expected section and `must_mention` against the ingested text, then set `verified_by` / `verified_on`. The Hindi question (`hi-reg-023-time-limit`) needs a Hindi speaker. `cpa-034-district-pecuniary` cites the Act's one-crore figure, but the Act lets the Central Government prescribe other values, and those rules aren't ingested.
2. Choose the third demo language (Session 4).

## Next step
Phase 2, following `docs/topics/ops/build-plan.md`: statutes.yaml + aliases.yaml for the full seed list (including the criminal-code transition), rule classifier, FTS5 keyword search, exact statute lookup, RRF, bge-reranker-v2-m3 and the evidence gate, context status headers, full validator, corpus expansion, gold set to 40–60, `praetor eval`, local-model benchmark.
