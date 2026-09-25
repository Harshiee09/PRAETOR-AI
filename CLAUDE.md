# PRAETOR AI — project memory for Claude Code

PRAETOR AI is an India-focused **informational** legal-assistance RAG system. It is not a lawyer.
Goal: a working, demoable MVP in 3 days on one local RTX 5070 Laptop GPU (8 GB VRAM, see DECISIONS D8).
Everything runs locally; no AWS (D47). The frontend is built separately and deployed on Vercel; it calls the local API (`praetor serve`).

Knowledge base (read the index, then open only the notes the task needs): @docs/INDEX.md
Live state: `docs/STATUS.md` (what works now) · `docs/DECISIONS.md` (dated decisions and verifications)

## Non-negotiables
1. **No invented authority.** The model may cite only the context IDs it was given (`[S1]`, `[S2]` …). Citation text shown to users is rendered from stored chunk metadata, never from model output. Unknown IDs are stripped; section numbers, case names or reporter citations that don't appear in the retrieved context are removed and logged. Spec: `docs/topics/legal/grounding-and-citations.md`.
2. **Abstain when evidence is thin.** If retrieval confidence is below `MIN_EVIDENCE_SCORE`, return an "insufficient sources" answer without calling the LLM.
3. **Provenance or it isn't indexed.** Every chunk carries the required fields in `docs/topics/architecture/chunk-schema.md`; ingestion rejects chunks that don't.
4. **Law changes over time.** `data/registry/statutes.yaml` is the source of truth for in-force/repealed status (the IPC, CrPC and Evidence Act were replaced by the BNS, BNSS and BSA from 2024-07-01). Answers that rely on repealed law must say so.
5. **No fakes.** No mock services presented as working, no invented datasets, case names or placeholder citations. Test fixtures are real excerpts saved with their source URL. If a dependency is unavailable, fail loudly or use the clearly labelled `extractive` fallback.
6. **Secrets and personal data.** Configuration comes from environment variables only. Never commit `.env`, credentials, raw user queries, downloaded corpora or model weights. Nothing is sent to a cloud service; logs store query hashes by default; the API key never goes into browser code.
7. **Verify, don't assume.** Hosting limits, model IDs, dataset licences, URLs and API shapes are checked against docs, the CLI or one real call, and recorded with the date in `docs/DECISIONS.md`.
8. **No paid services, small repo.** Nothing calls a paid API or creates cloud resources; never spend money without my explicit go-ahead in chat. The GitHub repository stays under 10 MB (`tests/unit/test_repo_size.py`).

## Stack (change only with a dated entry in docs/DECISIONS.md)
- Python 3.11+, FastAPI, pydantic-settings, SQLite, pytest, `regex`. No LangChain or LlamaIndex.
- PyTorch from a CUDA 12.8+ wheel index (the RTX 50-series is Blackwell). Prove `torch.cuda.is_available()` and a real GPU op before installing anything that depends on torch.
- Embeddings: `BAAI/bge-m3` via sentence-transformers, L2-normalised, 1024-d, into FAISS `IndexIDMap2(IndexFlatIP)` with **faiss-cpu** (the GPU embeds; exact search on CPU is fast enough at MVP scale).
- Keyword search: SQLite FTS5 `bm25()` in the same database as chunk metadata. Fusion: reciprocal rank fusion.
- Reranker: `BAAI/bge-reranker-v2-m3` via sentence-transformers `CrossEncoder`.
- LLM behind `app/llm/base.py`: `ollama` (local), `extractive` (no-LLM fallback).
- HTTP API: FastAPI + uvicorn, local only (`praetor serve`); contract in `docs/api/openapi.json`.
- PDF text: pdfplumber / pypdfium2. PyMuPDF is AGPL: don't add it without a DECISIONS.md entry.
- OCR: Tesseract with Indic traineddata, only for pages without a usable text layer.
- Language ID: Unicode script first, statistical LID second; all 22 scheduled languages live in `app/multilingual/languages.yaml`.

## Repo map (keep current)
```text
app/          api/ ingestion/ parsing/ ocr/ chunking/ embeddings/ retrieval/ reranking/
              rag/ llm/ citations/ multilingual/ store/ config/ documents/ (uploads, D50) cli.py
data/         raw/ processed/ indexes/   (gitignored)
              registry/                  (committed: statutes.yaml, aliases.yaml, sources.yaml, jurisdictions.yaml)
evaluation/   gold.jsonl  reports/
scripts/      one-off utilities only; real entry points live in app/cli.py
tests/        unit/  integration/ (marked; may need GPU or network)  fixtures/ (real excerpts + source URL)
docs/         INDEX.md  STATUS.md  DECISIONS.md  api/ (openapi.json, examples/)  reports/  sources/  topics/
frontend/     Next.js app for Vercel (Ask, Your document, About); see frontend/README.md
praetor.cmd   runs the CLI through Python if Windows blocks the praetor.exe launcher (V45)
```

## Commands (the CLI is created in Phase 0; keep this table accurate)
`praetor <cmd>` is the console script from `pyproject.toml`; run it as `uv run praetor <cmd>` (or activate `.venv`). Setup: `uv sync`.

| Task | Command |
|---|---|
| GPU and model smoke test | `praetor gpu-check` |
| Download sources | `praetor ingest --source indiacode --phase 2` · `praetor ingest --source sc-judgments --years 2016-2025 --limit 1000 --via tar` (`--dry-run` to preview) |
| Parse, chunk, embed, index (incremental; `--force` re-processes all; `--workers 2` if RAM is short) | `praetor index` |
| Corpus data profile | `praetor profile` |
| Ask from the terminal (`--mode dense|keyword|hybrid|hybrid_rerank|full`) | `praetor ask "question" --explain` |
| Run the API · export its contract | `praetor serve` (localhost:8000, docs at `/docs`) · `praetor openapi` |
| Evaluation: ablation + abstention (`--no-llm`), answers, gate sweep, model benchmark | `praetor eval [--split dev|test] [--no-llm] [--calibrate] [--model NAME]` |
| Tests | `pytest -m "not integration"` · `pytest -m integration` |
| Phase 1 acceptance | `python scripts/phase1_acceptance.py` · fixtures: `python scripts/make_fixtures.py [NAME ...]` |
| Demo (server running) | `python scripts/demo.py` · documents: `python scripts/demo_documents.py A.pdf [B.pdf]` |
| Cloud API on AWS (D58) | `scripts\aws_server.cmd status|start|stop` · https://3-111-113-83.sslip.io |
| Public demo: whole app, one link | `scripts\serve_app_public.cmd` (API tunnel only, for Vercel: `scripts\serve_public.cmd`) |
| Diagnostics | stage ranks: `python scripts/trace_stages.py OUT.json` · run-to-run variation: `python scripts/repeat_answers.py ID --runs 5` · gold review sheet: `python scripts/make_verification_sheet.py` |

## Working agreement
- Inspect before editing. Reuse working code; don't rewrite it without a reason recorded in DECISIONS.md.
- Work phase by phase from `docs/topics/ops/build-plan.md`: implement, run tests, run the phase's acceptance check, update `docs/STATUS.md`, commit as `phase-N: <what changed>`.
- Keep modules independently testable. Unit tests may stub network clients (e.g. botocore `Stubber`); integration tests hit the real service and carry the `integration` marker.
- Ask me before: installs that need admin rights, downloads over 2 GB, creating cloud resources or spending money, deleting anything outside `data/` scratch folders, and legal or data questions you can't settle from sources.
- If something non-essential blocks you for more than about 30 minutes, log it under "Deferred" in STATUS.md, take the simpler path and keep going.
- Keep this file under 200 lines. New detail goes into a KB note registered in `docs/INDEX.md`.
