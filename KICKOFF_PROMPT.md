# PRAETOR AI — Claude Code session prompts

## Before you start (for you, not for Claude)
1. Unzip the kit into your project root so `CLAUDE.md` and `docs/` sit at the top level. If the repo already has a `CLAUDE.md`, merge the two rather than overwriting.
2. Open a terminal in the project root and start Claude Code. `CLAUDE.md` loads automatically and pulls in `docs/INDEX.md`.
3. Paste **Session 1**. Review the plan it gives you, then reply "approved" (or correct it first).
4. Between phases, start a fresh conversation (`/clear`) and paste the next session prompt. The knowledge base and `docs/STATUS.md` carry context across sessions.
5. Have ready: admin rights for installs, a Hugging Face token only if a gated model is chosen, and for Day 3 an AWS named profile `praetor` plus access to the Billing console.
6. Fill in your third demo language in Session 4.

---

## Session 1 — inspect, plan, then build Phase 0 and Phase 1

You are the lead engineer for PRAETOR AI, an India-focused informational legal-assistance RAG system. Ship a working, demoable MVP in 3 days on this machine (RTX 5070, 12 GB VRAM) with about $50 of AWS credits. Local-first: use AWS only where it clearly adds value. Optimise for a functioning demo, not a theoretical production architecture. Write code and verify it; don't spend the session describing architecture.

Load context first:
- `CLAUDE.md` and `docs/INDEX.md` are already loaded. Now read these notes in full: `docs/topics/data/report-validation.md` (the original research reports contain errors; never reintroduce them), `docs/topics/architecture/minimum-viable-architecture.md`, `docs/topics/ops/build-plan.md` (Phases 0 and 1), and `docs/topics/architecture/chunk-schema.md`.
- Open other notes only when a task needs them.
- If `CLAUDE.md` or `docs/INDEX.md` is missing, stop and tell me the kit isn't installed.

Step 1 — inspect, read-only, change nothing:
- Repository: tree, languages, dependencies, entry points, tests, any existing ingestion, parsing, retrieval or LLM code, data folders, git status. If it isn't a git repository, tell me and I'll decide about `git init`.
- Environment: OS (Linux, WSL2 or Windows), Python version, `nvidia-smi` driver and CUDA version, installed torch and its CUDA build, free disk space, and whether Ollama, Tesseract (with which language packs), the AWS CLI and a `praetor` profile exist. Never print secrets.

Step 2 — report and plan:
- Write `docs/STATUS.md`: what exists, what actually works when run, gaps against the minimum viable architecture, and risks.
- Give me a short plan (at most 20 bullets) covering Phases 0 and 1: what you'll reuse versus write, files to create or change, install commands for this OS, and exactly what you need from me.
- Stop and wait for my approval. This is the only planned checkpoint.

Step 3 — after I approve, build without further check-ins:
- Implement Phase 0, then Phase 1, as the build plan specifies. After each milestone: run the tests, run the acceptance check, fix failures, update `docs/STATUS.md`, commit.
- Stop early only for the "ask me before" items in `CLAUDE.md` or a genuine blocker.

Rules that matter most today:
- Real data only. The Phase 1 corpus is 3 Acts from India Code (Registration Act 1908, Transfer of Property Act 1882, Consumer Protection Act 2019) and about 50 Supreme Court judgments from `s3://indian-supreme-court-judgments` (unsigned access). Profile the per-year metadata parquet — row count, columns, null rates — before choosing judgments. Every raw file gets a manifest row: URL, sha256, retrieved_at, licence.
- If a download is blocked (captcha, login, moved URL), don't work around it. Tell me and I'll fetch the file.
- The RTX 50-series needs a PyTorch build for CUDA 12.8 or newer. Prove the GPU works before installing anything that depends on torch.
- Citations come from metadata, never from model text. No LangChain or LlamaIndex. No AWS resources in this session.
- Test the section and paragraph splitters against real excerpts saved in `tests/fixtures/` with their source URL.

When Phase 1 is done, report in this format: 1) what was implemented, 2) what works, with the command that proves it, 3) what remains, 4) how to run it, 5) environment variables added, 6) known limitations, 7) next step.

---

## Session 2 — Phase 2: legal intelligence

Continue PRAETOR AI. Read `docs/STATUS.md`, then `docs/topics/ops/build-plan.md` (Phase 2), `docs/topics/architecture/retrieval-pipeline.md`, `docs/topics/legal/grounding-and-citations.md`, `docs/topics/legal/statute-status.md` and `docs/topics/ops/evaluation.md`.

Build Phase 2 in this order, testing and committing after each step:
1. `data/registry/statutes.yaml` and `aliases.yaml`, every entry verified against its source.
2. Query classifier, rules first.
3. FTS5 keyword search with query sanitisation and a Hindi/Tamil tokenisation test.
4. Exact statute lookup.
5. Reciprocal rank fusion.
6. Reranker and evidence gate.
7. Context builder with provenance and status headers.
8. Full citation validator.
9. Corpus expansion to the seed list plus 300–1,000 judgments.
10. Gold set to 40–60 questions: draft candidates for me to verify; never invent expected answers.
11. `praetor eval` with the ablation table.
12. Benchmark 2–3 local models and record the choice in `docs/DECISIONS.md`.

Stop when the Phase 2 gates pass or you're blocked, and give me the phase report with the eval table.

---

## Session 3 — Phase 3: only the AWS the demo needs

Continue PRAETOR AI. Read `docs/STATUS.md`, `docs/topics/ops/aws-cost-plan.md` and `docs/topics/architecture/llm-layer.md`.

1. Run only read-only, free checks: `aws sts get-caller-identity --profile praetor`, the region, and the Bedrock model and inference-profile listings. Ask me to confirm the credit balance, expiry and eligible services in the Billing console. Don't call the Cost Explorer API; it charges per request.
2. Show me the exact resources you'd create, and for each one the cost driver, why it's needed and the cheaper alternative. Take current prices and model availability from official pricing pages or the CLI, not from memory, and record them with the date. Wait for my "go".
3. Then: the CloudFormation stack (bucket, least-privilege IAM, budget and alerts), `praetor s3-sync push`, the Bedrock client behind the cost meter with its daily cap, one real Bedrock answer through the full pipeline with tokens and cost logged, and a local-versus-Bedrock comparison on 15 eval questions.
4. Recommend which provider to demo, based on the numbers. Build the cloud-lite Lambda only if I ask after seeing the comparison.

Remind me to check the next day that the test call billed under Amazon Bedrock and was offset by credits.

---

## Session 4 — Phase 4: polish, demo, final report

Continue PRAETOR AI. Read `docs/STATUS.md` and `docs/topics/ops/build-plan.md` (Phase 4).

Finish the FastAPI endpoints, error handling, logging, caching, and the multilingual demo (English, Hindi and [YOUR THIRD LANGUAGE]). Write the README from zero to demo, plus a scripted demo of 6–8 queries: a statute lookup, a procedure, case law, the criminal-code transition, a Hindi query, an out-of-corpus question that must abstain, and a high-stakes query. Then follow the README yourself from a fresh clone and fix whatever breaks.

End with the 10-item final report from the build plan, and save it to `docs/STATUS.md` as well.

---

## Utility prompts
- Resume: "Read `docs/STATUS.md` and the current phase of the build plan. Summarise where we are in five bullets, then continue from the next unfinished milestone."
- Data check: "Run `praetor profile`, compare it with the gates in the chunk-schema note, and fix ingestion for any field that isn't green. Show before and after."
- Cost check: "Report today's Bedrock spend from the cost meter, tokens per query, and the projected cost of the demo plus one full eval run."
- Citation audit: "Pick 10 random answers from the last eval run and trace every citation back to its chunk and source URL. Report anything that doesn't match."
