# PRAETOR AI — status

_Last updated: 2026-09-24 · **Phases 0–2 done** (Phase 2 gates pass on draft gold data) · next: Phase 3 (AWS, **waiting for your go-ahead**)_

## Resume here (next session)
Phase 2 is complete and committed (`phase-2: wrap-up — integration tests and final eval`): 11/11 integration tests, final eval on all 59 questions with `gemma4:latest` (`evaluation/reports/20260924T002232Z`), 0 invalid citations after validation.
Before Phase 3, decide whether to fix the jurisdiction-line quote issue first (see "Known limitations"; a prompt change needs one more eval run). Do not start Phase 3 or touch AWS until the user says go.
Uncommitted local-only file: `.env` (gitignored; `OLLAMA_MODEL=gemma4:latest`, `MIN_EVIDENCE_SCORE=0.10`).

## What works (with the command that proves it)
All commands run from `C:\dev\praetor-ai` as `uv run <command>`.

| Capability | Command | Result (2026-09-24) |
|---|---|---|
| Unit tests | `pytest -m "not integration"` | 56 passed |
| Integration tests (real corpus, GPU) | `pytest -m integration` | 11 passed in 83 s (Phase 1 set 5, Phase 2 set 6), Ollama idle |
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
| Invalid citations after validation | 0 | 0 on every one of the 59 questions (53 answered) with `gemma4:latest`, checked per row; also 0 for each of 3 models on the dev split — **pass** |
| Out-of-corpus questions abstained | ≥ 4 of 5 | 5 of 5 (1 false abstention of 54 answerable) — **pass**, threshold chosen after seeing all scores (D27) |

### Retrieval ablation (all 59 questions, 54 answerable; report `evaluation/reports/20260923T232023Z.md`, reproduced exactly by the final run `20260924T002232Z`)
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
`uv run praetor eval --split all`, `gemma4:latest`, `MIN_EVIDENCE_SCORE 0.10`, 2026-09-24; report `evaluation/reports/20260924T002232Z.md` (per-question rows in the `.json`).

| Metric | All (n=59) | dev (n=30) | test (n=29) | Hindi (n=5) |
|---|---|---|---|---|
| Answered | 53 | 26 | 27 | 5 |
| **Invalid citations after validation** | **0** (checked per row: 0 on all 59) | 0 | 0 | 0 |
| Answers with a citation | 100% | 100% | 100% | 100% |
| Invalid IDs removed by the validator | 4 (one answer cited S10, S11, S14, S16 with 8 sources given) | 0 | 4 | 0 |
| Unverified-authority removals | 1 (`section 438` in `tr-438-anticipatory`) | 0 | 1 | 0 |
| Unsupported-sentence flags | 10 | 5 | 5 | 0 |
| Stricter regenerations / extractive fallbacks | 4 / 1 (`tpa-105-lease`: both attempts 50% unsupported) | 0 fallbacks | 1 fallback | 0 |
| Must-mention hit | 95% (n=43) | 90% (n=21) | 100% (n=22) | — |
| Expected source cited | 92% (n=53) | 92% (n=26) | 93% (n=27) | 80% (n=5) |
| Regime note on criminal-transition questions | 100% (n=5) | | | |
| Latency p50 / p95 (model answers) | 11.5 / 15.9 s | 11.3 / 15.9 s | 12.1 / 14.3 s | 10.0 / 11.4 s |
| Mean tokens in / out | 3,560 / 393 | | | |
| Abstention | 5 of 5 out-of-corpus; 1 false (`hs-eviction-tomorrow`) | | | |

Misses: must-mention `tpa-106-lease-notice` (the sentence with "fifteen days" quoted the Act with an ellipsis and was removed as non-verbatim; it passed in the dev benchmark, so generation varies run to run) and `rera-018-refund` ("interest" not mentioned, s. 18 not cited). Expected source not cited: `rera-018-refund` and three BNSS s. 482 questions (`proc-bnss-482-anticipatory`, `hi-bnss-482-anticipatory`, `tr-438-anticipatory`): the known BNSS s. 482 limitation below.
Confidence: 56 of 59 answers are `low` because of the jurisdiction-line issue below, so the confidence level does not yet discriminate.

## What changed in Phase 2
- **Registries:** `statutes.yaml` (18 entries, every one with source URL, date and evidence; commencement dates and the BNS s. 106(2) exception from the Acts' own footnotes), `aliases.yaml` (an alias names one Act; search expands to successors), `jurisdictions.yaml`.
- **Retrieval:** rules classifier; FTS5 keyword search with sanitised queries and an Indic-safe tokenizer; exact lookup for sections and CPC rules; statute quota, Act-scoped search, case-name lookup, transition pin; RRF; bge-reranker-v2-m3; final order RRF(fused, rerank); rerank evidence gate (0.10).
- **Grounding:** full validator (authority scan for sections, Acts with years, case names and reporter citations; verbatim quotes; unsupported-sentence check with one stricter regeneration then the extractive fallback); deterministic high-stakes block, criminal-transition note, repeal notes; confidence levels.
- **Parsing:** CPC Orders and rules (`O. XXXIX r. 1`), appendices, Statement of Objects and Reasons dropped, table of contents read from "Arrangement of Sections"; OCR-garbled judgment markers; "In re" titles; memory-safe parsing of 300-page PDFs; parallel parsing.

## Known limitations
- **Jurisdiction line removed and confidence stuck at "low" (found 2026-09-24, not fixed).** `app/rag/prompts/answer_system.md:21` asks for `"based on texts retrieved on <date>"` in quotation marks; the model copies the quotes, the verbatim-quote check doesn't find that phrase in any source and removes the whole "Jurisdiction and date" line (45 of 53 answers in the final eval, 24 of 30 in the dev benchmark). The removal counts as an unverified quote, so `ValidationResult.changed` is true and `confidence = "low"` (`app/rag/pipeline.py:196`): 56 of 59 answers are low, and for 31 of the 52 model answers that line is the only reason. Citations are unaffected. Fix: drop the quotation marks from the prompt (new prompt version) or skip quote checks on that line, then re-run the eval.
- **Quotes with an ellipsis** (`"a lease... shall be deemed"`) fail the verbatim check and the sentence is removed; splitting quotes at `...` and checking each part would keep them.
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
2. **Jurisdiction-line fix:** approve a small prompt/validator fix plus one eval re-run (~15 min) before Phase 3, or defer it to Phase 4 polish.
3. **Phase 3 go-ahead:** AWS work needs the `praetor` profile, a look at your credit balance and eligible services, and your explicit "go" before anything is created.
4. Choose the third demo language (Phase 4).

## Next step
Phase 3 (`KICKOFF_PROMPT.md`, Session 3): read-only AWS checks, a costed resource list for your approval, then the stack, `s3-sync`, the Bedrock client behind the cost meter, and a local-versus-Bedrock comparison.
