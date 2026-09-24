# PRAETOR AI — status

_Last updated: 2026-09-24 · Phases 0–2 done · **post-Phase 2 audit done and verified end-to-end** on branch `audit-2026-09-24` (not merged) · AWS setup files ready for you · Phase 3 code waiting for your go-ahead_

## Resume here (next session)
1. Review and merge branch `audit-2026-09-24` into `main` if you accept the results below (DECISIONS D35–D46, V29–V42).
2. You: AWS setup with [infra/AWS_SETUP.md](../infra/AWS_SETUP.md); send the log. Then Phase 3 after your "go".
3. You: verify the gold set with `evaluation/verification_sheet.csv` (see "Needs you").
Windows Smart App Control blocked torch and the `praetor.exe` launcher from 09:18 until the afternoon of 2026-09-24 (V37); torch loads again. If it recurs, `uv run python -m app.cli <cmd>` avoids the launcher, but torch itself needs the Windows setting.
Uncommitted local-only file: `.env` (gitignored; `OLLAMA_MODEL=gemma4:latest`, `MIN_EVIDENCE_SCORE=0.10`; `LLM_TEMPERATURE` / `LLM_SEED` default to 0 / 42).

## AWS setup (you, in parallel; DECISIONS D43)
Runbook with checklists and tables to fill: [infra/AWS_SETUP.md](../infra/AWS_SETUP.md). In short: run `infra\aws_setup.cmd` from CMD in the repo and follow the menu in order: 1 profile → 2 pre-flight → 3 choose model → 4 budget → 5 bucket and policy → 7 `.env` lines (6 only if the profile is an IAM user). Steps 4–6 need you to type YES; nothing invokes Bedrock. Send me `data\scratch\aws\setup_*.log` afterwards so I can record the account checks, the chosen model and its prices in DECISIONS.md and `app/config/prices.yaml`. Remove everything later with `infra\aws_teardown.cmd`. The Bedrock client, cost meter and `s3-sync` are Phase 3 code and wait for your "go".

## What works (with the command that proves it)
All commands run from `C:\dev\praetor-ai` as `uv run <command>`.

| Capability | Command | Result |
|---|---|---|
| Unit tests | `pytest -m "not integration"` | **91 passed** (2026-09-24, after the audit; 56 before) |
| Integration tests (real corpus, GPU) | `pytest -m integration` | **16 passed** (11 before + 5 new: the four reported failures reach the context, and no guessed successor provision is pinned). One earlier run had a transient parse-worker failure in `test_index_twice_adds_zero_rows` (error not captured); it passed alone and in the final run |
| Corpus | `praetor ingest --source indiacode --phase 2` · `praetor ingest --source sc-judgments --years 2016-2025 --limit 1000 --via tar` | 12 central Acts + 1,000 SC judgments |
| Index | `praetor index` | 1,012 documents → 27,560 chunks (3,725 statute, 23,835 judgment); every FAISS vector re-checked against a fresh embedding on 2026-09-24 (min cosine 0.99976, V33) |
| Corpus profile gate | `praetor profile` (now `python -m app.cli profile`) | every required field 100% → **PASS** (re-run 2026-09-24 after the audit; only the timestamp changed) |
| Ask with per-stage ranks | `praetor ask "question" --explain` | also prints term expansions, the rewrite, statute slots and decoding |
| Stage trace | `python scripts/trace_stages.py OUT.json` | `evaluation/reports/diagnostics/20260924_stage_trace_before.json` and `..._after.json` (13 queries) |
| Repeated runs | `python scripts/repeat_answers.py ID ... --runs 5` | `evaluation/reports/repeat_20260924T092144Z.json` (new decoding), `repeat_20260924T092619Z.json` (Phase 2 decoding) |
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

### Results after the audit — also **exploratory** (same seen questions; the term list was chosen after seeing failures)
Final eval `evaluation/reports/20260924T174231Z.md` (prompt `answer-v3`, temperature 0, seed 42, same index and model digest):

| Metric | Before (20260924T002232Z) | After (20260924T174231Z) |
|---|---|---|
| Retrieval, full: Recall@5 / Recall@10 / MRR (n=54) | 0.91 / 0.93 / 0.84 | **0.96 / 1.00 / 0.85** |
| Expected source among the 8 context blocks | not measured | **1.00** |
| Hybrid + rerank Recall@5 · keyword · dense | 0.89 · 0.44 · 0.83 | 0.94 · 0.46 · 0.83 |
| Out-of-corpus abstained / false abstentions | 5 of 5 / 1 | 5 of 5 / **0** |
| Answered | 53 | 54 |
| **Invalid citations after validation** (checked per row) | 0 | **0** |
| Expected source cited | 92% (n=53) | **98%** (n=54) |
| Must-mention phrases | 95% (n=43) | 95% (n=44)¹ |
| Extractive fallbacks | 1 | 2¹ |
| Jurisdiction lines removed | 45 | **0** |
| Confidence high / medium / low | 3 / 0 / 56 | 26 / 6 / 27 |
| Authority removals | 1 | 6² |
| Latency p50 / p95 · output tokens | 11.5 / 15.9 s · 393 | 13.4 / 19.5 s · 514 |

¹ Both fallbacks were Ollama timeouts during the run (one question took ~60 min wall time); re-run afterwards, both answered normally with the expected source and must-mention phrase. ² 2 correct catches (the model put s. 438 and the CrPC's listed factors under the BNSS), 2 the old rule also makes, 2 costs of the strict act check (judgments saying only "the Code" or "the 1908 Act").

Stage trace (V39): BNSS s. 482 now reaches the context for the English, Hindi and s. 438 CrPC questions; RERA s. 18 for the refund question; the eviction question passes the gate. Repeated runs (V40): identical retrieval context every run; new decoding gives the same output from run 2 on (run 1 differs), Phase 2 decoding 5 different outputs; the required provision is cited in every run under both. All 7 questions naming a repealed Act cite the successor's repeal section.

## The 2026-09-24 audit (DECISIONS D35–D46, V29–V42)
### Reported failures: first stage where the authority is lost, and the repair
| Failure | First loss (traced) | Repair (code) | Verified (see "Results after the audit") |
|---|---|---|---|
| Anticipatory bail omits BNSS s. 482 (3 questions) | EN: reranker scores s. 482 0.025 (it never says "anticipatory"), final rank 12, outside the 8 context places; HI: first-stage retrieval (dense rank 715); s. 438 CrPC: transition pin picks another BNSS section, reranker 0.002 | term expansion to the statute's wording ([legal_terms.yaml](../data/registry/legal_terms.yaml)) in dense, keyword, pin and reranker ([hybrid.py](../app/retrieval/hybrid.py)); context statute slots ([context.py](../app/rag/context.py)); act-aware section check so "s. 482 CrPC" can never borrow BNSS s. 482 ([validator.py](../app/citations/validator.py)); transition pin limited to the repeal section (D44); repeal-first retry (D45) | s. 482 in context for all three; EN and HI answers cite it; the s. 438 answer now leads with the repeal (cites BNSS s. 531) but still does not cite s. 482 — model limitation |
| RERA refund omits s. 18 and interest | s. 18 top statute hit (fused 7) dropped to final 12 by the reranker | statute slots; "home buyer" → allottee/promoter; prompt `answer-v3` asks, under "How it may apply", for the conditions and alternatives the sources state (s. 18(1) distinguishes an allottee who withdraws — return of the amount with interest and compensation — from one who stays — interest for every month of delay) and forbids outside knowledge, so no fixed rate (s. 18 says "as may be prescribed", i.e. by state rules, which are not ingested) | s. 18 cited in every run; withdraw vs stay distinguished; no rate invented |
| Eviction question refused | evidence gate: TPA s. 106 is S1 but the top rerank score is 0.025 < 0.10 | eviction / landlord-tenant term expansion; high-stakes abstention now lists the facts that matter (state, written agreement, rent period, notice dates) and shows the closest statute text verbatim as unconfirmed, without the LLM; tenancy note that no state rent law is ingested; harmful-request refusal added (it did not exist) | now answered from TPA ss. 106 and 111 with the state-law note and safety block; 12 refusal unit cases |
| Lease notice passes once, fails later | not retrieval (s. 106 is S1 at every stage): sampling (temperature 0.1, no seed) plus the quote check rejecting an ellipsis quote | greedy decoding with seed 42; ellipsis-aware quote check; `repeat_answers.py` to measure | variation starts in generation; s. 106 cited and "fifteen days" present in all 10 runs |
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
- **s. 438 CrPC answer:** BNSS s. 482 is in the context (S2) and the answer now leads with the repeal (BNSS s. 531), but `gemma4:latest` still does not cite s. 482 for "anticipatory bail" — a model limitation to re-test with a stronger model in Phase 3's comparison.
- **Strict act check costs some true sentences:** when a judgment says only "Section 438(1) of the Code" or "the 1908 Act", the section cannot be tied to one Act, so a sentence naming the Act is removed (2 in the final eval). Accepted trade-off against carrying a number across Acts (D46).
- **Transition "closest provision" is a similarity guess** and is no longer pinned (D44); for s. 482 CrPC (inherent powers) the BNSS counterpart s. 528 is not surfaced — the answer relies on judgments about the old section.
- **Not bit-for-bit deterministic:** with temperature 0 and seed 42 the first run after loading can differ from later runs (V40); the cited required provisions were stable.
- **Ollama can time out** on a long run (2 of 59 in the final eval); the pipeline then shows verbatim sources (extractive), as designed.
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
- `C:\dev\praetor-ai` (git; audit work on branch `audit-2026-09-24`); Python 3.12 venv; torch 2.14.0+cu130 (was blocked by Smart App Control 09:18 to the afternoon of 2026-09-24, V37; loads again); RTX 5070 Laptop 8 GB. Ollama 0.34.3 (auto-updated from 0.34.2 on 2026-09-24), `gemma4:latest` = `c6eb396dbd59`. Run only one GPU job at a time (D34).
- Disk: data/raw 0.40 GB, data/processed 0.13 GB, data/indexes 0.11 GB.

## Deferred
- **Tesseract OCR** (D9): needed for 2 CPC image pages and for the official Hindi TPA / BNSS PDFs (V35).
- **Download contact address** in `HTTP_USER_AGENT`; **India Code terms of use** (V15).
- **Answer cache** (Phase 4 API).

## Needs you
1. **Merge decision:** review branch `audit-2026-09-24` (results above) and merge it into `main` if you accept it. If Smart App Control blocks torch again, the options are yours (turning it off — check Microsoft's documentation first, since it may not be possible to turn it back on without reinstalling Windows — or running the GPU parts elsewhere); I change no system setting.
2. **Verify the gold set** with `evaluation/verification_sheet.csv` (Hindi rows need a Hindi speaker), and ideally write a fresh holdout of 20–30 questions that nobody on the build side sees before it is frozen.
3. **Confirm the Hindi term** अग्रिम जमानत (and बेदखल, किरायेदार, मकान मालिक) in `data/registry/legal_terms.yaml`.
4. **CrPC text:** if you can obtain the official consolidated CrPC as in force on 30 June 2024 (e.g. from the Legislative Department), it can be ingested as `repealed` with the BNSS s. 531 savings rule; none was reachable today.
5. **Phase 3 go-ahead:** unchanged — nothing on AWS until you say go.
6. Choose the third demo language (Phase 4).

## Next step
Merge the audit branch if you accept it; finish the AWS setup with `infra/AWS_SETUP.md` and send the log; then Phase 3 (Bedrock client behind the cost meter, `s3-sync`, local-versus-Bedrock comparison) after your "go".
