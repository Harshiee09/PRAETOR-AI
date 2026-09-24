# PRAETOR AI — status

_Last updated: 2026-09-24 · Phases 0–2 done · **post-Phase 2 audit: repairs in code and unit-tested, end-to-end verification BLOCKED by Windows Smart App Control (torch cannot load)** · Phase 3 (AWS) waiting for your go-ahead_

## Resume here (next session)
1. **Blocker (needs you):** since 09:18 on 2026-09-24, Windows Smart App Control blocks the uv Python from loading `torch\lib\caffe2_nvrtc.dll` (`WinError 4551`, DECISIONS V37), and also blocks the `praetor.exe` launcher that uv generates (`uv run python -m app.cli <cmd>` runs the same CLI). Without torch there is no embedding or reranking, so `ask`, `eval` and 8 of 11 integration tests cannot run. The fix is a Windows security decision for you (see "Needs you"); nothing in the project was changed to get around it.
2. When torch loads again, run in this order, one GPU job at a time, with Ollama idle between steps:
   - `uv run pytest -m integration` (expect 11; compare with 11/11 before the audit)
   - `uv run python scripts/trace_stages.py evaluation/reports/diagnostics/20260924_stage_trace_after.json` (compare with `..._before.json`: is BNSS s. 482 in context for the three bail questions, RERA s. 18 for the refund question; does the eviction question pass the gate?)
   - `uv run python scripts/repeat_answers.py tpa-106-lease-notice rera-018-refund proc-bnss-482-anticipatory --runs 5` and the same with `--temperature 0.1 --no-seed` (Phase 2 decoding), to show where variation starts
   - `uv run praetor eval --split all` (~15 min) → fill "Answer metrics after the audit" below; confirm 0 invalid citations on all 59; report the dev and test slices separately
   - `uv run praetor index` once: bootstraps the new `vectors` table from the audited index (V33) and should add 0 chunks
3. Then commit on the audit branch and merge only if the numbers hold.
Uncommitted local-only file: `.env` (gitignored; `OLLAMA_MODEL=gemma4:latest`, `MIN_EVIDENCE_SCORE=0.10`; new settings `LLM_TEMPERATURE` / `LLM_SEED` default to 0 / 42).

## AWS setup (you, in parallel; DECISIONS D43)
Run `infra\aws_setup.cmd` from CMD in the repo and follow the menu in order: 1 profile → 2 pre-flight → 3 choose model → 4 budget → 5 bucket and policy → 7 `.env` lines (6 only if the profile is an IAM user). Steps 4–6 need you to type YES; nothing invokes Bedrock. Send me `data\scratch\aws\setup_*.log` afterwards so I can record the account checks, the chosen model and its prices in DECISIONS.md and `app/config/prices.yaml`. Remove everything later with `infra\aws_teardown.cmd`. The Bedrock client, cost meter and `s3-sync` are Phase 3 code and wait for your "go".

## What works (with the command that proves it)
All commands run from `C:\dev\praetor-ai` as `uv run <command>`.

| Capability | Command | Result |
|---|---|---|
| Unit tests | `pytest -m "not integration"` | **87 passed** (2026-09-24, after the audit; 56 before) |
| Integration tests (real corpus, GPU) | `pytest -m integration` | before the audit: 11 passed. After: 3 passed (parser, CPC Order split, BNS s. 106 status); 8 fail at `import torch` (Smart App Control), not on assertions |
| Corpus | `praetor ingest --source indiacode --phase 2` · `praetor ingest --source sc-judgments --years 2016-2025 --limit 1000 --via tar` | 12 central Acts + 1,000 SC judgments |
| Index | `praetor index` | 1,012 documents → 27,560 chunks (3,725 statute, 23,835 judgment); every FAISS vector re-checked against a fresh embedding on 2026-09-24 (min cosine 0.99976, V33) |
| Corpus profile gate | `praetor profile` (now `python -m app.cli profile`) | every required field 100% → **PASS** (re-run 2026-09-24 after the audit; only the timestamp changed) |
| Ask with per-stage ranks | `praetor ask "question" --explain` | now also prints term expansions, the rewrite, statute slots and decoding (not run since the block) |
| Stage trace | `python scripts/trace_stages.py OUT.json` | before-audit trace saved: `evaluation/reports/diagnostics/20260924_stage_trace_before.json` |
| Evaluation | `praetor eval [--no-llm] [--calibrate] [--split dev|test] [--model NAME]` | reports now carry a `run` block (commit, hashes, prompt, model digest, decoding), an "in context" metric and dev/test/Hindi answer slices |
| Verification sheet | `python scripts/make_verification_sheet.py` | `evaluation/verification_sheet.csv`, 59 rows, every expected source found in the index |

### Phase 2 results (before the audit) — **exploratory**
All numbers in this section come from 59 **unverified draft** questions that were all seen during development, with an evidence threshold chosen after seeing every score (D27). They are regression baselines, not validated accuracy (D38).

| Gate | Target | Result (2026-09-24, before the audit) |
|---|---|---|
| Hybrid + rerank beats dense-only on Recall@5 | > dense | 0.89 vs 0.83 (n=54) |
| Statute-lookup Recall@5 | ≥ 0.8 | 0.91 (n=22) |
| Invalid citations after validation | 0 | 0 on all 59 (53 answered), checked per row |
| Out-of-corpus questions abstained | ≥ 4 of 5 | 5 of 5 (1 false abstention of 54) |

Retrieval ablation (report `evaluation/reports/20260924T002232Z.md`): dense R@5 0.83 · keyword 0.44 · hybrid 0.85 · hybrid + rerank 0.89 · full 0.91 (MRR 0.84); English 0.92 (n=49), Hindi 0.80 (n=5).
Answers (`gemma4:latest`, same report): 53 answered, 0 invalid citations, 100% cited, 1 extractive fallback, 1 authority removal, must-mention 95% (n=43), expected source cited 92% (n=53), p50 11.5 s; 56 of 59 answers `low` confidence because of the jurisdiction-line bug (fixed below).

### Answer metrics after the audit
**Not run: blocked** (see "Resume here"). What was verified without torch:
- Validator replay on the 52 saved model answers of `20260924T002232Z` (no GPU): jurisdiction-line removals 45 → 0 (the system now writes that line); 31 answers lose their only reason for `low` confidence; first attempts that would trigger a stricter regeneration under the extended unsupported-claim rule 2 → 1, none newly triggered.
- Unit tests of every repair (below), on real statute excerpts (BNSS ss. 482 and 531, TPA s. 106, RERA s. 18 fixtures) and a verbatim judgment excerpt.

## The 2026-09-24 audit (DECISIONS D35–D42, V29–V37)
### Reported failures: first stage where the authority is lost, and the repair
| Failure | First loss (traced) | Repair (code) | Verified so far |
|---|---|---|---|
| Anticipatory bail omits BNSS s. 482 (3 questions) | EN: reranker scores s. 482 0.025 (it never says "anticipatory"), final rank 12, outside the 8 context places; HI: first-stage retrieval (dense rank 715); s. 438 CrPC: transition pin picks another BNSS section, reranker 0.002 | term expansion to the statute's wording ([legal_terms.yaml](../data/registry/legal_terms.yaml)) in dense, keyword, pin and reranker ([hybrid.py](../app/retrieval/hybrid.py)); context statute slots ([context.py](../app/rag/context.py)); act-aware section check so "s. 482 CrPC" can never borrow BNSS s. 482 ([validator.py](../app/citations/validator.py)) | unit tests; end-to-end pending |
| RERA refund omits s. 18 and interest | s. 18 top statute hit (fused 7) dropped to final 12 by the reranker | statute slots; "home buyer" → allottee/promoter; prompt `answer-v3` asks, under "How it may apply", for the conditions and alternatives the sources state (s. 18(1) distinguishes an allottee who withdraws — return of the amount with interest and compensation — from one who stays — interest for every month of delay) and forbids outside knowledge, so no fixed rate (s. 18 says "as may be prescribed", i.e. by state rules, which are not ingested) | unit tests; end-to-end pending |
| Eviction question refused | evidence gate: TPA s. 106 is S1 but the top rerank score is 0.025 < 0.10 | eviction / landlord-tenant term expansion; high-stakes abstention now lists the facts that matter (state, written agreement, rent period, notice dates) and shows the closest statute text verbatim as unconfirmed, without the LLM; tenancy note that no state rent law is ingested; harmful-request refusal added (it did not exist) | unit tests (12 refusal cases); end-to-end pending |
| Lease notice passes once, fails later | not retrieval (s. 106 is S1 at every stage): sampling (temperature 0.1, no seed) plus the quote check rejecting an ellipsis quote | greedy decoding with seed 42; ellipsis-aware quote check; `repeat_answers.py` to measure | unit tests; repeated runs pending |
| Jurisdiction line and "low" confidence | prompt v2 asked for a quoted phrase the quote check then removed | line rendered from metadata; prompt `answer-v3` | replay: 45 → 0 removals |

### Other defects found and fixed
- **Act-title keyword phrases never matched** when the title contains a stop-word ("transfer property act 1882": 0 hits vs 260) — fixed in [keyword.py](../app/retrieval/keyword.py).
- **FAISS/SQLite drift risk:** a reused rowid kept an old vector for new text (test fails on the old code) — `vectors` hash table in [index.py](../app/embeddings/index.py).
- **Silent duplicate drops** are now recorded in `rejects`; **page provenance** is enforced for PDF text ([schema.py](../app/chunking/schema.py)).
- **Validator logs** no longer contain model text (it can echo personal data).
- **Gold set:** paraphrase groups added; 4 questions moved so no group straddles dev/test; loader refuses a straddle.

### Sources compared (nothing new ingested; see the data-sources note)
BNSS ss. 482/531 match the Gazette; TPA s. 106 indexed wording is current (the alternate `tpa.pdf` is pre-2003, rejected); RERA s. 18 identical across copies; no reachable official CrPC text as in force on 30 June 2024 (all candidates lack s. 438(4)); Hindi TPA/BNSS need OCR; no state rent law without a named state.

## Known limitations
- **End-to-end effect of the repairs is unmeasured** until torch loads again.
- **Gold set unverified**; all percentages exploratory; no human-verified holdout exists, so no validated accuracy can be claimed.
- **CrPC text not ingested** (D20, D42): old-law answers rely on judgments and the BNSS repeal/savings section 531.
- **Term expansions** were chosen after seeing failures; their Hindi entries are unverified; the list is small (4 concepts).
- **Hindi:** no Hindi text indexed; answers are in English.
- **No state law** (rent control, RERA rules with the prescribed interest rate): answers must say so.
- **No answer cache** (`CACHE_ENABLED` has no effect yet).
- **Refusal rule** is a narrow regex (high precision, limited recall); it is not a general safety classifier.
- Judgment locators: 36% by page; 8 chunks over 450 tokens.
- Not built (cut list #2): LLM classification / query rewriting; soft domain filter.
- Privacy for Phase 3: the retrieval spec's redaction (Aadhaar/PAN/mobile/email regexes) is not implemented yet and would not cover names or addresses; judgment text in the context contains party names. Must be settled before any Bedrock call.

## Environment
- `C:\dev\praetor-ai` (git; audit work on branch `audit-2026-09-24`); Python 3.12 venv; torch 2.14.0+cu130 (currently blocked from loading, V37); RTX 5070 Laptop 8 GB. Ollama 0.34.3 (auto-updated from 0.34.2 on 2026-09-24), `gemma4:latest` = `c6eb396dbd59`. Run only one GPU job at a time (D34).
- Disk: data/raw 0.40 GB, data/processed 0.13 GB, data/indexes 0.11 GB.

## Deferred
- **Tesseract OCR** (D9): needed for 2 CPC image pages and for the official Hindi TPA / BNSS PDFs (V35).
- **Download contact address** in `HTTP_USER_AGENT`; **India Code terms of use** (V15).
- **Answer cache** (Phase 4 API).

## Needs you
1. **Smart App Control (blocks all end-to-end runs).** Options: (a) turn it off in Windows Security → App & browser control → Smart App Control — check Microsoft's current documentation first, because on the Windows versions I know of it cannot be turned back on without reinstalling Windows; (b) keep it on and run the GPU parts elsewhere (e.g. WSL2 with CUDA, a larger setup change), or (c) wait and retry in case the block was a reputation lookup that clears. I have not changed any system setting.
2. **Verify the gold set** with `evaluation/verification_sheet.csv` (Hindi rows need a Hindi speaker), and ideally write a fresh holdout of 20–30 questions that nobody on the build side sees before it is frozen.
3. **Confirm the Hindi term** अग्रिम जमानत (and बेदखल, किरायेदार, मकान मालिक) in `data/registry/legal_terms.yaml`.
4. **CrPC text:** if you can obtain the official consolidated CrPC as in force on 30 June 2024 (e.g. from the Legislative Department), it can be ingested as `repealed` with the BNSS s. 531 savings rule; none was reachable today.
5. **Phase 3 go-ahead:** unchanged — nothing on AWS until you say go.
6. Choose the third demo language (Phase 4).

## Next step
Clear the Smart App Control blocker, run the checks in "Resume here", then decide on merging the audit branch. Phase 3 only after your "go".
